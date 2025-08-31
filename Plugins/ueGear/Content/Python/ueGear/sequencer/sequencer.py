import os
import json

import unreal

from ueGear import helpers, assets
import ueGear.sequencer.bindings as seq_bindings

# Dictionary containing default FBX export options
DEFAULT_SEQUENCE_FBX_EXPORT_OPTIONS = {
    "ascii": True,
    "level_of_detail": False,
}


def get_current_level_sequence():
    """
    Returns the current opened root/master level sequence asset.

    :return: current level sequence.
    :rtype: LevelSequence or None
    """

    return (
        unreal.LevelSequenceEditorBlueprintLibrary.get_current_level_sequence()
    )


def get_subsequence_tracks(sequence: unreal.LevelSequence = None):
    """
    Gets all tracks that are sub-sequence tracks.
    :return: List of MovieSceneSubTrack, that exist in the sequence
    :rtype: [unreal.MovieSceneSubTrack]
    """
    if sequence is None:
        sequence = get_current_level_sequence()

    return sequence.find_tracks_by_exact_type(unreal.MovieSceneSubTrack)


def get_subsequences(track: unreal.MovieSceneSubTrack):
    """
    Gets all sequences that exist in the Sub sequence track.
    :return: List of MovieSceneSequences, that were part of the track.
    :rtype: [unreal.MovieSceneSequence]
    """
    sequences = []

    for section in track.get_sections():
        sequences.append(section.get_sequence())

    return sequences


def get_framerate(sequence: unreal.MovieSceneSequence = None):
    """
    Gets the sequencer's frame rate.
    :return: Frame rate for the specified sequencer. Frames per second.
    :rtype: int | None
    """

    if sequence is None:
        sequence = get_current_level_sequence()

    if sequence is None:
        return None

    return sequence.get_display_rate().numerator


def track_section_to_dict(section):
    """
    Parses given sequence track section and returns a dictionary with the data of the sequence track section.

    :param unreal.MovieSceneSection or unreal.MovieSceneCameraCutSection or unreal.MovieScene3DTransformTrack or unreal.MovieSceneCinematicShotSection section:
            movie scene sequence track section to convert into a dictionary.
    :return: sequence track section dictionary.
    :rtype: dict
    """

    section_type = section.get_class().get_name()
    section_data = {
        "type": section_type,
        "is_active": section.is_active(),
        "is_locked": section.is_locked(),
        "channels": list(),
    }

    for channel in section.get_all_channels():
        channel_data = {
            "name": str(channel.get_editor_property("channel_name"))
        }
        section_data["channels"].append(channel_data)

    if section_type == "MovieSceneCinematicShotSection":
        section_data["name"] = section.get_shot_display_name()
        section_data["range"] = {
            "has_start": section.has_start_frame(),
            "start": section.get_start_frame(),
            "has_end": section.has_end_frame(),
            "end": section.get_end_frame(),
        }
        section_sequence = section.get_sequence()
        if section_sequence:
            section_data["sequence"] = sequence_to_dict(section_sequence)

    elif section_type == "MovieSceneCameraCutSection":
        section_data["range"] = {
            "has_start": section.has_start_frame(),
            "start": section.get_start_frame(),
            "has_end": section.has_end_frame(),
            "end": section.get_end_frame(),
        }

    return section_data


def track_to_dict(track):
    """
    Parses given sequence track and returns a dictionary with the data of the sequence track.

    :param unreal.MovieSceneTrack track: movie scene sequence track to convert into a dictionary.
    :return: sequence track dictionary.
    :rtype: dict
    """

    track_data = {
        "name": str(track.get_display_name()),
        "type": track.get_class().get_name(),
        "sections": list(),
    }

    for section in track.get_sections():
        track_data["sections"].append(track_section_to_dict(section))

    return track_data


def sequence_to_dict(sequence):
    """
    Parses given sequence and returns a dictionary with the data of the sequence.

    :param unreal.MovieSceneSequence sequence: movie scene sequence to convert ito a dictionary.
    :return: sequence dictionary.
    :rtype: dict
    """

    sequence_data = dict()

    for master_trak in sequence.find_master_tracks_by_type(
            unreal.MovieSceneTrack
    ):
        sequence_data["master_tracks"].append(track_to_dict(master_trak))

    for binding in sequence.get_bindings():
        binding_data = {
            "name": str(binding.get_display_name()),
            "id": binding.get_id().to_string(),
            "tracks": list(),
        }

        for track in binding.get_tracks():
            binding_data["tracks"].append(track_to_dict(track))
        sequence_data["bindings"].append(binding_data)

    return sequence_data


def sequence_to_json(sequence):
    """
    Converts given sequence into a JSON compatible serialized string.

    :param unreal.MovieSceneSequence sequence: movie scene sequence to convert ito a dictionary.
    :return: serialized JSON compatible sequence.
    :rtype: str
    """

    return json.dumps(sequence_to_dict(sequence))


def get_bound_objects(sequence: unreal.LevelSequence):
    """
    Returns objects in the current map that are bound to the given sequence.

    :param unreal.LevelSequence sequence: sequence to get bound objects of.
    :return: list of bound objects.
    :rtype: [unreal.Object]
    """

    world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem
    ).get_editor_world()
    sequence_range = sequence.get_playback_range()
    seq_bound_objs = unreal.SequencerTools.get_bound_objects(
        world,
        sequence,
        sequence.get_bindings(),
        sequence_range
    )

    bound_objs = []
    for entry in seq_bound_objs:
        bound_objs.extend(entry.bound_objects)

    return bound_objs


def get_bound_object(track: unreal.MovieSceneBindingProxy, sequence: unreal.LevelSequence = None):
    """
    Queries the active Level Sequencer for the Objects that are bound to 
    the input Track ( MovieSceneBindingProxy ).

    :return: Bound objects that exist on the track input..
    :rtype: [unreal.Object]
    """
    seq_tools = unreal.SequencerTools()
    editor_system = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

    if sequence is None:
        sequence = get_current_level_sequence()

    world = editor_system.get_editor_world()
    range = sequence.get_playback_range()
    seq_bound_objs = seq_tools.get_bound_objects(world,
                                                 sequence,
                                                 [track],
                                                 range)

    bound_objs = []
    for entry in seq_bound_objs:
        bound_objs.extend(entry.bound_objects)

    return bound_objs


def get_selected_cameras():
    """
    Gets the Camera Bindings, from the selected Sequence Tracks.

    :return: Array of Camera bindings.
    :rtype: [unreal.MovieSceneBindingProxy]
    """
    print("    DEBUG: Get Selected Cameras")
    cameras = []

    lvl_seq_bpl = unreal.LevelSequenceEditorBlueprintLibrary

    # Track that is an objects and not an objects attribute.
    bindings = lvl_seq_bpl.get_selected_bindings()

    for binding in bindings:

        if seq_bindings.is_instanced_camera(binding):
            # Instanced Camera
            cameras.append(binding)

        elif seq_bindings.is_camera(binding):
            # Camera
            cameras.append(binding)

    return cameras


def import_fbx_camera(name: str, sequence: unreal.LevelSequence, fbx_path: str):
    """
    Imports the Camera FBX into the specified level sequencer. It overrides the camera that
    exists in the sequence and has a matching name.
    """
    camera_track = None

    # Looks over the Possessables for the correct name
    tracks = sequence.get_possessables()
    for track in tracks:
        if track.get_display_name() == name and seq_bindings.is_camera(track):
            camera_track = track
            break

    # Looks over the Spawnables for the correct name
    if camera_track is None:
        tracks = sequence.get_spawnables()
        for track in tracks:
            if track.get_display_name() == name and \
                    seq_bindings.is_instanced_camera(track):
                camera_track = track
                break

    if camera_track is None:
        unreal.log_error(f"Camera Track `{name}` was not found")
        return

    editor_system = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor_system.get_editor_world()
    fbx_config = unreal.MovieSceneUserImportFBXSettings()
    seq_tools = unreal.SequencerTools()

    fbx_config.set_editor_property("match_by_name_only", False)
    fbx_config.set_editor_property("replace_transform_track", True)
    fbx_config.set_editor_property("create_cameras", False)

    seq_tools.import_level_sequence_fbx(world,
                                        sequence,
                                        [camera_track],
                                        fbx_config,
                                        fbx_path)


def export_fbx_sequence(
        sequence,
        directory,
        root_sequence=None,
        fbx_filename="",
        export_options=None,
):
    """
    Exports a FBX from Unreal sequence.

    :param unreal.LevelSequence sequence: sequence to export.
    :param str directory: directory where FBX sequence will be exported.
    :param str fbx_filename: optional file name for the FBX.
    :param dict export_options: dictionary containing all the FBX export settings to use.
    :return: exported FBX file path.
    :rtype: str
    """

    fbx_path = helpers.clean_path(
        os.path.join(
            directory, "{}.fbx".format(fbx_filename or sequence.get_name())
        )
    )
    world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem
    ).get_editor_world()
    bindings = sequence.get_bindings()
    master_tracks = sequence.get_master_tracks()

    export_options = export_options or DEFAULT_SEQUENCE_FBX_EXPORT_OPTIONS
    fbx_export_options = unreal.FbxExportOption()
    for name, value in export_options.items():
        try:
            fbx_export_options.set_editor_property(name, value)
        except Exception:
            unreal.log_warning(
                "Was not possible to set FBX Export property: {}: {}".format(
                    name, value
                )
            )

    export_fbx_params = unreal.SequencerExportFBXParams(
        world,
        sequence,
        root_sequence,
        bindings,
        master_tracks,
        fbx_export_options,
        fbx_path,
    )
    result = unreal.SequencerTools.export_level_sequence_fbx(export_fbx_params)

    return fbx_path if result else ""


def export_fbx_binding(binding: unreal.MovieSceneBindingProxy,
                       path: str,
                       sequence: unreal.LevelSequence = None):
    """
    Exports the object that relates to the track, to the path specified, as an fbx.
    Example: Camera track, would export the camera object to the specified location.

    :param unreal.MovieSceneBindingProxy bindings: binding to export.
    :param str path: Full path to directory, where the fbxs will be exported.
    :param sequence, optional: LevelSequence that the bindings belong to, else it
    assumes to be the Active Sequncer.

    :return: The FBX export location.
    :rtype: str
    """

    editor_system = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor_system.get_editor_world()
    fbx_config = unreal.FbxExportOption()
    seq_tools = unreal.SequencerTools()

    if sequence is None:
        sequence = get_current_level_sequence()

    export_path = path + str(binding.get_display_name())

    seq_fbx_params = unreal.SequencerExportFBXParams(world=world,
                                                     sequence=sequence,
                                                     bindings=[binding],
                                                     override_options=fbx_config,
                                                     fbx_file_name=export_path
                                                     )

    complete = seq_tools.export_level_sequence_fbx(seq_fbx_params)

    if complete:
        return export_path + ".fbx"

    return None


def export_fbx_bindings(bindings: list, path: str, sequence: unreal.LevelSequence = None):
    """
    Exports the MovieSceneBindingProxy as an fbx, to the path specified.

    :param [unreal.MovieSceneBindingProxy] bindings: bindings to export.
    :param str path: Full path to directory, where the fbxs will be exported.
    :param sequence, optional: LevelSequence that the bindings belong to, else it
    assumes to be the Active Sequncer.

    :return: The FBX export locations.
    :rtype: [str]
    """
    export_paths = []

    if sequence is None:
        sequence = get_current_level_sequence()

    for proxy_bind in bindings:
        fbx_path = export_fbx_binding(
            binding=proxy_bind,
            path=path)

        export_paths.append(fbx_path)

    return export_paths


def remove_sequence_camera(level_sequence_name="", camera_name=""):
    """
    Removes the camera from the given sequence with given name.

    :param str level_sequence_name: name of the sequence that contains the camera.
    :param str camera_name: name of the camera to remove.
    :return: True if the camera was removed successfully; False otherwise.
    :rtype: bool
    """

    level_sequence_asset = unreal.load_asset(level_sequence_name)
    if not level_sequence_asset:
        return False

    sequence_bindings = level_sequence_asset.get_bindings()
    camera_bind = None
    for binding in sequence_bindings:
        if binding.get_name() or binding.get_display_name() == camera_name:
            camera_bind = binding
            break
    if not camera_bind:
        return False

    unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
    children_component = camera_bind.get_child_possessables() or list()
    for child_component in children_component:
        child_component.remove()
    camera_tracks = camera_bind.get_tracks()
    for camera_track in camera_tracks:
        camera_bind.remove_track(camera_track)
    camera_bind.remove()

    unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()
    unreal.EditorAssetLibrary.save_loaded_asset(level_sequence_asset)

    return True


# TODO: This needs to return unreal.MovieSceneSequence and not unreal.SubSections
def get_subsequences(level_sequence_name):
    """
    Returns a list of sequences from the given sequence name.

    :param str level_sequence_name: name of the sequence whose subsequences we want to retrieve.
    :return: list of sequence subsequences.
    :rtype: list(unreal.LevelSequence)
    """

    level_sequence_asset = unreal.load_asset(level_sequence_name)
    if not level_sequence_asset:
        return list()

    found_subscene_track = None
    tracks = level_sequence_asset.get_master_tracks()
    for track in tracks:
        if track.get_class() == unreal.MovieSceneSubTrack.static_class():
            found_subscene_track = track
            break

    return (
        found_subscene_track.get_sections() if found_subscene_track else list()
    )


def get_sequencer_playback_range(sequence: unreal.MovieSceneSequence = None):
    """
    Gets the Start and End frame of the sequence provided, else defaults to 
    active sequence.
    If Sequence has no start or end, then None is returned.
    
    :return: The Start and End Frame of the playback range.
    :rtype: [int, int]
    """
    playback_data = None
    start_frame = None
    end_frame = None

    if sequence is None:
        playback_data = get_current_level_sequence().get_playback_range()
    else:
        playback_data = sequence.get_playback_range()

    if playback_data.has_start():
        start_frame = playback_data.get_start_frame()
    if playback_data.has_end():
        end_frame = playback_data.get_end_frame()

    return start_frame, end_frame


def get_sequencer_view_range(sequence: unreal.MovieSceneSequence = None):
    """
    Gets the sequences view range.
    If no sequence is specified, then defaults to current active level sequencer.
    
    :return: The Start and End Frame of the view range.
    :rtype: [int, int]
    """
    start_frame = None
    end_frame = None

    if sequence is None:
        sequence = get_current_level_sequence()

    fps = sequence.get_display_rate().numerator

    start_frame = round(sequence.get_view_range_start() * fps)
    end_frame = round(sequence.get_view_range_end() * fps)

    return start_frame, end_frame


def get_sequencer_work_range(sequence: unreal.MovieSceneSequence = None):
    """
    Gets the sequences work range.
    If no sequence is specified, then defaults to current active level sequencer.

    :return: The Start and End Frame of the work range.
    :rtype: [int, int]
    """
    start_frame = None
    end_frame = None

    if sequence is None:
        sequence = get_current_level_sequence()

    fps = sequence.get_display_rate().numerator

    start_frame = round(sequence.get_work_range_start() * fps)
    end_frame = round(sequence.get_work_range_end() * fps)

    return start_frame, end_frame


def open_sequencer(level_sequence_path: str):
    """
    Opens the Sequencer UI in Unreal with the sequencer file.
    level_sequencer_path: Needs to be a PackageName (Start with /Game )

    :return: The LevelSequence that was opened inside the Sequencer.
    :rtype: unreal.LevelSequence
    """

    # Check if path is an Object path, if so remove the .##
    if level_sequence_path.find(".") > -1:
        level_sequence_path = level_sequence_path.split(".")[0]

    if not assets.asset_exists(level_sequence_path):
        return

    # Converts path to Asset
    asset_data = unreal.EditorAssetLibrary.find_asset_data(level_sequence_path)
    asset_editor = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)

    # Opens the Sequencer
    asset_editor.open_editor_for_assets([asset_data.get_asset()])

    return asset_data.get_asset()

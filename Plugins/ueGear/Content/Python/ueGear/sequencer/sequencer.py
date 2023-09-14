import os
import json

import unreal

from ueGear import helpers, assets

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

def get_framerate(sequence:unreal.MovieSceneSequence=None):
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

# TODO: DOES NOT RETURN ANYTHING
def get_bound_objects(sequence):
    """
    Returns objects in the current map that are bound to the given sequence.

    :param unreal.MovieSceneSequence sequence: sequence to get bound objects of.
    :return: list of bound objects.
    """

    world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem
    ).get_editor_world()
    sequence_range = sequence.get_playback_range()
    bound_objects = unreal.SequencerTools.get_bound_objects(
        world, sequence, sequence.get_bindings(), sequence_range
    )

    for bound_object in bound_objects:
        print("Binding: {}".format(bound_object.binding_proxy))
        print("Bound Objects: {}".format(bound_object.bound_objects))
        print("----\n")


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

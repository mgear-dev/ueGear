"""This is just a scratch area for simple class and function designs, before being refactored into a proper location."""

import unreal

import ueGear.sequencer as sequencer
import ueGear.sequencer.bindings

import ueGear.commands as ueCommands
import importlib
importlib.reload(ueCommands)
importlib.reload(sequencer)
# importlib.reload(ueGear.sequencer.bindings)

def DEPRECATED_get_viewport_camera_matrix():
    """
    Uses a deprecated unreal method.
    Gets the active viewport's camera matrix, if it is available.
    :return: Viewport's camera matrix if available, else None.
    :rtype: unreal.Matrix
    """
    cam_location, cam_rotation = unreal.EditorLevelLibrary.get_level_viewport_camera_info()
    
    # Exit early if no camera info was returned...
    if [cam_location, cam_rotation] is None:    
        return None
    
    camera_transform = cam_rotation.transform()
    camera_transform.translation = cam_location

    return camera_transform.to_matrix()


def get_viewport_camera_matrix():
    """
    Gets the active viewport's camera matrix, if it is available.
    :return: Viewport's camera matrix if available, else None.
    :rtype: unreal.Matrix
    """
    editor_system = unreal.UnrealEditorSubsystem
    cam_location, cam_rotation = editor_system.get_level_viewport_camera_info()
    
    # Exit early if no camera info was returned...
    if [cam_location, cam_rotation] is None:    
        return None
    
    camera_transform = cam_rotation.transform()
    camera_transform.translation = cam_location

    return camera_transform.to_matrix()


def set_viewport_camera_matrix(matrix: unreal.Matrix):
    """
    Gets the active viewport's camera matrix, if it is available.
    :return: Viewport's camera matrix if available, else None.
    :rtype: unreal.Matrix
    """

    editor_system = unreal.UnrealEditorSubsystem
    camera_transform = matrix.transform()

    cam_location = camera_transform.translation
    cam_rotation = camera_transform.rotation.rotator()
    
    editor_system.set_level_viewport_camera_info(cam_location, cam_rotation)


def get_current_level_sequence():
    """
    Get the current open level sequence.

    Note: The Sequencer UI has to be open, else return None.

    :rtype: unreal.LevelSequence|None
    """
    level_sequence = unreal.LevelSequenceEditorBlueprintLibrary
    return level_sequence.get_current_level_sequence()

# Minimum Version Unreal 5.2
# Minimum Maya Version.... As old as we can go

# [X] Look for Camera in level
# [X] Look for level sequencer in level
    # [X] Look for camera in level sequencer, or sequence
    # [X] Check Camera in level
    # [X] Look for SubSequence Cameras
# [X] Export FBX Camera Animation from Sequencer
# [X] Get Sequencer Work Range 
# [X] Get Sequencer View Range
# [X] Get Sequencer Start and End Time

# [ ] Look into mGears Maya import Sequencer Command [Maya Client]
    # [ ] Start up UE Server 
    # [ ] Shutdown up UE Server

# [ ] Access Camera Transform data
# [ ] Access Camera Specific component data
# [ ] Access Attributes
# [ ] Access Animated Attributes
# [ ] Create Animated Attributes
# [ ] Update Animation Attributes
# [ ] Save out and load data from Unreal to Unreal

# [ ] Need to add some MetaData to the Unreal Level, to associate it to the Maya level
    # [ ] Or ask everytime for the location.
    # [ ] Track which camera comes from which LevelSequencer / track, so they can be matched up on re-import



def get_cameras_in_level():
    """
    Returns all the Camera Actors that exist in the level, at this moment in time.
    
    NOTE: This MIGHT NOT return all camera's in the sequencer as the sequencer may have 
          Sequence instancable Cameras, that only appear when the current frame overlaps
          with its active track section.
        
    :return: List of CameraActors, that exist in the Level
    :rtype: [unreal.CameraActor]
    """
    world = unreal.EditorLevelLibrary.get_editor_world()
    cam_type = unreal.CameraActor
    return unreal.GameplayStatics().get_all_actors_of_class(world, cam_type)

def get_subsequence_tracks(sequence:unreal.LevelSequence=None):
    """
    Gets all tracks that have sub sequences tracks.
    :return: List of MovieSceneSubTrack, that exist in the sequence
    :rtype: [unreal.MovieSceneSubTrack]
    """
    if sequence is None:
        sequence = get_current_level_sequence()

    return sequence.find_tracks_by_exact_type(unreal.MovieSceneSubTrack)

def get_subsequences(track:unreal.MovieSceneSubTrack):
    """
    Gets all sequences that exist in the Sub sequence track.
    :return: List of MovieSceneSequences, that were part of the track.
    :rtype: [unreal.MovieSceneSequence]
    """
    sequences = []

    for section in track.get_sections():
        sequences.append(section.get_sequence())

    return sequences

def query_level_sequence():
    active_lvl_seq = get_current_level_sequence()
    
    if active_lvl_seq is None:
        return

    all_tracks = active_lvl_seq.get_tracks()

    print("All Tracks")
    for track in all_tracks:
        print(f"  {track.get_display_name()}")
        print(f"       {track.get_class()}")
        
        if track.get_class() == unreal.MovieSceneSubTrack().get_class():
            print( "     SUB-SEQUENCE")
            print(f"        {track.get_display_name()}")
            print(f"        {track.get_package()}")
            print(f"        {track.get_path_name()}")
            print(f"        {track.get_default_object()}")
            
            # print(get_subsequences(track))

            for sub_seq in get_subsequences(track):
                print( get_sequencer_playback_range( sub_seq ) )

            # for sctn in track.get_sections():
                # print(f"             {sctn}")
                # print(f"             {sctn.get_sequence()}")
                # print( get_sequencer_playback_range( sctn.get_sequence() ) )
            

    print("Find By Exact Type")
    for track in get_subsequence_tracks():
        print(f"  {track.get_display_name()}")
        print(f"       {track.get_class()}")

    print("Spawnable")
    for spawnable in active_lvl_seq.get_spawnables():
        print(f"  {spawnable.get_display_name()}")
        print(f"       {spawnable.get_name()}")
        print(f"       {spawnable.get_id()}")
        print(f"       {spawnable.get_binding_id()}")
        print(f"       {spawnable.get_child_possessables()}")
        print(f"       {spawnable.get_possessed_object_class() }")
        print(f"       {spawnable.get_possessed_object_class() }")
        # print(f"       {spawnable.__class__ }")

        # WORKING HERE:Trying to get detect If the Spawnable is a camera, looks like we have to go on Component name for now.
        if spawnable.get_child_possessables()[0].get_name() == "CameraComponent":

            # TODO: Shift the timeline to the start of the Spanwable camera, so one exists in the level at export time.

            print("     CAMERA ACTOR")
            export_level_sequence_bound_object(spawnable, "/Users/simonanderson/Documents/maya/projects/default/assets/")

        print("        TRACKS:")
        for track in spawnable.get_tracks():
            print(f"          {track.get_name()}")

        if spawnable.get_child_possessables():
            print("      CHILDREN:")
            for child in spawnable.get_child_possessables():
                print(f"         {child.get_display_name()}  : {child.get_name()}")

                for track in child.get_tracks():
                    print(f"              {track.get_name()}  : {track.get_display_name()}")
                    print(f"                 {track.get_section_to_key()}" )
                    sections = track.get_sections()
                    if sections:
                        for section in sections:
                            for channel in section.get_all_channels():
                                print(f"                 {channel.get_default()}" )
                                print(f"                 {channel.get_keys()}" )

                                for k in channel.get_keys():
                                    print(f"                 {k.get_time()} : {k.get_value()}")


    print("Possables")
    for possables in active_lvl_seq.get_possessables():
        print(f"  {possables.get_display_name() }")
        print(f"     {possables.get_id() }")
        print(f"     {possables.get_binding_id() }")
        print(f"     {possables.get_parent() }")
        print(f"     {possables.get_possessed_object_class() }")
        # print(f"     {possables.__class__ }")
        # print(f"     {possables.get_object_template() }")

        if possables.get_possessed_object_class() == unreal.CineCameraActor().get_class():
            print("     CAMERA ACTOR")
            print(f"        GUI: {possables.get_id()}")

            export_level_sequence_bound_object(possables, "/Users/simonanderson/Documents/maya/projects/default/assets/")

            objs = get_bound_object(possables)

            for obj in objs:
                camActor = unreal.CineCameraActor.cast(obj)
                print(f"        {camActor.get_name()}")
                print(f"        {camActor.camera_component}")


        try:
            cine_camera = unreal.CineCameraActor.cast(possables)
            print("     Cast SUCCESS!!")
        except:
            print("     ")
 
        if possables.get_tracks():
            print("     TRACKS:")
            for track in possables.get_tracks():
                print(f"          {track.get_name()}  : {track.get_display_name()}")

        if possables.get_child_possessables():
            print("      CHILDREN:")
            for child in possables.get_child_possessables():
                print(f"         {child.get_display_name()}  : {child.get_name()}")

                for track in child.get_tracks():
                    print(f"              {track.get_name()}  : {track.get_display_name()}")
                    print(f"                 {track.get_section_to_key()}" )
                    # print(f"                 {track.get_sections()}" )
                    sections = track.get_sections()
                    if sections:
                        for section in sections:
                            for channel in section.get_all_channels():
                                # channel = unreal.MovieSceneScriptingFloatChannel
                                print(f"                 {channel.get_default()}" )
                                print(f"                 {channel.get_keys()}" )



                    # channels = section.get_all_channels()
                    # for channel in channels:
                        # print(f"              {channel.get_full_name()}")
                        # print(f"              {channel.get_editor_property(channel.get_full_name())}")
                        
            

def get_bound_object(track:unreal.MovieSceneBindingProxy, sequence:unreal.LevelSequence=None):
    """
    Queries the active Level Sequencer for the Objects that are bound to 
    the input Track ( MovieSceneBindingProxy ).
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


def export_level_sequence_bound_object(track:unreal.MovieSceneBindingProxy, path:str, sequence:unreal.LevelSequence=None):
    """
    Exports the object that relates to the track, to the path specified.
    Example: Camera track, would export the camera object to the specified location.
    """
    editor_system = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor_system.get_editor_world()
    fbx_config = unreal.FbxExportOption()
    seq_tools = unreal.SequencerTools()

    if sequence is None:
        sequence = get_current_level_sequence()

    export_path = path + str(track.get_display_name())

    seq_fbx_params = unreal.SequencerExportFBXParams(world=world, 
                                                     sequence=sequence, 
                                                     bindings=[track],
                                                     override_options = fbx_config,
                                                     fbx_file_name = export_path
    )

    complete =  seq_tools.export_level_sequence_fbx(seq_fbx_params)

    if complete:
        print(f"FBX EXPORTED: {export_path}")
        return export_path

    return None

def get_sequencer_playback_range(sequence:unreal.MovieSceneSequence=None):
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


def get_sequencer_view_range(sequence:unreal.MovieSceneSequence=None):
    """
    Gets the sequences view range.
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


def get_sequencer_work_range(sequence:unreal.MovieSceneSequence=None):
    """
    Gets the sequences work range.
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

# [ ] Export Selected Camera From Sequencer
#   [ ] Full track
#   [ ] Active Track

def export_selected_sequencer_camera(active_track=True):
    """

    DESIGN ASSUMPTION: We will only be exporting Bindings and Sections.
    as tracks equate to object attributes, which require more custom
    handlingwhen exporting and importing the fbx.

    :return: Dictionary of paths exported(key), and the value 
    :rtype: [int, int]
    """
    level_sequence = unreal.LevelSequenceEditorBlueprintLibrary

    # Track that is an objects and not an objects attribute.
    bindings = level_sequence.get_selected_bindings()

    # otherwise refered to as clips, a segment that appears on the binding
    # Unreal Bug: Seems to not populate correctly all the time.
#    sections = level_sequence.get_selected_sections()

    print("SELECTED")
 #   print(f"  {sections}")
    print(f"  {bindings}")

    exported_cameras = dict()

#    for section in sections:
#        print("Section")
#        print(f"  {section.get_full_name()}")
#        print(f"  {section.get_path_name()}")
        
    for binding in bindings:

        if ueGear.sequencer.bindings.is_instanced_camera(binding):
            print("Binding: INSTANCED CAMERA")
            print(f"  {binding.get_name()}")
            print(f"  {binding.get_display_name()}")
            print(f"  {binding.static_struct()}")
            print(f"  {binding.get_possessed_object_class()}")
            print(f"       {binding.get_child_possessables()}")
            print(f"       {binding.get_possessed_object_class() }")
            print(f"       {binding.get_child_possessables()[0].get_name()}")

            export_path = export_level_sequence_bound_object(
                track=binding, 
                path="/Users/simonanderson/Documents/maya/projects/default/scenes"
            )

        if ueGear.sequencer.bindings.is_camera(binding):
            print("Binding: CAMERA")
            print(f"  {binding.get_name()}")
            print(f"  {binding.get_display_name()}")
            print(f"  {binding.static_struct()}")
            print(f"  {binding.get_possessed_object_class() == unreal.CineCameraActor.static_class()}")

        # export_path = export_level_sequence_bound_object(
        #     track=binding, 
        #     path="/Users/simonanderson/Documents/maya/projects/default/scenes"
        # )

        # exported_cameras[export_path] = binding

    return exported_cameras


# print("Getting current level Sequence")
# query_level_sequence()
export_selected_sequencer_camera()
print( sequencer.get_framerate() )



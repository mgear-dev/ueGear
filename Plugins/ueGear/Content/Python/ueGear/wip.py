"""This is just a scratch area for simple class and function designs, before being refactored into a proper location."""

import unreal

def DEPRECATED_get_viewport_camera_matrix():
    """
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

    cam_location, cam_rotation = unreal.UnrealEditorSubsystem.get_level_viewport_camera_info()
    
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

    Note: Level sequence has to be added to level.

    :rtype: unreal.LevelSequence|None
    """
    level_sequence = unreal.LevelSequenceEditorBlueprintLibrary
    return level_sequence.get_current_level_sequence()

# [ ] Look for Camera in level
# [ ] Look for level sequencer in level
    # [ ] Look for camera in level sequencer, or sequence
    # [ ] Check Camera in level
# [ ] Access Camera Transform data
# [ ] Access Camera Specific component data
# [ ] Access Attributes
# [ ] Access Animated Attributes
# [ ] Get Animation
# [ ] Write Animation
# [ ] Save out and load data from Unreal to Unreal

def get_cameras_in_level():
    return unreal.GameplayStatics().get_all_actors_of_class( unreal.EditorLevelLibrary.get_editor_world(), unreal.CameraActor)

def get_all_subsequences():
    active_lvl_seq = get_current_level_sequence()
    return active_lvl_seq.find_tracks_by_exact_type(unreal.MovieSceneSubTrack)

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
            print("  SUB-SEQUENCE")

    print("Find By Exact Type")
    for track in get_all_subsequences():
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
            export_level_sequence_bound_object(spawnable)

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

            export_level_sequence_bound_object(possables)

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
                        
            

def get_bound_object(track:unreal.MovieSceneBindingProxy):
    """
    Queries the active Level Sequencer for the Objects that are bound to 
    the input Track ( MovieSceneBindingProxy ).
    """
    seq_tools = unreal.SequencerTools()
    editor_system = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    active_lvl_seq = get_current_level_sequence()
    world = editor_system.get_editor_world()
    range = active_lvl_seq.get_playback_range()
    seq_bound_objs = seq_tools.get_bound_objects(world, 
                                                active_lvl_seq, 
                                                [track],
                                                range)

    bound_objs = []
    for entry in seq_bound_objs:
        bound_objs.extend(entry.bound_objects)

    return bound_objs


def export_level_sequence_bound_object(track:unreal.MovieSceneBindingProxy):
    editor_system = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    active_lvl_seq = get_current_level_sequence()
    world = editor_system.get_editor_world()
    range = active_lvl_seq.get_playback_range()

    fbx_config = unreal.FbxExportOption()

    TEMP_PATH = "/Users/simonanderson/Documents/maya/projects/default/assets/"

    export_path =TEMP_PATH + str(track.get_display_name())

    seq_fbx_params = unreal.SequencerExportFBXParams(world=world, 
                                                     sequence=active_lvl_seq, 
                                                     bindings=[track],
                                                     override_options = fbx_config,
                                                     fbx_file_name = export_path
    )

    seq_tools = unreal.SequencerTools()
    complete =  seq_tools.export_level_sequence_fbx(seq_fbx_params)

    if complete:
        print("FBX EXPORTED")
        print(export_path)


print("Getting current level Sequence")
query_level_sequence()
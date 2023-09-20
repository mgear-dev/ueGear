import unreal


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
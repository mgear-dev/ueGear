import unreal

def is_camera(binding:unreal.MovieSceneBindingProxy):
    """
    Check to see if binding is a Camera

    :return: True if binding is a Camera
    :rtype: Bool
    """
    return binding.get_possessed_object_class() == unreal.CineCameraActor.static_class()


def is_instanced_camera(binding:unreal.MovieSceneBindingProxy):
    """
    Check to see if binding is an Instancable Camera

    :return: True if binding is a Instancable Camera
    :rtype: Bool
    """
    possesable_is_camera = False
    no_possesible_objs = binding.get_possessed_object_class() == None
    possessable_children = len(binding.get_child_possessables()) > 0

    if no_possesible_objs and possessable_children:
        child = binding.get_child_possessables()[0]
        possesable_is_camera = child.get_name() == "CameraComponent"

    if possesable_is_camera:
        return True

    return False
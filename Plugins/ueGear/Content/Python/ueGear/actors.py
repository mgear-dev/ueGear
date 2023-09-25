import unreal

from . import helpers, assets


def get_all_actors_in_current_level():
    """
    Returns all current actors in the current opened level.

    :return: list of actors within level.
    :rtype: list(unreal.Actor)
    """

    return unreal.EditorActorSubsystem().get_all_level_actors()


def get_selected_actors_in_current_level():
    """
    Returns all current selected actors in the current opened level.

    :return: list of selected actors within level.
    :rtype: list(unreal.Actor)
    """

    return unreal.EditorActorSubsystem().get_selected_level_actors()


def get_all_actors_and_labels_in_current_level():
    """
    Returns a tuple with all current actors and their labels in the current opened level.

    :return: tuple with a list of actors and their labels within level.
    :rtype: tuple(list(unreal.Actor), list(str))
    """

    actors = get_all_actors_in_current_level()
    actor_names = [actor.get_actor_label() for actor in actors]

    return actors, actor_names


def get_selected_actors_and_labels_in_current_level():
    """
    Returns a tuple with all current selected actors and their labels in the current opened level.

    :return: tuple with a list of selected actors and their labels within level.
    :rtype: tuple(list(unreal.Actor), list(str))
    """

    actors = get_selected_actors_in_current_level()
    actor_names = [actor.get_actor_label() for actor in actors]

    return actors, actor_names


def get_all_actors_and_names_in_current_level():
    """
    Returns a tuple with all current actors and their names in the current opened level.

    :return: tuple with a list of actors and their names within level.
    :rtype: tuple(list(unreal.Actor), list(str))
    """

    actors = get_all_actors_in_current_level()
    actor_names = [actor.get_name() for actor in actors]

    return actors, actor_names


def get_selected_actors_and_names_in_current_level():
    """
    Returns a tuple with all current selected actors and their names in the current opened level.

    :return: tuple with a list of selected actors and their names within level.
    :rtype: tuple(list(unreal.Actor), list(str))
    """

    actors = get_selected_actors_in_current_level()
    actor_names = [actor.get_name() for actor in actors]

    return actors, actor_names


def get_actor_by_label_in_current_level(actor_label):
    """
    Return actor within current level with the given actor label.

    :param str actor_label: actor label.
    :return: found actor with given label in current level.
    :rtype: unreal.Actor or None

    ..warning:: Actor labels within a level are not unique, so if multiple actors have the same label we may return
            the undesired one.
    """

    found_actor = None
    all_actors = get_all_actors_in_current_level()
    for actor in all_actors:
        if actor.get_actor_label() == actor_label:
            found_actor = actor
            break

    return found_actor


def get_actor_by_guid_in_current_level(actor_guid):
    """
    Return actor within current level with the given actor guid.

    :param str actor_guid: actor guid.
    :return: found actor with given guid in current level.
    :rtype: unreal.Actor or None
    """

    found_actor = None
    all_actors = get_all_actors_in_current_level()
    for actor in all_actors:
        if actor.actor_guid.to_string() == actor_guid:
            found_actor = actor
            break

    return found_actor


def get_all_actors_with_component_of_type(component_class):
    found_actors = list()
    actors = unreal.EditorActorSubsystem().get_all_level_actors()
    for actor in actors:
        components = actor.get_components_by_class(component_class)
        if not components:
            continue
        found_actors.append(actor)

    return found_actors


def select_actors_in_current_level(actors):
    """
    Set the given actors as selected ones within current level.

    :param unreal.Actor or list(unreal.Actor) actors: list of actors to select.
    """

    unreal.EditorLevelLibrary().set_selected_level_actors(
        helpers.force_list(actors)
    )


def delete_actor(actor):
    """
    Deletes given actor from current scene.

    :param unreal.Actor actor: actor instance to delete.
    """

    unreal.EditorLevelLibrary.destroy_actor(actor)


def get_actor_asset(actor):
    """
    Returns the asset associated to given actor based on actor components.

    :param unreal.Actor actor: actor to get linked asset of.
    :return: found asset.
    :rtype: unreal.Object

    ..warning:: For now, only Static Mesh, Skeletal Meshes are supported.
    """

    is_static_mesh = False
    is_skeletal_mesh = False
    is_camera = False
    actor_asset = None

    static_mesh_components = list()
    skeletal_mesh_components = list()
    camera_components = list()

    static_mesh_components = actor.get_components_by_class(
        unreal.StaticMeshComponent
    )
    if static_mesh_components:
        is_static_mesh = True

    if not is_static_mesh:
        skeletal_mesh_components = actor.get_components_by_class(
            unreal.SkeletalMeshComponent
        )
        if skeletal_mesh_components:
            is_skeletal_mesh = True

    if is_static_mesh:
        static_mesh_component = helpers.get_first_in_list(
            static_mesh_components
        )
        static_mesh = static_mesh_component.get_editor_property("static_mesh")
        actor_asset = assets.get_asset(static_mesh.get_path_name())
    elif is_skeletal_mesh:
        skeletal_mesh_component = helpers.get_first_in_list(
            skeletal_mesh_components
        )
        skeletal_mesh = skeletal_mesh_component.get_editor_property(
            "skeletal_mesh"
        )
        actor_asset = assets.get_asset(skeletal_mesh.get_path_name())

    return actor_asset


def export_fbx_actor(actor, directory, export_options=None):
    """
    Exports a FBX of the given actor.

    :param unreal.Actor actor: actor to export as FBX.
    :param str directory: directory where FBX actor will be exported.
    :param dict export_options: dictionary containing all the FBX export settings to use.
    :return: exported FBX file path.
    :rtype: str
    """

    actor_asset = get_actor_asset(actor)
    if not actor_asset:
        unreal.log_warning(
            "Was not possible to retrieve valid asset for actor: {}".format(
                actor
            )
        )
        return ""

    return assets.export_fbx_asset(
        actor_asset,
        directory=directory,
        fbx_filename=actor.get_actor_label(),
        export_options=export_options,
    )


def export_all_fbx_actors_in_current_scene(directory, export_options=None):
    """
    Exports all actors in current scene.

    :param str directory: directory where FBX actor will be exported.
    :param dict export_options: dictionary containing all the FBX export settings to use.
    :return: exported FBX file paths.
    :rtype: list(str)
    """

    exported_actors = list()
    all_actors = get_all_actors_in_current_level()
    for actor in all_actors:
        actor_export_path = export_fbx_actor(
            actor, directory=directory, export_options=export_options
        )
        exported_actors.append(actor_export_path)

    return exported_actors

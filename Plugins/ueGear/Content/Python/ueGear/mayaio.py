#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Maya Import/Export functionality for ueGear
"""

from __future__ import print_function, division, absolute_import

import os
import tkinter as tk
from tkinter import filedialog

import unreal

from . import helpers, structs, tag, actors, assets, sequencer


# ======================================================================================================================
# BASE
# ======================================================================================================================


def import_data(
    source_files=None, destination_path="", start_frame=1, end_frame=1
):
    root = tk.Tk()
    root.withdraw()

    source_files = helpers.force_list(
        source_files
        or filedialog.askopenfilenames(
            filetypes=[("ueGear JSON files", "*.json")]
        )
    )
    if not source_files:
        return False

    level_sequence_name = ""
    level_sequence_asset = None
    source_files_sorted = list()
    layout_files = list()
    animation_files = list()

    for source_file in source_files:
        if source_file.endswith("_animation.json"):
            animation_files.append(source_file)
        elif source_file.endswith("_layout.json"):
            layout_files.append(source_file)
        else:
            source_files_sorted.append(source_file)
    source_files_sorted = source_files_sorted + layout_files + animation_files

    for source_file in source_files_sorted:
        if not source_file:
            unreal.log_warning("ueGear JSON file not found!")
            continue
        json_data = helpers.read_json_file(source_file)
        if not json_data:
            unreal.log_error(
                'ueGear JSON file "{}" contains invalid data!'.format(
                    source_file
                )
            )
            continue

        is_shot = True

        print(json_data)

    return True


# ======================================================================================================================
# ASSETS
# ======================================================================================================================


def export_assets(export_directory, assets_to_export=None):
    """
    Exports Unreal assets into FBX in the given directory.

    :param str export_directory: absolute path export directory where asset FBX files will be located.
    :param list(unreal.Object) or None assets_to_export: list of assets to export. If not given, current Content
            Browser selected assets will be exported.
    :return: list of asset export data struct instances.
    :rtype: list(structs.AssetExportData)
    """

    asset_export_datas = list()

    # if not assets to export given, we retrieve current selected assets in Unreal Engine Content Browser
    assets_to_export = helpers.force_list(
        assets_to_export or list(assets.selected_assets())
    )
    if not assets:
        unreal.log_warning("No assets to export")
        return asset_export_datas

    for asset_to_export in assets_to_export:
        asset_fbx_file = assets.export_fbx_asset(
            asset_to_export, export_directory
        )
        if not asset_fbx_file or not os.path.isfile(asset_fbx_file):
            unreal.log_warning(
                'Was not possible to export asset: "{}"'.format(
                    asset_to_export
                )
            )
            continue
        asset_export_data = structs.AssetExportData()
        asset_export_data.name = asset_to_export.get_name()
        asset_export_data.path = asset_to_export.get_path_name()
        asset_export_data.asset_type = (
            unreal.EditorAssetLibrary.get_metadata_tag(
                asset_to_export, tag.TAG_ASSET_TYPE_ATTR_NAME
            )
            or ""
        )
        asset_export_data.fbx_file = asset_fbx_file
        asset_export_datas.append(asset_export_data)

    return asset_export_datas


# ======================================================================================================================
# LEVELS
# ======================================================================================================================


def export_level(filename, level_name=""):
    """
    Exports the complete level.

    :param str filename: name of the level to export.
    :param str level_name: name of the level to export.
    """

    if not level_name:
        level_asset = unreal.LevelEditorSubsystem().get_current_level()
        level_name = (
            level_asset.get_path_name()
            .split("/")[-1]
            .split(":")[0]
            .split(".")[0]
        )

    level_to_export = None
    levels = (
        unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_class(
            "World"
        )
    )
    for level in levels:
        if level.get_editor_property("asset_name") == level_name:
            level_to_export = level.get_asset()
            break
    if not level_to_export:
        unreal.log_warning(
            'No level to export found with name: "{}"'.format(level_name)
        )
        return

    export_task = unreal.AssetExportTask()
    export_task.object = level_to_export
    export_task.filename = filename
    export_task.automated = True
    export_task.prompt = False
    export_task.exporter = unreal.LevelExporterLOD()
    export_task.options = unreal.FbxExportOption()

    unreal.Exporter.run_asset_export_task(export_task)


# ======================================================================================================================
# LAYOUT
# ======================================================================================================================


def import_layout_from_file(layout_file_path=""):
    """
    Imports given ueGear layout file into current opened Unreal level.

    :param str layout_file_path: absolute file path pointing to an ueGear layout JSON file. If not given, a file dialog
            will be opened, so user can manually select which file to open.
    :return: True if the import layout from file operation was successful; False otherwise.
    :rtype: bool
    """

    if not layout_file_path:
        root = tk.Tk()
        root.withdraw()
        layout_file_path = filedialog.askopenfile(
            title="Select ueGear Layout file to load",
            filetypes=[("ueGear Layout files", "*.json")],
        )
        layout_file_path = layout_file_path.name if layout_file_path else None
    if not layout_file_path or not os.path.isfile(layout_file_path):
        unreal.log_error("No valid Layout file path selected!")
        return False

    level_actors = actors.get_all_actors_in_current_level()
    actors_names = list()
    for actor in level_actors:
        actors_names.append(actor.get_actor_label())

    layout_data = helpers.read_json_file(layout_file_path)
    if not layout_data:
        unreal.log_error(
            "Was not possible to load layout data from layout file: {}".format(
                layout_file_path
            )
        )
        return False

    for layout_asset_name, layout_asset_data in layout_data.items():
        actor_in_level_name = layout_asset_data.get("actorName", "")
        if not actor_in_level_name:
            actor_in_level_name = layout_asset_name
        if ":" in actor_in_level_name:
            namespace = actor_in_level_name.split(":")[0]
            actor_in_level_name = "{}_{}".format(
                namespace, actor_in_level_name.split(":")[-1]
            )

        source_name = layout_asset_data.get(
            "assetName", ""
        ) or layout_asset_data.get("sourceName", "")
        translation_value = layout_asset_data.get("translation", None)
        rotation_value = layout_asset_data.get("rotation", None)
        scale_value = layout_asset_data.get("scale", None)
        if (
            not source_name
            or not translation_value
            or not rotation_value
            or not scale_value
        ):
            unreal.log_warning(
                'Layout Asset "{}" was not stored properly within layout file:\n\tsourceName:{}\n\ttranslation:{}'
                "\n\trotation:{}\n\tscale:{}".format(
                    layout_asset_data,
                    source_name,
                    translation_value,
                    rotation_value,
                    scale_value,
                )
            )
            continue

        (
            current_position,
            current_rotation,
            current_scale,
        ) = helpers.convert_maya_transforms_into_unreal_transforms(
            translation_value, rotation_value, scale_value
        )

        source_asset_path = ""

        if not layout_asset_name == actor_in_level_name:
            if layout_asset_name in actors_names:
                if actor_in_level_name not in actors_names:
                    current_actor = level_actors[
                        actors_names.index(layout_asset_name)
                    ]
                    current_actor.set_actor_label(actor_in_level_name)
                    actors_names.append(actor_in_level_name)

        if actor_in_level_name in actors_names:
            unreal.log("Updating transform on {}".format(actor_in_level_name))
            current_actor = level_actors[
                actors_names.index(actor_in_level_name)
            ]
            current_actor.set_actor_location(current_position, False, True)
            current_actor.set_actor_rotation(current_rotation, True)
            current_actor.set_actor_scale3d(current_scale)
        else:
            asset_name = "{}.{}".format(source_name, source_name)
            asset_paths = assets.list_asset_paths(
                "/Game/Assets/", recursive=True, include_folder=False
            )
            for asset_path in asset_paths:
                if asset_name in asset_path:
                    source_asset_path = asset_path
                    break

            if not source_asset_path:
                unreal.log(
                    'Skipping actor: {}, asset "{}" not found!'.format(
                        actor_in_level_name, source_asset_path
                    )
                )
                continue

            source_asset = unreal.load_asset(source_asset_path)
            unreal.log("Creating " + actor_in_level_name + "...")
            current_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
                source_asset, current_position, current_rotation
            )
            current_actor.set_actor_label(actor_in_level_name)
            current_actor.set_actor_location(current_position, False, True)
            current_actor.set_actor_rotation(current_rotation, False)
            current_actor.set_actor_scale3d(current_scale)
            actors_names.append(actor_in_level_name)
            level_actors.append(current_actor)

    return True


def export_layout_file(output_path="", only_selected_actors=False):
    """
    Exports ueGear layout file.

    :param str output_path: optional ueGear output directory.
    :param bool only_selected_actors: whether to export only selected actors.
    :return: True if the export layout operation was successful; False otherwise.
    :rtype: bool
    """

    root = tk.Tk()
    root.withdraw()
    output_path = output_path or filedialog.askdirectory(
        title="Select output folder for layout export"
    )
    if not output_path or not os.path.isdir(output_path):
        unreal.log_warning("No valid export layout directory defined!")
        return False

    level_asset = unreal.LevelEditorSubsystem().get_current_level()
    level_name = unreal.SystemLibrary.get_object_name(level_asset)
    if only_selected_actors:
        level_actors = actors.get_selected_actors_in_current_level()
    else:
        level_actors = actors.get_all_actors_in_current_level()
    if not level_actors:
        unreal.log_warning("No actors to export")
        return False

    layout_data = list()
    for level_actor in level_actors:
        level_actor_data = {
            "guid": str(level_actor.get_editor_property("actor_guid")),
            "name": level_actor.get_actor_label(),
            "path": level_actor.get_path_name(),
            "translation": level_actor.get_actor_location().to_tuple(),
            "rotation": level_actor.get_actor_rotation().to_tuple(),
            "scale": level_actor.get_actor_scale3d().to_tuple(),
        }
        layout_data.append(level_actor_data)

    output_file_path = os.path.join(
        output_path, "{}_layout.json".format(level_name)
    )
    result = helpers.write_to_json_file(layout_data, output_file_path)
    if not result:
        unreal.log_error("Was not possible to save ueGear layout file")
        return False

    unreal.log("Exported ueGear layout file: {}".format(output_file_path))

    return True


# ======================================================================================================================
# CAMERA
# ======================================================================================================================


def import_camera(
    destination_path="",
    level_sequence_name="",
    camera_name="",
    file_path="",
    custom_params=None,
):
    if destination_path and not destination_path.endswith("/"):
        destination_path = destination_path + "/"

    world = helpers.get_editor_world()
    (
        level_actors,
        actor_labels,
    ) = actors.get_all_actors_and_labels_in_current_level()
    level_sequence_name = destination_path + level_sequence_name
    level_sequence_asset = unreal.load_asset(level_sequence_name)
    if not level_sequence_asset:
        unreal.log_warning(
            'Impossible to import camera because no level sequence asset found with name: "{}"'.format(
                level_sequence_name
            )
        )
        return False

    bindings = level_sequence_asset.get_bindings()

    if camera_name in actor_labels:
        sequencer.remove_sequence_camera(
            level_sequence_name=level_sequence_name, camera_name=camera_name
        )
        actors.delete_actor(level_actors[actor_labels.index(camera_name)])
        helpers.save_current_level()

    import_options = unreal.MovieSceneUserImportFBXSettings()
    import_options.set_editor_property("create_cameras", 1)
    import_options.set_editor_property("force_front_x_axis", 0)
    import_options.set_editor_property("match_by_name_only", 0)
    import_options.set_editor_property("reduce_keys", 0)
    import_options.set_editor_property("reduce_keys_tolerance", 0.0001)

    unreal.SequencerTools.import_level_sequence_fbx(
        world, level_sequence_asset, bindings, import_options, file_path
    )

    (
        level_actors,
        actor_labels,
    ) = actors.get_all_actors_and_labels_in_current_level()
    camera_asset = level_actors[actor_labels.index(camera_name)]

    if custom_params:
        camera_component = camera_asset.get_cine_camera_component()
        camera_component.set_editor_property(
            "ortho_far_clip_plane", custom_params["farClipPlane"]
        )
        camera_component.set_editor_property(
            "ortho_near_clip_plane", custom_params["nearClipPlane"]
        )
        camera_focus_settings = unreal.CameraFocusSettings()
        camera_focus_settings.focus_method = unreal.CameraFocusMethod.DISABLE
        camera_component.set_editor_property(
            "focus_settings", camera_focus_settings
        )

    helpers.save_current_level()

    unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()
    unreal.EditorAssetLibrary.save_asset(level_sequence_name)

    return True


def convert_transform_maya_to_unreal(maya_transform, world_up):
    """
    Converts a unreal.Transform(), that stores Maya data, into a transformation matrix that
    works in Unreal.

    :param unreal.Transform() maya_transform: Transform with Maya transformation data.
    :param str world_up: Mayas world up setting.

    :return: Maya transformation now in Unreal transform space.
    :rtype: unreal.Transform()
    """
    convertion_mtx = unreal.Matrix(x_plane=[1, 0, 0, 0],
                             y_plane=[0, 0, -1, 0],
                             z_plane=[0, 1, 0, 0],
                             w_plane=[0, 0, 0, 1]
                            )

    if world_up == 'y':
        corrected_mtx =  convertion_mtx * maya_transform.to_matrix() * convertion_mtx.get_inverse()
        # update Rotation
        euler = maya_transform.rotation.euler()
        quat = unreal.Quat()
        quat.set_from_euler(unreal.Vector(euler.x + 90, euler.y, euler.z))
        trans = corrected_mtx.transform()
        trans.rotation = quat

        # Update Position
        pos = trans.translation
        pos_y =  pos.y
        pos_z =  pos.z
        pos.y =  pos_z
        pos.z =  -pos_y
        trans.translation = pos

    elif world_up == 'z':
        corrected_mtx = maya_transform.to_matrix() * convertion_mtx

        # update Rotation
        euler = maya_transform.rotation.euler()
        quat = unreal.Quat()
        quat.set_from_euler(unreal.Vector(euler.x, -euler.z, euler.y))
        trans = corrected_mtx.transform()
        trans.rotation = quat

        # Update Position
        pos = trans.translation
        pos_y = pos.y
        pos_z = pos.z
        pos.y = pos_z
        pos.z = pos_y
        trans.translation = pos

    return trans
#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ueGear Commands
"""

from __future__ import print_function, division, absolute_import

import os
import ast
import importlib

import unreal

from . import helpers, mayaio, structs, tag, assets, actors, textures, sequencer

# TODO: Remove the imports once we release into production
# importlib.reload(helpers)
# importlib.reload(structs)
# importlib.reload(tag)
# importlib.reload(assets)
# importlib.reload(actors)
# importlib.reload(textures)
# importlib.reload(mayaio)


# TODO: For some reason, unreal.Array(float) parameters defined within ufunction params argument are not
# TODO: with the correct number of elements within the list. As a temporal workaround, we convert them
# TODO: to strings in the client side and we parse them here.
# TODO: Update this once fix is done in Remote Control plugin.


@unreal.uclass()
class PyUeGearCommands(unreal.UeGearCommands):
    # ==================================================================================================================
    # OVERRIDES
    # ==================================================================================================================

    @unreal.ufunction(override=True, meta=dict(Category="ueGear Commands"))
    def import_maya_data(self):
        """
        Opens a file window that allow users to choose a JSON file that contains all the info needed to import asset or
        layout data.
        """

        mayaio.import_data()

    @unreal.ufunction(override=True, meta=dict(Category="ueGear Commands"))
    def import_maya_layout(self):
        """
        Opens a file window that allow users to choose a JSON file that contains layout data to load.
        """

        mayaio.import_layout_from_file()

    @unreal.ufunction(override=True, meta=dict(Category="ueGear Commands"))
    def export_unreal_layout(self):
        """
        Exports a layout JSON file based on the objects on the current Unreal level.
        """

        mayaio.export_layout_file()

    @unreal.ufunction(override=True, meta=dict(Catergory="ueGear Commands"))
    def generate_uegear_ui(self):
        """
        """
        widget_name = 'ueGear_ui'
        asset_path = f'/ueGear/Python/ueGear/ui/{widget_name}'
        asset_widget = unreal.EditorAssetLibrary.load_asset(asset_path)

        edit_utils = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
        edit_utils.spawn_and_register_tab(asset_widget)


    # ==================================================================================================================
    # PATHS
    # ==================================================================================================================

    @unreal.ufunction(
        ret=str, static=True, meta=dict(Category="ueGear Commands")
    )
    def project_content_directory():
        """
        Returns the content directory of the current game.

        :return: content directory.
        :rtype: str
        """
        # Gets the path relative to the project
        path = unreal.Paths.project_content_dir()
        # Standardises the path, removing any extra data
        return unreal.Paths.make_standard_filename(path)

    @unreal.ufunction(
        params=[bool],
        ret=unreal.Array(str),
        static=True,
        meta=dict(Category="ueGear Commands")
    )
    def selected_content_browser_directory(relative=False):
        """
        Returns the selected directory in the Content Browser.

        :return: selected directory.
        :rtype: str
        """
        unreal_array = unreal.Array(str)

        paths = assets.get_selected_folders(relative)
        for path in paths:
            unreal_array.append(path)

        return unreal_array

    @unreal.ufunction(
        ret=str,
        static=True,
        meta=dict(Category="ueGear Commands")
    )
    def get_mgear_gnx_path():
        """
        NOTE: Currently this is not being used in the Editor Utility Widget, as the UE widgets has a refresh issue.

        https://forums.unrealengine.com/t/custom-blueprint-nodes-defined-in-python-need-to-be-refreshed-every-time-i-reopen-the-editor/146413/8
        """
        import tkinter as tk
        from tkinter import filedialog

        # Hides the root window
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askopenfilename(
            title="Select a mGear GNX file",
            filetypes=[("GNX files", "*.gnx"), ("All files", "*.*")],
            defaultextension=".gnx"
        )
        return file_path

    # ==================================================================================================================
    # ASSETS
    # ==================================================================================================================

    @unreal.ufunction(
        params=[str],
        ret=bool,
        static=True,
        meta=dict(Category="ueGear Commands"),
    )
    def does_asset_exist(asset_path=""):
        """
        Returns whether asset exists at given path.

        :return: True if asset exists; False otherwise.
        :rtype: bool
        """

        return assets.asset_exists(asset_path)

    @unreal.ufunction(
        params=[str],
        ret=str,
        static=True,
        meta=dict(Category="ueGear Commands"),
    )
    def asset_export_path(asset_path):
        """
        Returns the path where the asset was originally exported.
        """

        return assets.get_export_path(asset_path)

    @unreal.ufunction(
        params=[str],
        ret=unreal.Array(structs.AssetExportData),
        static=True,
        meta=dict(Category="ueGear Commands"),
    )
    def export_selected_assets(directory):
        """
        Export into given directory current Content Browser selected assets.

        :param str directory: directory where assets will be exported.
        :return: list of asset export data struct instances.
        :rtype: list(structs.AssetExportData)
        """

        return mayaio.export_assets(directory)

    @unreal.ufunction(
        params=[str],
        ret=unreal.Array(structs.AssetExportData),
        static=True,
        meta=dict(Category="ueGear Commands"),
    )
    def export_selected_sequencer_cameras(directory):
        """
        Export selected Cameras from LevelSequencer.

        :param str directory: directory where assets will be exported.
        :return: 
        :rtype: 
        """
        meta_data = []

        # Validate directory, as osx required the path to end in a /
        directory = os.path.join(directory, "")

        level_sequencer_path_name = sequencer.get_current_level_sequence().get_path_name()

        # Gets the framerate of the Sequencer.
        fps = sequencer.get_framerate(sequencer.get_current_level_sequence())

        camera_bindings = sequencer.get_selected_cameras()
        if not camera_bindings:
            return []

        fbx_paths = sequencer.export_fbx_bindings(camera_bindings, directory)

        for binding, path in zip(camera_bindings, fbx_paths):
            asset_export_data = structs.AssetExportData()
            asset_export_data.name = binding.get_name()
            asset_export_data.path = level_sequencer_path_name
            asset_export_data.asset_type = "camera"
            asset_export_data.fbx_file = path

            meta_data.append(asset_export_data)

        return meta_data

    @unreal.ufunction(
        ret=int,
        static=True,
        meta=dict(Category="ueGear Commands")
        )
    def get_selected_sequencer_fps():
        """
        Returns the active Sequencer's fps
        """
        return sequencer.get_framerate(sequencer.get_current_level_sequence())

    @unreal.ufunction(
        params=[str, str, str],
        static=True,
        meta=dict(Category="ueGear Commands"),
    )
    def update_sequencer_camera_from_maya(camera_name, sequencer_package, fbx_path):
        """
        Updates the camera in the specified LevelSequencer

        :param str camera_name: The name of the camera that exists on the level sequnce.
        :param str sequencer_package: The package path to the sequencer file.
        :param str fbx_path: Location of the fbx camera.
        """

        print("[ueGear] Command Triggered - Update Sequencer Cameras")
        levelsequencer = sequencer.open_sequencer(sequencer_package)
        sequencer.import_fbx_camera(name=camera_name, sequence=levelsequencer, fbx_path=fbx_path)


    # ==================================================================================================================
    # ACTORS
    # ==================================================================================================================

    @unreal.ufunction(
        params=[str, str, str, str, str],
        static=True,
        meta=dict(Category="ueGear Commands"),
    )
    def set_actor_world_transform(actor_guid, translation, rotation, scale, world_up):
        """
        Sect the world transform of the actor with given GUID withing current opened level.

        :param str translation: actor world translation as a string [float, float, float] .
        :param str rotation: actor world rotation as a string [float, float, float].
        :param str scale: actor world scale as a string [float, float, float].
        :param str world_up: describes mayas world up axis.
        """
        found_actor = actors.get_actor_by_guid_in_current_level(actor_guid)
        if not found_actor:
            unreal.log_warning(
                'No Actor found with guid: "{}"'.format(actor_guid)
            )
            return

        maya_transform = unreal.Transform()
        rotation = ast.literal_eval(rotation)
        maya_transform.rotation = unreal.Rotator(rotation[0], rotation[1], rotation[2]).quaternion()
        maya_transform.translation = unreal.Vector(*ast.literal_eval(translation))
        maya_transform.scale3d = unreal.Vector(*ast.literal_eval(scale))

        ue_transform = mayaio.convert_transform_maya_to_unreal(maya_transform, world_up)

        found_actor.set_actor_transform(ue_transform, False, False)

    # ==================================================================================================================
    # STATIC MESHES
    # ==================================================================================================================

    @unreal.ufunction(
        params=[str, str, str],
        ret=str,
        static=True,
        meta=dict(Category="ueGear Commands"),
    )
    def import_static_mesh(fbx_file, import_path, import_options):
        """
        Imports skeletal mesh from FBX file.

        :param str fbx_file: skeletal mesh FBX file path.
        :param str import_path: package path location
        :param str import_options: FBX import options as a string.
        :return: imported skeletal mesh asset path.
        :rtype: str
        """

        # Check import path is a package path, else update it.
        is_package_path = False
        if import_path.find('game') == 0 or \
            import_path.find('game') == 1:
            is_package_path = True

        if not is_package_path:
            raw_path = unreal.Paths.project_content_dir()
            content_dir = unreal.Paths.make_standard_filename(raw_path)
            import_path = import_path.replace(content_dir,"")
            import_path = os.path.join(os.path.sep, "Game", import_path)

        import_options = ast.literal_eval(import_options)
        import_options["import_as_skeletal"] = False
        destination_name = import_options.pop("destination_name", None)
        save = import_options.pop("save", True)
        import_asset_path = assets.import_fbx_asset(
            fbx_file,
            import_path,
            destination_name=destination_name,
            save=save,
            import_options=import_options,
        )

        return import_asset_path

    # ==================================================================================================================
    # SKELETAL MESHES
    # ==================================================================================================================

    @unreal.ufunction(
        params=[str, str, str],
        ret=str,
        static=True,
        meta=dict(Category="ueGear Commands"),
    )
    def import_skeletal_mesh(fbx_file, import_path, import_options):
        """
        Imports skeletal mesh from FBX file.

        :param str import_path: skeletal mesh FBX file path.
        :param str import_options: FBX import options as a string.
        :return: imported skeletal mesh asset path.
        :rtype: str
        """

        try:
            import_options = ast.literal_eval(import_options)

            # If a skeletal string encoded dictionary exists, convert it to a dict.
            skeletal_data = import_options.get("skeletal_mesh_import_data", None)
            if skeletal_data:
                skeletal_data = ast.literal_eval(skeletal_data)
                import_options["skeletal_mesh_import_data"] = skeletal_data

        except SyntaxError:
            import_options = dict()

        name = import_options.get("destination_name", None)
        if name:
            import_options.pop("destination_name")

        import_options["import_as_skeletal"] = True

        import_asset_path = assets.import_fbx_asset(
            fbx_file,
            import_path,
            destination_name = name,
            import_options=import_options
        )

        return import_asset_path

    @unreal.ufunction(
        params=[bool],
        ret=unreal.Array(unreal.StringValuePair),
        static=True,
        meta=dict(Category="ueGear Commands"),)
    def get_skeletons_data(skeletal_mesh=False):
        """
        Returns a list of skeletons or skeletal meshes, that exist in the open unreal project.

        :param bool skeletal_mesh: If True return SkeletalMesh data, False return Skeleton data.
        :return: The package_name and asset_name. Stored in an Array of Key Value pairs.
        :rtype: unreal.Array(unreal.StringValuePair)
        """
        skeleton_list = unreal.Array(unreal.StringValuePair)

        if skeletal_mesh:
            skeletons = assets.get_skeleton_meshes()
        else:
            skeletons = assets.get_skeletons()

        for skeleton in skeletons:
            package_name = skeleton.get_editor_property("package_name")
            asset_name = skeleton.get_editor_property("asset_name")
            skeleton_list.append(unreal.StringValuePair(package_name, asset_name))

        return skeleton_list

    # ==================================================================================================================
    # ANIMATED SKELETAL MESHES
    # ==================================================================================================================
    @unreal.ufunction(
        params=[str, str, str, str],
        ret=unreal.Array(str),
        static=True,
        meta=dict(Category="ueGear Commands"),)
    def import_animation(animation_path, dest_path, name, skeleton_path):
        """
        Imports an Skeletal Animation into Unreal.
        
        :param str animation_path: Path to FBX location
        :param str dest_path: Package path to the folder that will store the animation.
        :param str name: Name of the animation file
        :param str skeleton_path: Package path to the Skeleton in Unreal
        
        :return: imported path.
        :rtype: str
        """
        result = assets.import_fbx_animation(fbx_path=animation_path, 
                                    dest_path=dest_path, 
                                    anim_sequence_name=name,
                                    skeleton_path=skeleton_path
                                    )
        
        return result

    # ==================================================================================================================
    # TEXTURES
    # ==================================================================================================================

    @unreal.ufunction(
        params=[str, str, str],
        ret=str,
        static=True,
        meta=dict(Category="ueGear Commands"),
    )
    def import_texture(texture_file, import_path, import_options):
        """
        Imports texture from disk into Unreal Asset.

        :param str import_path: texture file path.
        :param str import_options: texture import options as a string.
        :return: imported texture asset path.
        :rtype: str
        """

        try:
            import_options = ast.literal_eval(import_options)
        except SyntaxError:
            import_options = dict()
        import_asset_path = textures.import_texture_asset(
            texture_file, import_path, import_options=import_options
        )

        return import_asset_path

    # ==================================================================================================================
    # MAYA
    # ==================================================================================================================

    @unreal.ufunction(
        params=[str], static=True, meta=dict(Category="ueGear Commands")
    )
    def import_maya_data_from_file(data_file):
        """
        Imports ueGear data from the given file.

        :param str data_file: ueGear data file path.
        """

        mayaio.import_data(data_file)

    @unreal.ufunction(
        params=[str], static=True, meta=dict(Category="ueGear Commands")
    )
    def import_maya_layout_from_file(layout_file):
        """
        Imports ueGear layout from the given file.

        :param str layout_file: layout file path.
        """

        mayaio.import_layout_from_file(layout_file)

    @unreal.ufunction(
        params=[str, bool],
        ret=str,
        static=True,
        meta=dict(Category="ueGear Commands"),
    )
    def export_maya_layout(directory, export_assets):
        """
        Exports ueGear layout into Maya.

        :param str directory: export directory.
        """
        layout_data = list()
        actors_mapping = dict()

        level_asset = unreal.LevelEditorSubsystem().get_current_level()
        level_name = unreal.SystemLibrary.get_object_name(level_asset)

        level_actors = (
            actors.get_selected_actors_in_current_level()
            or actors.get_all_actors_in_current_level()
        )
        if not level_actors:
            unreal.log_warning("No actors to export")
            return ""

        for actor in level_actors:
            actor_asset = actors.get_actor_asset(actor)
            if not actor_asset:
                unreal.log_warning(
                    "Was not possible to retrieve asset for actor: {}".format(
                        actor
                    )
                )
                continue
            actor_asset_name = actor_asset.get_path_name()
            actors_mapping.setdefault(
                actor_asset_name, {"actors": list(), "export_path": ""}
            )
            actors_mapping[actor_asset_name]["actors"].append(actor)

        # Export assets
        if export_assets:
            actors_list = list(actors_mapping.keys())
            with unreal.ScopedSlowTask(
                len(actors_list), "Exporting Asset: {}".format(actors_list[0])
            ) as slow_task:
                slow_task.make_dialog(True)
                for asset_path in list(actors_mapping.keys()):
                    actor_asset = assets.get_asset(asset_path)
                    export_asset_path = assets.export_fbx_asset(
                        actor_asset, directory=directory
                    )
                    actors_mapping[asset_path][
                        "export_path"
                    ] = export_asset_path
                    slow_task.enter_progress_frame(
                        1, "Exporting Asset: {}".format(asset_path)
                    )

        for asset_path, asset_data in actors_mapping.items():
            asset_actors = asset_data["actors"]
            for asset_actor in asset_actors:
                actor_data = {
                    "guid": asset_actor.get_editor_property(
                        "actor_guid"
                    ).to_string(),
                    "name": asset_actor.get_actor_label(),
                    "path": asset_actor.get_path_name(),
                    "translation": asset_actor.get_actor_location().to_tuple(),
                    "rotation": asset_actor.get_actor_rotation().to_tuple(),
                    "scale": asset_actor.get_actor_scale3d().to_tuple(),
                    "assetPath": "/".join(asset_path.split("/")[:-1]),
                    "assetName": asset_path.split("/")[-1].split(".")[0],
                    "assetExportPath": asset_data["export_path"],
                    "assetType": unreal.EditorAssetLibrary.get_metadata_tag(
                        asset_actor, tag.TAG_ASSET_TYPE_ATTR_NAME
                    )
                    or "",
                }
                layout_data.append(actor_data)

        output_file_path = os.path.join(
            directory, "{}_layout.json".format(level_name)
        )
        result = helpers.write_to_json_file(layout_data, output_file_path)
        if not result:
            unreal.log_error("Was not possible to save ueGear layout file")
            return ""

        return output_file_path

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

from . import helpers, mayaio, structs, tag, assets, actors, textures

importlib.reload(helpers)
importlib.reload(structs)
importlib.reload(tag)
importlib.reload(assets)
importlib.reload(actors)
importlib.reload(textures)
importlib.reload(mayaio)


# TODO: For some reason, unreal.Array(float) parameters defined within ufunction params argument are not
# TODO: with the correct number of elements within the list. As a temporal workaround, we convert them
# TODO: to strings in the client side and we parse them here.
# TODO: Update this once fix is done in Remote Control plugin.

@unreal.uclass()
class PyUeGearCommands(unreal.UeGearCommands):

    # ==================================================================================================================
    # OVERRIDES
    # ==================================================================================================================

    @unreal.ufunction(override=True, meta=dict(Category='ueGear Commands'))
    def import_maya_data(self):
        """
        Opens a file window that allow users to choose a JSON file that contains all the info needed to import asset or
        layout data.
        """

        mayaio.import_data()

    @unreal.ufunction(override=True, meta=dict(Category='ueGear Commands'))
    def import_maya_layout(self):
        """
        Opens a file window that allow users to choose a JSON file that contains layout data to load.
        """

        mayaio.import_layout_from_file()

    @unreal.ufunction(override=True, meta=dict(Category='ueGear Commands'))
    def export_unreal_layout(self):
        """
        Exports a layout JSON file based on the objects on the current Unreal level.
        """

        mayaio.export_layout_file()

    # ==================================================================================================================
    # ASSETS
    # ==================================================================================================================

    @unreal.ufunction(params=[str], ret=bool, static=True, meta=dict(Category='ueGear Commands'))
    def does_asset_exist(asset_path=''):
        """
        Returns whether asset exists at given path.

        :return: True if asset exists; False otherwise.
        :rtype: bool
        """

        return assets.asset_exists(asset_path)

    @unreal.ufunction(params=[str, str], ret=str, static=True, meta=dict(Category='ueGear Commands'))
    def rename_asset(asset_path, new_name):
        """
        Renames asset with new given name.
        """

        new_name = assets.rename_asset(asset_path, new_name)
        unreal.log('Renamed to {}'.format(new_name))
        return new_name

    @unreal.ufunction(params=[str], ret=unreal.Array(structs.AssetExportData), static=True, meta=dict(Category='ueGear Commands'))
    def export_selected_assets(directory):
        """
        Export into given directory current Content Browser selected assets.

        :param str directory: directory where assets will be exported.
        :return: list of asset export data struct instances.
        :rtype: list(structs.AssetExportData)
        """

        return mayaio.export_assets(directory)

    # ==================================================================================================================
    # ACTORS
    # ==================================================================================================================

    @unreal.ufunction(params=[str, str, str, str], static=True, meta=dict(Category='ueGear Commands'))
    def set_actor_world_transform(actor_name, translation, rotation, scale):
        """
        Sect the world transform of the actor with given name withing current opened level.

        :param str translation: actor world translation as a string [float, float, float] .
        :param str rotation: actor world rotation as a string [float, float, float].
        :param str scale: actor world scale as a string [float, float, float].
        """

        # Actor is found using actor label within Unreal level.
        # TODO: Actor labels are not unique, so if two actors have the same label then maybe we are going to update
        # TODO: an undesired one. Try to find a workaround for this.
        found_actor = actors.get_actor_by_label_in_current_level(actor_name)
        if not found_actor:
            unreal.log_warning('No Actor found with label: "{}"'.format(actor_name))
            return

        ue_transform = unreal.Transform()
        rotation = ast.literal_eval(rotation)
        ue_transform.rotation = unreal.Rotator(rotation[0], rotation[1], rotation[2] * -1.0).quaternion()
        ue_transform.translation = unreal.Vector(*ast.literal_eval(translation))
        ue_transform.scale3d = unreal.Vector(*ast.literal_eval(scale))

        found_actor.set_actor_transform(ue_transform, False, False)

    # ==================================================================================================================
    # SKELETAL MESHES
    # ==================================================================================================================

    @unreal.ufunction(params=[str, str, str], ret=str, static=True, meta=dict(Category='ueGear Commands'))
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
        except SyntaxError:
            import_options = dict()
        import_options['import_as_skeletal'] = True
        import_asset_path = assets.import_fbx_asset(fbx_file, import_path, import_options=import_options)

        return import_asset_path

    # ==================================================================================================================
    # TEXTURES
    # ==================================================================================================================

    @unreal.ufunction(params=[str, str, str], ret=str, static=True, meta=dict(Category='ueGear Commands'))
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
        import_asset_path = textures.import_texture_asset(texture_file, import_path, import_options=import_options)

        return import_asset_path

    # ==================================================================================================================
    # MAYA
    # ==================================================================================================================

    @unreal.ufunction(params=[str], static=True, meta=dict(Category='ueGear Commands'))
    def import_maya_data_from_file(data_file):
        """
        Imports ueGear data from the given file.

        :param str data_file: ueGear data file path.
        """

        mayaio.import_data(data_file)

    @unreal.ufunction(params=[str], static=True, meta=dict(Category='ueGear Commands'))
    def import_maya_layout_from_file(layout_file):
        """
        Imports ueGear layout from the given file.

        :param str layout_file: layout file path.
        """

        mayaio.import_layout_from_file(layout_file)

    @unreal.ufunction(params=[str, bool], ret=str, static=True, meta=dict(Category='ueGear Commands'))
    def export_maya_layout(directory, export_assets):
        """
        Exports ueGear layout into Maya.

        :param str directory: export directory.
        """

        directory = r'E:\assets\warehouse\assets\output'

        layout_data = list()
        actors_mapping = dict()

        level_asset = unreal.LevelEditorSubsystem().get_current_level()
        level_name = unreal.SystemLibrary.get_object_name(level_asset)

        level_actors = actors.get_selected_actors_in_current_level() or actors.get_all_actors_in_current_level()
        if not level_actors:
            unreal.log_warning('No actors to export')
            return ''

        for actor in level_actors:
            actor_asset = actors.get_actor_asset(actor)
            if not actor_asset:
                unreal.log_warning('Was not possible to retrieve asset for actor: {}'.format(actor))
                continue
            actor_asset_name = actor_asset.get_path_name()
            actors_mapping.setdefault(actor_asset_name, {'actors': list(), 'export_path': ''})
            actors_mapping[actor_asset_name]['actors'].append(actor)

        # Export assets
        if export_assets:
            actors_list = list(actors_mapping.keys())
            with unreal.ScopedSlowTask(len(actors_list), 'Exporting Asset: {}'.format(actors_list[0])) as slow_task:
                slow_task.make_dialog(True)
                for asset_path in list(actors_mapping.keys()):
                    actor_asset = assets.get_asset(asset_path)
                    export_asset_path = assets.export_fbx_asset(actor_asset, directory=directory)
                    actors_mapping[asset_path]['export_path'] = export_asset_path
                    slow_task.enter_progress_frame(1, 'Exporting Asset: {}'.format(asset_path))

        for asset_path, asset_data in actors_mapping.items():
            asset_actors = asset_data['actors']
            for asset_actor in asset_actors:
                actor_data = {
                    'guid': asset_actor.get_editor_property('actor_guid').to_string(),
                    'name': asset_actor.get_actor_label(),
                    'path': asset_actor.get_path_name(),
                    'translation': asset_actor.get_actor_location().to_tuple(),
                    'rotation': asset_actor.get_actor_rotation().to_tuple(),
                    'scale': asset_actor.get_actor_scale3d().to_tuple(),
                    'assetPath': '/'.join(asset_path.split('/')[:-1]),
                    'assetName': asset_path.split('/')[-1].split('.')[0],
                    'assetExportPath': asset_data['export_path'],
                    'assetType': unreal.EditorAssetLibrary.get_metadata_tag(
                        asset_actor, tag.TAG_ASSET_TYPE_ATTR_NAME) or ''
                }
                layout_data.append(actor_data)

        output_file_path = os.path.join(directory, '{}_layout.json'.format(level_name))
        result = helpers.write_to_json_file(layout_data, output_file_path)
        if not result:
            unreal.log_error('Was not possible to save ueGear layout file')
            return ''

        return output_file_path

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

from . import helpers, mayaio
importlib.reload(helpers)
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

        mayaio.import_layout()

    @unreal.ufunction(override=True, meta=dict(Category='ueGear Commands'))
    def export_unreal_layout(self):
        """
        Exports a layout JSON file based on the objects on the current Unreal level.
        """

        mayaio.export_layout()

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

        return helpers.asset_exists(asset_path)

    @unreal.ufunction(params=[str, str], ret=str, static=True, meta=dict(Category='ueGear Commands'))
    def rename_asset(asset_path, new_name):
        """
        Renames asset with new given name.
        """

        new_name = helpers.rename_asset(asset_path, new_name)
        unreal.log('Renamed to {}'.format(new_name))
        return new_name

    @unreal.ufunction(params=[str], ret=unreal.Array(str), static=True, meta=dict(Category='ueGear Commands'))
    def export_selected_assets(directory):
        """
        Export into given directory current Content Browser selected assets.

        :param str directory: directory where assets will be exported.
        """

        export_files = list()
        result = mayaio.export_assets(directory)
        for export_data in result:
            export_files.append('{};{}'.format(export_data['fbx'], export_data['json']))

        return export_files

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
        found_actor = helpers.get_actor_by_label_in_current_level(actor_name)
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
        import_asset_path = helpers.import_fbx_asset(fbx_file, import_path, import_options=import_options)

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
        import_asset_path = helpers.import_texture_asset(texture_file, import_path, import_options=import_options)

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

        mayaio.import_layout(layout_file)

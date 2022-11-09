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

from . import helpers


# ======================================================================================================================
# BASE
# ======================================================================================================================

def import_data(source_files=None, destination_path='', start_frame=1, end_frame=1):

	root = tk.Tk()
	root.withdraw()

	source_files = helpers.force_list(
		source_files or filedialog.askopenfilenames(filetypes=[('ueGear JSON files', '*.json')]))
	if not source_files:
		return False

	level_sequence_name = ''
	level_sequence_asset = None
	source_files_sorted = list()
	layout_files = list()
	animation_files = list()

	for source_file in source_files:
		if source_file.endswith('_animation.json'):
			animation_files.append(source_file)
		elif source_file.endswith('_layout.json'):
			layout_files.append(source_file)
		else:
			source_files_sorted.append(source_file)
	source_files_sorted = source_files_sorted + layout_files + animation_files

	for source_file in source_files_sorted:
		if not source_file:
			unreal.log_warning('ueGear JSON file not found!')
			continue
		json_data = helpers.read_json_file(source_file)
		if not json_data:
			unreal.log_error('ueGear JSON file "{}" contains invalid data!'.format(source_file))
			continue

		is_shot = True

		print(json_data)

	return True


# ======================================================================================================================
# ASSETS
# ======================================================================================================================

def export_assets(export_directory, assets=None):
	"""
	Exports Unreal assets into FBX in the given directory.

	:param str export_directory: absolute path export directory where asset FBX files will be located.
	:param list(unreal.Object) or None assets: list of assets to export. If not given, current Content Browser selected
		assets will be exported.
	:return: list of export asset files.
	:rtype: list(dict)
	"""

	asset_export_files = list()

	assets = helpers.force_list(assets or list(helpers.get_selected_assets()))
	if not assets:
		unreal.log_warning('No assets to export')
		return asset_export_files

	for asset in assets:

		print(asset)

		asset_fbx_file = helpers.export_fbx_asset(asset, export_directory)
		if not asset_fbx_file or not os.path.isfile(asset_fbx_file):
			continue
		asset_name = asset.get_name()
		asset_data = {
			'name': asset_name,
			'path': asset.get_path_name()
		}
		json_file_path = os.path.join(export_directory, '{}.json'.format(asset_name))
		result = helpers.write_to_json_file(asset_data, json_file_path)
		if not result:
			unreal.log_error('Wa not possible to save ueGear export asset file')
			continue
		asset_export_files.append({
			'fbx': asset_fbx_file,
			'json': json_file_path
		})

	return asset_export_files


# ======================================================================================================================
# LAYOUT
# ======================================================================================================================

def import_layout(layout_file_path=''):

	if not layout_file_path:
		root = tk.Tk()
		root.withdraw()
		layout_file_path = filedialog.askopenfile(
			title='Select ueGear Layout file to load', filetypes=[('ueGear Layout files', '*.json')])
		layout_file_path = layout_file_path.name if layout_file_path else None
	if not layout_file_path or not os.path.isfile(layout_file_path):
		unreal.log_error('No valid Layout file path selected!')
		return False

	actors = helpers.get_all_actors_in_current_level()
	actors_names = list()
	for actor in actors:
		actors_names.append(actor.get_actor_label())

	layout_data = helpers.read_json_file(layout_file_path)
	if not layout_data:
		unreal.log_error('Was not possible to load layout data from layout file: {}'.format(layout_file_path))
		return False

	namespace = ''

	for layout_asset_name, layout_asset_data in layout_data.items():
		actor_in_level_name = layout_asset_name
		if ':' in layout_asset_name:
			namespace = layout_asset_name.split(':')[0]
			actor_in_level_name = '{}_{}'.format(namespace, layout_asset_name.split(':')[-1])

		source_name = layout_asset_data.get('sourceName', '')
		translation_value = layout_asset_data.get('translation', None)
		rotation_value = layout_asset_data.get('rotation', None)
		scale_value = layout_asset_data.get('scale', None)
		if not source_name or not translation_value or not rotation_value or not scale_value:
			unreal.log_warning(
				'Layout Asset "{}" was not stored properly within layout file:\n\tsourceName:{}\n\ttranslation:{}'
				'\n\trotation:{}\n\tscale:{}'.format(
					layout_asset_data, source_name, translation_value, rotation_value, scale_value))
			continue

		current_position, current_rotation, current_scale = helpers.convert_maya_transforms_into_unreal_transforms(
			translation_value, rotation_value, scale_value)

		source_asset_path = ''

		if not layout_asset_name == actor_in_level_name:
			if layout_asset_name in actors_names:
				if not actor_in_level_name in actors_names:
					current_actor = actors[actors_names.index(layout_asset_name)]
					current_actor.set_actor_label(actor_in_level_name)
					actors_names.append(actor_in_level_name)

		if actor_in_level_name in actors_names:
			unreal.log('Updating transform on {}'.format(actor_in_level_name))
			current_actor = actors[actors_names.index(actor_in_level_name)]
			current_actor.set_actor_location(current_position, False, True)
			current_actor.set_actor_rotation(current_rotation, True)
			current_actor.set_actor_scale3d(current_scale)
		else:
			asset_paths = helpers.list_asset_paths('/Game/Assets/', recursive=True, include_folder=False)
			for asset_path in asset_paths:
				if '{}.{}'.format(source_name, source_name) in asset_path:
					source_asset_path = asset_path
					break

			if not source_asset_path:
				unreal.log('Skipping actor: {}'.format(actor_in_level_name))
				continue

			source_asset = unreal.load_asset(source_asset_path)
			unreal.log('Creating ' + actor_in_level_name + '...')
			current_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
				source_asset, current_position, current_rotation)
			current_actor.set_actor_label(actor_in_level_name)
			current_actor.set_actor_location(current_position, False, True)
			current_actor.set_actor_rotation(current_rotation, False)
			current_actor.set_actor_scale3d(current_scale)
			actors_names.append(actor_in_level_name)
			actors.append(current_actor)

	return True


def export_layout(output_path=''):
	"""
	Exports ueGear layout file.

	:param str output_path: optional ueGear output directory.
	:return: True if the export layout operation was successful; False otherwise.
	:rtype: bool
	"""

	root = tk.Tk()
	root.withdraw()
	output_path = output_path or filedialog.askdirectory(title='Select output folder for layout export')
	if not output_path or not os.path.isdir(output_path):
		unreal.log_warning('No valid export layout directory defined!')
		return False

	level_asset = unreal.LevelEditorSubsystem().get_current_level()
	level_name = unreal.SystemLibrary.get_object_name(level_asset)
	actors = helpers.get_all_actors_in_current_level()

	layout_data = list()
	for level_actor in actors:
		layout_data.append(
			{
				'guid': str(level_actor.get_editor_property('actor_guid ')),
				'name': level_actor.get_actor_label(),
				'path': level_actor.get_path_name(),
				'translation': level_actor.get_actor_location().to_tuple(),
				'rotation': level_actor.get_actor_rotation().to_tuple(),
				'scale': level_actor.get_actor_scale3d().to_tuple()
			}
		)

	output_file_path = os.path.join(output_path, '{}_layout.json'.format(level_name))
	result = helpers.write_to_json_file(layout_data, output_file_path)
	if not result:
		unreal.log_error('Wa not possible to save ueGear layout file')
		return False

	unreal.log('Exported ueGear layout file: {}'.format(output_file_path))

	return True


# ======================================================================================================================
# CAMERA
# ======================================================================================================================


def import_camera(destination_path='', level_sequence_name='', camera_name='', file_path='', custom_params=None):

	if destination_path and not destination_path.endswith('/'):
		destination_path = destination_path + '/'

	world = helpers.get_editor_world()
	actors, actor_labels = helpers.get_all_actors_and_labels_in_current_level()
	level_sequence_name = destination_path + level_sequence_name
	level_sequence_asset = unreal.load_asset(level_sequence_name)
	if not level_sequence_asset:
		unreal.log_warning('Impossible to import camera because no level sequence asset found with name: "{}"'.format(
			level_sequence_name))
		return False

	bindings = level_sequence_asset.get_bindings()

	if camera_name in actor_labels:
		helpers.remove_sequence_camera(level_sequence_name=level_sequence_name, camera_name=camera_name)
		helpers.delete_actor(actors[actor_labels.index(camera_name)])
		helpers.save_current_level()

	import_options = unreal.MovieSceneUserImportFBXSettings()
	import_options.set_editor_property('create_cameras', 1)
	import_options.set_editor_property('force_front_x_axis', 0)
	import_options.set_editor_property('match_by_name_only', 0)
	import_options.set_editor_property('reduce_keys', 0)
	import_options.set_editor_property('reduce_keys_tolerance', .0001)

	unreal.SequencerTools.import_level_sequence_fbx(world, level_sequence_asset, bindings, import_options, file_path)

	actors, actor_labels = helpers.get_all_actors_and_labels_in_current_level()
	camera_asset = actors[actor_labels.index(camera_name)]

	if custom_params:
		camera_component = camera_asset.get_cine_camera_component()
		camera_component.set_editor_property("ortho_far_clip_plane", custom_params['farClipPlane'])
		camera_component.set_editor_property("ortho_near_clip_plane", custom_params['nearClipPlane'])
		camera_focus_settings = unreal.CameraFocusSettings()
		camera_focus_settings.focus_method = unreal.CameraFocusMethod.DISABLE
		camera_component.set_editor_property("focus_settings",camera_focus_settings)

	helpers.save_current_level()

	unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()
	unreal.EditorAssetLibrary.save_asset(level_sequence_name)

	return True


# importlib.reload(mayaio); mayaio.import_camera('/Game/Assets/Cinematics', 'shot0050_01', 'camera1', 'E:/assets/warehouse/scenes/output/camera1.fbx')

def export_camera(camera_name):
	"""
	Exports camera with given name.

	:param str camera_name: name of the camera to export.
	:return: export data.
	"""

	export_directory = helpers.create_temporary_directory()
	fbx_filename = '{}.fbx'.format(camera_name)

	current_level = unreal.EditorLevelLibrary.get_editor_world().get_path_name()





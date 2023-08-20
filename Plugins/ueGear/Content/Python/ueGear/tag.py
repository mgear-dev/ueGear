#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Unreal tag functionality for ueGear.
"""

from __future__ import print_function, division, absolute_import

import unreal

from . import helpers, assets

TAG_ASSET_TYPE_ATTR_NAME = "ueGearAssetType"
TAG_ASSET_ID_ATTR_NAME = "ueGearAssetId"


class TagTypes(object):
    """
    Class that holds all available tag types.
    """

    Skeleton = "skeleton"
    StaticMesh = "staticmesh"
    SkeletalMesh = "skeletalmesh"
    Alembic = "alembic"
    MetahumanBody = "metahumanbody"
    MetahumanFace = "metahumanface"


def auto_tag(asset=None, remove=False, save_assets=False):
    """
    Automatically tags given (or current selected assets) so ueGear exporter can identify how to export the specific
    assets.

    :param unreal.Object asset: Unreal asset to tag.
    :param bool remove: if True tag will be removed.
    :param bool save_assets: whether to save assets after tag is done.
    """

    found_assets = helpers.force_list(asset or list(assets.selected_assets()))

    for asset in found_assets:
        asset_class = asset.get_class()
        asset_name = asset.get_name()

        if asset_class == unreal.SkeletalMesh.static_class():
            remove_tag(asset) if remove else apply_tag(
                asset, attribute_value=TagTypes.SkeletalMesh
            )
        elif asset_class == unreal.StaticMesh.static_class():
            remove_tag(asset) if remove else apply_tag(
                asset, attribute_value=TagTypes.StaticMesh
            )
        elif asset_class == unreal.Skeleton.static_class():
            remove_tag(asset) if remove else apply_tag(
                asset, attribute_value=TagTypes.Skeleton
            )

        remove_tag(asset, TAG_ASSET_ID_ATTR_NAME) if remove else apply_tag(
            asset, TAG_ASSET_ID_ATTR_NAME, asset_name
        )

    if save_assets:
        with unreal.ScopedEditorTransaction("ueGear auto tag"):
            unreal.EditorAssetLibrary.save_loaded_assets(found_assets)


def apply_tag(
    asset=None, attribute_name=TAG_ASSET_TYPE_ATTR_NAME, attribute_value=""
):
    """
    Creates a new tag attribute with given value into given node/s (or selected nodes).

    :param unreal.Object or list(unreal.Object) or None asset: asset to apply tag to.
    :param str attribute_name: tag attribute value to use. By default, TAG_ASSET_TYPE_ATTR_NAME will be used.
    :param str attribute_value: value to set tag to.
    """

    found_assets = helpers.force_list(asset or list(assets.selected_assets()))
    attribute_value = str(attribute_value)

    for asset in found_assets:
        unreal.EditorAssetLibrary.set_metadata_tag(
            asset, attribute_name, attribute_value
        )
        if attribute_value:
            unreal.log(
                'Tagged "{}.{}" as {}.'.format(
                    asset, attribute_name, attribute_value
                )
            )
        else:
            unreal.log(
                'Tagged "{}.{}" as empty.'.format(asset, attribute_name)
            )


def remove_tag(asset=None, attribute_name=TAG_ASSET_TYPE_ATTR_NAME):
    """
    Removes tag attribute from the given node.

    :param unreal.Object or list(unreal.Object) or None asset: assets to remove tag from.
    :param str attribute_name: tag attribute value to remove. By default, TAG_ASSET_TYPE_ATTR_NAME will be used.
    """

    found_assets = helpers.force_list(asset or list(assets.selected_assets()))

    for asset in found_assets:
        if not unreal.EditorAssetLibrary.get_metadata_tag(
            asset, attribute_name
        ):
            continue
        unreal.EditorAssetLibrary.remove_metadata_tag(asset, attribute_name)
        unreal.log(
            'Removed attribute {} from "{}"'.format(attribute_name, asset)
        )

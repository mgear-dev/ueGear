#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ueGear Commands
"""

from __future__ import print_function, division, absolute_import

import ast
from importlib import reload

import unreal

from ueGear import helpers
reload(helpers)


@unreal.uclass()
class UeGearCommands(unreal.BlueprintFunctionLibrary):

    # TODO: For some reason, unreal.Array(float) parameters defined within ufunction params argument are not
    # TODO: with the correct number of elements within the list. As a temporal workaround, we convert them
    # TODO: to strings in the client side and we parse them here.
    # TODO: Update this once fix is done in Remote Control plugin.

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

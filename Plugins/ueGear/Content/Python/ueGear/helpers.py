#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains helper functions used by ueGear Unreal commands
"""

from __future__ import print_function, division, absolute_import

import unreal


def get_all_actors_in_current_level():
	"""
	Returns all current actors in the current opened level.

	:return: list of actors within level.
	:rtype: list(unreal.Actor)
	"""

	return unreal.EditorActorSubsystem().get_all_level_actors()


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

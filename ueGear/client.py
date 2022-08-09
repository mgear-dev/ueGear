#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
ueGear Client to interact with ueGear Commands within Unreal Engine
"""

from __future__ import print_function, division, absolute_import

import json
import pprint
from urllib.request import urlopen, Request

import pymel.core as pm
import maya.cmds as cmds

from ueGear import utils


class UeGearClient(object):
    """
    Unreal Engine Gear Client
    """

    def __init__(self, port=30010, host_address='127.0.0.1'):
        super(UeGearClient, self).__init__()

        self._host_address = host_address
        self._port = port
        self._timeout = 1000                    # connection to the server will time out after this value.
        self._echo_execution = True             # whether client should print the response coming from server.
        self._echo_payload = True               # whether client should print the JSON payload it's sending to server.
        self._is_executing = False              # whether client is still executing a command.
        self._commands_object_path = '/Engine/PythonTypes.Default__UeGearCommands'
        self._headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def port(self):
        return self._port

    @property
    def host_address(self):
        return self._host_address

    @property
    def is_executing(self):
        return self._is_executing

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    @property
    def echo_execution(self):
        return self._echo_execution

    @echo_execution.setter
    def echo_execution(self, value):
        self._echo_execution = value

    @property
    def echo_payload(self):
        return self._echo_payload

    @echo_payload.setter
    def echo_payload(self, value):
        self._echo_payload = value

    @property
    def commands_object_path(self):
        return self._commands_object_path

    @commands_object_path.setter
    def commands_object_path(self, value):
        self._commands_object_path = value

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def execute(self, command, parameters=None, timeout=0):
        """
        Executes given command for this client. The server will look for this command in the modules it has loaded.

        :param str command:  The command name that you want to execute within UeGearCommands class.
        :param dict parameters: arguments for the command to execute. These have to match the argument names on the
            function exactly.
        :param float timeout: time in seconds after which the request will timeout.
        :return: response coming from the Unreal Remote Server.
        :rtype: dict
        """

        self._is_executing = True
        timeout = timeout if timeout > 0 else self._timeout
        parameters = parameters or dict()

        url = 'http://{}:{}/remote/object/call'.format(self._host_address, self._port)
        payload = {
            'objectPath': self._commands_object_path,
            'functionName': command,
            'parameters': parameters,
            'generateTransaction': True
        }
        try:
            request = Request(url, json.dumps(payload).encode('ascii'), self._headers, method='PUT')
            with urlopen(request, timeout=timeout) as response:
                response = json.load(response)
        except Exception:
            response = {'return': False}
        try:
            evaluated_return = eval(response.get('return'))
            response = {'return': evaluated_return}
        except Exception:
            pass

        if self._echo_payload:
            pprint.pprint(payload)

        if self._echo_execution:
            pprint.pprint(response)

        self._is_executing = False

        return response

    # =================================================================================================================
    # TRANSFORM COMMANDS
    # =================================================================================================================

    def transform_selected_objects(self):
        """
        Updates matching Unreal objects within current level with the tranforms of the currently selected
        objects in Maya scene.
        """

        selected_nodes = pm.selected()
        old_rotation_orders = list()
        for selected_node in selected_nodes:
            old_rotation_orders.append(selected_node.getRotationOrder())
            selected_node.setRotationOrder('XZY', True)
        try:
            objects = cmds.ls(sl=True, sn=True)
            for obj in objects:
                ue_world_transform = utils.get_unreal_engine_transform_for_maya_node(obj)
                result =self.execute('set_actor_world_transform', parameters={
                'actor_name': obj,
                'translation': str(ue_world_transform['rotatePivot']),
                'rotation': str(ue_world_transform['rotation']),
                'scale': str(ue_world_transform['scale']),
                })
        finally:
            for i, selected_node in enumerate(selected_nodes):
                selected_node.setRotationOrder(old_rotation_orders[i], True)

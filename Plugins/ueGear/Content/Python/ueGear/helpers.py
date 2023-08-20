#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains helper functions used by ueGear Unreal commands.
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import json
import tempfile
import subprocess
import pkg_resources
from collections import OrderedDict

import unreal

if sys.version_info[0] == 2:
    string_types = (basestring,)
    text_type = unicode
else:
    string_types = (str,)
    text_type = str

SEPARATOR = "/"
BAD_SEPARATOR = "\\"
PATH_SEPARATOR = "//"
SERVER_PREFIX = "\\"
RELATIVE_PATH_PREFIX = "./"
BAD_RELATIVE_PATH_PREFIX = "../"
WEB_PREFIX = "https://"


def is_python2():
    """
    Returns whether current version is Python 2

    :return: bool
    """

    return sys.version_info[0] == 2


def is_python3():
    """
    Returns whether current version is Python 3

    :return: bool
    """

    return sys.version_info[0] == 3


def is_string(s):
    """
    Returns True if the given object has None type or False otherwise.

    :param s: object
    :return: bool
    """

    return isinstance(s, string_types)


def force_list(var):
    """
    Returns the given variable as list.

    :param object var: object we want to convert to list
    :return: object as list.
    :rtype: list(object)
    """

    if var is None:
        return list()

    if type(var) is not list:
        if type(var) in [tuple]:
            var = list(var)
        else:
            var = [var]

    return var


def get_index_in_list(list_arg, index, default=None):
    """
    Returns the item at given index. If item does not exist, returns default value.

    :param list(any) list_arg: list of objects to get from.
    :param int index: index to get object at.
    :param any default: any value to return as default.
    :return: any
    """

    return (
        list_arg[index] if list_arg and len(list_arg) > abs(index) else default
    )


def get_first_in_list(list_arg, default=None):
    """
    Returns the first element of the list. If list is empty, returns default value.

    :param list(any) list_arg: An empty or not empty list.
    :param any default: If list is empty, something to return.
    :return: Returns the first element of the list.  If list is empty, returns default value.
    :rtype: any
    """

    return get_index_in_list(list_arg, 0, default=default)


def normalize_path(path):
    """
    Normalizes a path to make sure that path only contains forward slashes.

    :param str path: path to normalize.
    :return: normalized path
    :rtype: str
    """

    path = path.replace(BAD_SEPARATOR, SEPARATOR).replace(
        PATH_SEPARATOR, SEPARATOR
    )

    if is_python2():
        try:
            path = unicode(
                path.replace(r"\\", r"\\\\"), "unicode_escape"
            ).encode("utf-8")
        except TypeError:
            path = path.replace(r"\\", r"\\\\").encode("utf-8")

    return path.rstrip("/")


def clean_path(path):
    """
    Cleans a path. Useful to resolve problems with slashes

    :param str path: path we want to clean
    :return: clean path
    :rtype: str
    """

    if not path:
        return ""

    # convert '~' Unix character to user's home directory
    path = os.path.expanduser(str(path))

    # Remove spaces from path and fixed bad slashes
    path = normalize_path(path.strip())

    # fix server paths
    is_server_path = path.startswith(SERVER_PREFIX)
    while SERVER_PREFIX in path:
        path = path.replace(SERVER_PREFIX, PATH_SEPARATOR)
    if is_server_path:
        path = PATH_SEPARATOR + path

    # fix web paths
    if not path.find(WEB_PREFIX) > -1:
        path = path.replace(PATH_SEPARATOR, SEPARATOR)

    # make sure drive letter is capitalized
    drive, tail = os.path.splitdrive(path)
    if drive:
        path = path[0].upper() + path[1:]

    return path


def create_temporary_directory(prefix="ueGear"):
    """
    Creates a temporary directory.

    :param str prefix: optional temporal directory prefix.
    :return: absolute file path to temporary directory.
    :rtype: str
    """

    return tempfile.mkdtemp(prefix="{}}_tmp_".format(prefix))


def read_json_file(filename, maintain_order=False):
    """
    Returns data from JSON file.

    :param str filename: name of JSON file we want to read data from.
    :param bool maintain_order: whether to maintain the order of the returned dictionary or not.
    :return: data readed from JSON file as dictionary.
    :return: dict
    """

    if os.stat(filename).st_size == 0:
        return None
    else:
        try:
            with open(filename, "r") as json_file:
                if maintain_order:
                    data = json.load(json_file, object_pairs_hook=OrderedDict)
                else:
                    data = json.load(json_file)
        except Exception as err:
            unreal.log_warning("Could not read {0}".format(filename))
            raise err

    return data


def write_to_json_file(data, filename, **kwargs):
    """
    Writes data to JSON file.

    :param dict, data: data to store into JSON file.
    :param str filename: name of the JSON file we want to store data into.
    :param dict, kwargs:
    :return: file name of the stored file.
    :rtype: str
    """

    indent = kwargs.pop("indent", 4)

    try:
        with open(filename, "w") as json_file:
            json.dump(data, json_file, indent=indent, **kwargs)
    except IOError:
        unreal.log_error("Data not saved to file {}".format(filename))
        return None

    unreal.log("File correctly saved to: {}".format(filename))

    return filename


def get_unreal_version_name():
    """
    Returns the version name of Unreal engine.

    :return: Unreal engine version name.
    :rtype: str
    """

    return unreal.SystemLibrary.get_engine_version()


def get_unreal_version():
    """
    Returns current version of Unreal engine.

    :return: Unreal engine version list.
    :rtype: list(int)
    """

    version_name = get_unreal_version_name()
    version_split = version_name.split("+++")[0]
    versions = version_split.split("-")
    main_version = versions[0].split(".")
    extra_version = versions[-1]
    version_int = [int(version) for version in main_version]
    version_int.append(int(extra_version))

    return version_int


def get_current_unreal_project_path():
    """
    Returns the current Unreal project absolute file path.

    :return: Absolute path to current .uproject file.
    :rtype: str
    """

    return unreal.Paths.get_project_file_path()


def save_current_level():
    """
    Saves current Unreal level.
    """

    unreal.EditorLevelLibrary.save_current_level()


def get_editor_world():
    """
    Returns the world in the editor world. It can then be used as WorldContext by other libraries like GameplayStatics.

    :return: world used by the editor world.
    :rtype: unreal.World
    """

    return unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem
    ).get_editor_world()


def get_game_world():
    """
    Returns the game world.

    :return: game world.
    :rtype: unreal.World
    """

    return unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem
    ).get_game_world()


def create_folder(root, name):
    """
    Creates new folder.

    :param str root: root path.
    :param str name: folder name.
    :return: newly created folder.
    :rtype: str
    """

    index = 1
    while True:
        if not unreal.EditorAssetLibrary.does_directory_exist(
            "{}/{}".format(root, name)
        ):
            unreal.EditorAssetLibrary.make_directory(
                "{}/{}".format(root, name)
            )
            break
        name = "{}{}".format(name, index)
        index += 1

    return "{}/{}".format(root, name)


def convert_maya_transforms_into_unreal_transforms(
    translation, rotation, scale
):
    """
    Converts given Maya transforms into Unreal transforms.

    :param list(float, float, float) translation:
    :param list(float, float, float) rotation:
    :param list(float, float, float) scale:
    :return: Unreal transforms.
    :rtype: tuple(unreal.Vector, unreal.Vector, unreal.Vector)
    """

    maya_translation = translation or [0.0, 0.0, 0.0]
    maya_rotation = rotation or [0.0, 0.0, 0.0]
    maya_scale = scale or [1.0, 1.0, 1.0]

    # unreal_translation = unreal.Vector(maya_translation[0], maya_translation[2], maya_translation[1])
    # unreal_rotation = unreal.Rotator(maya_rotation[0], maya_rotation[2], maya_rotation[1] * -1)
    # unreal_scale = unreal.Vector(maya_scale[0], maya_scale[2], maya_scale[1])

    unreal_translation = unreal.Vector(
        -maya_translation[0] * -1, maya_translation[2], maya_translation[1]
    )
    unreal_rotation = unreal.Rotator(
        maya_rotation[0] + 90, maya_rotation[2], maya_rotation[1] * -1
    )
    unreal_scale = unreal.Vector(maya_scale[0], maya_scale[1], maya_scale[2])

    return unreal_translation, unreal_rotation, unreal_scale


def clear_level_selection():
    """
    Clears the selection of the current opened level.
    """

    unreal.EditorLevelLibrary().select_nothing()


def get_unreal_python_interpreter_path():
    """
    Returns path where Unreal Python interpreter is located.

    :return: Unreal Python interpreter absolute path.
    :rtype: str
    """

    return unreal.get_interpreter_executable_path()


def pip_install(packages):
    packages = set(packages)
    installed_packages = {pkg.key for pkg in pkg_resources.working_set}
    missing = packages - installed_packages

    if not missing:
        unreal.log("All Python requirements already satisfied!")
        return

    python_interpreter_path = get_unreal_python_interpreter_path()
    if not python_interpreter_path or os.path.exists(python_interpreter_path):
        unreal.log_warning(
            "Impossible to install packages ({}) using pip because Unreal Python interpreter was not found: {}!".format(
                packages, python_interpreter_path
            )
        )
        return

    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    proc = subprocess.Popen(
        [
            python_interpreter_path,
            "-m",
            "pip",
            "install",
            "--no-warn-script-location",
            *packages,
        ],
        startupinfo=info,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    while proc.poll() is None:
        unreal.log(proc.stdout.readline().strip())
        unreal.log_warning(proc.stderr.readline().strip())

    return proc.poll()

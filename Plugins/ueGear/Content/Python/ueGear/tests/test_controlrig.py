import os

import unreal

from ueGear.controlrig import mgear
from ueGear.controlrig.manager import UEGearManager
from ueGear import assets

# ---
# TO BE REMOVED FROM FINAL RELEASE
import importlib
from ueGear.controlrig import manager as ueM
from ueGear.controlrig.components import *
from ueGear.controlrig import components
from ueGear.controlrig.mgear import component, rig
importlib.reload(components)
importlib.reload(mgear)
importlib.reload(component)
importlib.reload(rig)
importlib.reload(ueM)

# ---

def test_build_component_count():
    TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.scd"
    mgear_rig = mgear.convert_json_to_mg_rig(TEST_BUILD_JSON)
    if len(mgear_rig.components) == 55:
        print("Test: Component Count Correct: 55 Components")
    else:
        unreal.log_error("Test: Component Count Correct: Failed")


def test_build_fk_count():
    TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.scd"
    mgear_rig = mgear.convert_json_to_mg_rig(TEST_BUILD_JSON)
    fk_components = mgear_rig.get_component_by_type("EPIC_control_01")
    if len(fk_components) == 19:
        print("Test: FK Component Count Correct: 19 Found")
    else:
        unreal.log_error("Test: FK Component Count Correct: Failed")


def test_create_control_rig_bp():
    """
    Testing the creation of an empty blueprint and the creation of a blueprint from a skeleton.
    """
    TEST_CONTROLRIG_PATH = "/Game/TEST/test_empty_control_rig_bp"
    gear_manager = UEGearManager()

    # Create
    bp_1 = gear_manager.create_controlrig_by_location(TEST_CONTROLRIG_PATH)

    bp_2 = gear_manager.create_control_rig("test_empty_skm_control_rig_bp",
                                           "/Game/TEST",
                                           skm_package_path="/Game/ButcherBoy/ButcherBoy_Master")

    if bp_1 and bp_2:
        print("Test: Create Empty Blueprint: Successful")
    else:
        unreal.log_error("Test: Create Empty Blueprint: Failed")

    # Clean up
    unreal.EditorAssetLibrary.delete_directory("/Game/TEST/")


def test_create_fk_control():
    """
    Test will check to see if a control is generated and added to the correct Construction, Forward and Backwards Solve.

    - No active control rig is set, so it should generate a new control rig
    """
    TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.scd"
    TEST_CONTROLRIG_PATH = "/Game/TEST"
    TEST_CONTROLRIG_NAME = "test_create_fk_control"
    TEST_CONTROLRIG_SKM = "/Game/ButcherBoy/ButcherBoy_Master"

    # Converts teh json data into a class based structure, filters out non-required metadata.
    mgear_rig = mgear.convert_json_to_mg_rig(TEST_BUILD_JSON)

    gear_manager = UEGearManager()
    gear_manager.load_rig(mgear_rig)

    # Creates an asset path
    cr_path = TEST_CONTROLRIG_PATH + "/" + TEST_CONTROLRIG_NAME
    # Control Rig Blueprint
    cr_bp = assets.get_asset_object(cr_path)

    if cr_bp is None:
        cr_bp = gear_manager.create_control_rig(TEST_CONTROLRIG_PATH, TEST_CONTROLRIG_NAME, TEST_CONTROLRIG_SKM)
    else:
        gear_manager.set_active_blueprint(cr_bp)

    if cr_bp is None:
        unreal.log_error("Test: test_create_fk_control - Failed : Could not create control rig blue print")
        unreal.EditorAssetLibrary.delete_directory("/Game/TEST/")
        return None

    # At this point we now have The Manager, with an empty Control Rig BP

    # Builds the world control if it has been enabled in the Main Settings
    gear_manager.build_world_control()

    # Builds component by name
    gear_manager.build_component('global_C0', ignore_parent=True)

    fk_components = mgear_rig.get_component_by_type("EPIC_control_01")
    gear_manager.build_component(fk_components[1].fullname, ignore_parent=True)

    gear_manager.build_component('root_C0', ignore_parent=True)

    # At this point there are many components created, but not connected to one another

    gear_manager.populate_parents()

    gear_manager.connect_components()

    gear_manager.group_components()


def test_create_spine_shoulders_control():
    """
    Test will check to see if a control is generated and added to the correct Construction, Forward and Backwards Solve.

    - No active control rig is set, so it should generate a new control rig
    """
    TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.gnx"
    TEST_CONTROLRIG_PATH = "/Game/TEST"
    TEST_CONTROLRIG_NAME = "test_create_rig"
    TEST_CONTROLRIG_SKM = "/Game/ButcherBoy/ButcherBoy_Master"

    # Converts teh json data into a class based structure, filters out non-required metadata.
    mgear_rig = mgear.convert_json_to_mg_rig(TEST_BUILD_JSON)

    gear_manager = UEGearManager()
    gear_manager.load_rig(mgear_rig)

    # Creates an asset path
    cr_path = TEST_CONTROLRIG_PATH + "/" + TEST_CONTROLRIG_NAME
    # Control Rig Blueprint
    cr_bp = assets.get_asset_object(cr_path)

    if cr_bp is None:
        cr_bp = gear_manager.create_control_rig(TEST_CONTROLRIG_PATH, TEST_CONTROLRIG_NAME, TEST_CONTROLRIG_SKM)
    else:
        gear_manager.set_active_blueprint(cr_bp)

    if cr_bp is None:
        unreal.log_error("Test: test_create_fk_control - Failed : Could not create control rig blue print")
        unreal.EditorAssetLibrary.delete_directory("/Game/TEST/")
        return None

    # At this point we now have The Manager, with an empty Control Rig BP

    # Builds the world control if it has been enabled in the Main Settings
    gear_manager.build_world_control()

    # Builds component by name
    gear_manager.build_component('global_C0', ignore_parent=True)
    gear_manager.build_component('local_C0', ignore_parent=True)
    gear_manager.build_component('root_C0', ignore_parent=True)
    gear_manager.build_component('body_C0', ignore_parent=True)
    gear_manager.build_component('spine_C0', ignore_parent=True)

    gear_manager.build_component('neck_C0', ignore_parent=True)

    gear_manager.build_component('shoulder_L0', ignore_parent=True)
    # gear_manager.build_component('shoulder_R0', ignore_parent=True)
    #
    gear_manager.build_component('arm_L0', ignore_parent=True)
    # gear_manager.build_component('arm_R0', ignore_parent=True)
    #
    # gear_manager.build_component('leg_L0', ignore_parent=True)
    # gear_manager.build_component('leg_R0', ignore_parent=True)
    #
    # gear_manager.build_component('foot_L0', ignore_parent=True)
    # gear_manager.build_component('foot_R0', ignore_parent=True)

    gear_manager.build_component("finger_L0")
    gear_manager.build_component("finger_L1")
    gear_manager.build_component("finger_L2")
    gear_manager.build_component("finger_L3")
    gear_manager.build_component("thumb_L0")
    gear_manager.build_component("meta_L0")

    # At this point there are many components created, but not connected to one another

    gear_manager.populate_parents()

    gear_manager.connect_components()

    gear_manager.group_components()


def test_build_mgRig():
    """
    Test to build an entire mgear rig from the JSON file

    - No active control rig is set, so it should generate a new control rig
    """
    TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.scd"
    TEST_CONTROLRIG_PATH = "/Game/TEST"
    TEST_CONTROLRIG_NAME = "test_create_fk_control"
    TEST_CONTROLRIG_SKM = "/Game/ButcherBoy/ButcherBoy_Master"

    # Converts teh json data into a class based structure, filters out non-required metadata.
    mgear_rig = mgear.convert_json_to_mg_rig(TEST_BUILD_JSON)

    gear_manager = UEGearManager()
    gear_manager.load_rig(mgear_rig)

    # Creates an asset path
    cr_path = TEST_CONTROLRIG_PATH + "/" + TEST_CONTROLRIG_NAME
    # Control Rig Blueprint
    cr_bp = assets.get_asset_object(cr_path)

    if cr_bp is None:
        cr_bp = gear_manager.create_control_rig(TEST_CONTROLRIG_PATH, TEST_CONTROLRIG_NAME, TEST_CONTROLRIG_SKM)
    else:
        gear_manager.set_active_blueprint(cr_bp)

    if cr_bp is None:
        unreal.log_error("Test: test_create_fk_control - Failed : Could not create control rig blue print")
        unreal.EditorAssetLibrary.delete_directory("/Game/TEST/")
        return None

    # At this point we now have The Manager, with an empty Control Rig BP

    # Builds the world control if it has been enabled in the Main Settings
    gear_manager.build_world_control()

    # Builds all components
    gear_manager.build_components()

    # gear_manager.populate_parents()

    # gear_manager.connect_components()

def test_manager_create_control_rig():
    TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.gnx"
    TEST_CONTROLRIG_PATH = "/Game/TEST"
    TEST_CONTROLRIG_NAME = "test_manager_create"
    TEST_CONTROLRIG_SKM = "/Game/ButcherBoy/ButcherBoy_Master"

    ueM.create_control_rig(TEST_CONTROLRIG_NAME,
                           TEST_CONTROLRIG_SKM,
                           TEST_CONTROLRIG_PATH,
                           TEST_BUILD_JSON)

#----

# test_build_component_count()
# test_build_fk_count()
# test_create_control_rig_bp()
# test_create_fk_control()

# test_create_spine_shoulders_control()

# test_build_mgRig()

test_manager_create_control_rig()
import unreal

from ueGear.controlrig import mComponents
from ueGear.controlrig.manager import UEGearManager

#---
# TO BE REMOVED FROM FINAL RELEASE
import importlib
from ueGear.controlrig import manager as ueM

importlib.reload(ueM)
importlib.reload(mComponents)
#---

def test_build_component_count():
    TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.scd"
    mgear_rig = mComponents.convert_json_to_mg_rig(TEST_BUILD_JSON)
    if len(mgear_rig.components) == 55:
        print("Test: Component Count Correct: 55 Components")
    else:
        unreal.log_error("Test: Component Count Correct: Failed")


def test_build_fk_count():
    TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.scd"
    mgear_rig = mComponents.convert_json_to_mg_rig(TEST_BUILD_JSON)
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
                                           skm_path="/Game/ButcherBoy/ButcherBoy_Master")

    if bp_1 and bp_2:
        print("Test: Create Empty Blueprint: Successful")
    else:
        unreal.log_error("Test: Create Empty Blueprint: Failed")

    # Clean up
    unreal.EditorAssetLibrary.delete_directory("/Game/TEST/")


def test_create_fk_control():
    """
    Test will check to see if a control is generated and added to the correct Contruction, Forward and Backwards Solve.

    - No active control rig is set, so it should generate a new control rig
    """
    TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.scd"
    TEST_CONTROLRIG_PATH = "/Game/TEST"
    TEST_CONTROLRIG_NAME = "test_create_fk_control"
    TEST_CONTROLRIG_SKM = "/Game/ButcherBoy/ButcherBoy_Master"

    mgear_rig = mComponents.convert_json_to_mg_rig(TEST_BUILD_JSON)

    gear_manager = UEGearManager()
    gear_manager.load_rig(mgear_rig)
    cr_bp = gear_manager.create_control_rig(TEST_CONTROLRIG_NAME, TEST_CONTROLRIG_PATH, TEST_CONTROLRIG_SKM)

    if cr_bp is None:
        unreal.log_error("Test: test_create_fk_control - Failed : Could not create control rig blue print")
        unreal.EditorAssetLibrary.delete_directory("/Game/TEST/")

    # At this point we now have The Manager, with an empty Control Rig BP

    # [ ] Trying to get one component to be created
    gear_manager.build_component('global_C0', ignore_parent=True)

    fk_components = mgear_rig.get_component_by_type("EPIC_control_01")

#----

# test_build_component_count()
# test_build_fk_count()
# test_create_control_rig_bp()

test_create_fk_control()
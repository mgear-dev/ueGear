# from ueGear.controlrig import components
import ueGear.controlrig.mgear as mgear

if __name__ == "__main__":
    TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.scd"
    #   TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\ueGear_ControlRig\butcherBuildData_v002.scd"
    mg_guide_data = mgear.convert_json_to_mg_rig(TEST_BUILD_JSON)

# Test basic component
cf_lookup_component = {}

# available_components = components.lookup_mgear_component("EPIC_control_01")
# print(available_components)

import json
import unreal

from ueGear import assets as ue_assets

import importlib
importlib.reload(ue_assets)
"""
The thought behind this investigation it to 
-[ ] load in the build data JSON file. 
-[ ] Find the serialised skeleton and related datablobs
-[ ] Collect the data to pass it to the Control Rig generation

IDEA
-[ ] Discussion: Generate the JSON data from the skeleton, even if it was not created at 'Build' time?
"""

class mgComponent():
    """
    Simple Component object that wraps the maya compoent data, for easy access
    """

    fullname:str = ""
    """Components Fullname, this is usually used as the default name"""
    name:str = ""
    """Name of the Component."""
    side:str = ""
    """The side that the component exists on. L(left), R(right) C(center)."""
    comp_type:str = ""
    """The mGear Component Type, that was used in Maya to generate it."""
    data_contracts:dict = {}

    def __init__(self) -> None:
        pass


class mgRig():
    """
    Simple Component object that wraps the mGear Maya Rig
    """
    components:dict[str, mgComponent] = {}

    def __init__(self) -> None:
        pass

    def component(self, name:str=None, new_component:mgComponent=None):
        """
        Gets or Sets the specific component.

        If setting the compnent, you can specify the name, or leave it blank and it will default to the new_components name
        """
        if new_component and name:
            self.components[name] = new_component
        elif new_component:
            self.components[new_component.fullname] = new_component

        return self.components.get(name, None)

    def __repr__(self) -> str:
        msg = ""
        for (name, comp) in self.components.items():
            msg +=  "o------------------\n"
            msg += f"|  Rig's Key    : {name}\n"
            msg += f"|     Full Name : {comp.fullname}\n"
            msg += f"|          Name : {comp.name}\n"
            msg += f"|          Side : {comp.side}\n"
            msg += f"|          Type : {comp.comp_type}\n"
            msg +=  "o - - - - - - - - -\n"
        return msg

def load_json_file(file_path):
    """
    Load a JSON file using the json module.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def convert_json_to_mg_rig(build_json_path:str) -> mgRig:
    """
    Converts the mGear build json file into a mgRig object.

    This process filters out all none required data.
    """
    data = load_json_file(build_json_path)

    rig = mgRig()

    for component in data["Components"]:
        if len(component["DataContracts"]) > 0:
            component_type = component["Type"]
            component_side = component["Side"]
            component_name = component["Name"]
            component_fullname = component["FullName"]
            data_contrat = component["DataContracts"]

            mgear_component = mgComponent()
            mgear_component.name = component_name
            mgear_component.side = component_side
            mgear_component.comp_type = component_type
            mgear_component.fullname = component_fullname

            rig.component(new_component=mgear_component)

            for contract_name in data_contrat:
                related_joints = component[contract_name]
                mgear_component.data_contracts[contract_name] = related_joints

    return rig


UE_GEAR_FUNCTION_LIBRARY_PATH = "/Game/StarterContent/Character/ueGearFunctionLibrary.ueGearFunctionLibrary_C"

class ueGearManager():

    _factory:unreal.ControlRigBlueprintFactory = None
    _cr_blueprints:list[unreal.ControlRigBlueprint] = []
    _active_blueprint:unreal.ControlRigBlueprint = None

    _ue_gear_standard_library = None

    @property
    def active_control_rig(self):
        return self._active_blueprint

    @active_control_rig.setter
    def active_control_rig(self, value):
        self._active_blueprint = value

    def __init__(self) -> None:
        """
        Initialises the ueGear Manager, making sure that the plugin exists and the factory has been accessed.
        """
        unreal.load_module('ControlRigDeveloper')
        factory = unreal.ControlRigBlueprintFactory
        self.get_open_controlrig_blueprints()

    def get_open_controlrig_blueprints(self):
        """Gets all open Control Rig Blueprints
        
        Defaults the active CR BP to the first element in the list
        """
        cr_blueprints = unreal.ControlRigBlueprint.get_currently_open_rig_blueprints()

        self._set_control_blueprint(cr_blueprints)

        return self._cr_blueprints

    def _set_control_blueprint(self, control_blueprints):
        """
        Assigns all the control blueprints and will assign the first element to the active CR BP

        :param list(unreal.ControlRigBlueprint) control_blueprints: list of control rig blueprints.
        """
        self._cr_blueprints = control_blueprints

        # No CR BP found to be open.
        if len(self._cr_blueprints) == 0:
            self.set_active_blueprint(None)
            self._cr_blueprints = []
            return None

        self.set_active_blueprint(self._cr_blueprints[0])


    def set_active_blueprint(self, bp:unreal.ControlRigBlueprint):
        """Sets the blueprint that will be getting modified by the ueGearManager"""
        self._active_blueprint = bp

    def create_control_rig(self, cr_name:str, cr_path:str):
        """Generates a new Control Rig Blueprint
        
        cr_name:str = Name of the control rig file
        cr_path:str = Path to the location where the new cr will be generated.
        """
        pass

    def create_component(self):
        pass

    # SUB MODULE - Control Rig Interface. -------------
    #   This may be abstracting away to much

    def create_node(self):
        pass

    def select_node(self, node_name:str):
        pass

    def select_nodes(self):
        pass

    # ---------------------------------------

    def create_controlrig_by_location(self, package_path, set_default=True):
        """
        Creates the control rig at the specific location, and set the manager to use the newly created control rig.

        package_path: path to the newly created control rig blue print.
        set_default: If disabled, the manager will not automatically set the active CR BP to the newly created CR BP.
        """
        factory = unreal.ControlRigBlueprintFactory()
        rig = factory.create_new_control_rig_asset(desired_package_path = package_path)

        if set_default:
            self._active_blueprint = rig

        return rig

    def create_controlrig_by_mesh(self, mesh_package_path):
        # load a skeletal mesh
        mesh = unreal.load_object(name = mesh_package_path, outer = None)
        # create a control rig for the mesh
        factory = unreal.ControlRigBlueprintFactory
        rig = factory.create_control_rig_from_skeletal_mesh_or_skeleton(selected_object = mesh)
        return rig

    def set_active_control_rig(self, path=None):
        """
        Sets the active control rig to be the selected control rig blue print in the Content Browser.
        """

        if path:
            loaded_control_rig = unreal.load_object(name = path, outer = None)
            self.set_active_blueprint(loaded_control_rig)

            if loaded_control_rig == None:
                print(f"Warning: No Control Rig Blue Print found at {path}")
                return None

            return loaded_control_rig

        selected_blueprints = ue_assets.selected_assets(unreal.ControlRigBlueprint)

        self._set_control_blueprint(selected_blueprints)

        return self._active_blueprint

#----------------------------------------------------------------------

# .add_external_function_reference_node(UE_GEAR_FUNCTION_LIBRARY_PATH, 'gear_FK_Constructor', unreal.Vector2D(-1649.118012, -931.602505), 'gear_FK_Constructor')
# .set_node_selection(['gear_FK_Constructor'])


TEST_BUILD_JSON = "/Users/simonanderson/Desktop/SIJO_STUDIOS/Contract_Work/mGear/GIT_REPOS/ueGear/Plugins/ueGear/Content/Python/ueGear/controlrig/butcher_data.json"
TEST_CR_PATH = "/Game/StarterContent/Character/anim_test_001_CtrlRig.anim_test_001_CtrlRig"

mgear_rig = convert_json_to_mg_rig(TEST_BUILD_JSON)

gear_manager = ueGearManager()
print(f"Active CR BP : {gear_manager._active_blueprint}")
print(f"Open CR BP : {gear_manager._cr_blueprints}")

# gear_manager.load_rig(mgear_rig)
# manager.create_controlrig_by_location()

#active_blueprint = gear_manager.set_active_control_rig()
gear_manager.set_active_control_rig(TEST_CR_PATH)


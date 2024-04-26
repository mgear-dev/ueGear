import json

import unreal

from ueGear import assets as ue_assets

import importlib

importlib.reload(ue_assets)

from ueGear.controlrig import mComponents

importlib.reload(mComponents)
"""
The thought behind this investigation it to 
-[ ] load in the build data JSON file. 
-[ ] Find the serialised skeleton and related datablobs
-[ ] Collect the data to pass it to the Control Rig generation

IDEA
-[ ] Discussion: Generate the JSON data from the skeleton, even if it was not created at 'Build' time?
"""

UE_GEAR_FUNCTION_LIBRARY_PATH = "/ueGear/Python/ueGear/controlrig/ueGearFunctionLibrary.ueGearFunctionLibrary_C"
"""Location of the Function Library that stores all the ueGear functions, that will be used to generate the Control Rig"""


class UEGearManager:
    _factory: unreal.ControlRigBlueprintFactory = None
    """Unreals Control Rig Blue Print Factory. This performs all the alterations to the Control Rig"""

    _cr_blueprints: list[unreal.ControlRigBlueprint] = []
    """List of all available blueprints"""

    _active_blueprint: unreal.ControlRigBlueprint = None
    """The Active Blueprint is the current blueprint that will be modified by the UE Gear Manager"""

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
        self._factory = unreal.ControlRigBlueprintFactory
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

    def set_active_blueprint(self, bp: unreal.ControlRigBlueprint):
        """Sets the blueprint that will be getting modified by the ueGearManager

        The Control Rig Blueprint that will be modified by the  manager, is referred to as the "Active Blueprint"
        """
        self._active_blueprint = bp

    def create_control_rig(self, cr_name: str, cr_path: str, skm_path: str, set_default=True):
        """Generates a new Control Rig Blueprint

        NOTE: This method requires a Skeleton Mesh to generate the Control Rig.

        By default, this will fail if a control rig already exists at the location.
        The newly created control rig will be set to the "Active Control Rig"

        cr_name:str = Name of the control rig file
        cr_path:str = Package Path to the location where the new cr will be generated.
        skeleton_path = Path to the Skeleton Mesh object that will be used to generate the control rig
        """

        # Check control rig does not exists
        # Check skeleton to use exists
        # Create Control Rig blue print
        # Set control rig to active blueprint

        package_path = unreal.Paths.combine([cr_path, cr_name])
        if unreal.Paths.file_exists(package_path):
            unreal.log_warning("Control Rig File already exists")
            return None

        if not ue_assets.asset_exists(skm_path):
            unreal.log_warning(f"Skeleton Mesh not found - {skm_path}")
            return None

        # Generates Control Rig Blueprint in place
        skm_obj = ue_assets.get_asset_object(skm_path)
        blueprint = self._factory.create_control_rig_from_skeletal_mesh_or_skeleton(skm_obj)

        if blueprint is None:
            unreal.log_warning(f"Failed to create Control Rig BP - {package_path}")
            return None

        # Move blueprint to correct location
        moved_success = unreal.EditorAssetLibrary.rename_asset(blueprint.get_path_name(), package_path)
        if not moved_success:
            unreal.log_warning(f"Failed to rename Control Rig BP - {blueprint.get_path_name()}")
            # Deletes invalid CRBP which is now stale, and should not exist in this location.
            unreal.EditorAssetLibrary.delete_asset(blueprint.get_path_name())
            return None

        if set_default:
            self._active_blueprint = blueprint

        return blueprint

    def create_component(self, name: str):
        pass

    # SUB MODULE - Control Rig Interface. -------------
    #   This may be abstracting away to much

    def create_node(self):
        pass

    def select_node(self, node_name: str):
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
        rig = factory.create_new_control_rig_asset(desired_package_path=package_path)

        if set_default:
            self._active_blueprint = rig

        return rig

    def create_controlrig_by_mesh(self, mesh_package_path):
        """Generates the control rig using the mesh package path"""
        # load a skeletal mesh
        mesh = unreal.load_object(name=mesh_package_path, outer=None)
        # create a control rig for the mesh
        factory = unreal.ControlRigBlueprintFactory
        rig = factory.create_control_rig_from_skeletal_mesh_or_skeleton(selected_object=mesh)
        return rig

    def set_active_control_rig(self, path=None):
        """
        Sets the active control rig to be the selected control rig blue print in the Content Browser.
        """

        if path:
            loaded_control_rig = unreal.load_object(name=path, outer=None)
            self.set_active_blueprint(loaded_control_rig)

            if loaded_control_rig == None:
                print(f"Warning: No Control Rig Blue Print found at {path}")
                return None

            return loaded_control_rig

        selected_blueprints = ue_assets.selected_assets(unreal.ControlRigBlueprint)

        self._set_control_blueprint(selected_blueprints)

        return self._active_blueprint

    def load_rig(self, mgear_rig: mComponents.mgRig):
        """
        Loads the mgear rig object into the manager, so the manager can generate the control rig and its components.
        """
        self.mg_rig = mgear_rig

    def get_graph(self) -> unreal.RigVMGraph:
        """
        Gets the graph of the current loaded control rig

        https://docs.unrealengine.com/5.3/en-US/PythonAPI/class/RigVMGraph.html#unreal.RigVMGraph

        """
        rig_vm_controller = self._active_blueprint.get_controller_by_name('RigVMModel')
        active_cr_graph = rig_vm_controller.get_graph()
        return active_cr_graph

    def get_selected_nodes(self) -> list[str]:
        if self._active_blueprint is None:
            print("Error, please set the sctive Control Rig blueprint.")
        graph = self.get_graph()
        return graph.get_select_nodes()


# ----------------------------------------------------------------------

class ComponentAssociation:
    """
    Keeps track of the association between an mGear Component and a ueGear Component
    """
    mgear: str = None
    uegear: str = None
    functions: list = []
    blueprint_variables: list = []

    def __init__(self, mg, ue, funcs, vars) -> None:
        self.mgear = mg
        self.uegear = ue
        self.functions = funcs
        self.blueprint_variables = vars

    def __repr__(self) -> str:
        return f"{self.mgear} = {self.uegear} : {self.functions} : {self.blueprint_variables}"


def test_full_build():
    # Key for this dictionary is the mGear component Type name
    component_conversion = {}
    # component_conversion["EPIC_leg_02"] = ComponentAssociation("EPIC_leg_02", "EPIC_leg_02", ["gear_FK_Construction", "gear_FK_ForwardSolve"], [])
    # component_conversion["EPIC_arm_02"] = ComponentAssociation("EPIC_arm_02", "EPIC_arm_02", ["gear_FK_Construction", "gear_FK_ForwardSolve"], [])
    # component_conversion["EPIC_neck_02"] = ComponentAssociation("EPIC_neck_02", "EPIC_neck_02", {"Construction":["gear_FK_Constructor"], "Forward":["gear_FK_ForwardSolve"]}, [])

    gear_manager.component_association = component_conversion

    print(gear_manager.component_association)

    # How to tell which function is needed to get connected in what order?
    # How to tell which function is needed to get connected to which execte?

    rig_controller = gear_manager.active_control_rig.get_controller_by_name('RigVMModel')

    current_graph = rig_controller.get_graph()

    # Checks the current graph for the Execution nodes, if they do not exist creates them
    has_construction_node = current_graph.find_node("RigUnit_BeginExecution")
    has_forward_node = current_graph.find_node("PrepareForExecution")
    has_inverse_node = current_graph.find_node("InverseExecution")

    for comp_key in gear_manager.mg_rig.components:
        # Gets the data from the mGear Dictionary
        mgear_comp = gear_manager.mg_rig.components[comp_key]
        mgear_comp_type = mgear_comp.comp_type
        ue_gear_comp = component_conversion.get(mgear_comp_type, None)

        if ue_gear_comp is None:
            print(f"Warning: Component Association Missing `{mgear_comp_type}`. Please create a new association.")
            continue

        # Loops over the functions in the component and generates them.
        for function_node_name in ue_gear_comp.functions:

            # Unique name to destinguish the component's functions
            component_function_name = f"{mgear_comp.fullname}_{function_node_name}"

            component_function_exists = current_graph.find_node_by_name(component_function_name)
            print(f"Component Function exists : {component_function_exists}")

            # Component's function does not exist, Create it
            if component_function_exists is None:
                # Create the functions for the component in CR
                function_node = rig_controller.add_external_function_reference_node(UE_GEAR_FUNCTION_LIBRARY_PATH,
                                                                                    function_node_name,
                                                                                    unreal.Vector2D(0, 0),
                                                                                    component_function_name)

        # Attache meta data to bones from the component
        # Check if meta data has already been setup
        # Generate Functions Nodes, and connect them to the available execution pipeline
        # Check if associated node exists in the pipeline already

    # Forward Solve Node
    rig_controller.set_node_selection(['RigUnit_BeginExecution'])

    # Construction Node
    rig_controller.set_node_selection(['PrepareForExecution'])


def create_components_metadata_node(contract_name, skeleton_joints):
    """
    Creates and populates list nodes that represent the component contracts from mGear.

    Will check if the node exists, and if so will clear its pins and create new ones.
    """
    # Node path
    _item_array_node = '/Script/ControlRig.RigUnit_ItemArray'
    # Position where node will be created
    _pos = unreal.Vector2D(0, 0)

    node_name = contract_name + '_ItemArray'

    current_graph = rig_vm_controller.get_graph()
    node_exists = current_graph.find_node_by_name(node_name)

    if node_exists:
        # If node exists, we remove all pins and readd them
        rig_vm_controller.set_pin_default_value(f'{node_name}.Items', '()', True)
    else:
        # Create Item Array Node
        rig_vm_controller.add_unit_node_from_struct_path(_item_array_node, 'Execute', _pos, node_name)

    for index, jnt_name in enumerate(skeleton_joints):
        # add a new pin to the Iteam Array Node, at the end.
        rig_vm_controller.insert_array_pin(f'{node_name}.Items', -1, '')
        # Set Item at array element 0 to be bone type
        rig_vm_controller.set_pin_default_value(f'{node_name}.Items.{index}.Type', 'Bone', False)
        # Set the name of the skeleton joint
        rig_vm_controller.set_pin_default_value(f'{node_name}.Items.{index}.Name', jnt_name, False)

    return node_name


def create_component_meta_data(component: mComponents.MGComponent):
    """
    Creates all the required skeleton joint data contract lookups required for the mgComponent.
    """
    new_cr_nodes = []

    for contract_name in component.data_contracts:
        long_contract_name = f"{component.fullname}_{contract_name}"
        contract_joints = component.data_contracts[contract_name]

        new_node = create_components_metadata_node(contract_name=long_contract_name, skeleton_joints=contract_joints)
        new_cr_nodes.append(new_node)

    # TODO: Still working on grouping the code on creation time, to allow for easier debugging.
    # Creates a Comment Block


#    rig_vm_controller.set_node_selection(new_cr_nodes)
#    rig_vm_controller.add_comment_node(f"{mgear_comp.fullname} mgComponent metadata", unreal.Vector2D(0, 0), unreal.Vector2D(286.000000, 279.000000), unreal.LinearColor(1.000000, 1.000000, 1.000000, 1.000000), f"{mgear_comp.fullname}_Comment")

# ======================================================================

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
    Test will check to see if a control is generated and added to the correct Contruction, Forward and Backwards Solve
    """
    TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.scd"
    TEST_CONTROLRIG_PATH = "/Game/TEST/test_create_fk_control"

    mgear_rig = mComponents.convert_json_to_mg_rig(TEST_BUILD_JSON)
    fk_components = mgear_rig.get_component_by_type("EPIC_control_01")

    gear_manager = UEGearManager()
    gear_manager.load_rig(mgear_rig)
    gear_manager.set_active_control_rig(TEST_CONTROLRIG_PATH)


# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------

# test_build_component_count()
# test_build_fk_count()
test_create_control_rig_bp()

# test_create_fk_control()

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------

TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.scd"
# TEST_CR_PATH = "/Game/StarterContent/Character/anim_test_001_CtrlRig"

mgear_rig = mComponents.convert_json_to_mg_rig(TEST_BUILD_JSON)

gear_manager = UEGearManager()
# gear_manager.load_rig(mgear_rig)
# gear_manager.set_active_control_rig(TEST_CR_PATH)

# rig_vm_controller = gear_manager.active_control_rig.get_controller_by_name('RigVMModel')
# active_cr_graph = rig_vm_controller.get_graph()

# neck_component = gear_manager.mg_rig.components["neck_C0"]

# for comp_key in gear_manager.mg_rig.components:
#    # Gets the data from the mGear Dictionary
#    mgear_comp = gear_manager.mg_rig.components[comp_key]
#    create_component_meta_data(mgear_comp)

# create_component_meta_data(neck_component)

# gear_manager.set_active_control_rig()
# sel_nodes = gear_manager.get_selected_nodes()

# print(sel_nodes)

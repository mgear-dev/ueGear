import json

import unreal

from ueGear import assets as ue_assets

import importlib

importlib.reload(ue_assets)

from ueGear.controlrig.manager import UEGearManager
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





# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------

TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.scd"
# TEST_CR_PATH = "/Game/StarterContent/Character/anim_test_001_CtrlRig"

mgear_rig = mComponents.convert_json_to_mg_rig(TEST_BUILD_JSON)

gear_manager = UEGearManager()
# gear_manager.load_rig(mgear_rig)
# gear_manager.set_active_control_rig(TEST_CR_PATH)

# rig_vm_controller = gear_manager.get_active_controller()
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

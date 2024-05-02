__all__ = ['fkComponent']

import unreal

from ..components import base_component
from .base_component import UEComponent
from ..manager import CONTROL_RIG_FUNCTION_PATH


class fkComponent(UEComponent):
    name = "test_FK"
    mgear_component = "EPIC_control_01"

    # skeleton_joints = None
    # skeleton_array_node = None

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['construct_FK_singleton'],
                          'forward_functions': ['forward_FK_singleton'],
                          'backwards_functions': [],
                          }
        self.cr_variables = {}



    def create_functions(self, controller: unreal.RigVMController = None):
        if controller is None:
            return

        print("-------------------------------")
        print(" Create ControlRig Functions")
        print("-------------------------------")

        # Generate Function Nodes
        for evaluation_path in self.functions.keys():

            # Skip the forward function creation if no joints are needed to be driven
            if evaluation_path == 'forward_functions' and self.metadata.joints is None:
                continue

            for cr_func in self.functions[evaluation_path]:
                new_node_name = f"{self.name}_{cr_func}"

                print(f"  New Node Name: {new_node_name}")

                ue_cr_node = controller.get_graph().find_node_by_name(new_node_name)

                # Create Component if doesn't exist
                if ue_cr_node is None:
                    print("  Generating CR Node...")
                    print(new_node_name)
                    ue_cr_ref_node = controller.add_external_function_reference_node(CONTROL_RIG_FUNCTION_PATH,
                                                                                     cr_func,
                                                                                     unreal.Vector2D(0.0, 0.0),
                                                                                     node_name=new_node_name)
                    # In Unreal, Ref Node inherits from Node
                    ue_cr_node = ue_cr_ref_node
                else:
                    unreal.log_error(f"  Cannot create function {new_node_name}, it already exists")
                    return

                print(ue_cr_node)
                self.nodes[evaluation_path].append(ue_cr_node)

        # Setup the control name
        construct_func = base_component.get_construction_node(self, f"{self.name}_construct_FK_singleton")
        if construct_func is None:
            unreal.log_error("  Create Functions Error - Cannot find construct singleton node")
        controller.set_pin_default_value(construct_func.get_name() + '.control_name',
                                         self.metadata.controls[0],
                                         False)

    def populate_bones(self, bones: list[unreal.RigBoneElement] = None, controller: unreal.RigVMController = None):
        if bones is None or len(bones) > 1:
            return
        if controller is None:
            return
        print("-----------------")
        print(" Populate Bones")
        print("-----------------")

        bone_name = bones[0].key.name
        print(f"  {self.name} > {bone_name}")

        # Unique name for this skeleton node array
        array_node_name = f"{self.metadata.fullname}_RigUnit_ItemArray"

        # node already exists
        if controller.get_graph().find_node_by_name(array_node_name):
            unreal.log_error("Cannot populate bones, node already exists!")
            return

        # Creates an Item Array Node to the control rig
        controller.add_unit_node_from_struct_path(
            '/Script/ControlRig.RigUnit_ItemArray',
            'Execute',
            unreal.Vector2D(-54.908936, 204.649109),
            array_node_name)

        # Populates the Item Array Node
        controller.insert_array_pin(f'{array_node_name}.Items', -1, '')
        controller.set_pin_default_value(f'{array_node_name}.Items.0',
                                         f'(Type=Bone,Name="{bone_name}")',
                                         True)
        controller.set_pin_expansion(f'{array_node_name}.Items.0', True)
        controller.set_pin_expansion(f'{array_node_name}.Items', True)

        # Connects the Item Array Node to the functions.
        for evaluation_path in self.nodes.keys():
            for function_node in self.nodes[evaluation_path]:
                print(f"  Creating Connection:   {array_node_name}.Items >> {function_node.get_name()}.Array")
                controller.add_link(f'{array_node_name}.Items',
                                    f'{function_node.get_name()}.Array')

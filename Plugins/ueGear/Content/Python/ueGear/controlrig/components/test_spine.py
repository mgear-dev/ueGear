__all__ = ['SpineComponent']

import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component
from ueGear.controlrig.components.base_component import UEComponent


class SpineComponent(UEComponent):
    name = "test_Spine"
    mgear_component = "EPIC_spine_02"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['construct_FK_hierarchy'],
                          'forward_functions': ['forward_FK_hierarchy'],
                          'backwards_functions': [],
                          }
        self.cr_variables = {}

        # Control Rig Inputs
        self.cr_inputs = {'construction_functions': ['parent'],
                       'forward_functions': [],
                       'backwards_functions': [],
                       }

        # Control Rig Outputs
        self.cr_output = {'construction_functions': ['root'],
                       'forward_functions': [],
                       'backwards_functions': [],
                       }

        # mGear
        self.inputs = []
        self.outputs = []

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
                    # if exists, add it to the nodes
                    self.nodes[evaluation_path].append(ue_cr_node)

                    unreal.log_error(f"  Cannot create function {new_node_name}, it already exists")
                    continue

                print(ue_cr_node)
                self.nodes[evaluation_path].append(ue_cr_node)

        # Gets the Construction Function Node and sets the control name

        func_name = self.functions['construction_functions'][0]

        print(func_name)

        construct_func = base_component.get_construction_node(self, f"{self.name}_{func_name}")
        print(construct_func)

        if construct_func is None:
            unreal.log_error("  Create Functions Error - Cannot find construct singleton node")
        controller.set_pin_default_value(construct_func.get_name() + '.control_name',
                                         self.metadata.controls[0],
                                         False)


    def populate_bones(self, bones: list[unreal.RigBoneElement] = None, controller: unreal.RigVMController = None):
        """
        Generates the Bone array node that will be utilised by control rig to drive the component
        """
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

    def populate_control_transforms(self, controller: unreal.RigVMController = None):
        """Updates the transform data for the controls generated, with the data from the mgear json
        file.
        """

        print("Still need to set this up")
        return

        control_name = self.metadata.controls[0]
        control_transform = self.metadata.control_transforms[control_name]

        const_func = self.nodes['construction_functions'][0].get_name()

        quat = control_transform.rotation
        pos = control_transform.translation

        controller.set_pin_default_value(f"{const_func}.control_world_transform",
            f"(Rotation=(X={quat.x},Y={quat.y},Z={quat.z},W={quat.w}), "
            f"Translation=(X={pos.x},Y={pos.y},Z={pos.z}),"
            f"Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))",
            True)
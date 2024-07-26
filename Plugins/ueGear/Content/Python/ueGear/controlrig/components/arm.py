__all__ = ['ArmComponent']

import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component
from ueGear.controlrig.components.base_component import UEComponent

class ArmComponent(UEComponent):
    name = "test_Arm"
    mgear_component = "EPIC_arm_02"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['construct_shoulder'],
                          'forward_functions': ['forward_shoulder'],
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

        # calls the super method
        super().create_functions(controller)

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

        construct_func = base_component.get_construction_node(self, f"{self.name}_{func_name}")

        if construct_func is None:
            unreal.log_error("  Create Functions Error - Cannot find construct singleton node")


    def populate_bones(self, bones: list[unreal.RigBoneElement] = None, controller: unreal.RigVMController = None):
        """
        Generates the Bone array node that will be utilised by control rig to drive the component
        """
        if bones is None or len(bones) < 3:
            unreal.log_error("[Bone Populate] Failed - Less then 3 Bones found")
            return
        if controller is None:
            unreal.log_error("[Bone Populate] Failed no Controller found")
            return
        print("-----------------")
        print(" Populate Bones")
        print("-----------------")

        # Unique name for this skeleton node array
        array_node_name = f"{self.metadata.fullname}_bones_RigUnit_ItemArray"

        # node doesn't exists, create the joint node
        if not controller.get_graph().find_node_by_name(array_node_name):
            self._init_master_joint_node(controller, array_node_name, bones)

        #     # Connects the Item Array Node to the functions.
        #     for evaluation_path in self.nodes.keys():
        #         for function_node in self.nodes[evaluation_path]:
        #             print(f"  Creating Connection:   {array_node_name}.Items >> {function_node.get_name()}.Joints")
        #             controller.add_link(f'{array_node_name}.Items',
        #                                 f'{function_node.get_name()}.Joints')
        #
        # outpu_joint_node_name = self._init_output_joints(controller, bones)
        #
        # construction_func_name = self.nodes["construction_functions"][0].get_name()
        #
        # controller.add_link(f'{outpu_joint_node_name}.Items',
        #                     f'{construction_func_name}.joint_outputs')


    def _init_master_joint_node(self, controller, node_name: str, bones):
        """Create the master bones node that will drive the creation of the joint, and be driven by the fk joints
        """

        print(" - Init Master Joints")

        # Creates an Item Array Node to the control rig
        controller.add_unit_node_from_struct_path(
            '/Script/ControlRig.RigUnit_ItemArray',
            'Execute',
            unreal.Vector2D(-54.908936, 204.649109),
            node_name)

        pin_index = 0  # stores the current pin index that is being updated

        for bone in bones:
            bone_name = str(bone.key.name)
            print(f"  {self.name} > {bone_name}")

            # Populates the Item Array Node
            controller.insert_array_pin(f'{node_name}.Items', -1, '')
            controller.set_pin_default_value(f'{node_name}.Items.{str(pin_index)}',
                                             f'(Type=Bone,Name="{bone_name}")',
                                             True)
            controller.set_pin_expansion(f'{node_name}.Items.{str(pin_index)}', True)
            controller.set_pin_expansion(f'{node_name}.Items', True)

            pin_index += 1


    def init_input_data(self, controller: unreal.RigVMController):

        self._set_side_colour(controller)


    def _set_side_colour(self, controller: unreal.RigVMController):
        """Sets the controls default colour depending on the side"""

        construction_node = self.nodes["construction_functions"][0]
        func_name = construction_node.get_name()

        # Sets the colour channels to be 0
        for channel in ["R","G","B"]:
            controller.set_pin_default_value(
                f'{func_name}.colour.{channel}',
                '0.000000',
                False)

        if self.metadata.side == "L":
            controller.set_pin_default_value(
                f'{func_name}.colour.B',
                '1.000000',
                False)

        elif self.metadata.side == "R":
            controller.set_pin_default_value(
                f'{func_name}.colour.G',
                '1.000000',
                False)

        elif self.metadata.side == "M" or self.metadata.side == "C":
            controller.set_pin_default_value(
                f'{func_name}.colour.R',
                '1.000000',
                False)


    def populate_control_transforms(self, controller: unreal.RigVMController = None):
        """Updates the transform data for the controls generated, with the data from the mgear json
        file.
        """
        import ueGear.controlrig.manager as ueMan

        names_node = ueMan.create_array_node(f"{self.metadata.fullname}_control_names", controller)
        trans_node = ueMan.create_array_node(f"{self.metadata.fullname}_control_transforms", controller)

        # Connecting nodes needs to occur first, else the array node does not know the type and will not accept default
        # values
        construction_func_name = self.nodes["construction_functions"][0].get_name()
        controller.add_link(f'{trans_node}.Array',
                            f'{construction_func_name}.world_control_transforms')
        controller.add_link(f'{names_node}.Array',
                            f'{construction_func_name}.control_names')

        # Checks the pins
        name_pins_exist = ueMan.array_node_has_pins(names_node, controller)
        trans_pins_exist = ueMan.array_node_has_pins(trans_node, controller)

        pin_index = 0

        for control_name in self.metadata.controls:
            control_transform = self.metadata.control_transforms[control_name]

            if not name_pins_exist:
                found_node = controller.get_graph().find_node_by_name(names_node)
                existing_pin_count = len(found_node.get_pins()[0].get_sub_pins())
                if existing_pin_count < len(self.metadata.controls):
                    controller.insert_array_pin(f'{names_node}.Values',
                                                -1,
                                                '')
            if not trans_pins_exist:
                found_node = controller.get_graph().find_node_by_name(trans_node)
                existing_pin_count = len(found_node.get_pins()[0].get_sub_pins())
                if existing_pin_count < len(self.metadata.controls):
                    controller.insert_array_pin(f'{trans_node}.Values',
                                                -1,
                                                '')

            quat = control_transform.rotation
            pos = control_transform.translation

            controller.set_pin_default_value(f'{names_node}.Values.{pin_index}',
                                             control_name,
                                             False)

            controller.set_pin_default_value(f"{trans_node}.Values.{pin_index}",
                                             f"(Rotation=(X={quat.x},Y={quat.y},Z={quat.z},W={quat.w}), "
                                             f"Translation=(X={pos.x},Y={pos.y},Z={pos.z}),"
                                             f"Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))",
                                             True)

            pin_index += 1

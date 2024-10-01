__all__ = ['FootComponent']

import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component
from ueGear.controlrig.components.base_component import UEComponent


class FootComponent(UEComponent):
    name = "foot_component"
    mgear_component = "EPIC_foot_01"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ["construct_IK_foot"],
                          'forward_functions': ["forward_IK_foot"],
                          'backwards_functions': [],
                          }
        self.cr_variables = {}

        # Control Rig Inputs
        self.cr_inputs = {'construction_functions': ["parent"],
                          'forward_functions': ["ik_active"],
                          'backwards_functions': [],
                          }

        # Control Rig Outputs
        self.cr_output = {'construction_functions': [],
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

        # Calls the super method, which creates the comment block
        super().create_functions(controller)

        # Generate Function Nodes
        for evaluation_path in self.functions.keys():

            # Skip the forward function creation if no joints are needed to be driven
            if evaluation_path == 'forward_functions' and self.metadata.joints is None:
                continue

            # loop over control rig function nodes
            for cr_func in self.functions[evaluation_path]:
                new_node_name = f"{self.name}_{cr_func}"

                print(f"  New Node Name: {new_node_name}")

                ue_cr_node = controller.get_graph().find_node_by_name(new_node_name)

                # Create Component if it does not exist
                if ue_cr_node is None:
                    print("  Generating CR Node...")
                    print(new_node_name)
                    ue_cr_ref_node = controller.add_external_function_reference_node(CONTROL_RIG_FUNCTION_PATH,
                                                                                     cr_func,
                                                                                     unreal.Vector2D(0.0, 0.0),
                                                                                     node_name=new_node_name)
                    # In Unreal, Ref Node inherits from Node
                    ue_cr_node = ue_cr_ref_node
                    self.nodes[evaluation_path].append(ue_cr_node)
                else:
                    # if exists, add it to the nodes
                    self.nodes[evaluation_path].append(ue_cr_node)

                    unreal.log_error(f"  Cannot create function {new_node_name}, it already exists")
                    continue

        # Gets the Construction Function Node and sets the control name

        func_name = self.functions['construction_functions'][0]

        construct_func = base_component.get_construction_node(self, f"{self.name}_{func_name}")

        if construct_func is None:
            unreal.log_error("  Create Functions Error - Cannot find construct singleton node")

    def populate_bones(self, bones: list[unreal.RigBoneElement] = None, controller: unreal.RigVMController = None):
        """
        Populates the ball joint data on the foot nodes.
        """
        if bones is None or len(bones) != 1:
            unreal.log_error("[Bone Populate] Failed - No Bones found")
            return
        if controller is None:
            unreal.log_error("[Bone Populate] Failed no Controller found")
            return

        print("-----------------")
        print(" Populate Bones")
        print("-----------------")

        # Ball Joint
        ball_jnt = bones[0]
        jnt_name = str(ball_jnt.key.name)

        # Assign ball joint to the construct node

        construction_node = self.nodes["construction_functions"][0]
        controller.set_pin_default_value(f'{construction_node.get_name()}.ball_joint',
                                         f'(Type=Bone, Name="{jnt_name}")',
                                         True)

        # Assign ball joint to the forward node

        forward_node = self.nodes["forward_functions"][0]
        controller.set_pin_default_value(f'{forward_node.get_name()}.ball_joint',
                                         f'(Type=Bone, Name="{jnt_name}")',
                                         True)

    def _init_master_joint_node(self, controller, node_name: str, bones):
        """Creates an array node of all the bones
        """

        print(" - Init Master Joints")

        # Creates an Item Array Node to the control rig
        node = controller.add_unit_node_from_struct_path(
            '/Script/ControlRig.RigUnit_ItemArray',
            'Execute',
            unreal.Vector2D(-54.908936, 204.649109),
            node_name)

        self.add_misc_function(node)

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

        self.set_side_colour(controller)
        # self._set_mirrored_ik_upvector(controller)

    def _set_mirrored_ik_upvector(self, controller: unreal.RigVMController):
        """
        As the legs are mirrored, if a right leg is being built then we need to setup the
        up axis to align with the upvector and joints
        """

        forward_function = self.nodes["forward_functions"][0]
        func_name = forward_function.get_name()

        if self.metadata.side == "R":

            controller.set_pin_default_value(f'{func_name}.ik_PrimaryAxis',
                                             '(X=-1.000000, Y=0.000000, Z=0.000000)',
                                             True)
            controller.set_pin_default_value(f'{func_name}.ik_SecondaryAxis',
                                             '(X=0.000000, Y=1.000000, Z=0.000000)',
                                             True)


    def _set_transform_pin(self, node_name, pin_name, transform_value, controller):
        quat = transform_value.rotation
        pos = transform_value.translation

        controller.set_pin_default_value(f"{node_name}.{pin_name}",
                                         f"("
                                         f"Rotation=(X={quat.x},Y={quat.y},Z={quat.z},W={quat.w}),"
                                         f"Translation=(X={pos.x},Y={pos.y},Z={pos.z}),"
                                         f"Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))",
                                         True)



    def populate_control_transforms(self, controller: unreal.RigVMController = None):
        """Generates the list nodes of controls names and transforms

        The foot does not rely on control positions as it uses the guideTransforms to place the
        locations where the foot will rotate around.
        """
        print("--------------------------------------------------")
        print(" Generating Control Names and Transform Functions")
        print("--------------------------------------------------")

        import ueGear.controlrig.manager as ueMan

        # Gets the construction function name
        construction_func_name = self.nodes["construction_functions"][0].get_name()

        for guide_name, guide_mtx in self.metadata.guide_transforms.items():

            print(guide_name)
            print(guide_mtx)

            transform = guide_mtx.transform()

            pin_name = None

            if guide_name == "root":
                pin_name = "roll"
            elif guide_name == "0_loc":
                pin_name = "tip"
            elif guide_name == "1_loc":
                pin_name = "tip"
            elif guide_name == "heel":
                pin_name = "heel"
            elif guide_name == "outpivot":
                print("todo: outpivot not setup yet")
            elif guide_name == "inpivot":
                print("todo: inpivot not setup yet")

            # todo: clean up or populate the following pins on the function node
            "bk0"
            "bk1"
            "fk"


            # Populate the pins transform data
            if pin_name is None:
                continue

            _trn = transform.translation
            _rot = transform.rotation
            _scl = transform.scale3d

            controller.set_pin_default_value(f'{construction_func_name}.{pin_name}',
                                             f'(Rotation=(X={_rot.x}, Y={_rot.y}, Z={_rot.z},W={_rot.w}),'
                                             f'Translation=(X={_trn.x},Y={_trn.y},Z={_trn.z}),'
                                             f'Scale3D=(X={_scl.x},Y={_scl.y},Z={_scl.z}))',
                                             True)

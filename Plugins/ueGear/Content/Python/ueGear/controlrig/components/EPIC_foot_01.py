import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component


class Component(base_component.UEComponent):
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

        func_name = self.name + "_" + self.functions['construction_functions'][0]

        construct_func = base_component.get_construction_node(self, f"{func_name}")

        if construct_func is None:
            unreal.log_error("  Create Functions Error - Cannot find construct singleton node")
        else:
            # Set construction functions side
            controller.set_pin_default_value(f'{func_name}.side', self.metadata.side, False)

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

    def _set_transform_pin(self, node_name: str, pin_name: str, transform_value: unreal.Transform, controller):
        quat = transform_value.rotation
        pos = transform_value.translation

        controller.set_pin_default_value(f"{node_name}.{pin_name}",
                                         f"("
                                         f"Rotation=(X={quat.x},Y={quat.y},Z={quat.z},W={quat.w}),"
                                         f"Translation=(X={pos.x},Y={pos.y},Z={pos.z}),"
                                         f"Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))",
                                         True)

    # todo: refactor the guide population code here
    def _set_control(self, name, transform, controller: unreal.RigVMController):
        pass

    # todo: refactor the guide population code here
    def _populate_guide_transform(self):
        pass

    def populate_control_transforms(self, controller: unreal.RigVMController = None):
        """Generates the list nodes of controls names and transforms

        The foot does not rely on control positions as it uses the guideTransforms to place the
        locations where the foot will rotate around.
        """
        print("--------------------------------------------------")
        print(" Generating Control Names and Transform Functions")
        print("--------------------------------------------------")

        space_mtx = unreal.Matrix(x_plane=[1.000000, 0.000000, 0.000000, 0.000000],
                                  y_plane=[0.000000, 0.000000, 1.000000, 0.000000],
                                  z_plane=[0.000000, 1.000000, 0.000000, 0.000000],
                                  w_plane=[0.000000, 0.000000, 0.000000, 1.000000])

        # Gets the construction function name
        construction_func_name = self.nodes["construction_functions"][0].get_name()

        for guide_name, guide_mtx in self.metadata.guide_transforms.items():

            # Space Convert between Maya and Unreal
            guide_mtx = guide_mtx * space_mtx
            transform = guide_mtx.transform()

            # Rotates the Maya transformation data
            corrected_quat = unreal.Quat()
            transform.rotation = corrected_quat

            pin_name = None

            if guide_name == "root":
                pin_name = "root"
            elif guide_name == "1_loc":
                pin_name = "tip"
            elif guide_name == "heel":
                pin_name = "heel"
            elif guide_name == "0_loc":
                pin_name = "fk0"
            elif guide_name == "outpivot":
                pin_name = "outer_pivot"
            elif guide_name == "inpivot":
                pin_name = "inner_pivot"

            # Populate the pins transform data
            if pin_name is None:
                continue

            self._set_transform_pin(construction_func_name,
                                    pin_name,
                                    transform,
                                    controller)

        # Setting the transform locations, in a specific order

        if len(self.metadata.controls) != 6:
            raise IOError("Please Contact developer, as only 6 controls are accounted for..")

        # Creates an ordered list of control transforms
        ordered_ctrl_trans = [None] * 6
        ordered_bounding_box = [None] * 6
        role_order = ["heel", "tip", "roll", "bk0", "bk1", "fk0"]

        for ctrl_name in self.metadata.controls:
            # Use the controls.Role metadata to detect the type
            ctrl_role = self.metadata.controls_role[ctrl_name]
            ctrl_trans = self.metadata.control_transforms[ctrl_name]
            ctrl_bb = self.metadata.controls_aabb[ctrl_name]
            # rudementary way of ordering the output list
            if ctrl_role == role_order[0]:
                ordered_ctrl_trans[0] = ctrl_trans
                ordered_bounding_box[0] = ctrl_bb
            elif ctrl_role == role_order[1]:
                ordered_ctrl_trans[1] = ctrl_trans
                ordered_bounding_box[1] = ctrl_bb
            elif ctrl_role == role_order[2]:
                ordered_ctrl_trans[2] = ctrl_trans
                ordered_bounding_box[2] = ctrl_bb
            elif ctrl_role == role_order[3]:
                ordered_ctrl_trans[3] = ctrl_trans
                ordered_bounding_box[3] = ctrl_bb
            elif ctrl_role == role_order[4]:
                ordered_ctrl_trans[4] = ctrl_trans
                ordered_bounding_box[4] = ctrl_bb
            elif ctrl_role == role_order[5]:
                ordered_ctrl_trans[5] = ctrl_trans
                ordered_bounding_box[5] = ctrl_bb

        # Adds a pin to the control_transforms pin on the construction node
        for trans in ordered_ctrl_trans:
            quat = trans.rotation
            pos = trans.translation
            controller.insert_array_pin(f'{construction_func_name}.control_transforms',
                                        -1,
                                        f"("
                                        f"Rotation=(X={quat.x},Y={quat.y},Z={quat.z},W={quat.w}),"
                                        f"Translation=(X={pos.x},Y={pos.y},Z={pos.z}),"
                                        f"Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))"
                                        )

        self.populate_control_scale(construction_func_name, ordered_bounding_box, controller)
        self.populate_control_shape_offset(construction_func_name, ordered_bounding_box, controller)

    def populate_control_scale(self, node_name, bounding_boxes, controller: unreal.RigVMController):
        reduce_ratio = 4.0
        """Magic number to try and get the maya control scale to be similar to that of unreal.
        As the mGear uses a square and ueGear uses a cirlce.
        """

        for aabb in bounding_boxes:
            unreal_size = [round(element / reduce_ratio, 4) for element in aabb[1]]

            # rudementary way to check if the bounding box might be flat, if it is then
            # the first value if applied onto the axis
            if unreal_size[0] == unreal_size[1] and unreal_size[2] < 0.2:
                unreal_size[2] = unreal_size[0]
            elif unreal_size[1] == unreal_size[2] and unreal_size[0] < 0.2:
                unreal_size[0] = unreal_size[1]
            elif unreal_size[0] == unreal_size[2] and unreal_size[1] < 0.2:
                unreal_size[1] = unreal_size[0]

            controller.insert_array_pin(f'{node_name}.control_sizes',
                                        -1,
                                        f'(X={unreal_size[0]},Y={unreal_size[1]},Z={unreal_size[2]})'
                                        )

    def populate_control_shape_offset(self, node_name, bounding_boxes, controller: unreal.RigVMController):
        """
        As some controls have there pivot at the same position as the transform, but the control is actually moved
        away from that pivot point. We use the bounding box position as an offset for the control shape.
        """

        for aabb in bounding_boxes:
            bb_center = aabb[0]

            controller.insert_array_pin(f'{node_name}.control_offsets',
                                        -1,
                                        f'(X={bb_center[0]},Y={bb_center[1]},Z={bb_center[2]})'
                                        )

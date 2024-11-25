import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component


class Component(base_component.UEComponent):
    name = "test_Arm"
    mgear_component = "EPIC_arm_02"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['construct_IK_arm'],
                          'forward_functions': ['forward_IK_arm'],
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
        # calls the super method
        super().create_functions(controller)

        # Generate Function Nodes
        for evaluation_path in self.functions.keys():

            # Skip the forward function creation if no joints are needed to be driven
            if evaluation_path == 'forward_functions' and self.metadata.joints is None:
                continue

            for cr_func in self.functions[evaluation_path]:
                new_node_name = f"{self.name}_{cr_func}"

                ue_cr_node = controller.get_graph().find_node_by_name(new_node_name)

                # Create Component if doesn't exist
                if ue_cr_node is None:
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

        filtered_bones = []
        """List of bones that do not contain twist bones"""

        # Ignore Twist bones as we have not implemented them yet in the Control Rig Node
        for b in bones:
            bone_name = str(b.key.name)
            if "twist" in bone_name:
                continue
            filtered_bones.append(b)

        # Unique name for this skeleton node array
        array_node_name = f"{self.metadata.fullname}_bones_RigUnit_ItemArray"
        upper_bone_node_name = f"{self.metadata.fullname}_upper_RigUnit_ItemArray"
        mid_bone_node_name = f"{self.metadata.fullname}_mid_RigUnit_ItemArray"
        lower_bone_node_name = f"{self.metadata.fullname}_forward_lower_RigUnit_ItemArray"

        # We have to create another At function for the construction node, as nodes cannot be connected on both
        # construction and forward streams
        con_lower_bone_node_name = f"{self.metadata.fullname}_construction_lower_RigUnit_ItemArray"

        individual_bone_node_names = [upper_bone_node_name,
                                      mid_bone_node_name,
                                      lower_bone_node_name,
                                      con_lower_bone_node_name]

        # node doesn't exists, create the joint node
        if not controller.get_graph().find_node_by_name(array_node_name):
            self._init_master_joint_node(controller, array_node_name, filtered_bones)

        for idx, individual_index_node in enumerate(individual_bone_node_names):
            if not controller.get_graph().find_node_by_name(individual_index_node):
                node = controller.add_template_node(
                    'DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)',
                    unreal.Vector2D(3500, 800),
                    individual_index_node
                    )
                self.add_misc_function(node)

                controller.add_link(f'{array_node_name}.Items',
                                    f'{individual_index_node}.Array'
                                    )
                # assigns the last bone in the list to both lower_bone variables
                if idx > 2:
                    idx = 2

                controller.set_pin_default_value(
                    f'{individual_index_node}.Index',
                    str(idx),
                    False
                )

        # Connects the joint node to the Construction function

        for function_node in self.nodes["construction_functions"]:
            controller.add_link(f'{array_node_name}.Items',
                                f'{function_node.get_name()}.fk_joints')

            controller.add_link(f'{con_lower_bone_node_name}.Element',
                                f'{function_node.get_name()}.effector_joint')

        # Connects the joint node to the Forward function

        for function_node in self.nodes["forward_functions"]:
            controller.add_link(f'{upper_bone_node_name}.Element',
                                f'{function_node.get_name()}.top_bone')

            controller.add_link(f'{mid_bone_node_name}.Element',
                                f'{function_node.get_name()}.mid_bone')

            controller.add_link(f'{lower_bone_node_name}.Element',
                                f'{function_node.get_name()}.end_bone')

    def _init_master_joint_node(self, controller, node_name: str, bones):
        """Creates an array node of all the bones
        """

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
            # Populates the Item Array Node
            controller.insert_array_pin(f'{node_name}.Items', -1, '')
            controller.set_pin_default_value(f'{node_name}.Items.{str(pin_index)}',
                                             f'(Type=Bone,Name="{bone_name}")',
                                             True)
            controller.set_pin_expansion(f'{node_name}.Items.{str(pin_index)}', True)
            controller.set_pin_expansion(f'{node_name}.Items', True)

            pin_index += 1

    def init_input_data(self, controller: unreal.RigVMController):

        # commented out while developing arm
        self._set_mirrored_ik_upvector(controller)

    def _set_mirrored_ik_upvector(self, controller: unreal.RigVMController):
        """
        The Arms can be mirrored, if a right side is being built then we need to setup the
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
        """
        import ueGear.controlrig.manager as ueMan

        # Control names
        fk_control_names = []
        ik_upv_name = ""
        ik_eff_name = ""

        # Filter our required names and transforms
        for ctrl_name in self.metadata.controls:
            # Use the controls.Role metadata to detect the type
            ctrl_role = self.metadata.controls_role[ctrl_name]
            if "fk" in ctrl_role:
                fk_control_names.append(ctrl_name)
            elif "upv" in ctrl_role:
                ik_upv_name = ctrl_name
            elif "ik" == ctrl_role:
                ik_eff_name = ctrl_name

        # Gets the construction function name
        construction_func_name = self.nodes["construction_functions"][0].get_name()

        # SETUP IK DATA

        # Gets the names of the ik controls and their transforms, and applies it directly to the node
        controller.set_pin_default_value(f'{construction_func_name}.effector_name',
                                         ik_eff_name, False)
        controller.set_pin_default_value(f'{construction_func_name}.upVector_name',
                                         ik_upv_name, False)

        ik_eff_trans = self.metadata.control_transforms[ik_eff_name]
        ik_upv_trans = self.metadata.control_transforms[ik_upv_name]

        self._set_transform_pin(construction_func_name,
                                'effector',
                                ik_eff_trans,
                                controller)

        self._set_transform_pin(construction_func_name,
                                'upVector',
                                ik_upv_trans,
                                controller)

        # SETUP FK DATA

        # Generates the array nodes for fk names and transforms
        fk_names_node_name = ueMan.create_array_node(f"{self.metadata.fullname}_fk_control_names", controller)
        fk_trans_node_name = ueMan.create_array_node(f"{self.metadata.fullname}_fk_control_transforms", controller)

        fk_names_node = controller.get_graph().find_node_by_name(fk_names_node_name)
        fk_trans_node = controller.get_graph().find_node_by_name(fk_trans_node_name)

        self.add_misc_function(fk_names_node)
        self.add_misc_function(fk_trans_node)

        # Connecting nodes needs to occur first, else the array node does not know the type and will not accept default
        # values
        controller.add_link(f'{fk_names_node_name}.Array',
                            f'{construction_func_name}.fk_control_names')
        controller.add_link(f'{fk_trans_node_name}.Array',
                            f'{construction_func_name}.fk_control_transforms')

        # Populate the array node with new pins that contain the name and transform data

        # Checks to see if the array has existing pins
        name_pins_exist = ueMan.array_node_has_pins(fk_names_node_name, controller)
        trans_pins_exist = ueMan.array_node_has_pins(fk_trans_node_name, controller)

        pin_index = 0

        for control_name in fk_control_names:
            control_transform = self.metadata.control_transforms[control_name]

            if not name_pins_exist:
                found_node = controller.get_graph().find_node_by_name(fk_names_node_name)
                existing_pin_count = len(found_node.get_pins()[0].get_sub_pins())
                if existing_pin_count < len(fk_control_names):
                    controller.insert_array_pin(f'{fk_names_node_name}.Values',
                                                -1,
                                                '')
            if not trans_pins_exist:
                found_node = controller.get_graph().find_node_by_name(fk_trans_node_name)
                existing_pin_count = len(found_node.get_pins()[0].get_sub_pins())
                if existing_pin_count < len(fk_control_names):
                    controller.insert_array_pin(f'{fk_trans_node_name}.Values',
                                                -1,
                                                '')

            self._set_transform_pin(fk_trans_node_name,
                                    f'Values.{pin_index}',
                                    control_transform,
                                    controller)

            controller.set_pin_default_value(f'{fk_names_node_name}.Values.{pin_index}',
                                             control_name,
                                             False)

            pin_index += 1

        self.populate_control_scale(
            fk_control_names,
            ik_upv_name,
            ik_eff_name,
            controller)

        self.populate_control_shape_offset(fk_control_names,
            ik_upv_name,
            ik_eff_name,
            controller)

        self.populate_control_colour(fk_control_names,
            ik_upv_name,
            ik_eff_name,
            controller)

    def populate_control_scale(self, fk_names: list[str], ik_upv: str, ik_eff: str, controller: unreal.RigVMController):
        """
        Generates a scale value per a control
        """
        import ueGear.controlrig.manager as ueMan

        reduce_ratio = 4.0
        """Magic number to try and get the maya control scale to be similar to that of unreal.
        As the mGear uses a square and ueGear uses a cirlce.
        """

        # Generates the array node
        array_name = ueMan.create_array_node(f"{self.metadata.fullname}_control_scales", controller)
        array_node = controller.get_graph().find_node_by_name(array_name)
        self.add_misc_function(array_node)

        # connects the node of scales to the construction node
        construction_func_name = self.nodes["construction_functions"][0].get_name()
        controller.add_link(f'{array_name}.Array',
                            f'{construction_func_name}.control_sizes')

        pins_exist = ueMan.array_node_has_pins(array_name, controller)
        pin_index = 0

        # Calculates the unreal scale for the control and populates it into the array node.
        for control_name in fk_names + [ik_upv, ik_eff]:
            aabb = self.metadata.controls_aabb[control_name]
            unreal_size = [round(element / reduce_ratio, 4) for element in aabb[1]]

            # rudementary way to check if the bounding box might be flat, if it is then
            # the first value if applied onto the axis
            if unreal_size[0] == unreal_size[1] and unreal_size[2] < 0.2:
                unreal_size[2] = unreal_size[0]
            elif unreal_size[1] == unreal_size[2] and unreal_size[0] < 0.2:
                unreal_size[0] = unreal_size[1]
            elif unreal_size[0] == unreal_size[2] and unreal_size[1] < 0.2:
                unreal_size[1] = unreal_size[0]

            if not pins_exist:
                existing_pin_count = len(array_node.get_pins()[0].get_sub_pins())
                if existing_pin_count < len(self.metadata.controls_aabb):
                    controller.insert_array_pin(f'{array_name}.Values',
                                                -1,
                                                '')

            controller.set_pin_default_value(f'{array_name}.Values.{pin_index}',
                                             f'(X={unreal_size[0]},Y={unreal_size[1]},Z={unreal_size[2]})',
                                             False)

            pin_index += 1

    def populate_control_shape_offset(self, fk_names: list[str], ik_upv: str, ik_eff: str, controller: unreal.RigVMController):
        """
        As some controls have there pivot at the same position as the transform, but the control is actually moved
        away from that pivot point. We use the bounding box position as an offset for the control shape.
        """
        import ueGear.controlrig.manager as ueMan

        # Generates the array node
        array_name = ueMan.create_array_node(f"{self.metadata.fullname}_control_offset", controller)
        array_node = controller.get_graph().find_node_by_name(array_name)
        self.add_misc_function(array_node)

        # connects the node of scales to the construction node
        construction_func_name = self.nodes["construction_functions"][0].get_name()
        controller.add_link(f'{array_name}.Array',
                            f'{construction_func_name}.control_offsets')

        pins_exist = ueMan.array_node_has_pins(array_name, controller)
        pin_index = 0

        for control_name in fk_names + [ik_upv, ik_eff]:
            aabb = self.metadata.controls_aabb[control_name]
            bb_center = aabb[0]

            if not pins_exist:
                existing_pin_count = len(array_node.get_pins()[0].get_sub_pins())
                if existing_pin_count < len(self.metadata.controls_aabb):
                    controller.insert_array_pin(f'{array_name}.Values',
                                                -1,
                                                '')

            controller.set_pin_default_value(f'{array_name}.Values.{pin_index}',
                                             f'(X={bb_center[0]},Y={bb_center[1]},Z={bb_center[2]})',
                                             False)

            pin_index += 1

    def populate_control_colour(self, fk_names: list[str], ik_upv: str, ik_eff: str,
                                              controller: unreal.RigVMController):

        cr_func = self.functions["construction_functions"][0]
        construction_node = f"{self.name}_{cr_func}"

        for i, control_name in enumerate(fk_names + [ik_upv, ik_eff]):
            colour = self.metadata.controls_colour[control_name]

            controller.insert_array_pin(f'{construction_node}.control_colours', -1, '')
            controller.set_pin_default_value(f'{construction_node}.control_colours.{i}.R', f"{colour[0]}", False)
            controller.set_pin_default_value(f'{construction_node}.control_colours.{i}.G', f"{colour[1]}", False)
            controller.set_pin_default_value(f'{construction_node}.control_colours.{i}.B', f"{colour[2]}", False)
            controller.set_pin_default_value(f'{construction_node}.control_colours.{i}.A', "1", False)

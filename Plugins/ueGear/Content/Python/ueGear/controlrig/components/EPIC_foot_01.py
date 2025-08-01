import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component, EPIC_control_01
from ueGear.controlrig.helpers import controls

class Component(base_component.UEComponent):
    name = "foot_component"
    mgear_component = "EPIC_foot_01"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ["construct_IK_foot"],
                          'forward_functions': ["forward_IK_foot"],
                          'backwards_functions': ['backwards_IK_foot'],
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

                ue_cr_node = controller.get_graph().find_node_by_name(new_node_name)

                # Create Component if it does not exist
                if ue_cr_node is None:
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
        Populates the ball joint data on the foot nodes/functions.
        """

        if bones is None or len(bones) < 1:
            unreal.log_error("[Bone Populate] Failed - No Bones found")
            return
        if controller is None:
            unreal.log_error("[Bone Populate] Failed no Controller found")
            return

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

        # Assign ball joint to the backwards node
        forward_node = self.nodes["backwards_functions"][0]
        controller.set_pin_default_value(f'{forward_node.get_name()}.ball_joint',
                                         f'(Type=Bone, Name="{jnt_name}")',
                                         True)

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
        pass

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
        ordered_colours = [None] * 6
        role_order = ["heel", "tip", "roll", "bk0", "bk1", "fk0"]

        for ctrl_name in self.metadata.controls:
            # Use the controls.Role metadata to detect the type
            ctrl_role = self.metadata.controls_role[ctrl_name]
            ctrl_trans = self.metadata.control_transforms[ctrl_name]
            ctrl_bb = self.metadata.controls_aabb[ctrl_name]
            ctrl_colour = self.metadata.controls_colour[ctrl_name]
            # rudementary way of ordering the output list
            if ctrl_role == role_order[0]:
                ordered_ctrl_trans[0] = ctrl_trans
                ordered_bounding_box[0] = ctrl_bb
                ordered_colours[0] = ctrl_colour
            elif ctrl_role == role_order[1]:
                ordered_ctrl_trans[1] = ctrl_trans
                ordered_bounding_box[1] = ctrl_bb
                ordered_colours[1] = ctrl_colour
            elif ctrl_role == role_order[2]:
                ordered_ctrl_trans[2] = ctrl_trans
                ordered_bounding_box[2] = ctrl_bb
                ordered_colours[2] = ctrl_colour
            elif ctrl_role == role_order[3]:
                ordered_ctrl_trans[3] = ctrl_trans
                ordered_bounding_box[3] = ctrl_bb
                ordered_colours[3] = ctrl_colour
            elif ctrl_role == role_order[4]:
                ordered_ctrl_trans[4] = ctrl_trans
                ordered_bounding_box[4] = ctrl_bb
                ordered_colours[4] = ctrl_colour
            elif ctrl_role == role_order[5]:
                ordered_ctrl_trans[5] = ctrl_trans
                ordered_bounding_box[5] = ctrl_bb
                ordered_colours[5] = ctrl_colour

        default_values = ""
        # Adds a pin to the control_transforms pin on the construction node
        for trans in ordered_ctrl_trans:
            quat = trans.rotation
            pos = trans.translation

            string_entry = (f"(Rotation=(X={quat.x},Y={quat.y},Z={quat.z},W={quat.w}), "
                            f"Translation=(X={pos.x},Y={pos.y},Z={pos.z}), "
                            f"Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)),")
            default_values += string_entry

        # trims off the extr ','
        default_values = default_values[:-1]

        # Populates and resizes the pin in one go
        controller.set_pin_default_value(
            f"{construction_func_name}.control_transforms",
            f"({default_values})",
            True,
            setup_undo_redo=True,
            merge_undo_action=True)

        self.populate_control_scale(construction_func_name, ordered_bounding_box, controller)
        self.populate_control_shape_offset(construction_func_name, ordered_bounding_box, controller)
        self.populate_control_colour(construction_func_name, ordered_colours, controller)

    def populate_control_scale(self, node_name, bounding_boxes, controller: unreal.RigVMController):
        reduce_ratio = 4.0
        """Magic number to try and get the maya control scale to be similar to that of unreal.
        As the mGear uses a square and ueGear uses a cirlce.
        """

        default_values = ""
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

            default_values += f'(X={unreal_size[0]},Y={unreal_size[1]},Z={unreal_size[2]}),'

        # trims off the extr ','
        default_values = default_values[:-1]

        # Populates and resizes the pin in one go
        controller.set_pin_default_value(
            f'{node_name}.control_sizes',
            f'({default_values})',
            True,
            setup_undo_redo=True,
            merge_undo_action=True)

    def populate_control_shape_offset(self, node_name, bounding_boxes, controller: unreal.RigVMController):
        """
        As some controls have there pivot at the same position as the transform, but the control is actually moved
        away from that pivot point. We use the bounding box position as an offset for the control shape.
        """

        default_values = ""
        for aabb in bounding_boxes:
            bb_center = aabb[0]
            string_entry = f'(X={bb_center[0]}, Y={bb_center[1]}, Z={bb_center[2]}),'
            default_values += string_entry

        # trims off the extr ','
        default_values = default_values[:-1]

        controller.set_pin_default_value(
            f'{node_name}.control_offsets',
            f'({default_values})',
            True,
            setup_undo_redo=True,
            merge_undo_action=True)

    def populate_control_colour(self, node_name, ordered_colours, controller: unreal.RigVMController):
        default_values = ""

        for colour in ordered_colours:
            default_values += f"(R={colour[0]}, G={colour[1]}, B={colour[2]}, A=1.0),"

        # trims off the extr ','
        default_values = default_values[:-1]

        # Populates and resizes the pin in one go
        controller.set_pin_default_value(
            f'{node_name}.control_colours',
            f"({default_values})",
            True,
            setup_undo_redo=True,
            merge_undo_action=True)

class ManualComponent(Component):
    name = "EPIC_foot_01"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['manual_construct_IK_foot'],
                          'forward_functions': ['manual_forward_IK_foot'],
                          'backwards_functions': ['backwards_IK_foot'],
                          }

        self.is_manual = True

        # These are the roles that will be parented directly under the parent component.
        self.root_control_children = ["roll", "heel"]

        self.hierarchy_schematic_roles = {
            "heel": ["tip"],
            "tip": ["bk0"],
            "bk0": ["bk1"],
            "bk1": ["null_fk0"],
            "null_fk0": ["fk0"]
            }

        # Default to fall back onto
        self.default_shape = "Circle_Thick"
        self.control_shape = {
            "fk0": "Box_Thick",
            "roll": "Box_Thick",
            "heel": "Sphere_Solid",
            "bk1": "Sphere_Solid",
            "bk0": "Sphere_Solid"
        }

        # Roles that will not be generated
        # This is more of a developmental ignore, as we have not implemented this part of the component yet.
        self.skip_roles = []

        # todo: HANDLE OUTPIVOT AND INNERPIVOT => They are not Controls

    def create_functions(self, controller: unreal.RigVMController):
        EPIC_control_01.ManualComponent.create_functions(self, controller)

        func_name = self.name + "_" + self.functions['construction_functions'][0]
        controller.set_pin_default_value(f'{func_name}.side', self.metadata.side, False)



    # todo: Create Null controls and add them to the hierarhcy_schematic
    def generate_manual_null(self, hierarchy_controller: unreal.RigHierarchyController):

        null_names = ["foot_{side}0_fk0_inverse"]
        rolls_for_trans = ["bk1"]
        control_trans_to_use = []

        # Finds the controls name that has the role ik. it will be used to get the
        # transformation data
        for search_roll in rolls_for_trans:
            for control_name in self.metadata.controls:
                role = self.metadata.controls_role[control_name]
                if role == search_roll:
                    control_trans_to_use.append(control_name)

        # As this null does not exist, we create a new "fake" name and add it to the control_by_role. This is done
        # so the parent hierarchy can detect it.
        injected_role_name = ["null_fk0"]

        for i, null_meta_name in enumerate(null_names):
            trans_meta_name = control_trans_to_use[i]
            null_role = injected_role_name[i]

            null_name = null_meta_name.format(**{"side": self.metadata.side})
            trans_name = trans_meta_name.format(**{"side": self.metadata.side})
            control_transform = self.metadata.control_transforms[trans_name]

            # Generate the Null
            new_null = controls.CR_Control(name=null_name)
            new_null.set_control_type(unreal.RigElementType.NULL)
            new_null.build(hierarchy_controller)

            new_null.set_transform(quat_transform=control_transform)

            # rig_hrc = hierarchy_controller.get_hierarchy()

            self.control_by_role[null_role] = new_null

    def generate_manual_controls(self, hierarchy_controller: unreal.RigHierarchyController):
        """Creates all the manual controls for the Spine"""
        # Stores the controls by Name
        control_table = dict()

        for control_name in self.metadata.controls:
            new_control = controls.CR_Control(name=control_name)
            role = self.metadata.controls_role[control_name]

            # Skip a control that contains a role that has any of the keywords to skip
            if any([skip in role for skip in self.skip_roles]):
                continue

            # stored metadata values
            control_transform = self.metadata.control_transforms[control_name]
            control_colour = self.metadata.controls_colour[control_name]
            control_aabb = self.metadata.controls_aabb[control_name]
            control_offset = control_aabb[0]
            # - modified for epic arm
            control_scale = [control_aabb[1][2] / 4.0,
                             control_aabb[1][2] / 4.0,
                             control_aabb[1][2] / 4.0]

            # Set the colour, required before build
            new_control.colour = control_colour
            if role not in self.control_shape.keys():
                new_control.shape_name = self.default_shape
            else:
                new_control.shape_name = self.control_shape[role]

            # Generate the Control
            new_control.build(hierarchy_controller)

            # Sets the controls position, and offset translation and scale of the shape
            new_control.set_transform(quat_transform=control_transform)
            # - Modified for epic arm
            new_control.shape_transform_global(pos=control_offset,
                                               scale=control_scale,
                                               rotation=[90, 0, 90])

            control_table[control_name] = new_control

            # Stores the control by role, for loopup purposes later
            self.control_by_role[role] = new_control

        self.generate_manual_null(hierarchy_controller)

        self.initialize_hierarchy(hierarchy_controller)

    def initialize_hierarchy(self, hierarchy_controller: unreal.RigHierarchyController):
        """Performs the hierarchical restructuring of the internal components controls"""
        # Parent control hierarchy using roles
        for parent_role in self.hierarchy_schematic_roles.keys():
            child_roles = self.hierarchy_schematic_roles[parent_role]

            parent_ctrl = self.control_by_role[parent_role]

            for child_role in child_roles:
                child_ctrl = self.control_by_role[child_role]
                hierarchy_controller.set_parent(child_ctrl.rig_key, parent_ctrl.rig_key)

    def populate_control_transforms(self, controller: unreal.RigVMController = None):
        construction_func_name = self.nodes["construction_functions"][0].get_name()

        controls = []
        nulls = []

        for role_key in ["heel", "tip", "roll", "bk0", "bk1", "fk0"]:
            control = self.control_by_role[role_key]
            controls.append(control)

        for role_key in ["null_fk0"]:
            control = self.control_by_role[role_key]
            nulls.append(control)

        # Converts RigElementKey into a string of key data.
        def update_input_plug(plug_name, control_list):
            """
            Simple helper function making the plug population reusable for ik and fk
            """
            control_metadata = []
            for entry in control_list:
                if entry.rig_key.type == unreal.RigElementType.CONTROL:
                    t = "Control"
                if entry.rig_key.type == unreal.RigElementType.NULL:
                    t = "Null"
                n = entry.rig_key.name
                entry = f'(Type={t}, Name="{n}")'
                control_metadata.append(entry)

            concatinated_controls = ",".join(control_metadata)

            controller.set_pin_default_value(
                f'{construction_func_name}.{plug_name}',
                f"({concatinated_controls})",
                True,
                setup_undo_redo=True,
                merge_undo_action=True)

        update_input_plug("controls", controls)
        update_input_plug("nulls", nulls)


    def forward_solve_connect(self, controller: unreal.RigVMController):
        """
        Performs any custom connections between forward solve components
        """
        parent_forward_node_name = self.parent_node.nodes["forward_functions"][0].get_name()
        forward_node_name = self.nodes["forward_functions"][0].get_name()

        controller.add_link(f'{parent_forward_node_name}.ik_active_out',
                            f'{forward_node_name}.ik_active')

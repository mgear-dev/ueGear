import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component, EPIC_control_01
from ueGear.controlrig.helpers import controls


class Component(base_component.UEComponent):
    name = "EPIC_leg_3jnt_01"
    mgear_component = "EPIC_leg_3jnt_01"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['construct_IK_leg_3jnt'],
                          'forward_functions': ['forward_IK_leg_3jnt'],
                          'backwards_functions': ['backwards_IK_leg_3jnt'],
                          }
        self.cr_variables = {}

        # Control Rig Inputs
        self.cr_inputs = {'construction_functions': ['parent'],
                          'forward_functions': [],
                          'backwards_functions': [],
                          }

        # Control Rig Outputs
        self.cr_output = {'construction_functions': ['ankle'],
                          'forward_functions': ['ik_active_out'],
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
        if bones is None or len(bones) < 4:
            unreal.log_error("[Bone Populate] Failed - Less then 4 Bones found")
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
        foot_bone_node_name = f"{self.metadata.fullname}_forward_foot_RigUnit_ItemArray"

        # We have to create another At function for the construction node, as nodes cannot be connected on both
        # construction and forward streams
        con_lower_bone_node_name = f"{self.metadata.fullname}_construction_lower_RigUnit_ItemArray"

        individual_bone_node_names = [upper_bone_node_name,
                                      mid_bone_node_name,
                                      lower_bone_node_name,
                                      foot_bone_node_name,
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
                # fixme: This entry could be seperated into a construction list and a forward list.
                # The last element in the individual_bone_node_name, is the lower bone, which needs to
                # point to bone index 2
                if idx > 3:
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
                                f'{function_node.get_name()}.femur_bone')

            controller.add_link(f'{mid_bone_node_name}.Element',
                                f'{function_node.get_name()}.tibia_bone')

            controller.add_link(f'{lower_bone_node_name}.Element',
                                f'{function_node.get_name()}.cannon_bone')

            controller.add_link(f'{foot_bone_node_name}.Element',
                                f'{function_node.get_name()}.foot_bone')

        # Connects the joint node to the Construction function
        for function_node in self.nodes["backwards_functions"]:
            controller.add_link(f'{array_node_name}.Items',
                                f'{function_node.get_name()}.fk_joints')

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

        default_values = ""
        for i, bone in enumerate(bones):
            bone_name = str(bone.key.name)
            default_values += f'(Type=Bone,Name="{bone_name}"),'

        # trims off the extr ','
        default_values = default_values[:-1]
        # Populates and resizes the pin in one go
        controller.set_pin_default_value(f'{node_name}.Items',
                                         f'({default_values})',
                                         True,
                                         setup_undo_redo=True,
                                         merge_undo_action=True)

    def init_input_data(self, controller: unreal.RigVMController):

        self._set_mirrored_ik_upvector(controller)

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

        Design Decision: All feet IK Controls are built in World Space, oriented to World Space
        """
        # Gets the construction function name
        construction_func_name = self.nodes["construction_functions"][0].get_name()

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

        # SETUP IK DATA

        # Gets the names of the ik controls and their transforms, and applies it directly to the node
        controller.set_pin_default_value(f'{construction_func_name}.effector_name',
                                         ik_eff_name, False)
        controller.set_pin_default_value(f'{construction_func_name}.upVector_name',
                                         ik_upv_name, False)

        ik_eff_trans = self.metadata.control_transforms[ik_eff_name]
        ik_upv_trans = self.metadata.control_transforms[ik_upv_name]

        # Orient the ik effector into unreal world space, by creating a new Transform, and assinging only the position.
        ik_eff_trans = unreal.Transform(location=ik_eff_trans.translation)

        self._set_transform_pin(construction_func_name,
                                'effector',
                                ik_eff_trans,
                                controller)

        self._set_transform_pin(construction_func_name,
                                'upVector',
                                ik_upv_trans,
                                controller)

        # SETUP FK DATA
        # Populate the array node with new pins that contain the name and transform data

        default_values = ""

        for control_name in fk_control_names:
            control_transform = self.metadata.control_transforms[control_name]
            quat = control_transform.rotation
            pos = control_transform.translation

            string_entry = (f"(Rotation=(X={quat.x},Y={quat.y},Z={quat.z},W={quat.w}), "
                            f"Translation=(X={pos.x},Y={pos.y},Z={pos.z}), "
                            f"Scale3D=(X=1.000000,Y=1.000000,Z=1.000000)),")

            default_values += string_entry

        # trims off the extr ','
        default_values = default_values[:-1]

        controller.set_pin_default_value(
            f"{construction_func_name}.fk_control_transforms",
            f"({default_values})",
            True,
            setup_undo_redo=True,
            merge_undo_action=True)

        # Populate names
        names = ",".join([name for name in fk_control_names])
        controller.set_pin_default_value(
            f'{construction_func_name}.fk_control_names',
            f"({names})",
            True,
            setup_undo_redo=True,
            merge_undo_action=True)


        # post processes
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
        reduce_ratio = 5.0
        """Magic number to try and get the maya control scale to be similar to that of unreal.
        As the mGear uses a square and ueGear uses a cirlce.
        """

        # connects the node of scales to the construction node
        construction_func_name = self.nodes["construction_functions"][0].get_name()

        default_values = ""
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

            default_values += f'(X={unreal_size[0]},Y={unreal_size[1]},Z={unreal_size[2]}),'

        # trims off the extr ','
        default_values = default_values[:-1]

        # Populates and resizes the pin in one go
        controller.set_pin_default_value(
            f'{construction_func_name}.control_sizes',
            f'({default_values})',
            True,
            setup_undo_redo=True,
            merge_undo_action=True)


    def populate_control_shape_offset(self, fk_names: list[str], ik_upv: str, ik_eff: str,
                                      controller: unreal.RigVMController):
        """
        As some controls have there pivot at the same position as the transform, but the control is actually moved
        away from that pivot point. We use the bounding box position as an offset for the control shape.
        """
        construction_func_name = self.nodes["construction_functions"][0].get_name()

        default_values = ""
        for control_name in fk_names + [ik_upv, ik_eff]:
            aabb = self.metadata.controls_aabb[control_name]
            bb_center = aabb[0]

            string_entry = f'(X={bb_center[0]}, Y={bb_center[1]}, Z={bb_center[2]}),'

            default_values += string_entry

        # trims off the extr ','
        default_values = default_values[:-1]

        controller.set_pin_default_value(
            f'{construction_func_name}.control_offsets',
            f'({default_values})',
            True,
            setup_undo_redo=True,
            merge_undo_action=True)


    def populate_control_colour(self, fk_names: list[str], ik_upv: str, ik_eff: str,
                                controller: unreal.RigVMController):

        cr_func = self.functions["construction_functions"][0]
        construction_node = f"{self.name}_{cr_func}"

        default_values = ""
        for i, control_name in enumerate(fk_names + [ik_upv, ik_eff]):
            colour = self.metadata.controls_colour[control_name]
            string_entry = f"(R={colour[0]}, G={colour[1]}, B={colour[2]}, A=1.0),"
            default_values += string_entry

        # trims off the extr ','
        default_values = default_values[:-1]

        # Populates and resizes the pin in one go
        controller.set_pin_default_value(
            f'{construction_node}.control_colours',
            f"({default_values})",
            True,
            setup_undo_redo=True,
            merge_undo_action=True)


class ManualComponent(Component):
    name = "EPIC_leg_3jnt_01"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['manual_construct_IK_leg_3jnt'],
                          'forward_functions': ['forward_IK_leg_3jnt'],
                          'backwards_functions': ['backwards_IK_leg_3jnt'],
                          }

        self.is_manual = True

        # These are the roles that will be parented directly under the parent component.
        self.root_control_children = ["root", "upv", "null_offset"]  # ,"knee", "ankle"]

        self.hierarchy_schematic_roles = {
            "root": ["fk0"],
            "fk0": ["fk1"],
            "fk1": ["fk2"],
            "fk2": ["fk3"],
            "ik": ["null_inv"],
            "null_offset": ["ik"],
            "null_inv": ["roll"]
        }
        """The control hierarchy. keys are parent, values are children"""

        # Default to fall back onto
        self.default_shape = "Box_Thick" #"Circle_Thick"
        self.control_shape = {
            "ik": "Box_Thick",
            "upv": "Diamond_Thick",
            "knee": "Sphere_Thin",
            "ankle": "Sphere_Thin",
            "roll": "Circle_Thick"
        }

        # Roles that will not be generated
        # This is more of a developmental ignore, as we have not implemented this part of the component yet.
        self.skip_roles = ["tweak", "ikcns", "knee", "ankle"]
        """List of keywords that if found in a control name will be skipped."""

        self.control_shape_rotation = {}
        """Custom shape rotations applied to specific roles"""

    def create_functions(self, controller: unreal.RigVMController):
        EPIC_control_01.ManualComponent.create_functions(self, controller)

        # todo: handle noodle arm creation. This also needs to be setup in the Unreal Control Rig Function/Node
        # self.setup_dynamic_hierarchy_roles(end_control_role="head")

    def setup_dynamic_hierarchy_roles(self, end_control_role=None):
        """Manual controls have some dynamic control creation. This function sets up the
        control relationship for the dynamic control hierarchy."""

        # todo: Implement div0, div1
        # # Calculate the amount of fk's based on the division amount
        # fk_count = self.metadata.settings['division']
        # for i in range(fk_count):
        #     parent_role = f"fk{i}"
        #     child_index = i + 1
        #     child_role = f"fk{child_index}"
        #
        #     # end of the fk chain, parent the end control if one specified
        #     if child_index >= fk_count:
        #         if end_control_role:
        #             self.hierarchy_schematic_roles[parent_role] = [end_control_role]
        #             continue
        #
        #     self.hierarchy_schematic_roles[parent_role] = [child_role]
        return

    def generate_manual_controls(self, hierarchy_controller: unreal.RigHierarchyController):
        """Creates all the manual controls for the Spine"""
        # Stores the controls by Name
        control_table = dict()

        for control_name in self.metadata.controls:
            # print(f"Initializing Manual Control - {control_name}")
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
            shape_rotation = [90, 0, 90]

            # Applies custom shape rotation to the control being generated, if role exists in the table.
            if role in self.control_shape_rotation.keys():
                shape_rotation = self.control_shape_rotation[role]

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

            # Remove's the Scale and Rotation on the leg ik control
            if role == "ik":
                control_transform.set_editor_property("rotation", unreal.Quat.IDENTITY)
                control_transform.set_editor_property("scale3D", unreal.Vector(1,1,1))

            # Sets the controls position, and offset translation and scale of the shape
            new_control.set_transform(quat_transform=control_transform)
            new_control.shape_transform_global(pos=control_offset,
                                               scale=control_scale,
                                               rotation=shape_rotation)

            control_table[control_name] = new_control

            # Stores the control by role, for loopup purposes later
            self.control_by_role[role] = new_control

        self.generate_manual_null(hierarchy_controller)

        self.initialize_hierarchy(hierarchy_controller)

    def generate_manual_null(self, hierarchy_controller: unreal.RigHierarchyController):

        null_names = ["leg_{side}0_ik_cns", "leg_{side}0_roll_inv"]
        rolls_for_trans = ["ik", "roll"]
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
        injected_role_name = ["null_offset", "null_inv"]

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

        fk_controls = []
        ik_controls = []

        # Groups all the controls into ik and fk lists

        for role_key in self.control_by_role.keys():
            # Generates the list of fk controls
            if 'fk' in role_key:
                control = self.control_by_role[role_key]
                fk_controls.append(control)
            elif "ik" == role_key or "upv" in role_key or "roll" in role_key:
                control = self.control_by_role[role_key]

                if "ik" == role_key:
                    ik_controls.insert(0, control)
                elif "upv" in role_key:
                    ik_controls.insert(1, control)
                elif "roll" in role_key:
                    ik_controls.insert(1, control)
            else:
                #     todo: Implement noodle
                continue

        # Converts RigElementKey into one long string of key data.
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

        update_input_plug("fk_controls", fk_controls)
        update_input_plug("ik_controls", ik_controls)

    def forward_solve_connect(self, controller: unreal.RigVMController):
        """
        Performs any custom connections between forward solve components
        """

        # print("Forward Solve - Parent Node")
        # print(f"   parent:{self.parent_node}")
        # print(f"   parent metadata:{self.parent_node.metadata}")
        # print(f"   parent metadata.name:{self.parent_node.metadata.name}")
        # f_nodes = self.parent_node.nodes["forward_functions"]
        # print(f"   parent nodes: {f_nodes}")
        #
        # _parent_node = self.parent_node
        # while _parent_node.metadata.name != "root" and _parent_node != None:
        #
        #     if _parent_node.metadata.name != "root":
        #         _parent_node = _parent_node.parent_node
        #
        # if _parent_node is None:
        #     return
        #
        # root_forward_node_name = _parent_node.nodes["forward_functions"][0].get_name()
        # forward_node_name = self.nodes["forward_functions"][0].get_name()
        #
        # controller.add_link(f'{root_forward_node_name}.control',
        #                     f'{forward_node_name}.root_ctrl')
        return
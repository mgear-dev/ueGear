import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component, EPIC_control_01
from ueGear.controlrig.helpers import controls


class Component(base_component.UEComponent):
    name = "metacarpal"
    mgear_component = "EPIC_meta_01"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['construct_metacarpal'],
                          'forward_functions': ['forward_metacarpal'],
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
        populates the bone shoulder joint node
        """

        if bones is None or len(bones) < 1:
            unreal.log_error(f"[Bone Populate] Failed no Bones found: Found {len(bones)} bones")
            return
        if controller is None:
            unreal.log_error("[Bone Populate] Failed no Controller found")
            return

        # Unique name for this skeleton node array
        array_node_name = f"{self.metadata.fullname}_RigUnit_ItemArray"

        # node doesn't exists, create the joint node
        if not controller.get_graph().find_node_by_name(array_node_name):
            self._init_master_joint_node(controller, array_node_name, bones)

        node = controller.get_graph().find_node_by_name(array_node_name)
        self.add_misc_function(node)

    def init_input_data(self, controller: unreal.RigVMController):
        self._connect_bones(controller)

    def _connect_bones(self, controller: unreal.RigVMController):
        """Connects the bone array list to the construction node"""

        bone_node_name = f"{self.metadata.fullname}_RigUnit_ItemArray"

        construction_node_name = self.nodes["construction_functions"][0].get_name()
        forward_node_name = self.nodes["forward_functions"][0].get_name()

        controller.add_link(f'{bone_node_name}.Items',
                            f'{construction_node_name}.bones')

        controller.add_link(f'{bone_node_name}.Items',
                            f'{forward_node_name}.bones')

    def populate_control_names(self, controller: unreal.RigVMController):
        construction_func_name = self.nodes["construction_functions"][0].get_name()

        default_values = ""
        for control_name in self.metadata.controls:
            default_values += f"{control_name},"

        # trims off the extr ','
        default_values = default_values[:-1]

        # Populates and resizes the pin in one go
        controller.set_pin_default_value(f'{construction_func_name}.control_names',
                                         f"({default_values})",
                                         True,
                                         setup_undo_redo=True,
                                         merge_undo_action=True)

    # TODO: setup an init_controls method and move this method and the populate controls method into it
    def populate_control_transforms(self, controller: unreal.RigVMController = None):
        """Updates the transform data for the controls generated, with the data from the mgear json
        file.
        """
        construction_func_name = self.nodes["construction_functions"][0].get_name()

        default_values = ""
        for i, control_name in enumerate(self.metadata.controls):
            control_transform = self.metadata.control_transforms[control_name]

            quat = control_transform.rotation
            pos = control_transform.translation

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

        self.populate_control_names(controller)
        self.populate_control_scale(controller)
        self.populate_control_shape_offset(controller)
        self.populate_control_colour(controller)

    def get_associated_parent_output(self, name: str, controller: unreal.RigVMController) -> str:
        """
        name: Name of the relative key that will be used to get the associated bone index.
        controller: The BP controller that will manipulate the graph.

        return: The name of the pin to be connected from.
        """
        # Looks at the metacarpals jointRelative dictionary for the name and the index of the output
        joint_index = str(self.metadata.joint_relatives[name])

        node_name = "_".join([self.name, name, joint_index])

        # Create At Index
        node = controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayGetAtIndex(in Array,in Index,out Element)',
            unreal.Vector2D(3500, 1000),
            node_name
        )
        self.add_misc_function(node)

        # Set At index
        controller.set_pin_default_value(
            f'{node_name}.Index',
            str(joint_index),
            False
        )

        # Connect At Index to Array output "controls"
        construction_node_name = self.nodes["construction_functions"][0].get_name()
        controller.add_link(f'{construction_node_name}.controls',
                            f'{node_name}.Array'
                            )

        return f'{node_name}.Element'

    def populate_control_shape_offset(self, controller: unreal.RigVMController):
        """
        As some controls have there pivot at the same position as the transform, but the control is actually moved
        away from that pivot point. We use the bounding box position as an offset for the control shape.
        """
        construction_func_name = self.nodes["construction_functions"][0].get_name()

        default_values = ""
        for i, control_name in enumerate(self.metadata.controls):
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

    def populate_control_scale(self, controller: unreal.RigVMController):
        """
        Generates a scale value per a control
        """
        # connects the node of scales to the construction node
        construction_func_name = self.nodes["construction_functions"][0].get_name()

        aabb_divisor = 3
        """Magic number to try and get the maya control scale to be similar to that of unreal"""

        default_values = ""
        # populate array
        for i, control_name in enumerate(self.metadata.controls):
            aabb = self.metadata.controls_aabb[control_name]
            unreal_size = [round(element / aabb_divisor, 4) for element in aabb[1]]

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
            f'{construction_func_name}.control_scale',
            f'({default_values})',
            True,
            setup_undo_redo=True,
            merge_undo_action=True)

    def populate_control_colour(self, controller: unreal.RigVMController):
        cr_func = self.functions["construction_functions"][0]
        construction_node = f"{self.name}_{cr_func}"

        default_values = ""
        for i, control_name in enumerate(self.metadata.controls):
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
    name = "EPIC_meta_01"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['manual_construct_metacarpal'],
                          'forward_functions': ['forward_metacarpal'],
                          'backwards_functions': [],
                          }

        self.is_manual = True

        # These are the roles that will be parented directly under the parent component.
        self.root_control_children = ["meta0", "meta1", "meta2", "meta3", "ctl"]

        # parent role as key, then all child control roles in a list
        self.hierarchy_schematic_roles = {}

        # Default to fall back onto
        self.default_shape = "Box_Thick"
        self.control_shape = {}

        # Roles that will not be generated
        # This is more of a developmental ignore, as we have not implemented this part of the component yet.
        self.skip_roles = []

    def create_functions(self, controller: unreal.RigVMController):
        EPIC_control_01.ManualComponent.create_functions(self, controller)

    def generate_manual_controls(self, hierarchy_controller: unreal.RigHierarchyController):
        """Creates all the manual controls for the Spine"""
        # Stores the controls by Name
        control_table = dict()

        for control_name in self.metadata.controls:
            print(f"Initializing Manual Control - {control_name}")
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

        self.initialize_internal_hierarchy(hierarchy_controller)

    def initialize_internal_hierarchy(self, hierarchy_controller: unreal.RigHierarchyController):
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

        # Groups all the controls into ik and fk lists
        for role_key in self.control_by_role.keys():
            control = self.control_by_role[role_key]
            controls.append(control)


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

        update_input_plug("controls", controls)

import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component


class Component(base_component.UEComponent):
    name = "test_Shoulder"
    mgear_component = "EPIC_shoulder_01"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['construct_shoulder'],
                          'forward_functions': ['forward_shoulder'],
                          'backwards_functions': ['backwards_shoulder'],
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
            unreal.log_error("[Bone Populate] Failed no Bones found")
            return
        if controller is None:
            unreal.log_error("[Bone Populate] Failed no Controller found")
            return

        bone_name = bones[0].key.name

        construction_node = self.nodes["construction_functions"][0]
        forward_node = self.nodes["forward_functions"][0]
        backwards_node = self.nodes["backwards_functions"][0]

        for function in [construction_node, forward_node, backwards_node]:
            construction_node_name = function.get_name()

            controller.set_pin_default_value(
                f'{construction_node_name}.shoulder_jnt.Name', bone_name, False)
            controller.set_pin_default_value(
                f'{construction_node_name}.shoulder_jnt.Type', 'Bone', False)

    def init_input_data(self, controller: unreal.RigVMController):
        pass

    def populate_control_transforms(self, controller: unreal.RigVMController = None):
        """Updates the transform data for the controls generated, with the data from the mgear json
        file.
        """
        construction_func_name = self.nodes["construction_functions"][0].get_name()

        default_values = ""

        for control_name in self.metadata.controls:
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
            f"{construction_func_name}.world_control_transforms",
            f"({default_values})",
            True,
            setup_undo_redo=True,
            merge_undo_action=True)

        # Populate names
        names = ",".join([control_name for control_name in self.metadata.controls])
        controller.set_pin_default_value(
            f'{construction_func_name}.control_names',
            f"({names})",
            True,
            setup_undo_redo=True,
            merge_undo_action=True)


        self.populate_control_scale(controller)
        self.populate_control_shape_offset(controller)
        self.populate_control_colour(controller)

    def populate_control_scale(self, controller: unreal.RigVMController):
        """
        Generates a scale value per a control
        """
        # connects the node of scales to the construction node
        construction_func_name = self.nodes["construction_functions"][0].get_name()

        reduce_ratio = 4.0
        """Magic number to try and get the maya control scale to be similar to that of unreal.
        As the mGear uses a square and ueGear uses a cirlce.
        """

        default_values = ""
        # Calculates the unreal scale for the control and populates it into the array node.
        for control_name in self.metadata.controls:
            aabb = self.metadata.controls_aabb[control_name]
            unreal_size = [round(element / reduce_ratio, 4) for element in aabb[1]]

            # todo: this is a test implementation, for a more robust validation, each axis should be checked.
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
            f'{construction_func_name}.control_offset',
            f'({default_values})',
            True,
            setup_undo_redo=True,
            merge_undo_action=True)

    def populate_control_colour(self, controller):
        cr_func = self.functions["construction_functions"][0]
        construction_node = f"{self.name}_{cr_func}"

        for i, control_name in enumerate(self.metadata.controls):
            colour = self.metadata.controls_colour[control_name]

            controller.insert_array_pin(f'{construction_node}.control_colours', -1, '')
            controller.set_pin_default_value(f'{construction_node}.control_colours.{i}.R', f"{colour[0]}", False)
            controller.set_pin_default_value(f'{construction_node}.control_colours.{i}.G', f"{colour[1]}", False)
            controller.set_pin_default_value(f'{construction_node}.control_colours.{i}.B', f"{colour[2]}", False)
            controller.set_pin_default_value(f'{construction_node}.control_colours.{i}.A', "1", False)

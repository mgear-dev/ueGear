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
        populates the bone shoulder joint node
        """

        if bones is None or len(bones) < 1:
            unreal.log_error("[Bone Populate] Failed no Bones found")
            return
        if controller is None:
            unreal.log_error("[Bone Populate] Failed no Controller found")
            return
        print("-----------------")
        print(" Populate Bones")
        print("-----------------")

        bone_name = bones[0].key.name

        construction_node = self.nodes["construction_functions"][0]
        forward_node = self.nodes["forward_functions"][0]

        for function in [construction_node, forward_node]:
            construction_node_name = function.get_name()

            controller.set_pin_default_value(
                f'{construction_node_name}.shoulder_jnt.Name', bone_name, False)
            controller.set_pin_default_value(
                f'{construction_node_name}.shoulder_jnt.Type', 'Bone', False)


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

        node_names = controller.get_graph().find_node_by_name(names_node)
        node_trans = controller.get_graph().find_node_by_name(trans_node)

        self.add_misc_function(node_names)
        self.add_misc_function(node_trans)

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

        self.populate_control_scale(controller)
        self.populate_control_shape_offset(controller)

    def populate_control_scale(self, controller: unreal.RigVMController):
        """
        Generates a scale value per a control
        """
        import ueGear.controlrig.manager as ueMan

        # Generates the array node
        array_name = ueMan.create_array_node(f"{self.metadata.fullname}_control_scales", controller)
        array_node = controller.get_graph().find_node_by_name(array_name)
        self.add_misc_function(array_node)

        # connects the node of scales to the construction node
        construction_func_name = self.nodes["construction_functions"][0].get_name()
        controller.add_link(f'{array_name}.Array',
                            f'{construction_func_name}.control_sizes')

        pins_exist = ueMan.array_node_has_pins(array_name, controller)

        reduce_ratio = 4.0
        """Magic number to try and get the maya control scale to be similar to that of unreal.
        As the mGear uses a square and ueGear uses a cirlce.
        """

        pin_index = 0

        # Calculates the unreal scale for the control and populates it into the array node.
        for control_name in self.metadata.controls:
            aabb = self.metadata.controls_aabb[control_name]
            print(f"Shoulder > {control_name} > {aabb}")
            unreal_size = [round(element/reduce_ratio, 4) for element in aabb[1]]

            # todo: this is a test implementation, for a more robust validation, each axis should be checked.
            # rudementary way to check if the bounding box might be flat, if it is then
            # the first value if applied onto the axis
            if unreal_size[0] == unreal_size[1] and unreal_size[2] < 1.0:
                unreal_size[2] = unreal_size[0]

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

    def populate_control_shape_offset(self, controller: unreal.RigVMController):
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
                            f'{construction_func_name}.control_offset')

        pins_exist = ueMan.array_node_has_pins(array_name, controller)

        pin_index = 0

        for control_name in self.metadata.controls:
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
import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component

class Component(base_component.UEComponent):
    name = "test_Spine"
    mgear_component = "EPIC_spine_02"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['construct_FK_spine'],
                          'forward_functions': ['forward_FK_spine'],
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

        # TODO:
        # [ ] Check how many bones exist, as that will drive the fk system
        # [ ] Add input for ik
        # [ ] Calculate output bones joints

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
                                         self.metadata.fullname,
                                         False)

    def populate_bones(self, bones: list[unreal.RigBoneElement] = None, controller: unreal.RigVMController = None):
        """
        Generates the Bone array node that will be utilised by control rig to drive the component
        """
        if bones is None or len(bones) < 3:
            unreal.log_error("[Bone Populate] Failed no Bones found")
            return
        if controller is None:
            unreal.log_error("[Bone Populate] Failed no Controller found")
            return
        print("-----------------")
        print(" Populate Bones")
        print("-----------------")

        # Unique name for this skeleton node array
        array_node_name = f"{self.metadata.fullname}_RigUnit_ItemArray"

        # node doesn't exists, create the joint node
        if not controller.get_graph().find_node_by_name(array_node_name):
            self._init_master_joint_node(controller, array_node_name, bones)

            # Connects the Item Array Node to the functions.
            for evaluation_path in self.nodes.keys():
                for function_node in self.nodes[evaluation_path]:
                    print(f"  Creating Connection:   {array_node_name}.Items >> {function_node.get_name()}.Joints")
                    controller.add_link(f'{array_node_name}.Items',
                                        f'{function_node.get_name()}.Joints')

        outpu_joint_node_name = self._init_output_joints(controller, bones)

        construction_func_name = self.nodes["construction_functions"][0].get_name()

        controller.add_link(f'{outpu_joint_node_name}.Items',
                            f'{construction_func_name}.joint_outputs')

        node = controller.get_graph().find_node_by_name(array_node_name)
        self.add_misc_function(node)

    def _init_master_joint_node(self, controller, node_name: str, bones):
        """Create the bone node, that will contain a list of all the bones that need to be
        driven.
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

    def _init_output_joints(self, controller: unreal.RigVMController, bones):
        """Creates an array of joints that will be fed into the node and then drive the output pins

        TODO: Refactor this, as it is no longer needed due to relatives now existsing in the json file.
        """

        print(" - Init Output Joints")

        # Unique name for this skeleton output array
        array_node_name = f"{self.metadata.fullname}_OutputSkeleton_RigUnit_ItemArray"

        # Create a lookup table of the bones, to speed up interactions
        bone_dict = {}
        for bone in bones:
            bone_dict[str(bone.key.name)] = bone

        # Checks if node exists, else creates node
        found_node = controller.get_graph().find_node_by_name(array_node_name)

        if not found_node:
            # Create the ItemArray node
            found_node = controller.add_unit_node_from_struct_path(
                '/Script/ControlRig.RigUnit_ItemArray',
                'Execute',
                unreal.Vector2D(500.0, 500.0),
                array_node_name)

        # Do pins already exist on the node, if not then we will have to create them. Else we dont
        existing_pins = found_node.get_pins()[0].get_sub_pins()

        generate_new_pins = True
        if len(existing_pins) > 0:
            generate_new_pins = False

        pin_index = 0

        # Loops over all the joint relatives to setup the array
        for jnt_name, jnt_index in self.metadata.joint_relatives.items():
            joint_name = self.metadata.joints[jnt_index]
            found_bone = bone_dict.get(joint_name, None)

            if found_bone is None:
                unreal.log_error(f"[Init Output Joints] Cannot find bone {joint_name}")
                continue

            # No pins are found then we add new pins on the array to populate
            if generate_new_pins:
                # Add new Item to array
                controller.insert_array_pin(f'{array_node_name}.Items', -1, '')

            bone_name = joint_name
            # Set Item to be of bone type
            controller.set_pin_default_value(f'{array_node_name}.Items.{pin_index}.Type', 'Bone', False)
            # Set the pin to be a specific bone name
            controller.set_pin_default_value(f'{array_node_name}.Items.{pin_index}.Name', bone_name, False)

            pin_index += 1

        node = controller.get_graph().find_node_by_name(array_node_name)
        self.add_misc_function(node)

        return array_node_name

    def populate_control_transforms(self, controller: unreal.RigVMController = None):
        """Updates the transform data for the controls generated, with the data from the mgear json
        file.
        """
        import ueGear.controlrig.manager as ueMan

        names_node = ueMan.create_array_node("control_names", controller)
        trans_node = ueMan.create_array_node("control_transforms", controller)

        node_names = controller.get_graph().find_node_by_name(names_node)
        node_trans = controller.get_graph().find_node_by_name(trans_node)

        self.add_misc_function(node_names)
        self.add_misc_function(node_trans)

        # Connecting nodes needs to occur first, else the array node does not know the type and will not accept default
        # values
        construction_func_name = self.nodes["construction_functions"][0].get_name()
        controller.add_link(f'{trans_node}.Array',
                            f'{construction_func_name}.fk_world_transforms')
        controller.add_link(f'{names_node}.Array',
                            f'{construction_func_name}.fk_world_keys')

        # Checks the pins
        name_pins_exist = ueMan.array_node_has_pins(names_node, controller)
        trans_pins_exist = ueMan.array_node_has_pins(trans_node, controller)

        pin_index = 0

        for control_name in self.metadata.controls:
            control_transform = self.metadata.control_transforms[control_name]

            if not name_pins_exist:
                controller.insert_array_pin(f'{names_node}.Values', -1, '',
                                             print_python_command=True)
            if not trans_pins_exist:
                controller.insert_array_pin(f'{trans_node}.Values', -1, '',
                                             print_python_command=True)

            quat = control_transform.rotation
            pos = control_transform.translation

            controller.set_pin_default_value(f'{names_node}.Values.{pin_index}',
                                             control_name,
                                             False,
                                             print_python_command=True)

            controller.set_pin_default_value(f"{trans_node}.Values.{pin_index}",
                                             f"(Rotation=(X={quat.x},Y={quat.y},Z={quat.z},W={quat.w}), "
                                             f"Translation=(X={pos.x},Y={pos.y},Z={pos.z}),"
                                             f"Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))",
                                             True,
                                             print_python_command=True)

            pin_index += 1

        self.populate_control_scale(controller)
        self.populate_control_shape_offset(controller)
        self.populate_control_colour(controller)

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
            unreal_size = [round(element/reduce_ratio, 4) for element in aabb[1]]

            # todo: this is a test implementation for the spine, for a more robust validation, each axis should be checked.
            # rudementary way to check if the bounding box might be flat, if it is then
            # the first value if applied onto the axis
            if unreal_size[0] == unreal_size[1] and unreal_size[2] < 0.01:
                unreal_size[2] = unreal_size[0]
            elif unreal_size[1] == unreal_size[2] and unreal_size[0] < 0.01:
                unreal_size[0] = unreal_size[1]
            elif unreal_size[0] == unreal_size[2] and unreal_size[1] < 0.01:
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
                            f'{construction_func_name}.control_offsets')

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

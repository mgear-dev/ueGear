import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component


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

        if bones is None or len(bones) < 3:
            unreal.log_error(f"[Bone Populate] Failed no Bones found: Found {len(bones)} bones")
            return
        if controller is None:
            unreal.log_error("[Bone Populate] Failed no Controller found")
            return
        print("-----------------")
        print(" Populate Bones")
        print("-----------------")

        for bone in bones:
            bone_name = bone.key.name

        # Unique name for this skeleton node array
        array_node_name = f"{self.metadata.fullname}_RigUnit_ItemArray"

        # node doesn't exists, create the joint node
        if not controller.get_graph().find_node_by_name(array_node_name):
            self._init_master_joint_node(controller, array_node_name, bones)

        node = controller.get_graph().find_node_by_name(array_node_name)
        self.add_misc_function(node)

    def init_input_data(self, controller: unreal.RigVMController):

        # todo:
        # self._set_side_colour(controller)

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

    def _set_side_colour(self, controller: unreal.RigVMController):
        """Sets the controls default colour depending on the side"""

        construction_node = self.nodes["construction_functions"][0]
        func_name = construction_node.get_name()

        # Sets the colour channels to be 0
        for channel in ["R", "G", "B"]:
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

    def populate_control_names(self, controller: unreal.RigVMController):
        import ueGear.controlrig.manager as ueMan

        names_node = ueMan.create_array_node(f"{self.metadata.fullname}_control_names", controller)
        node_names = controller.get_graph().find_node_by_name(names_node)

        self.add_misc_function(node_names)

        # Connecting nodes needs to occur first, else the array node does not know the type and will not accept default
        # values
        construction_func_name = self.nodes["construction_functions"][0].get_name()
        controller.add_link(f'{names_node}.Array',
                            f'{construction_func_name}.control_names')
        # Checks the pins
        name_pins_exist = ueMan.array_node_has_pins(names_node, controller)

        pin_index = 0

        for control_name in self.metadata.controls:
            if not name_pins_exist:
                found_node = controller.get_graph().find_node_by_name(names_node)
                existing_pin_count = len(found_node.get_pins()[0].get_sub_pins())
                if existing_pin_count < len(self.metadata.controls):
                    controller.insert_array_pin(f'{names_node}.Values',
                                                -1,
                                                '')

            controller.set_pin_default_value(f'{names_node}.Values.{pin_index}',
                                             control_name,
                                             False)
            pin_index += 1

    # TODO: Setup control size scale from mGear AABB
    def populate_control_scale(self, controller: unreal.RigVMController):
        """
        Generates a scale value per a control
        """

        import ueGear.controlrig.manager as ueMan

        # logs the AABB for each control
        for control_name in self.metadata.controls:
            print(control_name)
            print(self.metadata.controls_aabb[control_name])

        # Generates the array node
        array_name = ueMan.create_array_node(f"{self.metadata.fullname}_control_scales", controller)
        array_node = controller.get_graph().find_node_by_name(array_name)
        self.add_misc_function(array_node)

        # connects the node of scales to the construction node
        construction_func_name = self.nodes["construction_functions"][0].get_name()
        controller.add_link(f'{array_name}.Array',
                            f'{construction_func_name}.control_scale')

        name_pins_exist = ueMan.array_node_has_pins(array_name, controller)

        aabb_divisor = 3
        """Magic number to try and get the maya control scale to be similar to that of unreal"""

        # populate array
        pin_index = 0
        for control_name in self.metadata.controls:
            aabb = self.metadata.controls_aabb[control_name]
            aabb = [axi/aabb_divisor for axi in aabb]

            if not name_pins_exist:
                existing_pin_count = len(array_node.get_pins()[0].get_sub_pins())
                if existing_pin_count < len(self.metadata.controls_aabb):
                    controller.insert_array_pin(f'{array_name}.Values',
                                                -1,
                                                '')

            controller.set_pin_default_value(f'{array_name}.Values.{pin_index}',
                                             f'(X={aabb[0]},Y={aabb[1]},Z={aabb[2]})',
                                             False)

            pin_index += 1

    # TODO: setup an init_controls method and move this method and the populate controls method into it
    def populate_control_transforms(self, controller: unreal.RigVMController = None):
        """Updates the transform data for the controls generated, with the data from the mgear json
        file.
        """
        import ueGear.controlrig.manager as ueMan

        trans_node = ueMan.create_array_node(f"{self.metadata.fullname}_control_transforms", controller)
        node_trans = controller.get_graph().find_node_by_name(trans_node)
        self.add_misc_function(node_trans)

        # Connecting nodes needs to occur first, else the array node does not know the type and will not accept default
        # values
        construction_func_name = self.nodes["construction_functions"][0].get_name()
        controller.add_link(f'{trans_node}.Array',
                            f'{construction_func_name}.control_transforms')

        # Checks the pins
        trans_pins_exist = ueMan.array_node_has_pins(trans_node, controller)

        pin_index = 0

        for control_name in self.metadata.controls:
            control_transform = self.metadata.control_transforms[control_name]

            if not trans_pins_exist:
                found_node = controller.get_graph().find_node_by_name(trans_node)
                existing_pin_count = len(found_node.get_pins()[0].get_sub_pins())
                if existing_pin_count < len(self.metadata.controls):
                    controller.insert_array_pin(f'{trans_node}.Values',
                                                -1,
                                                '')

            quat = control_transform.rotation
            pos = control_transform.translation

            controller.set_pin_default_value(f"{trans_node}.Values.{pin_index}",
                                             f"(Rotation=(X={quat.x},Y={quat.y},Z={quat.z},W={quat.w}), "
                                             f"Translation=(X={pos.x},Y={pos.y},Z={pos.z}),"
                                             f"Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))",
                                             True)

            pin_index += 1

        self.populate_control_names(controller)
        self.populate_control_scale(controller)

    def get_associated_parent_output(self, name: str, controller: unreal.RigVMController) -> str:
        """
        name: Name of the relative key that will be used to get the associated bone index.
        controller: The BP controller that will manipulate the graph.

        return: The name of the pin to be connected from.
        """
        print("--- get_associated_parent_output ---")

        # Looks at the metacarpals jointRelative dictionary for the name and the index of the output
        joint_index = str(self.metadata.joint_relatives[name])

        print(f"  {self.name} > {name} : {joint_index}")

        node_name = "_".join( [self.name, name, joint_index] )

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

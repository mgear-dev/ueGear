import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component
from ueGear.controlrig.helpers import controls


class Component(base_component.UEComponent):
    name = "test_FK"
    mgear_component = "EPIC_control_01"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['construct_FK_singleton'],
                          'forward_functions': ['forward_FK_singleton'],
                          'backwards_functions': ['backwards_FK_singleton'],
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

        # ---- TESTING
        self.bones = []

    def create_functions(self, controller: unreal.RigVMController):
        if controller is None:
            return

        # calls the super method
        super().create_functions(controller)

        # Generate Function Nodes
        for evaluation_path in self.functions.keys():

            # Skip the forward function creation if no joints are needed to be driven
            if evaluation_path == 'forward_functions' and self.metadata.joints is None:
                continue

            # Skip the backwards function creation if no joints are needed to be driven
            if evaluation_path == 'backwards_functions' and self.metadata.joints is None:
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

        construct_func = base_component.get_construction_node(self, f"{self.name}_construct_FK_singleton")
        if construct_func is None:
            unreal.log_error("  Create Functions Error - Cannot find construct singleton node")
        controller.set_pin_default_value(construct_func.get_name() + '.control_name',
                                         self.metadata.controls[0],
                                         False)

        # self._fit_comment(controller)

    def populate_bones(self, bones: list[unreal.RigBoneElement] = None, controller: unreal.RigVMController = None):
        """
        Generates the Bone array node that will be utilised by control rig to drive the component
        """
        if bones is None or len(bones) > 1:
            unreal.log_error(f"[populate_bones] {self.name}: No bone provided")
            return
        if controller is None:
            unreal.log_error(f"{self.name}: No controller provided")
            return

        bone_name = bones[0].key.name

        if bone_name == "":
            unreal.log_error(f"[populate_bones] Bone name cannot be empty:{bones}")
            return

        # Populates the joint pin
        for evaluation_path in self.nodes.keys():
            for function_node in self.nodes[evaluation_path]:
                success = controller.set_pin_default_value(f'{function_node.get_name()}.joint',
                                                 f'(Type=Bone,Name="{bone_name}")', True)
                if not success:
                    unreal.log_error(f"[populate_bones] Setting Pin failed:{function_node.get_name()}.joint << {bone_name}")

    def populate_control_transforms(self, controller: unreal.RigVMController = None):
        """Updates the transform data for the controls generated, with the data from the mgear json
        file.
        """

        control_name = self.metadata.controls[0]
        control_transform = self.metadata.control_transforms[control_name]

        const_func = self.nodes['construction_functions'][0].get_name()

        quat = control_transform.rotation
        pos = control_transform.translation

        controller.set_pin_default_value(f"{const_func}.control_world_transform",
                                         f"(Rotation=(X={quat.x},Y={quat.y},Z={quat.z},W={quat.w}), "
                                         f"Translation=(X={pos.x},Y={pos.y},Z={pos.z}),"
                                         f"Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))",
                                         True)

        self.populate_control_shape_orientation(controller)
        self.populate_control_scale(controller)
        self.populate_control_colour(controller)

    def populate_control_shape_orientation(self, controller: unreal.RigVMController = None):
        """Populates the control's shapes orientation"""

        for cr_func in self.functions["construction_functions"]:
            construction_node = f"{self.name}_{cr_func}"

            ue_cr_node = controller.get_graph().find_node_by_name(construction_node)

            controller.set_pin_default_value(f'{construction_node}.control_orientation.X',
                                             '90.000000',
                                             False)

    def populate_control_scale(self, controller: unreal.RigVMController):
        """Calculates the size of the control from the Bounding Box"""

        for cr_func in self.functions["construction_functions"]:
            construction_node = f"{self.name}_{cr_func}"

            control_name = self.metadata.controls[0]
            aabb = self.metadata.controls_aabb[control_name]
            reduce_ratio = 6.0
            unreal_size = [round(element / reduce_ratio, 4) for element in aabb[1]]

            for axis, value in zip(["X", "Y", "Z", ], unreal_size):

                # an ugly way to ensure that the bounding box is not 100% flat,
                # causing the control to be scaled flat on Z
                if axis == "Z" and value <= 1.0:
                    value = unreal_size[0]

                controller.set_pin_default_value(
                    f'{construction_node}.control_size.{axis}',
                    str(value),
                    False)

    def populate_control_colour(self, controller):
        cr_func = self.functions["construction_functions"][0]
        construction_node = f"{self.name}_{cr_func}"

        control_name = self.metadata.controls[0]
        colour = self.metadata.controls_colour[control_name]

        default_value = f"(R={colour[0]}, G={colour[1]}, B={colour[2]}, A=1.0)"

        # Populates and resizes the pin in one go
        controller.set_pin_default_value(
            f'{construction_node}.control_colour',
            f"{default_value}",
            True,
            setup_undo_redo=True,
            merge_undo_action=True)


class ManualComponent(Component):
    name = "Manual_FK_Singleton"

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['manual_construct_FK_singleton'],
                          'forward_functions': ['forward_FK_singleton'],
                          'backwards_functions': ['backwards_FK_singleton'],
                          }

        self.is_manual = True

        self.root_control_children = ["ctl"]

    def create_functions(self, controller: unreal.RigVMController):
        if controller is None:
            return

        # calls the super method and creates the comment block
        base_component.UEComponent.create_functions(self, controller)

        # Generate Function Nodes
        for evaluation_path in self.functions.keys():

            # Skip the forward function creation if no joints are needed to be driven
            if evaluation_path == 'forward_functions' and self.metadata.joints is None:
                continue

            # Skip the backwards function creation if no joints are needed to be driven
            if evaluation_path == 'backwards_functions' and self.metadata.joints is None:
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

    def generate_manual_controls(self, hierarchy_controller):
        """Creates all the manual controls in the designated structure"""

        for control_name in self.metadata.controls:
            print(f"Initializing Manual Control - {control_name}")
            new_control = controls.CR_Control(name=control_name)
            role = self.metadata.controls_role[control_name]

            # stored metadata values
            control_transform = self.metadata.control_transforms[control_name]
            control_colour = self.metadata.controls_colour[control_name]
            control_aabb = self.metadata.controls_aabb[control_name]
            control_offset = control_aabb[0]
            control_scale = [control_aabb[1][0] / 4.0,
                             control_aabb[1][1] / 4.0,
                             control_aabb[1][2] / 4.0]

            # Set the colour, required before build
            new_control.colour = control_colour
            new_control.shape_name = "RoundedSquare_Thick"

            # Generate the Control
            new_control.build(hierarchy_controller)

            # Sets the controls position, and offset translation and scale of the shape
            new_control.set_transform(quat_transform=control_transform)
            new_control.shape_transform_global(pos=control_offset,
                                               scale=control_scale,
                                               rotation=[90, 0, 0])

            # Stores the control by role, for loopup purposes later
            self.control_by_role[role] = new_control

    def populate_control_transforms(self, controller: unreal.RigVMController = None):

        construction_func_name = self.nodes["construction_functions"][0].get_name()

        controls = []

        for role_key in self.control_by_role.keys():
            control = self.control_by_role[role_key]
            controls.append(control)

        def update_input_plug(plug_name, control_list):
            """
            Simple helper function making the plug population reusable for ik and fk
            """
            for entry in control_list:
                if entry.rig_key.type == unreal.RigElementType.CONTROL:
                    t = "Control"
                if entry.rig_key.type == unreal.RigElementType.NULL:
                    t = "Null"
                n = entry.rig_key.name
                entry = f'(Type={t}, Name="{n}")'

                controller.set_pin_default_value(
                    f'{construction_func_name}.{plug_name}',
                    f"{entry}",
                    True,
                    setup_undo_redo=True,
                    merge_undo_action=True)

        update_input_plug("control", controls)

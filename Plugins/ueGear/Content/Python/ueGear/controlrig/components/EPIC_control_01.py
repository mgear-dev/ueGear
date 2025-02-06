import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component


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
            return
        if controller is None:
            return
        bone_name = bones[0].key.name

        # Unique name for this skeleton node array
        array_node_name = f"{self.metadata.fullname}_RigUnit_ItemArray"

        # node already exists
        if controller.get_graph().find_node_by_name(array_node_name):
            unreal.log_error("Cannot populate bones, node already exists!")
            return

        # Creates an Item Array Node to the control rig
        controller.add_unit_node_from_struct_path(
            '/Script/ControlRig.RigUnit_ItemArray',
            'Execute',
            unreal.Vector2D(-54.908936, 204.649109),
            array_node_name)

        # Populates the Item Array Node
        controller.insert_array_pin(f'{array_node_name}.Items', -1, '')
        controller.set_pin_default_value(f'{array_node_name}.Items.0',
                                         f'(Type=Bone,Name="{bone_name}")',
                                         True)
        controller.set_pin_expansion(f'{array_node_name}.Items.0', True)
        controller.set_pin_expansion(f'{array_node_name}.Items', True)

        # Connects the Item Array Node to the create/forward/backwards functions.
        for evaluation_path in self.nodes.keys():
            for function_node in self.nodes[evaluation_path]:
                controller.add_link(f'{array_node_name}.Items',
                                    f'{function_node.get_name()}.Array')

        node = controller.get_graph().find_node_by_name(array_node_name)
        self.add_misc_function(node)

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
            unreal_size = [round(element/reduce_ratio, 4) for element in aabb[1]]

            for axis, value in zip(["X", "Y", "Z",], unreal_size):

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

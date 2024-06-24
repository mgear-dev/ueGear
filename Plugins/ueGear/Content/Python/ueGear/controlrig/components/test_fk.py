__all__ = ['fkComponent']

import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component
from ueGear.controlrig.components.base_component import UEComponent

# class mfkComponent(fkComponent):
# # When building Maya use this node
#     def create_functions(self, controller: unreal.RigVMController = None):
#         fkComponent.create_functions()
#
#         # inject matrix data and orientation
#

class fkComponent(UEComponent):
    name = "test_FK"
    mgear_component = "EPIC_control_01"

    # skeleton_joints = None
    # skeleton_array_node = None

    def __init__(self):
        super().__init__()

        self.functions = {'construction_functions': ['construct_FK_singleton'],
                          'forward_functions': ['forward_FK_singleton'],
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

        # ---- TESTING
        self.bones = []

        # parent = root
        # Item = root
        # root = parent + Item

    def _init_comment(self, controller: unreal.RigVMController):
        """Creates the comment node"""

        graph = controller.get_graph()

        if not graph:
            return

        comment_node_name = self.name
        comment_text = f"ueComponent: {self.name}"
        node = graph.find_node_by_name(comment_node_name)

        if node:
            self.comment_node = node
            return

        # Create the comment node in unreal
        self.comment_node = controller.add_comment_node(comment_text, node_name=comment_node_name)

    def _fit_comment(self, controller: unreal.RigVMController):
        """Tries to fit the comment to the nodes that were generated"""

        # [ ] Loop over all the nodes in the component
        # [ ] Build a size map of all the components
        # [ ] Move comment block outside of the size mapped

        # Stores the smallest position, as that will be the top left
        pos = None

        height = 0
        width = 0

        node_count = 0
        node_offset_x = 0
        node_offset_y = 0

        max_node_width = 0

        pre_size = None
        y_spacing = 10

        for flow_name in ['construction_functions', 'forward_functions', 'backwards_functions']:
            nodes = self.nodes[flow_name]

            for node in nodes:
                # start with the position equal to the first node
                if pos is None:
                    pos = node.get_position()

                if pre_size:
                    controller.set_node_position(node, unreal.Vector2D(pos.x, pos.y + pre_size + (y_spacing * node_count) ))


                # Get top left most position
                current_pos = node.get_position()

                if current_pos.x < pos.x:
                    pos.x = current_pos.x
                if current_pos.y < pos.y:
                    pos.y = current_pos.y

                #stores the previous size
                pre_size = node.get_size().y + pos.y

                node_count += 1

        for flow_name in ['construction_functions', 'forward_functions', 'backwards_functions']:
            nodes = self.nodes[flow_name]
            for node in nodes:

                current_pos = node.get_position()
                size = node.get_size()

                height = height + size.y + 10

                controller.set_node_position(node, unreal.Vector2D(pos.x, pos.y + height))







    def create_functions(self, controller: unreal.RigVMController):
        if controller is None:
            return

        print("-------------------------------")
        print(" Create ControlRig Functions")
        print("-------------------------------")

        self._init_comment(controller)

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
        print("-----------------")
        print(" Populate Bones")
        print("-----------------")

        bone_name = bones[0].key.name
        print(f"  {self.name} > {bone_name}")

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

        # Connects the Item Array Node to the functions.
        for evaluation_path in self.nodes.keys():
            for function_node in self.nodes[evaluation_path]:
                print(f"  Creating Connection:   {array_node_name}.Items >> {function_node.get_name()}.Array")
                controller.add_link(f'{array_node_name}.Items',
                                    f'{function_node.get_name()}.Array')

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
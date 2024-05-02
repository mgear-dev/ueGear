__all__ = ['fkComponent']

import unreal

from .base_component import UEComponent


class fkComponent(UEComponent):
    name = "test_FK"
    mgear_component = "EPIC_control_01"
    cr_variables = {}

    functions: dict = {'construction_functions': ['construct_FK_singleton'],
                       'forward_functions': ['forward_FK_singleton'],
                       'backwards_functions': [],
                       }

    def __init__(self):
        super().__init__()

    """
    Brain fart!
    looking into each component being a recipe, that can do its own creation / rewiring
    
    The biggest issue is the interconnected nodes and order of evaluation required for 
    input and output driven plugs.
    """

    skeleton_joints = None
    skeleton_array_node = None

    def _pre_skeleton_connection(self):
        pass

    def skeleton_connection(self):
        pass


    def populate_bones(self, bones: list[unreal.RigBoneElement] = None, controller: unreal.RigVMController = None):
        if bones is None or len(bones) > 1:
            return
        if controller is None:
            return
        print("Populate Bones")

        bone_name = bones[0].key.name
        print(f"{self.name} > {bone_name}")

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
                controller.add_link(f'{array_node_name}.Items',
                                    f'{function_node.get_name()}.Array')

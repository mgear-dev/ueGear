__all__ = ['fkComponent']

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
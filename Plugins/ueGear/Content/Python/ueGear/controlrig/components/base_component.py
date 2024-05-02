__all__ = ['UEComponent']

import unreal

from ..mgear import mgComponent


class UEComponent(object):
    name: str = ""
    """Name of the ueGear Component"""

    mgear_component: str = ""
    """The mGear Component that this ueGear component relates too"""

    cr_variables: dict = None
    """Control Rig Variables that will be generated on the control rig 
    Variable list. This is required for some part of the CR to evaluate 
    correctly"""

    # DEVELOPMENT!!!!!!!

    functions: dict = None
    """List of Control Rig functions that make up this ueComponent"""

    connection: dict = None

    # nodes are the generated control rig functions that relate to the component
    nodes: dict = None

    # Stores the mgear metadata component, so this uegear component knows what it relates too.
    metadata: mgComponent = None

    # Component is made up of multiple nodes
    # Each node can have multiple inputs and outputs
    # Components can be in one of 3 streams

    def __init__(self):
        self.functions = {'construction_functions': [],
                          'forward_functions': [],
                          'backwards_functions': [],
                          }
        self.nodes = {'construction_functions': [],
                      'forward_functions': [],
                      'backwards_functions': [],
                      }
        self.cr_variables = {}
        self.connection = {}

    def find_parent(self):
        pass

    def create_functions(self):
        """OVERLOAD THIS METHOD

        This method will be used to generate all the associated functions with the mGear component, and apply any
        alterations specific to the component.
        """
        pass

    def populate_bones(self):
        """OVERLOAD THIS METHOD

        This method should handle the population of bones into the functions
        """
        pass

    # DEVELOPMENT!!!!!!!

    def repr(self):
        return " : ".join(["UEG Component  ", self.name, self.mgear_component, self.functions, self.cr_variables])


def get_construction_node(comp: UEComponent, name) -> unreal.RigVMNode:
    """Tries to return the construction node with the specified name"""
    nodes = comp.nodes["construction_functions"]

    for node in nodes:
        if node.get_name() == name:
            return node

__all__ = ['UEComponent']

from ..mComponents import MGComponent


class UEComponent(object):
    name: str = ""
    """Name of the ueGear Component"""
    mgear_component: str = ""

    """List of Control Rig functions that make up this ueComponent"""
    cr_variables: dict = {}
    """Control Rig Variables that will be generated on the control rig 
    Variable list. This is required for some part of the CR to evaluate 
    correctly"""

    # DEVELOPMENT!!!!!!!

    construction_functions: list = []
    forward_functions: list = []
    backwards_functions: list = []

    """The mGear Component that this ueGear component relates too"""
    functions: dict = {'construction_functions': [],
                       'forward_functions': [],
                       'backwards_functions': [],
                       }

    connection: dict = {}

    # nodes are the generated control rig functions that relate to the component
    nodes: dict = {'construction_functions': [],
                   'forward_functions': [],
                   'backwards_functions': [],
                   }

    # Stores the mgear metadata component, so this uegear component knows what it relates too.
    metadata: MGComponent = None

    # Component is made up of multiple nodes
    # Each node can have multiple inputs and outputs
    # Components can be in one of 3 streams

    # DEVELOPMENT!!!!!!!

    def repr(self):
        return " : ".join(["UEG Component  ", self.name, self.mgear_component, self.functions, self.cr_variables])

__all__ = ['UEComponent']

import unreal

from ueGear.controlrig.mgear import mgComponent


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
    """Stores the generated Control Rig Nodes [Function Nodes]"""

    # Stores the mgear metadata component, so this uegear component knows what it relates too.
    metadata: mgComponent = None

    # Component is made up of multiple nodes
    # Each node can have multiple inputs and outputs
    # Components can be in one of 3 streams

    parent_node = None
    """Stores the mGear component that is the parent"""
    children_node = None
    """Stores the child mGear components"""

    inputs = None
    """List of inputs into the mgear component"""
    outputs = None
    """List of outputs from the mgear component"""

    bones = None
    """Storing all the SKM bones that have been found using Control Rig"""

    comment_node: unreal.RigVMCommentNode = None
    """Stores a reference to the comment node that will be used to group functions together"""

    def __init__(self):
        self.functions = {'construction_functions': [],
                          'forward_functions': [],
                          'backwards_functions': [],
                          }
        self.nodes: dict[str, list[unreal.RigVMNode]] = {
            'construction_functions': [],
            'forward_functions': [],
            'backwards_functions': [],
        }
        self.cr_variables = {}
        self.connection = {}

        self.children_node = []

        self.inputs = []
        self.outputs = []


    @property
    def pos(self):
        """Return the position of the comment block, that should encompass all the nodes
        - The top left corner of the comment block.
        """
        if self.comment_node is None:
            return

        return self.comment_node.get_position()

    @property
    def size(self):
        """Returns the size of the comment block"""
        if self.comment_node is None:
            return

        return self.comment_node.get_size()

    def component_size(self, size:unreal.Vector2D, controller:unreal.RigVMController):
        """Sets the size of the comment block"""
        if self.comment_node is None:
            return
        controller.set_node_size(self.comment_node,size)

    def add_child(self, child_comp):

        # Checks if node about to be added as a child exist as a child of another node,
        # if so removed itself
        if child_comp.parent_node:
            child_comp.parent_node.remove_child(node=child_comp)

        self.children_node.append(child_comp)
        child_comp.parent_node = self

    def get_children(self, name):
        found_nodes = []
        for node in self.children_node:
            if node.name == name:
                found_nodes.append(node)

        return found_nodes

    def remove_child(self, name=None, node=None):
        child_count = len(self.children_node)

        if name is None or node is None or child_count == 0:
            return False

        if name:
            child_count = len(self.children_node)
            for i in reversed(range(child_count)):
                if self.children_node[i].name == name:
                    child_node = self.children_node.pop(i)
                    child_node.parent_node = None

        if node:
            child_count = len(self.children_node)
            for i in reversed(range(child_count)):
                if self.children_node[i] == node:
                    child_node = self.children_node.pop(i)
                    child_node.parent_node = None

        return True

    def set_parent(self, parent_comp):
        self.remove_parent()
        self.parent_node = parent_comp
        self.parent_node.children_node.append(parent_comp)

    def remove_parent(self):
        if self.parent_node is None:
            return

        parent_node = self.parent_node
        self.parent_node = None
        parent_node.remove_child(node=self)

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

    def __repr__(self):
        data = f"Component Name : {self.name}"
        return data


def get_construction_node(comp: UEComponent, name) -> unreal.RigVMNode:
    """Tries to return the construction node with the specified name"""
    nodes = comp.nodes["construction_functions"]

    for node in nodes:
        if node.get_name() == name:
            return node

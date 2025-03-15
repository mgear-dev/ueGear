__all__ = ['UEComponent']

import unreal

from ueGear.controlrig.helpers.controls import CR_Control
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

    #------------ MANUAL Attributes ---------------

    is_manual: bool = False
    """If this component is manual then this will be set to true"""

    # root_control_name = None
    # """Stores the root control for the component. This is used to reparent the generated node with the parent node"""

    root_control_children: list[str] = None
    """List of Control Roles will be used to look up controls that will be parented to the Parent Component."""

    control_by_role: dict[str, CR_Control]
    """Stores the controls by there role name, so they can easily be looked up"""



    #==============================================

    def __init__(self):
        self.functions = {'construction_functions': [],
                          'forward_functions': [],
                          'backwards_functions': [],
                          }
        self.nodes: dict[str, list[unreal.RigVMNode]] = {
            'construction_functions': [],
            'forward_functions': [],
            'backwards_functions': [],
            'misc_functions': []
        }
        self.cr_variables = {}
        self.connection = {}

        self.children_node = []

        self.inputs = []
        self.outputs = []

        # -- Manual Attributes --
        self.is_manual = False
        self.root_control_children = []
        self.control_by_role = {}

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

    def component_size(self, size: unreal.Vector2D, controller: unreal.RigVMController):
        """Sets the size of the comment block"""
        if self.comment_node is None:
            return
        controller.set_node_size(self.comment_node, size)

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
        self.parent_node.children_node.append(self)

    def remove_parent(self):
        if self.parent_node is None:
            return

        parent_node = self.parent_node
        self.parent_node = None
        parent_node.remove_child(node=self)

    def create_functions(self, controller: unreal.RigVMController):
        """OVERLOAD THIS METHOD

        This method will be used to generate all the associated functions with the mGear component, and apply any
        alterations specific to the component.
        """

        self._init_comment(controller)

    def populate_bones(self):
        """OVERLOAD THIS METHOD

        This method should handle the population of bones into the functions
        """
        pass

    def populate_control_transforms(self):
        """OVERLOAD THIS METHOD

        This method should handle the population of control transforms and control names
        """
        pass

    def init_input_data(self, controller: unreal.RigVMController):
        """OVERLOAD THIS METHOD

        This method should handle all input node data population
        """
        pass

    def get_associated_parent_output(self, name: str, controller: unreal.RigVMController):
        """OVERLOAD THIS METHOD

        This is a helper function that should be used to query the node for a specific mGear parent object,
        which relates to a specific output pin of the current function
        """
        pass

    def forward_solve_connect(self, controller: unreal.RigVMController):
        """OVERLOAD THIS METHOD

        This is the location you would add any custom node to node connection logic, for forward
        solved nodes/functions.
        """
        pass

    def add_misc_function(self, node):
        """
        Adds a miscilanois function(node) to this component so it can be more easily accessed
        and used at a later time.

        misc nodes are nodes that we use as input to the component
        """
        self.nodes["misc_functions"].append(node)

    def get_misc_functions(self):
        """Gets all miscellaneous functions relating to this component"""
        return self.nodes["misc_functions"]

    def set_side_colour(self, controller: unreal.RigVMController):
        """Sets the controls default colour depending on the side"""

        construction_node = self.nodes["construction_functions"][0]
        func_name = construction_node.get_name()

        # Sets the colour channels to be 0,0,0
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

    def _init_master_joint_node(self, controller, node_name: str, bones):
        """Create the bone node, that will contain a list of all the bones that need to be
        driven.

        TODO: This could be made more generic and reusable
        """

        # Creates an Item Array Node to the control rig
        node = controller.add_unit_node_from_struct_path(
            '/Script/ControlRig.RigUnit_ItemArray',
            'Execute',
            unreal.Vector2D(-54.908936, 204.649109),
            node_name)

        default_values = ""
        for i, bone in enumerate(bones):
            bone_name = str(bone.key.name)
            default_values += f'(Type=Bone,Name="{bone_name}"),'

        # trims off the extr ','
        default_values = default_values[:-1]
        # Populates and resizes the pin in one go
        controller.set_pin_default_value(f'{node_name}.Items',
                                         f'({default_values})',
                                         True,
                                         setup_undo_redo=True,
                                         merge_undo_action=True)

        return node

    # DEVELOPMENT!!!!!!!

    def __repr__(self):
        data = f"Component Name : {self.name}"
        return data

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

        raise NotImplementedError

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
                    controller.set_node_position(node,
                                                 unreal.Vector2D(pos.x, pos.y + pre_size + (y_spacing * node_count)))

                # Get top left most position
                current_pos = node.get_position()

                if current_pos.x < pos.x:
                    pos.x = current_pos.x
                if current_pos.y < pos.y:
                    pos.y = current_pos.y

                # stores the previous size
                pre_size = node.get_size().y + pos.y

                node_count += 1

        for flow_name in ['construction_functions', 'forward_functions', 'backwards_functions']:
            nodes = self.nodes[flow_name]
            for node in nodes:
                current_pos = node.get_position()
                size = node.get_size()

                height = height + size.y + 10

                controller.set_node_position(node, unreal.Vector2D(pos.x, pos.y + height))


def get_construction_node(comp: UEComponent, name) -> unreal.RigVMNode:
    """Tries to return the construction node with the specified name"""
    nodes = comp.nodes["construction_functions"]

    for node in nodes:
        if node.get_name() == name:
            return node

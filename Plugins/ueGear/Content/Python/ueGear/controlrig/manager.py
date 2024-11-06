from typing import Optional

import unreal

from ueGear import assets as ue_assets
from ueGear.controlrig import mgear
from ueGear.controlrig import components
from ueGear.controlrig.components import EPIC_control_01


class UEGearManager:
    _factory: unreal.ControlRigBlueprintFactory = None
    """Unreals Control Rig Blue Print Factory. This performs all the alterations to the Control Rig"""

    _cr_blueprints: list[unreal.ControlRigBlueprint] = []
    """List of all available blueprints"""

    _active_blueprint: unreal.ControlRigBlueprint = None
    """The Active Blueprint is the current blueprint that will be modified by the UE Gear Manager"""

    _ue_gear_standard_library = None

    mg_rig: mgear.mgRig = None
    """The mGear rig description, that is used to generate the ueGear 'Control Rig'"""

    uegear_components: list[components.base_component.UEComponent] = []
    """Keeps track of all the created components that relate the the mGear Rig being created"""

    # Thought: We could create a wrapper object that encompasses both mgear and ueGear rigs. keeping them more coupled, for easier data manipulation. but this will add to complexity.

    @property
    def active_control_rig(self):
        return self._active_blueprint

    @active_control_rig.setter
    def active_control_rig(self, value):
        self._active_blueprint = value

    def __init__(self) -> None:
        """
        Initialises the ueGear Manager, making sure that the plugin exists and the factory has been accessed.
        """
        unreal.load_module('ControlRigDeveloper')
        self._factory = unreal.ControlRigBlueprintFactory
        self.get_open_controlrig_blueprints()

        # # Generates the 'Create', 'Forward' and 'Backwards' nodes
        # self.create_solves()

    def get_open_controlrig_blueprints(self):
        """Gets all open Control Rig Blueprints

        Defaults the active CR BP to the first element in the list
        """
        cr_blueprints = unreal.ControlRigBlueprint.get_currently_open_rig_blueprints()

        self._set_control_blueprint(cr_blueprints)

        return self._cr_blueprints

    def _set_control_blueprint(self, control_blueprints):
        """
        Assigns all the control blueprints and will assign the first element to the active CR BP

        :param list(unreal.ControlRigBlueprint) control_blueprints: list of control rig blueprints.
        """
        self._cr_blueprints = control_blueprints

        # No CR BP found to be open.
        if len(self._cr_blueprints) == 0:
            self.set_active_blueprint(None)
            self._cr_blueprints = []
            return None

        self.set_active_blueprint(self._cr_blueprints[0])

    def set_active_blueprint(self, bp: unreal.ControlRigBlueprint):
        """Sets the blueprint that will be getting modified by the ueGearManager

        The Control Rig Blueprint that will be modified by the  manager, is referred to as the "Active Blueprint"
        """
        self._active_blueprint = bp

    def build_world_control(self, force_build=False):
        """
        Generates the world contol. The control will come in at world origin
         - Control is also world aligned.

        :return:
        """
        controller = self.get_active_controller()

        create_ctrl = self.mg_rig.settings["worldCtl"]
        name = self.mg_rig.settings["world_ctl_name"]

        if force_build:
            create_ctrl = True
            name.get("world_ctl_name", "world_ctl")

        if not create_ctrl:
            return

        # Creates the Forward,Backwards and Construction event
        self.create_solves()

        # As the world control is not a specific component in mGear, we create a psudo
        # component for it.
        placeholder_component = mgear.mgComponent()
        placeholder_component.controls = [name]
        placeholder_component.joints = None
        placeholder_component.comp_type = "world_ctrl"
        # populating the boundin box
        placeholder_component.controls_aabb = dict()
        placeholder_component.controls_aabb[name] = [[0, 0, 0], [120.0, 120.0, 120.0]]

        ueg_comp = EPIC_control_01.Component()
        ueg_comp.metadata = placeholder_component
        ueg_comp.name = name

        self.uegear_components.append(ueg_comp)

        ueg_comp.create_functions(controller)

        # Orients the control shape
        ueg_comp.populate_control_shape_orientation(controller)
        ueg_comp.populate_control_scale(controller)

    def build_component(self, name, ignore_parent=True):
        """Create an individual component from the mgear scene desciptor file.

        """

        print("------------------------------")
        print(f" BUILDING COMPONENT: {name}")
        print("------------------------------")

        if self._active_blueprint is None:
            unreal.log_error("ueGear Manager > Cannot create Control Rig Blueprint, please specify active blueprint.")

        guide_component = self.mg_rig.components.get(name, None)

        if guide_component is None:
            unreal.log_warning(f"Unable to find component, {name}")
            return None

        guide_type = guide_component.comp_type
        guide_name = guide_component.fullname

        # Finds the ueGear Component class that matches the guide data class type.
        ue_comp_classes = components.lookup_mgear_component(guide_type)

        # If component not found, report error and exit early
        if ue_comp_classes is None or not ue_comp_classes:
            unreal.log_error(f"Component not found : {guide_type}")
            return

        ueg_comp = ue_comp_classes[0]()
        ueg_comp.metadata = guide_component  # Could be moved into the init of the ueGear component class
        ueg_comp.name = guide_component.fullname

        self.uegear_components.append(ueg_comp)

        print(ueg_comp)
        print(f"      NAME : {ueg_comp.name}")
        print(f"mGear Comp : {ueg_comp.mgear_component}")
        print(f" Functions : {ueg_comp.functions}")
        print(f"Guide Name : {guide_name}")
        print(f"  metadata :\n {ueg_comp.metadata}")
        print("--------------------")

        bp_controller = self.get_active_controller()

        # Create Function Nodes
        ueg_comp.create_functions(bp_controller)

        # Setup Driven Joint
        bones = get_driven_joints(self, ueg_comp)
        ueg_comp.populate_bones(bones, bp_controller)

        # populate control positions
        ueg_comp.populate_control_transforms(bp_controller)

        ueg_comp.init_input_data(bp_controller)

    def group_components(self):
        """Loops over all components that have been created and generates a comment box and positions them in a
        more human readilbe layout.
        """

        controller = self.get_active_controller()

        for i, ue_comp in enumerate(self.uegear_components):

            pos = unreal.Vector2D(i * 512, 0)

            node_count = 0
            comment_size = 0

            for flow_name in ['construction_functions', 'forward_functions', 'backwards_functions']:
                nodes = ue_comp.nodes[flow_name]

                for n in nodes:
                    # Calculates the size of the node, via extimation method
                    # todo: utilise calculation
                    (w, h) = calculate_node_size(n)
                    controller.set_node_position(n, pos + unreal.Vector2D(40, node_count * 300))
                    controller.set_node_position(ue_comp.comment_node, pos - unreal.Vector2D(5, 50))
                    node_count += 1

            comment_size = unreal.Vector2D(500, node_count * 300)
            # print(f"Comment Size {comment_size}")
            controller.set_node_size(ue_comp.comment_node, comment_size)

            # TODO: Rezise comment to encapsulate the entirety of control rig functions
            # TODO: Query the nodes pins and pin names to try and estimate the possible size of the node, then use that to drive the layout.

            # print("GROUP COMPONENTS")
            for node in ue_comp.get_misc_functions():
                (w, h) = calculate_node_size(node)
                # print(w, h)

                controller.set_node_position(node, pos + unreal.Vector2D(40, 450))

        # for i, ue_comp in enumerate(self.uegear_components):
        #     ue_comp.comment_node

    def build_components(self, ignore_component_names: list = None, ignore_component_types: list = None):
        """Builds all components

        ignore_component_names : list(str) - list of names that will be ignored if the name of the component matches
        ignore_component_type : list(str) - list of types that will not be build, if found component matches

        # todo: implement the ignore functionality
        """

        for comp in self.mg_rig.components.values():
            self.build_component(comp.fullname)

    def populate_parents(self):
        """
        Assigns all the ueGear components parent child relationships.
        It does this by searching for the associated component by name.
        """
        print("---------------------------------")
        print(" Finding Parent Associations")
        print("---------------------------------")

        # Find the world component if it exists
        world_component = self.get_uegear_world_component()

        for comp in self.uegear_components:
            # Ignore world control
            if comp.metadata.comp_type == "world_ctrl":
                continue
            # Ignore root component
            if world_component == comp:
                continue

            if comp.metadata.parent_fullname:
                parent_comp_name = comp.metadata.parent_fullname

                print(f" {comp.name} > Finding parent component: {parent_comp_name}")

                # parent_comp = self.mg_rig.components.get(parent_comp_name, None)
                parent_component = self.get_uegear_component(parent_comp_name)
                if parent_component is None:
                    print(f"    Could not find parent component > {parent_comp_name}")
                    continue

                print(f"      > Found parent component: {parent_comp_name}")
                comp.set_parent(parent_component)

            elif comp.metadata.parent_fullname is None and world_component:
                # Component has no parent specified, and a World Component exists
                # Set the World Component as the parent
                print(f" {comp.name} > Has no parent, World Component Exists")
                comp.set_parent(world_component)

    def connect_execution(self):
        """Connects the individual functions Execution port, in order of parent hierarchy"""

        keys = ['construction_functions',
                'forward_functions',
                'backwards_functions']

        bp_controller = self.get_active_controller()

        for func_key in keys:

            for comp in self.uegear_components:

                parent_nodes = self._find_parent_node_function(comp, func_key)
                comp_nodes = comp.nodes[func_key]

                if len(comp_nodes) == 0:
                    continue

                # check parent node and comp node should always only be one node
                if len(comp_nodes) > 1:
                    unreal.log_error(f"There should not be more then one node per a function > {comp.name}")

                p_func = parent_nodes.get_name()
                c_func = comp_nodes[0].get_name()

                # Check if parent node, has already been connected, else branch off

                execute_pin = parent_nodes.find_pin("ExecuteContext")
                target_pins = execute_pin.get_linked_target_pins()

                if len(target_pins) == 0:
                    print("Pin not connected, setting up basic connection")
                    bp_controller.add_link(f'{p_func}.ExecuteContext',
                                           f'{c_func}.ExecuteContext')
                else:
                    # Checks if the pin belongs to a branch node, if not creates a branch node.

                    first_driven_node = target_pins[0].get_node()
                    is_sequence = str(first_driven_node.get_node_title()) == "Sequence"

                    if is_sequence:
                        print("Sequence Node, insert new pin and connect")

                        source_node_name = p_func
                        new_connection_node_name = c_func
                        seq_node_name = f'{source_node_name}_RigVMFunction_Sequence'

                        # Generate next available plug on the Sequence Node
                        new_pin = bp_controller.add_aggregate_pin(seq_node_name, '', '')

                        bp_controller.add_link(new_pin,
                                               f'{new_connection_node_name}.ExecuteContext')

                    else:
                        print("Creating Sequence Node for execution")

                        source_node_name = p_func
                        connected_node_name = first_driven_node.get_name()
                        new_connection_node_name = c_func
                        seq_node_name = f'{source_node_name}_RigVMFunction_Sequence'

                        # Create Sequence Node

                        bp_controller.add_unit_node_from_struct_path(
                            '/Script/RigVM.RigVMFunction_Sequence',
                            'Execute',
                            unreal.Vector2D(1125.814540, 650.259969),
                            seq_node_name)

                        # Connect Parent/Source node to the sequence node

                        bp_controller.add_link(f'{source_node_name}.ExecuteContext',
                                               f'{seq_node_name}.ExecuteContext')

                        # Connect Sequence node to the nodes that were connected to the Parent node, and the new
                        # node that will be connected.
                        bp_controller.add_link(f'{seq_node_name}.A',
                                               f'{connected_node_name}.ExecuteContext')
                        bp_controller.add_link(f'{seq_node_name}.B',
                                               f'{new_connection_node_name}.ExecuteContext')

    def _find_parent_node_function(self, component, function_name: str):
        """Recursively looks at the function, then if one does not exist looks for
        the next one in the parent/child hierarchy

        function_name : is the name of the evaluation function, forward, backwards, construction.
        """

        solve = {'construction_functions': self.get_construction_node(),
                 'forward_functions': self.get_forward_node(),
                 'backwards_functions': self.get_backwards_node()
                 }

        parent_comp = component.parent_node

        if parent_comp is None:
            return solve[function_name]

        comp_nodes = parent_comp.nodes[function_name]

        if len(comp_nodes) > 1:
            unreal.log_error(f"There should not be more then one node per a function > {parent_comp.name}")

        if len(comp_nodes) == 0:
            return self._find_parent_node_function(parent_comp, function_name)

        return comp_nodes[0]

    def pin_exists(self, function: unreal.RigVMNode, pin_name: str, input_pin: bool = True) -> bool:
        """Checks if a pin exists as in input our output
        function
        """
        for pin in function.get_pins():
            name = pin.get_display_name()

            if name != pin_name:
                continue

            pin_direction = pin.get_direction()
            if pin_direction == unreal.RigVMPinDirection.INPUT and input_pin:
                return True
            elif pin_direction == unreal.RigVMPinDirection.OUTPUT and not input_pin:
                return True
        return False

    def connect_construction_functions(self):
        """Connects all the construction functions in control rig"""
        construction_key = 'construction_functions'

        bp_controller = self.get_active_controller()

        # Find the world component if it exists
        root_comp = self.get_uegear_world_component()

        for comp in self.uegear_components:

            # Ignore world control
            if comp.metadata.comp_type == "world_ctl":
                continue
            # Ignore root component
            if root_comp == comp:
                continue

            parent_comp_name = comp.metadata.parent_fullname
            parent_pin_name = comp.metadata.parent_localname

            print(f" -- {comp.name} --")

            if comp.parent_node is None:
                print(f"  Parent Node does not exist in graph: {parent_comp_name}")
                continue

            print(f"  parent: {parent_comp_name}")
            print(f"  parent port: {parent_pin_name}")
            print(f"  Relationship Parent: {comp.parent_node.name}")

            if comp.metadata.parent_fullname is None and comp.parent_node.name == "world_ctl":
                # Defaulting to the world control, the output pin is "root"
                parent_pin_name = "root"

                print("    Connect to World Control")
                print(f"      Parent Pin: {parent_pin_name}")

                parent_comp = comp.parent_node

                comp_functions = comp.nodes[construction_key]
                parent_functions = parent_comp.nodes[construction_key]

                # If the component or parent has no functions then skip the function
                # TODO: This should walk up the ueGear node parent relationship to see what is available to connect to
                if len(comp_functions) == 0 or len(parent_functions) == 0:
                    continue

                comp_function = comp_functions[0]
                parent_function = parent_functions[0]

                # Connects the parent function node to the chile function node..
                p_func_name = parent_function.get_name()
                c_func_name = comp_function.get_name()

                bp_controller.add_link(f"{p_func_name}.{parent_pin_name}",
                                       f"{c_func_name}.parent")

            elif comp.metadata.parent_fullname == comp.parent_node.name:
                print("  Connect via relationships/Association")
                print(f"      Parent Pin: {parent_pin_name}")

                parent_comp = comp.parent_node

                comp_functions = comp.nodes[construction_key]
                parent_functions = parent_comp.nodes[construction_key]

                # If the component or parent has no functions then skip the function
                # TODO: This should walk up the ueGear node parent relationship to see what is available to connect to
                if len(comp_functions) == 0 or len(parent_functions) == 0:
                    continue

                comp_function = comp_functions[0]
                parent_function = parent_functions[0]

                # Connects the parent function node to the chile function node..
                p_func_name = parent_function.get_name()
                c_func_name = comp_function.get_name()

                # Function that returns the correct pin from the name of the parent_pin_name
                # If no pin is found then we fall back to specified parent mGear name.
                pin = parent_comp.get_associated_parent_output(parent_pin_name, bp_controller)

                if pin:
                    print(f"Associated Parent Pin : {pin}")
                    print(f"{pin} > {c_func_name}.parent ")

                    bp_controller.add_link(pin,
                                           f"{c_func_name}.parent")
                else:
                    print(f"{p_func_name}.{parent_pin_name} > {c_func_name}.parent ")

                    bp_controller.add_link(f"{p_func_name}.{parent_pin_name}",
                                           f"{c_func_name}.parent")

            else:
                unreal.log_error(f"Invalid relationship data found: {comp.name}")

    def connect_components(self):
        """Connects all the built components"""

        self.connect_execution()

        print("---------------------------------")
        print("     Connecting Components       ")
        print("---------------------------------")

        self.connect_construction_functions()

        return

        bp_controller = self.get_active_controller()

        # Find the world component if it exists
        root_comp = self.get_uegear_world_component()

        for comp in self.uegear_components:

            # Ignore world control
            if comp.metadata.comp_type == "world_ctl":
                continue
            # Ignore root component
            if root_comp == comp:
                continue

            print(f" -- {comp.name} --")

            print(f"  parent: {comp.metadata.parent_fullname}")
            print(f"  parent port: {comp.metadata.parent_localname}")
            print(f"  Relationship Parent: {comp.parent_node.name}")

            if comp.metadata.parent_fullname is None and comp.parent_node.name == "world_ctl":
                print("   Connect to World Control")

                keys = ['construction_functions',
                        'forward_functions',
                        'backwards_functions']

                parent_comp = comp.parent_node

                for evaluation_key in keys:
                    comp_functions = comp.nodes[evaluation_key]
                    parent_functions = parent_comp.nodes[evaluation_key]

                    # If the component or parent has no functions then skip the function
                    # TODO: This should walk up the ueGear node parent relationship to see what is available to connect to
                    if len(comp_functions) == 0 or len(parent_functions) == 0:
                        continue

                    comp_function = comp_functions[0]
                    parent_function = parent_functions[0]

                    print(f"   Function Name: {comp_function}")
                    # print(comp_function.get_pins())  # Gets all the pins that are available on the function
                    for pin in comp_function.get_pins():
                        pin_name = pin.get_display_name()
                        pin_direction = pin.get_direction()
                        print(f"      {pin_name} : {pin_direction}")

                    print(parent_function)

                    # Connects the parent function node to the chile function node..

                    # This implementation is assumin to much, needs to be more generic
                    p_func_name = parent_function.get_name()
                    c_func_name = comp_function.get_name()

                    bp_controller.add_link(f"{p_func_name}.root",
                                           f"{c_func_name}.parent")


            elif comp.metadata.parent_fullname == comp.parent_node.name:
                print("  Connect via relationships/Association")
            else:
                unreal.log_error(f"Invalid relationship data found: {comp.name}")

        # loop over components
        # if world exists then it is the master root
        # if no world exists then we might have to seach for parents and see what is available

    def get_uegear_world_component(self) -> components.base_component.UEComponent:
        for comp in self.uegear_components:
            if comp.metadata.comp_type == "world_ctrl":
                return comp

    def get_uegear_component(self, name) -> components.base_component.UEComponent:
        """Find the ueGear component that has been created.
        If the component cannot be found it means that it has not been generated yet.

        :param str name: The name of the ueGear component you wish to find.
        :return: The UEComponent that exists with the matching name.
        :rtype: components.base_component.UEComponent or None
        """
        for ue_component in self.uegear_components:
            if ue_component.name == name:
                return ue_component
        return None

    # SUB MODULE - Control Rig Interface. -------------
    #   This may be abstracting away to much

    def get_node(self, node_name: str,
                 create_if_missing: bool = False, function_path: str = None,
                 function_name: str = None) -> Optional[unreal.RigVMNode]:
        """
        Gets a node by name in the current graph that is active in the Manager.

        :param str node_name: Name of the node that is to be retrieved.
        :param bool create_if_missing: If the node does not exist then create it
        :param str function_path: Path to the function library that contains the function to be created.
        :param str function_name: Name of the function node that will be created.
        :return: Node that is found or created, else None.
        :rtype: unreal.RigVMNode or None
        """
        graph = self.get_graph()

        if graph is None:
            unreal.log_error("No graph object found in manager, please make sure an active blueprint is set.")
            return None

        node = graph.find_node_by_name(node_name)

        if node is None and create_if_missing and function_path and function_name:
            node = self.create_node()

        return node

    def create_node(self):
        raise NotImplementedError

    def select_nodes(self):
        raise NotImplementedError

    # ---------------------------------------

    def create_control_rig(self, cr_path: str, cr_name: str, skm_package_path: str, set_default=True):
        """Generates a new Control Rig Blueprint

        NOTE: This method requires a Skeleton Mesh to generate the Control Rig.

        By default, this will fail if a control rig already exists at the location.
        The newly created control rig will be set to the "Active Control Rig"

        cr_name:str = Name of the control rig file
        cr_path:str = Package Path to the location where the new cr will be generated.
        skeleton_path = Path to the Skeleton Mesh object that will be used to generate the control rig
        """

        package_path = unreal.Paths.combine([cr_path, cr_name])
        if unreal.Paths.file_exists(package_path):
            unreal.log_error("Control Rig File already exists")
            return None

        if not ue_assets.asset_exists(skm_package_path):
            unreal.log_error(f"Skeleton Mesh not found - {skm_package_path}")
            return None

        # Generates Control Rig Blueprint in place
        skm_obj = ue_assets.get_asset_object(skm_package_path)
        blueprint = self._factory.create_control_rig_from_skeletal_mesh_or_skeleton(skm_obj)

        if blueprint is None:
            unreal.log_error(f"Failed to create Control Rig BP - {package_path}")
            return None

        # Move blueprint to correct location
        moved_success = unreal.EditorAssetLibrary.rename_asset(blueprint.get_path_name(), package_path)
        if not moved_success:
            unreal.log_error(f"Failed to rename Control Rig BP - {blueprint.get_path_name()}")
            # Deletes invalid CRBP which is now stale, and should not exist in this location.
            unreal.EditorAssetLibrary.delete_asset(blueprint.get_path_name())
            return None

        if set_default:
            self.set_active_blueprint(blueprint)

        # Create Forwards, Backwards and Construction Solve Node
        self.create_solves()

        return blueprint

    def create_controlrig_by_location(self, package_path, set_default=True):
        """
        Creates the control rig at the specific location, and set the manager to use the newly created control rig.

        package_path: path to the newly created control rig blue print.
        set_default: If disabled, the manager will not automatically set the active CR BP to the newly created CR BP.
        """
        factory = unreal.ControlRigBlueprintFactory()
        rig = factory.create_new_control_rig_asset(desired_package_path=package_path)

        if set_default:
            self._active_blueprint = rig

        return rig

    def create_controlrig_by_mesh(self, mesh_package_path):
        """Generates the control rig using the mesh package path"""
        # load a skeletal mesh
        mesh = unreal.load_object(name=mesh_package_path, outer=None)
        # create a control rig for the mesh
        factory = unreal.ControlRigBlueprintFactory
        rig = factory.create_control_rig_from_skeletal_mesh_or_skeleton(selected_object=mesh)
        return rig

    def set_active_control_rig(self, path=None):
        """
        Sets the active control rig to be the selected control rig blue print in the Content Browser.
        """

        if path:
            loaded_control_rig = unreal.load_object(name=path, outer=None)
            self.set_active_blueprint(loaded_control_rig)

            if loaded_control_rig == None:
                print(f"Warning: No Control Rig Blue Print found at {path}")
                return None

            return loaded_control_rig

        selected_blueprints = ue_assets.selected_assets(unreal.ControlRigBlueprint)

        self._set_control_blueprint(selected_blueprints)

        return self._active_blueprint

    def load_rig(self, mgear_rig: mgear.mgRig):
        """
        Loads the mgear rig object into the manager, so the manager can generate the control rig and its components.
        """
        self.mg_rig = mgear_rig

    def get_graph(self) -> unreal.RigVMGraph:
        """
        Gets the graph of the current loaded control rig

        https://docs.unrealengine.com/5.3/en-US/PythonAPI/class/RigVMGraph.html#unreal.RigVMGraph

        """
        rig_vm_controller = self._active_blueprint.get_controller_by_name('RigVMModel')

        if rig_vm_controller is None:
            # If Controller cannot be found, create a new controller
            rig_vm_controller = self._active_blueprint.get_or_create_controller()

        active_cr_graph = rig_vm_controller.get_graph()
        return active_cr_graph

    def get_active_controller(self, name: str = "RigVMModel") -> unreal.RigVMController:
        """
        Returns the active control rig blue print controller.

        name:str = The name of the blueprint controller.
        """
        rig_vm_controller = self._active_blueprint.get_controller_by_name(name)

        # If Controller cannot be found, create a new controller
        if rig_vm_controller is None:
            rig_vm_controller = self._active_blueprint.get_or_create_controller()

        return rig_vm_controller

    def get_selected_nodes(self) -> list[str]:
        if self._active_blueprint is None:
            print("Error, please set the sctive Control Rig blueprint.")
        graph = self.get_graph()
        return graph.get_select_nodes()

    def create_solves(self):
        """
        Creates the Execution Nodes, for the following paths, as they are not created by default.
        - Forward
        - Backwards (Inverse)
        - Construction
        """

        rig_vm_controller = self.get_active_controller()

        if rig_vm_controller is None:
            unreal.log_error("No Control Rig Controller found, please open up a control Rig UI and try again")
            return

        position_offset = unreal.Vector2D(-300, 0)

        # Forward
        if not self.get_node("BeginExecution") and not self.get_node("RigUnit_BeginExecution"):
            rig_vm_controller.add_unit_node_from_struct_path(
                '/Script/ControlRig.RigUnit_BeginExecution',
                'Execute',
                position_offset + unreal.Vector2D(0, 512),
                'BeginExecution')

        # Backward
        if not self.get_node("InverseExecution"):
            rig_vm_controller.add_unit_node_from_struct_path(
                '/Script/ControlRig.RigUnit_InverseExecution',
                'Execute',
                position_offset + unreal.Vector2D(0, 1024),
                'InverseExecution')

        # Construction
        if not self.get_node("PrepareForExecution"):
            rig_vm_controller.add_unit_node_from_struct_path(
                '/Script/ControlRig.RigUnit_PrepareForExecution',
                'Execute',
                position_offset,
                'PrepareForExecution')

    def get_forward_node(self) -> unreal.RigVMNode:
        """Gets the Forward Execution Node"""
        return self.get_node('BeginExecution')

    def get_backwards_node(self) -> unreal.RigVMNode:
        """Gets the Backwards Execution Node"""
        return self.get_node('InverseExecution')

    def get_construction_node(self) -> unreal.RigVMNode:
        """Gets the Construction Execution Node"""
        return self.get_node('PrepareForExecution')


def get_forward_solve(manager: UEGearManager):
    controller = manager.get_active_controller()
    controller.set_node_selection(['RigUnit_BeginExecution'])
    # manager.active_control_rig.get_controller_by_name('RigVMModel').get
    raise NotImplementedError


def get_driven_joints(manager: UEGearManager, ueg_component: components.base_component.UEComponent):
    """
    Finds all the bones is they exist that populate the ueGear metadata joint property.
    """
    joint_names = ueg_component.metadata.joints

    if joint_names is None:
        return

    rig_hierarchy = manager.active_control_rig.hierarchy

    found_bones = []

    for name in joint_names:
        rek = unreal.RigElementKey()
        rek.name = name
        rek.type = unreal.RigElementType.BONE
        bone = rig_hierarchy.find_bone(rek)
        if bone:
            found_bones.append(bone)

    ueg_component.bones = found_bones

    return found_bones


def create_array_node(node_name: str,
                      controller: unreal.RigVMController,
                      pos_x: float = 700,
                      pos_y: float = 700) -> str:
    """Generates a make array node"""

    array_node_name = f"{node_name}_arrayNode"

    found_node = controller.get_graph().find_node_by_name(array_node_name)

    if not found_node:
        controller.add_template_node(
            'DISPATCH_RigVMDispatch_ArrayMake(in Values,out Array)', unreal.Vector2D(pos_x, pos_y),
            array_node_name)

    return array_node_name


def array_node_has_pins(node_name: str,
                        controller: unreal.RigVMController,
                        minimum_pins: int = 1):
    """
    Checks if the array node contains any pins.

    As different nodes get generated with different default pin values, we have a minimum cound to query against.
    """
    # Checks if node exists, else creates node
    found_node = controller.get_graph().find_node_by_name(node_name)

    # Do pins already exist on the node, if not then we will have to create them. Else we dont
    existing_pins = found_node.get_pins()[0].get_sub_pins()

    if len(existing_pins) > minimum_pins:
        return True

    return False


def calculate_node_size(node: unreal.RigVMUnitNode):
    """
    Calculates the node size by checking the amount of input and output pins,
    as well as the names of the pins.
    """
    # todo: calculate the size of  node by the amount of pins and size of the name
    input_pins = []
    outpu_pins = []
    longest_input_name = ""
    longest_output_name = ""
    node_name = node.get_name()

    for pin in node.get_pins():

        pin_name = str(pin.get_display_name())

        if pin.get_direction() == unreal.RigVMPinDirection.INPUT:
            input_pins.append(pin)
            if len(pin_name) > len(longest_input_name):
                longest_input_name = pin_name

        if pin.get_direction() == unreal.RigVMPinDirection.OUTPUT:
            outpu_pins.append(pin)
            if len(pin_name) > len(longest_output_name):
                longest_output_name = pin_name

    # print(f"{len(input_pins)} > {node_name} > {len(outpu_pins)}")
    # print(f"{len(longest_input_name)} > {node_name} > {len(longest_output_name)}")

    offset = 10
    char_width = 2
    char_height = 7

    width = len(longest_input_name) * char_width + offset + \
            len(node_name) * char_width + offset + \
            len(longest_output_name) * char_width

    height = (len(input_pins) + 1) * char_height + \
             1 * char_height + \
             (len(outpu_pins) + 1) * char_height

    return (width, height)


def create_control_rig(rig_name: str, skeleton_package: str, output_path: str, gnx_path: str):
    """
    Generates the control rig from the available components
    """
    TEST_BUILD_JSON = gnx_path
    TEST_CONTROLRIG_PATH = output_path
    TEST_CONTROLRIG_NAME = rig_name
    TEST_CONTROLRIG_SKM = skeleton_package

    print("-------------------------------------------")
    print(" Creating Control Rig from mGear .gnx file")
    print(f"   {rig_name}")
    print(f"   {skeleton_package}")
    print(f"   {output_path}")
    print(f"   {gnx_path}")
    print("-------------------------------------------")

    # Converts teh json data into a class based structure, filters out non-required metadata.
    mgear_rig = mgear.convert_json_to_mg_rig(TEST_BUILD_JSON)

    gear_manager = UEGearManager()
    gear_manager.load_rig(mgear_rig)

    # Creates an asset path
    cr_path = TEST_CONTROLRIG_PATH + "/" + TEST_CONTROLRIG_NAME
    # Control Rig Blueprint
    cr_bp = ue_assets.get_asset_object(cr_path)

    print(f" --  Could not find Control Rig Blueprint > {cr_bp}")

    if cr_bp is None:
        print(f" --  Creating Control Rig Blueprint > {cr_path}")
        cr_bp = gear_manager.create_control_rig(TEST_CONTROLRIG_PATH, TEST_CONTROLRIG_NAME, TEST_CONTROLRIG_SKM)
        if cr_bp is None:
            unreal.log_error("No Control Rig Graph found..")
            return

    # ------ Causes Unreal to Crash -------
    # aes = unreal.AssetEditorSubsystem()
    # aes.open_editor_for_assets([cr_bp])
    # -------------------------------------

    gear_manager.set_active_blueprint(cr_bp)

    # todo: commented out as the folder should only be deleted if it is empty.
    # if cr_bp is None:
    #     unreal.log_error("Test: test_create_fk_control - Failed : Could not create control rig blue print")
    #     unreal.EditorAssetLibrary.delete_directory("/Game/TEST/")
    #     return None

    # - At this point we now have The Manager, with an empty Control Rig BP
    # Builds the world control if it has been enabled in the Main Settings
    gear_manager.build_world_control()
    gear_manager.build_components()

    # - At this point there are many components created, but not connected to one another
    gear_manager.populate_parents()
    gear_manager.connect_components()
    gear_manager.group_components()

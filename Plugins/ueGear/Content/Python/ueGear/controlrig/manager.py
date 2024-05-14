import unreal

from ueGear import assets as ue_assets
from ueGear.controlrig import mgear
from ueGear.controlrig import components


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

        ueg_comp = components.test_fk.fkComponent()
        ueg_comp.metadata = placeholder_component
        ueg_comp.name = name

        self.uegear_components.append(ueg_comp)

        ueg_comp.create_functions(self.get_active_controller())

    def build_component(self, name, ignore_parent=True):
        """Create an individual component from the mgear scene desciptor file.

        """

        if self._active_blueprint is None:
            unreal.log_error("ueGear Manager > Cannot create Control Rig Blueprint, please specify active blueprint.")

        self.create_solves()

        guide_component = self.mg_rig.components.get(name, None)

        if guide_component is None:
            unreal.log_warning(f"Unable to find component, {name}")
            return None

        guide_type = guide_component.comp_type
        guide_name = guide_component.fullname

        # Finds the ueGear Component class that matches the guide data class type.
        ue_comp_classes = components.lookup_mgear_component(guide_type)
        ueg_comp = ue_comp_classes[0]()
        ueg_comp.metadata = guide_component  # Could be moved into the init of the ueGear component class

        ueg_comp.name = guide_component.fullname

        self.uegear_components.append(ueg_comp)

        print("------------------------------")
        print(f" BUILDING COMPONENT: {name}")
        print("------------------------------")
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

        # Parent Setup
        # TODO: WORKING HERE!!! trying to figure out the best way to handle connectivity between components
        if ueg_comp.metadata.parent_fullname:
            parent_comp_name = ueg_comp.metadata.parent_fullname

            print("---------------------------------")
            print(" Initialising Parent Connections")
            print("---------------------------------")
            print(f" Finding parent component: {parent_comp_name}")

            # parent_comp = self.mg_rig.components.get(parent_comp_name, None)
            parent_component = self.get_uegear_component(parent_comp_name)
            if parent_component is None:
                print(f"    Could not find parent component > {parent_comp_name}")
                return

            # print(" Parent Component Found")
            # ueg_comp.set_parent(parent_component)
            # ueg_comp.parent_node

            return

            # !!! This cannot be assumed as they may be multiple functions in a node classification
            parent_node = parent_component.nodes["construction_functions"][0]
            child_node = ueg_comp.nodes["construction_functions"][0]

            print(parent_node)
            parent_construct_func_name = parent_node.get_name()
            child_construct_func_name = child_node.get_name()
            print(parent_construct_func_name)
            print(child_construct_func_name)

            bp_controller.add_link(f'{parent_construct_func_name}.ExecuteContext',
                                   f'{child_construct_func_name}.ExecuteContext')

            if len(parent_component.nodes["forward_functions"]) > 0:
                parent_node = parent_component.nodes["forward_functions"][0]
                child_node = ueg_comp.nodes["forward_functions"][0]

                print(parent_node)
                parent_construct_func_name = parent_node.get_name()
                child_construct_func_name = child_node.get_name()
                print(parent_construct_func_name)
                print(child_construct_func_name)

                bp_controller.add_link(f'{parent_construct_func_name}.ExecuteContext',
                                       f'{child_construct_func_name}.ExecuteContext')


    # TODO: WORKING ON CONNECTIONS
    def connect_components(self):
        """Connects all the built components"""

        print("---------------------------------")
        print("     Connecting Components       ")
        print("---------------------------------")

        # Find the world component if it exists
        root_comp = self.get_uegear_world_component()

        # Find new root component
#        if root_comp is None:
#            for comp in self.uegear_components:

                # want a way to easily access the input / output plugs for the component
                #comp.metadata.input
                #comp.metadata.output

        for comp in self.uegear_components:

            # ignore world control
            if comp.metadata.comp_type == "world_ctrl":
                continue
            if root_comp == comp:
                continue

            print(comp.metadata.parent_fullname)
            print(comp.metadata.parent_localname)

            # Component has no root parent, then it is a child of the world_ctrl or should be the root.
            if comp.metadata.parent_fullname is None:
                root_comp.add_child(comp)




            parent_component = self.get_uegear_component(comp.metadata.parent_fullname)
            print(parent_component)


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
                 function_name: str = None) -> unreal.RigVMNode:
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
        print("-----------------------------------------------------------")
        print("GET GRAPH")

        rig_vm_controller = self._active_blueprint.get_controller_by_name('RigVMModel')

        if rig_vm_controller is None:
            # If Controller cannot be found, create a new controller
            rig_vm_controller = self._active_blueprint.get_or_create_controller()

        active_cr_graph = rig_vm_controller.get_graph()

        print("-----------------------------------------------------------")

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
        - Backwards / Inverse
        - Construction
        """

        rig_vm_controller = self.get_active_controller()

        # Forward
        if not self.get_node("BeginExecution"):
            rig_vm_controller.add_unit_node_from_struct_path(
                '/Script/ControlRig.RigUnit_BeginExecution',
                'Execute',
                unreal.Vector2D(0.0, 0.0),
                'BeginExecution')

        # Backward
        if not self.get_node("InverseExecution"):
            rig_vm_controller.add_unit_node_from_struct_path(
                '/Script/ControlRig.RigUnit_InverseExecution',
                'Execute',
                unreal.Vector2D(0.0, 0.0),
                'InverseExecution')

        # Construction
        if not self.get_node("PrepareForExecution"):
            rig_vm_controller.add_unit_node_from_struct_path(
                '/Script/ControlRig.RigUnit_PrepareForExecution',
                'Execute',
                unreal.Vector2D(0.0, 0.0),
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

    return found_bones

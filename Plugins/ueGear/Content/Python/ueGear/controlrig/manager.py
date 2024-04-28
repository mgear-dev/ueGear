import unreal

from ueGear import assets as ue_assets
from ueGear.controlrig import mComponents
from ueGear.controlrig import components

class UEGearManager:
    _factory: unreal.ControlRigBlueprintFactory = None
    """Unreals Control Rig Blue Print Factory. This performs all the alterations to the Control Rig"""

    _cr_blueprints: list[unreal.ControlRigBlueprint] = []
    """List of all available blueprints"""

    _active_blueprint: unreal.ControlRigBlueprint = None
    """The Active Blueprint is the current blueprint that will be modified by the UE Gear Manager"""

    _ue_gear_standard_library = None

    mg_rig = None
    """The mGear rig description, that is used to generate the ueGear 'Control Rig'"""

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

    def build_component(self, name="global_C0", ignore_parent=True):
        """Create an individual component from the mgear scene desciptor file.

        """

        if self._active_blueprint is None:
            unreal.log_error("Cannot create Control Rig Blueprint, please specify active blueprint.")

        guide_component = self.mg_rig.components.get(name, None)

        if guide_component is None:
            unreal.log_warning(f"Unable to find component, {name}")
            return None

        print(guide_component)
        guide_type = guide_component.comp_type

        ue_comp_classes = components.lookup_mgear_component(guide_type)
        ueg_comp = ue_comp_classes[0]()
        print(ueg_comp)





    # SUB MODULE - Control Rig Interface. -------------
    #   This may be abstracting away to much

    def create_node(self):
        pass

    def select_node(self, node_name: str):
        pass

    def select_nodes(self):
        pass

    # ---------------------------------------

    def create_control_rig(self, cr_name: str, cr_path: str, skm_package_path: str, set_default=True):
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
            unreal.log_warning("Control Rig File already exists")
            return None

        if not ue_assets.asset_exists(skm_package_path):
            unreal.log_warning(f"Skeleton Mesh not found - {skm_package_path}")
            return None

        # Generates Control Rig Blueprint in place
        skm_obj = ue_assets.get_asset_object(skm_package_path)
        blueprint = self._factory.create_control_rig_from_skeletal_mesh_or_skeleton(skm_obj)

        if blueprint is None:
            unreal.log_warning(f"Failed to create Control Rig BP - {package_path}")
            return None

        # Move blueprint to correct location
        moved_success = unreal.EditorAssetLibrary.rename_asset(blueprint.get_path_name(), package_path)
        if not moved_success:
            unreal.log_warning(f"Failed to rename Control Rig BP - {blueprint.get_path_name()}")
            # Deletes invalid CRBP which is now stale, and should not exist in this location.
            unreal.EditorAssetLibrary.delete_asset(blueprint.get_path_name())
            return None

        if set_default:
            self._active_blueprint = blueprint

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

    def load_rig(self, mgear_rig: mComponents.mgRig):
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
        active_cr_graph = rig_vm_controller.get_graph()
        return active_cr_graph

    def get_selected_nodes(self) -> list[str]:
        if self._active_blueprint is None:
            print("Error, please set the sctive Control Rig blueprint.")
        graph = self.get_graph()
        return graph.get_select_nodes()



mgear_rig = convert_json_to_mg_rig(test_file)
"""
Reads the build file that gets generated from Maya.
"""

manager = ueGearManager()
"""Manager will perform all the interactions with Control Rig API"""

manager.loadRig(mgear_rig)
"""Loads in the mgear rig object"""

# UPDATE COMPONENTS association 

manager.generate.create_new_component(mgear_type="EPIC_neck_03", ueGear_type="EPIC_neck_03")
"""
This will export the selected function nodes from inside of the active control rig blueprint. and update the association `ueGear Component` json file.

As nodes in the CR BP need to exist in ueGearFunctionLibrary, they will need to be moved there manually[or automatically but that will be later].
"""

manager.generate.update_components_functions(ueGear_type="EPIC_neck_03")
"""
Updates the component functions.
"""

# QUERY MAYA MGEAR DATA

manager.associated_components()
"""
Shows a list of all the Compoent types that exist in the rig. The ueGear equivalent, the functions that relate to the ueGear component and and Blueprint variables that will need to be added to the environment.

    mGear          ueGear              Functions                                                                                      Control Rig Variable
EPIC_leg_02   :  EPIC_leg_02  :  gear_EPIC_leg_02_Constructor, gear_EPIC_leg_02_ForwardSolve, gear_EPIC_leg_02_BackwardsSolve       :
EPIC_arm_02   :  EPIC_arm_02  :  gear_EPIC_arm_02_Constructor, gear_EPIC_arm_02_ForwardSolve, gear_EPIC_arm_02_BackwardsSolve       :
EPIC_spine_02 : EPIC_spine_02 :  gear_EPIC_spine_02_Constructor, gear_EPIC_spine_02_ForwardSolve, gear_EPIC_spine_02_BackwardsSolve :
EPIC_neck_02  : EPIC_neck_02  :  gear_EPIC_neck_02_Constructor, gear_EPIC_neck_02_ForwardSolve, gear_EPIC_neck_02_BackwardsSolve    :
"""

# control rig variables are variables that need to be added to the control rig blueprint for the functions to work correctly.

manager.active_control_rig
"""
The Control Rig file that is being modified. This will be updated when a new control rig is generated
"""

manager.skeletal_mesh
"""
The skeletal that is associated with this build, it will be used to generate the Control Rig
"""


# Getting / Assinging the Control Rig File

manager.create_control_rig(package_path="")
"""
Creates a new Control Rig Blue Print, at a specific location. and sets it as the active control rig
"""

manager.create_control_rig(mesh_package_path="", package_path="")
"""
Creates a new Control Rig Blue Print, at a specific package_path location, if it has been provided, and uses the skeleton, or skeletal mesh as its base.
If no package path is provided, it will fall back onto the location of the mesh_package_path.
If no mesh_package_path is provided then it will fall back to creating a CRBP at the package_path.
If both are left out, then no CRBP will be created.
"""

manager.set_active_control_rig_from_selection()
"""
Uses the current selection to get the control rig that will be used by the manager.
"""

manager.set_active_control_rig()
"""Sets the active control rig to be the selected control rig blue print in the Content Browser."""

manager.set_active_control_rig(path="")
"""Path to the control rigs package"""

# Build Contrl Rig

manager.build()
"""
Build the entire Control Rig, using the skeletal_mesh associated with the `manager`
"""

manager.build(skeletal_mesh="Some_skeletal_mesh_package_path")
"""
Generates a new Control Rig file, for the entire input rig using the specified skeleton. Updates the active_control_rig
"""

manager.build(component_full_name="neck_C0")
"""
Updates the current active control rig file, and buid only the specific component. if the component exists, it will update it
"""

manager.build(uegear_type="EPIC_arm_02")
"""
Build/Rebuild all components that exist of the specific type. In this case it would rebuild the left and right arm
"""

manager.build_component(name="global_C0", ignore_parent=True)
"""
Builds a component that exists in the managers 
"""

# Rig Validation

manager.stale()
"""
Gets all Components which are added on the CR BP, but do not have an association to a component in the mgRig
"""
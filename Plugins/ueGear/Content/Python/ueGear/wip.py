"""This is just a scratch area for simple class and function designs, before being refactored into a proper location."""

import unreal

import ueGear.sequencer as sequencer
import ueGear.sequencer.bindings
import ueGear.assets as assets
import ueGear.commands as ueCommands
import ueGear.mayaio as mayaio
import importlib
importlib.reload(ueCommands)
importlib.reload(sequencer)
importlib.reload(mayaio)
importlib.reload(assets)
# importlib.reload(ueGear.sequencer.bindings)


# Minimum Version Unreal 5.2
# Minimum Maya Version.... As old as we can go

def create_controlrig_by_location(package_path):
    factory = unreal.ControlRigBlueprintFactory()
    rig = factory.create_new_control_rig_asset(desired_package_path = package_path)
    return rig

def create_controlrig_by_mesh(mesh_package_path):
    # load a skeletal mesh
    mesh = unreal.load_object(name = mesh_package_path, outer = None)
    # create a control rig for the mesh
    factory = unreal.ControlRigBlueprintFactory
    rig = factory.create_control_rig_from_skeletal_mesh_or_skeleton(selected_object = mesh)
    return rig

def load_controlrig(package_path):
    rig = unreal.load_object(name = package_path, outer = None)
    return rig

def get_open_controlrig():
    rigs = unreal.ControlRigBlueprint.get_currently_open_rig_blueprints()
    return rigs

unreal.load_module('ControlRigDeveloper')

# Loads a specific control rig blueprint into memory
rig = load_controlrig('/Game/StarterContent/Character/anim_test_001_CtrlRig')
new_rig = create_controlrig_by_location('/Game/StarterContent/Character/empty_control_rig_test')

vm_controller = new_rig.get_controller_by_name('RigVMModel')

# Create For Each Node
vm_controller.add_template_node('DISPATCH_RigVMDispatch_ArrayIterator(in Array,out Element,out Index,out Count,out Ratio)', unreal.Vector2D(-75.366699, -788.375000), 'DISPATCH_RigVMDispatch_ArrayIterator_3')

# Create Construction Event Node
vm_controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_PrepareForExecution', 'Execute', unreal.Vector2D(-381.200012, -600.554932), 'PrepareForExecution')

# Create Forward Solve Event
vm_controller.add_unit_node_from_struct_path('/Script/ControlRig.RigUnit_BeginExecution', 'Execute', unreal.Vector2D(-27.200012, -405.554932), 'BeginExecution')

# Create link between two nodes
vm_controller.add_link('PrepareForExecution.ExecuteContext', 'DISPATCH_RigVMDispatch_ArrayIterator_3.ExecuteContext')

# Adds the foreach node to the selection
vm_controller.set_node_selection(['DISPATCH_RigVMDispatch_ArrayIterator_3'])
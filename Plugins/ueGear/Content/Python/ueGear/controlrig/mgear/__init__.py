import json

import unreal
from .component import mgComponent
from .rig import mgRig

"""
This container handles all the mGear component data that will be used to deserialise the `*.scd` file.
"""

def load_json_file(file_path: str):
    """
    Load a JSON file using the json module.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def _conversion_matrix_space(matrix: unreal.Matrix) -> unreal.Transform:
    """Converts from Maya Y up to Unreals

    matrix - is the matrix that needs to be converted into unreal space

    returns a transform
    """
    conversion_mtx = unreal.Matrix(x_plane= [1, 0,  0, 0],
                                   y_plane= [0, 0, -1, 0],
                                   z_plane= [0, 1,  0, 0],
                                   w_plane= [0, 0,  0, 1]
                                   )


    corrected_mtx = conversion_mtx * matrix * conversion_mtx.get_inverse()
    # update Rotation
    euler = matrix.transform().rotation.euler()
    quat = unreal.Quat()
    # quat.set_from_euler(unreal.Vector(euler.x + 90, euler.y, euler.z))
    quat.set_from_euler(unreal.Vector(euler.x, euler.y, euler.z))
    trans = corrected_mtx.transform()
    trans.rotation = quat

    # Update Position
    pos = trans.translation
    # pos_y = pos.y
    # pos_z = pos.z
    # pos.y = pos_z
    # pos.z = -pos_y
    trans.translation = pos

    return trans

def convert_json_to_mg_rig(build_json_path: str) -> mgRig:
    """
    Converts the mGear build json file into a mgRig object.

    This process filters out all none required data.
    """
    data = load_json_file(build_json_path)

    rig = mgRig()

    # Dumps the entire MainSettings dictionary into the rig.settings
    rig.settings = data["MainSettings"]

    for data_component in data["Components"]:

        component_type = data_component["Type"]
        component_side = data_component["Side"]
        component_name = data_component["Name"]
        component_fullname = data_component["FullName"]
        data_contrat = data_component["DataContracts"]
        joints = data_component["Joints"]
        controls = data_component["Controls"]

        mgear_component = mgComponent()
        mgear_component.name = component_name
        mgear_component.side = component_side
        mgear_component.comp_type = component_type
        mgear_component.fullname = component_fullname
        mgear_component.parent_fullname = data_component['parent_fullName']
        mgear_component.parent_localname = data_component['parent_localName']
        mgear_component.data_contracts = {}
        mgear_component.joint_relatives = data_component['jointRelatives']

        # Stores all the controls associated with this component
        for ctrl in controls:
            if mgear_component.controls is None:
                mgear_component.controls = []
            mgear_component.controls.append(ctrl["Name"])

            # Checks the controls transform data and records it as a Unreal.Transform
            # Convert the maya to world transform

            world_pos = ctrl["WorldPosition"]
            world_rot = ctrl["WorldRotation"]

            ue_trans = unreal.Transform()
            ue_quaternion = unreal.Quat()

            world_pos = [world_pos['x'], world_pos['y'], world_pos['z']] # reordering for orientation change
            ue_quaternion.set_from_euler(world_rot)
            ue_trans.set_editor_property("translation", world_pos)
            ue_trans.set_editor_property("rotation", ue_quaternion)

            # Converts from Maya space to Unreal Space
            maya_mtx = ue_trans.to_matrix()
            ue_trans = _conversion_matrix_space(maya_mtx)

            if mgear_component.control_transforms is None:
                mgear_component.control_transforms = {}

            # mgear_component.control_transforms[ctrl["Name"]] = ue_trans
            mgear_component.control_transforms[ctrl["Name"]] = maya_mtx.transform()

        # Stores all the joints associated with this component
        for jnt in joints:
            if mgear_component.joints is None:
                mgear_component.joints = []
            mgear_component.joints.append(jnt["Name"])

        # Stores all the contracts and their related joints
        for contract_name in data_contrat:
            related_joints = data_component[contract_name]
            mgear_component.data_contracts[contract_name] = related_joints

        rig.add_component(new_component=mgear_component)

    return rig
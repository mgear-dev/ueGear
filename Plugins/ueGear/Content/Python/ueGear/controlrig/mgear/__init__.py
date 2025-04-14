import json

import unreal
from .component import mgComponent
from .rig import mgRig
from .colour import MAYA_LOOKUP

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
        guide_transforms = data_component.get("guideTransforms", None)

        mgear_component = mgComponent()
        mgear_component.name = component_name
        mgear_component.side = component_side
        mgear_component.comp_type = component_type
        mgear_component.fullname = component_fullname
        mgear_component.parent_fullname = data_component['parent_fullName']
        mgear_component.parent_localname = data_component['parent_localName']
        mgear_component.data_contracts = {}
        mgear_component.joint_relatives = data_component['jointRelatives']
        mgear_component.control_relatives = data_component['controlRelatives']
        mgear_component.alias_relatives = data_component['aliasRelatives']
        mgear_component.settings = data_component['Settings']

        # checks if guide transforms exists, as not all components have this attribute.
        if guide_transforms:
            # Converts the numeric list matrix into an Unreal Matrix
            for key, val in guide_transforms.items():
                mtx = unreal.Matrix()

                mtx.x_plane = unreal.Plane(val[0][0], val[0][1], val[0][2], val[0][3])
                mtx.y_plane = unreal.Plane(val[1][0], val[1][1], val[1][2], val[1][3])
                mtx.z_plane = unreal.Plane(val[2][0], val[2][1], val[2][2], val[2][3])
                mtx.w_plane = unreal.Plane(val[3][0], val[3][1], val[3][2], val[3][3])

                guide_transforms[key] = mtx

            mgear_component.guide_transforms = guide_transforms

        # Stores all the controls associated with this component
        for ctrl in controls:
            if mgear_component.controls is None:
                mgear_component.controls = []
                mgear_component.controls_role = {}
                mgear_component.controls_aabb = {}
                mgear_component.controls_colour = {}

            mgear_component.controls.append(ctrl["Name"])
            mgear_component.controls_role[ctrl["Name"]] = ctrl["Role"]

            # Store the RGB Color
            # ::ASSUMPTION:: A control will all have the  same colour
            shape_category = ctrl["Shape"]
            for crv_name in shape_category["curves_names"]:
                crv_color = shape_category[crv_name]["crv_color"]

            if crv_color is None or crv_color == "null":
                # There is an edge case where the colour is null
                mgear_component.controls_colour[ctrl["Name"]] = None
            elif type(crv_color) == type([]):
                # There is an edge case where the colour is stored as an RGB value
                mgear_component.controls_colour[ctrl["Name"]] = crv_color
            else:
                mgear_component.controls_colour[ctrl["Name"]] = MAYA_LOOKUP[crv_color]

            # Calculate control size
            bounding_box_data = _calculate_bounding_box(ctrl)
            mgear_component.controls_aabb[ctrl["Name"]] = bounding_box_data

            # Checks the controls transform data and records it as a Unreal.Transform
            world_pos = ctrl["WorldPosition"]
            world_rot = ctrl["QuaternionWorldRotation"]
            world_pos = [world_pos['x'], world_pos['y'], world_pos['z']]
            ue_quaternion = unreal.Quat(world_rot[0], world_rot[1], world_rot[2], world_rot[3])

            # Setting the transform with a euler instead of quaternion, due to slight difference in how
            # unreal handles them
            world_euler = ctrl["WorldRotation"]
            euler = unreal.Vector(x=world_euler['x'],
                                  y=world_euler['y'],
                                  z=world_euler['z'])
            # ue_quaternion.set_from_euler(euler)

            ue_trans = unreal.Transform()
            ue_trans.set_editor_property("translation", world_pos)
            ue_trans.set_editor_property("rotation", ue_quaternion)

            # Converts from Maya space into Unreal Space
            ue_trans = _convert_maya_matrix(ue_trans.to_matrix())

            if mgear_component.control_transforms is None:
                mgear_component.control_transforms = {}

            mgear_component.control_transforms[ctrl["Name"]] = ue_trans

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


def _calculate_bounding_box(control_data: dict) -> tuple[list, list]:
    """
    Calculates a bounding box around the control, by evaluating the control points.

    This bounding box is used to help scale the control rig's control shape.

    - Shape points are in local space

    The bounding box will be a centered bounding box, storing the offset position
    from the center to the corners. This is an Axis Aligned Bounding Box (AABB)

    :todo: bounding box center needs to be calculated in Maya space, else multiplying it back in unreal causes an issue due to orientation

    """
    min_point, max_point = _calculate_min_max_points(control_data)
    bb_center, bb_offset = _calculate_bb(min_point, max_point)

    bb_center = _calculate_maya_bb_center(control_data)

    return bb_center, bb_offset


def _calculate_maya_bb_center(control_data: dict) -> list:
    """
    The center of the bounding box is required to be in Maya space to make multiplying and conversion easier in
    the control rig build node.
    """
    bb_min = [float('inf')] * 3
    bb_max = [float('-inf')] * 3

    shape_category = control_data["Shape"]
    for crv_name in shape_category["curves_names"]:

        shape_meta_data = shape_category[crv_name]["shapes"]
        shape_data_list = shape_meta_data.values()
        for shape_data in shape_data_list:
            shape_points = shape_data["points"]

            # Loop over all the points and record the largest and smallest positions
            for point in shape_points:
                pos = [round(point[0], 4), round(point[1], 4), round(point[2], 4)]

                # Finds the largest and smallest value, by comparison
                for index in range(len(pos)):
                    bb_min[index] = min(bb_min[index], pos[index])
                    bb_max[index] = max(bb_max[index], pos[index])

    # Calculate the center of the bb in Maya coordinates
    bb_center = []

    for i, ii in zip(bb_min, bb_max):
        center = round((i + ii) / 2, 4)
        bb_center.append(center)

    return bb_center


def _calculate_min_max_points(control_data: dict):
    """
    Finds the minimum and the maximum points for all the points that exist in
    the controls dictionary.
    """
    # Initialise the min and max points to be infinity
    bb_min = [float('inf')] * 3
    bb_max = [float('-inf')] * 3

    shape_category = control_data["Shape"]
    for crv_name in shape_category["curves_names"]:

        shape_meta_data = shape_category[crv_name]["shapes"]
        shape_data_list = shape_meta_data.values()
        for shape_data in shape_data_list:
            shape_points = shape_data["points"]

            # Loop over all the points and record the largest and smallest positions
            for point in shape_points:

                # Converts the Point from maya space into Unreal space, else the bounding box will not align
                # correctly to the object in Unreal
                point_mtx = unreal.Matrix.IDENTITY
                point_mtx.w_plane = point + [1.0]
                # ue_space_trans = _convert_maya_matrix(point_mtx)
                ue_space_trans = _convert_maya_shape_matrix(point_mtx)
                trans = ue_space_trans.translation
                pos = [round(trans.x, 4), round(trans.y, 4), round(trans.z, 4)]

                # Finds the largest and smallest value, by comparison
                for index in range(len(pos)):
                    bb_min[index] = min(bb_min[index], pos[index])
                    bb_max[index] = max(bb_max[index], pos[index])

    return bb_min, bb_max


def _calculate_bb(min, max):
    """
    Calculates the center point of the bounding box, and the distance to the corners

    :param min: smallest value for each axis that exists in the bounding box
    :param max: largest value for each axis that exists in the bounding box
    :return: The center of the bounding box, the length to the corner
    """
    bb_offset = []
    bb_center = []

    for i, ii in zip(min, max):
        center = round((i + ii) / 2, 4)
        offset = ii - center

        bb_offset.append(offset)
        bb_center.append(center)

    # Checks no axis is 0 as unreal 5.3 has an issue that is a shape
    # has an axis of 0 then shape updating does not work.
    for idx, value in enumerate(bb_offset):
        if value < 0.001:
            bb_offset[idx] = 0.01

    return bb_center, bb_offset


def _convert_maya_matrix(maya_mtx: unreal.Matrix) -> unreal.Transform:
    # Reorient Matrix
    # This matrix is used to turn left hand rule into right hand rule
    plane_x = unreal.Plane(x=1, y=0, z=0, w=0)
    plane_y = unreal.Plane(x=0, y=0, z=-1, w=0)
    plane_z = unreal.Plane(x=0, y=1, z=0, w=0)
    plane_w = unreal.Plane(x=0, y=0, z=0, w=1)
    reordered_mtx = unreal.Matrix(plane_x, plane_y, plane_z, plane_w)

    t = unreal.Transform()
    t_qaut = unreal.Quat()
    t_qaut.set_from_euler(unreal.Vector(0, 0, 0))
    t.rotation = t_qaut
    rot_mtx = t.to_matrix()

    plane_x2 = unreal.Plane(x=1, y=0, z=0, w=0)
    plane_y2 = unreal.Plane(x=0, y=1, z=0, w=0)
    plane_z2 = unreal.Plane(x=0, y=0, z=-1, w=0)
    plane_w2 = unreal.Plane(x=0, y=0, z=0, w=1)
    scale_mtx = unreal.Matrix(plane_x2, plane_y2, plane_z2, plane_w2)


    # Calculates the new space by multiplying the reorder matrix and
    # Rotating the new Y rotation by 180
    corrected_space_mtx = maya_mtx * reordered_mtx * rot_mtx * scale_mtx


    corrected_space_trans = corrected_space_mtx.transform()


    # quat_rotation = corrected_space_mtx.to_quat()
    # euler_rotation = quat_rotation.euler()
    # euler_rotation.y = euler_rotation.z + 180
    # quat_rotation.set_from_euler(euler_rotation)
    # corrected_space_trans.rotation = quat_rotation


    return corrected_space_trans

def _convert_maya_shape_matrix(maya_mtx: unreal.Matrix) -> unreal.Transform:
    # Reorient Matrix
    # This matrix is used to turn left hand rule into right hand rule
    plane_x = unreal.Plane(x=1, y=0, z=0, w=0)
    plane_y = unreal.Plane(x=0, y=0, z=1, w=0)
    plane_z = unreal.Plane(x=0, y=1, z=0, w=0)
    plane_w = unreal.Plane(x=0, y=0, z=0, w=1)
    reordered_mtx = unreal.Matrix(plane_x, plane_y, plane_z, plane_w)

    # Calculates the new space by multiplying the reorder matrix and
    # Rotating the new Y rotation by 180
    corrected_space_mtx = maya_mtx * reordered_mtx
    corrected_space_trans = corrected_space_mtx.transform()
    quat_rotation = corrected_space_mtx.to_quat()
    euler_rotation = quat_rotation.euler()
    euler_rotation.y = euler_rotation.y + 180
    quat_rotation.set_from_euler(euler_rotation)
    corrected_space_trans.rotation = quat_rotation

    return corrected_space_trans
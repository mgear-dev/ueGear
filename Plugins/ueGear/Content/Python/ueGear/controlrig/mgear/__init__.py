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


# def _conversion_matrix_space(matrix: unreal.Matrix) -> unreal.Transform:
#     """Converts from Maya Y up to Unreals
#
#     matrix - is the matrix that needs to be converted into unreal space
#
#     returns a transform
#     """
#     conversion_mtx = unreal.Matrix(x_plane=[1, 0, 0, 0],
#                                    y_plane=[0, 0, -1, 0],
#                                    z_plane=[0, 1, 0, 0],
#                                    w_plane=[0, 0, 0, 1]
#                                    )
#
#     corrected_mtx = conversion_mtx * matrix * conversion_mtx.get_inverse()
#     # update Rotation
#     euler = matrix.transform().rotation.euler()
#     quat = unreal.Quat()
#     # quat.set_from_euler(unreal.Vector(euler.x + 90, euler.y, euler.z))
#     quat.set_from_euler(unreal.Vector(euler.x, euler.y, euler.z))
#     trans = corrected_mtx.transform()
#     trans.rotation = quat
#
#     # Update Position
#     pos = trans.translation
#     # pos_y = pos.y
#     # pos_z = pos.z
#     # pos.y = pos_z
#     # pos.z = -pos_y
#     trans.translation = pos
#
#     return trans


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

        # checks if guide transforms exists, as not all components have this attribute.
        if guide_transforms:
            # Converts the numeric list matrix into an Unreal Matrix
            for key, val in guide_transforms.items():
                mtx = unreal.Matrix()

                # mtx.x_plane = unreal.Plane(val[0][0], val[1][0], val[2][0], val[3][0])
                # mtx.y_plane = unreal.Plane(val[0][1], val[1][1], val[2][1], val[3][1])
                # mtx.z_plane = unreal.Plane(val[0][2], val[1][2], val[2][2], val[3][2])
                # mtx.w_plane = unreal.Plane(val[0][3], val[1][3], val[2][3], val[3][3])

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

            mgear_component.controls.append(ctrl["Name"])
            mgear_component.controls_role[ctrl["Name"]] = ctrl["Role"]

            # Calculate control size
            control_size = _calculate_control_size(ctrl)
            mgear_component.controls_aabb[ctrl["Name"]] = control_size

            # Checks the controls transform data and records it as a Unreal.Transform
            world_pos = ctrl["WorldPosition"]
            world_rot = ctrl["QuaternionWorldRotation"]
            world_pos = [world_pos['x'], world_pos['y'], world_pos['z']]
            ue_quaternion = unreal.Quat(world_rot[0], world_rot[1], world_rot[2], world_rot[3])

            ue_trans = unreal.Transform()
            ue_trans.set_editor_property("translation", world_pos)
            ue_trans.set_editor_property("rotation", ue_quaternion)
            maya_mtx = ue_trans.to_matrix()

            if mgear_component.control_transforms is None:
                mgear_component.control_transforms = {}

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


def _calculate_control_size(control_data: dict) -> list[int]:
    """
    Calculates a bounding box around the control, by evaluating the control points.

    This bounding box is used to help scale the control rig's control shape.

    """

    # TODO: Convert the world space points into local space points using a matrix. Then calculate the BB.

    bounding_box = [[0, 0, 0]]
    """The bounding box will be a centered bounding box, storing the offset position 
    from the center to the corners. This is an Axis Aligned Bounding Box (AABB)
    """

    bb_min = None
    bb_max = None

    shape_catergory = control_data["Shape"]
    for crv_name in shape_catergory["curves_names"]:
        shape_meta_data = shape_catergory[crv_name]["shapes"]
        shape_data_list = shape_meta_data.values()
        for shape_data in shape_data_list:
            shape_points = shape_data["points"]

            # Loop over all the points and record the largest and smallest positions
            for point in shape_points:
                # Initialises the min and max if they have not been populated yet
                if bb_min is None and bb_max is None:
                    bb_min = point[:]
                    bb_max = point[:]
                    continue

                bb_min = list(map(min, bb_min, point))
                bb_max = list(map(max, bb_max, point))

    if bb_min and bb_max:
        bounding_box = [(abs(min_i) + abs(max_i))/2 for min_i, max_i in zip(bb_min, bb_max)]

    return bounding_box

import json

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


def convert_json_to_mg_rig(build_json_path: str) -> mgRig:
    """
    Converts the mGear build json file into a mgRig object.

    This process filters out all none required data.
    """
    data = load_json_file(build_json_path)

    rig = mgRig()

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

        # Stores all the controls associated with this component
        for ctrl in controls:
            if mgear_component.controls is None:
                mgear_component.controls = []
            mgear_component.controls.append(ctrl["Name"])

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
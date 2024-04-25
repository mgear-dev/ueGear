import json


"""
This module contains all the mGear component data that will be used to deserialise the `*.scd` file.
"""


class MGComponent:
    """
    Simple Component object that wraps the maya compoent data, for easy access
    """

    fullname:str = ""
    """Components Fullname, this is usually used as the default name"""
    name:str = ""
    """Name of the Component."""
    side:str = ""
    """The side that the component exists on. L(left), R(right) C(center)."""
    comp_type:str = ""
    """The mGear Component Type, that was used in Maya to generate it."""
    data_contracts:dict = None


    # NOTE: it would be great to have input/output plugs stipulated. That way we know exactly what object in another component drives the object in this component

    """Name of the guide component that is the parent of this guide component"""
    parent_fullname: str = None
    """Name of the guide control that drives this guide component"""
    parent_localname: str = None

    def __init__(self) -> None:
        pass

    def __repr__(self) -> str:
        msg = "\n"
        msg += f"|  Full Name : {self.fullname}\n"
        msg += f"|       Name : {self.name}\n"
        msg += f"|       Side : {self.side}\n"
        msg += f"|       Type : {self.comp_type}\n"
        msg += f"|  Contracts : {self.data_contracts}\n"
        msg += f"|  Parent Component : {self.parent_fullname}\n"
        msg += f"|      Attach Point : {self.parent_localname}\n"
        return msg


class mgRig():
    """
    Simple Component object that wraps the mGear Maya Rig
    """
    components: dict[str, MGComponent] = {}

    def __init__(self) -> None:
        pass

    def add_component(self, name:str=None, new_component: MGComponent=None):
        """
        Gets or Sets the specific component.

        If setting the compnent, you can specify the name, or leave it blank and it will default to the new_components name
        """
        if new_component and name:
            self.components[name] = new_component
        elif new_component:
            self.components[new_component.fullname] = new_component

        return self.components.get(name, None)

    def get_component_by_type(self, type_name: str) -> list:
        """
        Gets all components that match the type specified.
        """
        found_components = []
        for comp in self.components.values():
            if comp.comp_type == type_name:
                found_components.append(comp)

        return found_components

    def __repr__(self) -> str:
        msg = ""
        for (name, comp) in self.components.items():
            msg +=  "o------------------\n"
            msg += f"|  Rig's Key    : {name}\n"
            msg += str(comp)
            msg +=  "o - - - - - - - - -\n"
        return msg


def load_json_file(file_path:str):
    """
    Load a JSON file using the json module.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def convert_json_to_mg_rig(build_json_path:str) -> mgRig:
    """
    Converts the mGear build json file into a mgRig object.

    This process filters out all none required data.
    """
    data = load_json_file(build_json_path)

    rig = mgRig()

    for component in data["Components"]:

        component_type = component["Type"]
        component_side = component["Side"]
        component_name = component["Name"]
        component_fullname = component["FullName"]
        data_contrat = component["DataContracts"]

        mgear_component = MGComponent()
        mgear_component.name = component_name
        mgear_component.side = component_side
        mgear_component.comp_type = component_type
        mgear_component.fullname = component_fullname
        mgear_component.parent_fullname = component['parent_fullName']
        mgear_component.parent_localname = component['parent_localName']
        mgear_component.data_contracts = {}

        for contract_name in data_contrat:
            related_joints = component[contract_name]
            mgear_component.data_contracts[contract_name] = related_joints

        rig.add_component(new_component=mgear_component)

    return rig

if __name__ == "__main__":
    TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\repos\ueGear\Plugins\ueGear\Content\Python\ueGear\controlrig\butcher_data.scd"
 #   TEST_BUILD_JSON = r"C:\SIMON_WORK\mGear\ueGear_ControlRig\butcherBuildData_v002.scd"
    mg_guide_data = convert_json_to_mg_rig(TEST_BUILD_JSON)

# Test basic component
cf_lookup_component = {}

from ueGear.controlrig import components
available_components = components.lookup_mgear_component("EPIC_control_01")
print(available_components)

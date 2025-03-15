from ueGear.controlrig.mgear.component import mgComponent

class mgRig():
    """
    Simple Component object that wraps the mGear Maya Rig
    """

    settings = None
    """Dictionary that stores all the 'Main Settings' """

    components: dict[str, mgComponent] = {}
    """Dictionary of all the components with the key being the component name"""

    def __init__(self) -> None:
        self.components = dict()
        self.settings = None

    def add_component(self, name: str = None, new_component: mgComponent = None):
        """
        Gets or Sets the specific component.

        If setting the compnent, you can specify the name, or leave it blank and it will default to the new_components name
        """
        if new_component and name:
            self.components[name] = new_component
        elif new_component:
            self.components[new_component.fullname] = new_component

        return self.components.get(name, None)

    def get_component_by_type(self, type_name: str) -> list[mgComponent]:
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
            msg += "o------------------\n"
            msg += f"|  Rig's Key    : {name}\n"
            msg += str(comp)
            msg += "o - - - - - - - - -\n"
        return msg
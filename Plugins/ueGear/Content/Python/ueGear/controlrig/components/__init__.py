
from types import ModuleType

from ueGear.controlrig.components import base_component, test_fk, test_spine, shoulder, arm, leg

__all__ = [base_component, test_fk, test_spine, shoulder, arm, leg,
           'lookup_mgear_component'
           ]


def lookup_mgear_component(mg_component_name: str) -> list[base_component.UEComponent]:
    """
    Looks up the class components that match the mgear_component name.

    returns a list of components that relate to the mGear component
    """
    matching_components = []

    for comp in __all__:
        if (type(comp) == ModuleType):
            for cls in map(comp.__dict__.get, comp.__all__):
                is_mgear_comp = hasattr(cls, "mgear_component")
                if not is_mgear_comp:
                    continue
                if cls.mgear_component == mg_component_name:
                    matching_components.append(cls)

    return matching_components
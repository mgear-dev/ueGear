import importlib
import pkgutil
import inspect

from types import ModuleType

# from . import *
import ueGear.controlrig.components.base_component

def lookup_mgear_component(mg_component_name: str) -> list[base_component.UEComponent]:
    """
    Looks up the class components that match the mgear_component name.

    returns a list of components that relate to the mGear component
    """
    matching_components = []

    package_name = __name__
    for _, module_name, _ in pkgutil.iter_modules(__path__, package_name + "."):
        module = importlib.import_module(module_name)

        # Makes sure that the imported module is exactly that, a module
        if type(module) == ModuleType:

            # Inspects the module for the classes within it, and checks if the class contains
            # an mgear_component attribute, and if so does it match the name being searched for.
            for name, cls in inspect.getmembers(module, inspect.isclass):

                # for cls in map(module.__dict__.get, module.__all__):
                if not hasattr(cls, "mgear_component"):
                    break
                if cls.mgear_component == mg_component_name:
                    matching_components.append(cls)

    return matching_components


MAYA_COLOURS = {6: [0.0, 0.0, 1.0],
                18: [0.0, 0.25, 1.0]}
"""A look up table for maya index colours"""

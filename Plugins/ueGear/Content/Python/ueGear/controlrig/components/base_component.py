__all__ = ['UEComponent']

class UEComponent(object):
    name: str = ""
    """Name of the ueGear Component"""
    mgear_component: str = ""
    """The mGear Component that this ueGear component relates too"""
    functions: list = []
    """List of Control Rig functions that make up this ueComponent"""
    cr_variables: dict = {}
    """Control Rig Varialbes that will be generated on the control rig Variable list. This is required for some part of the CR to evaluate correctly"""
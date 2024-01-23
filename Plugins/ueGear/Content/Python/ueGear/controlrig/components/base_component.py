class ueComponent():
    name:str = ""
    """Name of the ueGear Component"""
    mgear_component:str = ""
    """The mGear Component that this ueGear component relates too"""
    functions:list = []
    """List of Control Rig functions that make up this ueComponent"""
    cr_variables:dict = {}
    """Varialbes that will be required to be generated on the control rig, for the ueGear functions to evaluate correctly"""
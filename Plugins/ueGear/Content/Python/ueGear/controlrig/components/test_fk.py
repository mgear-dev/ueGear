__all__ = ['fkComponent']

from .base_component import UEComponent

class fkComponent(UEComponent):

    name = "test_FK"
    mgear_component = "EPIC_control_01"
    functions = ['gear_FK_Constructor', 'gear_FK_ForwardSolve']
    cr_variables = {}

    def __init__(self):
        super().__init__()

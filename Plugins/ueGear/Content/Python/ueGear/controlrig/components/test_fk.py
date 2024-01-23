from base_component import ueComponent

class fkComponent(ueComponent):
    def __init__(self) -> None:
        super().__init__()
        name = "test_FK"
        mgear_component = "test_FK"
        functions = ['gear_FK_Constructor', 'gear_FK_ForwardSolve']
        cr_variables = {}
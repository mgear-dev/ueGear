import unreal

from ueGear.controlrig.paths import CONTROL_RIG_FUNCTION_PATH
from ueGear.controlrig.components import base_component, EPIC_control_01, EPIC_leg_01
from ueGear.controlrig.helpers import controls


class Component(EPIC_leg_01.Component):
    name = "test_Leg"
    mgear_component = "EPIC_leg_02"

    def __init__(self):
        super().__init__()


class ManualComponent(EPIC_leg_01.ManualComponent):
    name = "EPIC_leg_02"
    mgear_component = "EPIC_leg_02"

    def __init__(self):
        super().__init__()

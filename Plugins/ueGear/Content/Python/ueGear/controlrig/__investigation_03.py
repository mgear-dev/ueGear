"""
This inbestigation will be using a fake object that would 
represent the guide data and skeleton data of an mGear Component


"""

class Epic_arm_02:
    """
    NOT FOR PRODUCTION

    This is a custom made arm, that should try and encapsulate
    all the required data from the relating mGear Component.

    """

    # Control Placement
    # IDEA: Have all the bones tagged with the controls that generate at there location,
    #       or visa-versa. Then use the json to generate at there position

    fk_controls = [
        "arm_C0_upperarm_jnt",
        "arm_C0_lowerarm_jnt",
        "arm_C0_hand_jnt",
    ]
    """The joints where the master FK controls will generate"""

    tweak_controls = [
        "arm_C0_upperarm_jnt",
        "arm_C0_upperarm_twist_01_jnt", 
        "arm_C0_upperarm_twist_02_jnt",
        "arm_C0_upperarm_twist_03_jnt",
        "arm_C0_lowerarm_jnt",
        "arm_C0_lowerarm_twist_03_jnt",
        "arm_C0_lowerarm_twist_02_jnt",
        "arm_C0_lowerarm_twist_01_jnt",
    ]
    """The joints where the tweak controls will generate"""


    bendy_controls = [["arm_C0_upperarm_jnt", "arm_C0_lowerarm_jnt", 0.5],
                      ["arm_C0_lowerarm_jnt", "arm_C0_hand_jnt", 0.5]]
                      
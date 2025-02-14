import unreal

class CR_Control:
    """
    Control Rig Wrapper
    """

    def __init__(self, name, parent_name=""):
        self.name = name
        self.parent = parent_name

        self.ctrl_type = unreal.RigElementType.CONTROL
        self.rig_key = unreal.RigElementKey(type=self.ctrl_type, name=self.name)

        self.hierarchy_ctrlr = None
        """Stores the Hierarchy controller that is used to modify the skeleton hierarchy"""

        self.colour = [1, 0, 0]

        self.settings = unreal.RigControlSettings()

    def build(self, hierarchy_controller):
        self.hierarchy_ctrlr = hierarchy_controller

        self._setup_default_control_configuration()

        self.rig_key = self.hierarchy_ctrlr.add_control(
            self.name,
            self.parent,
            self.settings,
            unreal.RigHierarchy.make_control_value_from_euler_transform(
                unreal.EulerTransform(
                    location=[0.000000, 0.000000, 0.000000],
                    rotation=[0.000000, -0.000000, 0.000000],
                    scale=[1.000000, 1.000000, 1.000000]
                )
            )
        )

        # The control name generated might be different from the one you input due
        # to collisions with an existing control name
        self.name = self.rig_key.name

        print(self.rig_key)
        print(f"Building: {self.name}")

    def _setup_default_control_configuration(self):
        self.settings.animation_type = unreal.RigControlAnimationType.ANIMATION_CONTROL
        self.settings.control_type = unreal.RigControlType.EULER_TRANSFORM
        self.settings.display_name = 'None'
        self.settings.draw_limits = True
        self.settings.shape_color = unreal.LinearColor(self.colour[0], self.colour[1], self.colour[2], 1.000000)
        self.settings.shape_name = 'Default'
        self.settings.shape_visible = True
        self.settings.is_transient_control = False
        self.settings.limit_enabled = [
            unreal.RigControlLimitEnabled(False, False),
            unreal.RigControlLimitEnabled(False, False),
            unreal.RigControlLimitEnabled(False, False),
            unreal.RigControlLimitEnabled(False, False),
            unreal.RigControlLimitEnabled(False, False),
            unreal.RigControlLimitEnabled(False, False),
            unreal.RigControlLimitEnabled(False, False),
            unreal.RigControlLimitEnabled(False, False),
            unreal.RigControlLimitEnabled(False, False)]

        self.settings.minimum_value = unreal.RigHierarchy.make_control_value_from_euler_transform(
            unreal.EulerTransform(
                location=[0.000000, 0.000000, 0.000000],
                rotation=[0.000000, 0.000000, 0.000000],
                scale=[1.000000, 1.000000, 1.000000]
            )
        )
        self.settings.maximum_value = unreal.RigHierarchy.make_control_value_from_euler_transform(
            unreal.EulerTransform(
                location=[0.000000, 0.000000, 0.000000],
                rotation=[0.000000, 0.000000, 0.000000],
                scale=[1.000000, 1.000000, 1.000000]
            )
        )
        self.settings.primary_axis = unreal.RigControlAxis.X

    def shape_transform(self, pos=None, rotation=None, scale=None):
        if pos is None:
            pos = [0,0,0]
        if rotation is None:
            rotation = [0,0,0]
        if scale is None:
            scale = [1,1,1]

        self.hierarchy_ctrlr.get_hierarchy().set_control_shape_transform(self.rig_key,
                                                         unreal.Transform(location=pos,
                                                                          rotation=rotation,
                                                                          scale=scale),
                                                         True)

    def min(self, pos=None, rotation=None, scale=None):
        if pos is None:
            pos = [0,0,0]
        if rotation is None:
            rotation = [0,0,0]
        if scale is None:
            scale = [1,1,1]
        self.hierarchy_ctrlr.get_hierarchy().set_control_value(self.rig_key,
                                               unreal.RigHierarchy.make_control_value_from_euler_transform(
                                                   unreal.EulerTransform(location=[0.000000, 0.000000, 0.000000],
                                                                         rotation=[0.000000, 0.000000, 0.000000],
                                                                         scale=[1.000000, 1.000000, 1.000000])),
                                               unreal.RigControlValueType.MINIMUM)

    def max(self, pos=None, rotation=None, scale=None):
        if pos is None:
            pos = [0,0,0]
        if rotation is None:
            rotation = [0,0,0]
        if scale is None:
            scale = [1,1,1]
        self.hierarchy_ctrlr.get_hierarchy().set_control_value(self.rig_key,
                                               unreal.RigHierarchy.make_control_value_from_euler_transform(
                                                   unreal.EulerTransform(location=pos,
                                                                         rotation=rotation,
                                                                         scale=scale)),
                                               unreal.RigControlValueType.MAXIMUM)

    def offset(self, pos=None, rotation=None, scale=None):
        if pos is None:
            pos = [0,0,0]
        if rotation is None:
            rotation = [0,0,0]
        if scale is None:
            scale = [1,1,1]

        self.hierarchy_ctrlr.get_hierarchy().set_control_offset_transform(self.rig_key,
                                                          unreal.Transform(location=pos,
                                                                           rotation=rotation,
                                                                           scale=scale),
                                                          True,
                                                          True)

    def transform(self, pos=None, rotation=None, scale=None):
        if pos is None:
            pos = [0,0,0]
        if rotation is None:
            rotation = [0,0,0]
        if scale is None:
            scale = [1,1,1]

        self.hierarchy_ctrlr.get_hierarchy().set_control_value(
            self.rig_key,
            unreal.RigHierarchy.make_control_value_from_euler_transform(
                unreal.EulerTransform(
                    location=pos,
                    rotation=rotation,
                    scale=scale
                )
            ),
            unreal.RigControlValueType.CURRENT
        )
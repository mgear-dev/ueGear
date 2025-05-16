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

        self.hierarchy_ctrlr: unreal.RigHierarchyController = None
        """Stores the Hierarchy controller that is used to modify the skeleton hierarchy"""

        self.colour = [1, 0, 0]

        self.shape_name = 'Default'

        self.settings = unreal.RigControlSettings()

    def set_control_type(self, cr_type:unreal.RigElementType):
        self.ctrl_type = cr_type
        self.rig_key = unreal.RigElementKey(type=self.ctrl_type, name=self.name)

    def build(self, hierarchy_controller):
        self.hierarchy_ctrlr = hierarchy_controller

        rig_hierarchy = self.hierarchy_ctrlr.get_hierarchy()

        # If control exists then store the rig key and return early
        control_key = unreal.RigElementKey(self.ctrl_type, self.name)
        control_exists = rig_hierarchy.find_control(control_key)

        if control_exists.index > -1:
            self.rig_key = control_exists.key

            # resets the control position and offset
            rig_hierarchy.set_global_transform(
                self.rig_key,
                unreal.Transform(),
                initial=True,
                affect_children=True)

            self.offset()

            print("   - Control already exists.")
            return

        self._setup_default_control_configuration()

        if self.ctrl_type == unreal.RigElementType.NULL:
            self.rig_key = self.hierarchy_ctrlr.add_null(
                self.name,
                self.parent,
                unreal.Transform()
            )
        else:
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
        self.settings.shape_name = self.shape_name
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

    def shape_transform_global(self, pos=None, rotation=None, scale=None):
        """Sets one or all of the shape tranforms attributes."""
        rig_hrc = self.hierarchy_ctrlr.get_hierarchy()
        shape_trans = rig_hrc.get_global_control_shape_transform(self.rig_key)

        if pos:
            shape_trans.translation = unreal.Vector(pos[0], pos[1], pos[2])

        if rotation:
            temp_quat = unreal.Quat()
            temp_quat.set_from_euler(unreal.Vector(rotation[0], rotation[1], rotation[2]))
            shape_trans.rotation = temp_quat

        if scale:
            temp_scale = unreal.Vector(scale[0], scale[1], scale[2])
            shape_trans.scale3d = temp_scale

        rig_hrc.set_control_shape_transform(
            self.rig_key,
            shape_trans,
            True
        )

    def min(self, pos=None, rotation=None, scale=None):
        if pos is None:
            pos = [0, 0, 0]
        if rotation is None:
            rotation = [0, 0, 0]
        if scale is None:
            scale = [1, 1, 1]
        self.hierarchy_ctrlr.get_hierarchy().set_control_value(
            self.rig_key,
            unreal.RigHierarchy.make_control_value_from_euler_transform(
                unreal.EulerTransform(
                    location=pos,
                    rotation=rotation,
                    scale=scale
                )
            ),
            unreal.RigControlValueType.MINIMUM)

    def max(self, pos=None, rotation=None, scale=None):
        if pos is None:
            pos = [0, 0, 0]
        if rotation is None:
            rotation = [0, 0, 0]
        if scale is None:
            scale = [1, 1, 1]
        rig_hrc = self.hierarchy_ctrlr.get_hierarchy()
        rig_hrc.set_control_value(
            self.rig_key,
            unreal.RigHierarchy.make_control_value_from_euler_transform(
                unreal.EulerTransform(location=pos,
                                      rotation=rotation,
                                      scale=scale)),
            unreal.RigControlValueType.MAXIMUM)

    def offset(self, pos=None, rotation=None, scale=None):
        if pos is None:
            pos = [0, 0, 0]
        if rotation is None:
            rotation = [0, 0, 0]
        if scale is None:
            scale = [1, 1, 1]

        rig_hrc = self.hierarchy_ctrlr.get_hierarchy()
        rig_hrc.set_control_offset_transform(
            self.rig_key,
            unreal.Transform(
                location=pos,
                rotation=rotation,
                scale=scale
            ),
            True,
            True
        )

    def transform(self, pos=None, rotation=None, scale=None):
        if pos is None:
            pos = [0, 0, 0]
        if rotation is None:
            rotation = [0, 0, 0]
        if scale is None:
            scale = [1, 1, 1]

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

    def set_transform(self,
                      quat_transform: unreal.Transform = None,
                      euler_transform: unreal.EulerTransform = None):
        """
        Populates the transform data for the control, using either an Euler Transform
        or a Quaternion (standard Unreal Transform)
        """
        if quat_transform is None and euler_transform is None:
            print("Cannot Set transform, no Transform or Quaternion Transform object passed in")
            return

        rig_hrc = self.hierarchy_ctrlr.get_hierarchy()

        if euler_transform:
            rig_hrc.set_control_value(
                self.rig_key,
                rig_hrc.make_control_value_from_euler_transform(
                    euler_transform
                ),
                unreal.RigControlValueType.CURRENT
            )

        if quat_transform:

            rig_hrc.set_global_transform(
                self.rig_key,
                quat_transform,
                initial=True,
                affect_children=False)

            # If the control being generated is only a Null then we only set its global position
            if (self.ctrl_type == unreal.RigElementType.NULL):
                return

            # initial_local_trans = rig_hrc.get_local_transform(self.rig_key, True)

            rig_hrc.set_control_offset_transform(
                self.rig_key,
                unreal.Transform(),
                initial=True,
                affect_children=False
            )

            rig_hrc.set_local_transform(
                self.rig_key,
                unreal.Transform(),
                initial=True,
                affect_children=False)

    def set_parent(self,
                   parent_name=None,
                   parent_type: unreal.RigElementType = None,
                   parent_rekey: unreal.RigElementKey = None
                   ):
        rig_hrc = self.hierarchy_ctrlr.get_hierarchy()

        # Child Rig Element Key
        child_rekey = unreal.RigElementKey(type=self.ctrl_type, name=self.name)

        # Creates a parent rig element key if one metadata passed in.
        if parent_name and parent_type:
            parent_rekey = unreal.RigElementKey(type=parent_type, name=parent_name)

        # updated hierarchy
        rig_hrc.set_parent(parent_rekey, child_rekey, True)

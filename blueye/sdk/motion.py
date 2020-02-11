class Motion:
    """Control the motion of the Pioneer, and set automatic control modes

    Motion can be set one degree of freedom at a time by using the 4 motion properties
    (surge, sway, heave and yaw) or for all 4 degrees of freedom in one go through the
    `send_thruster_setpoint` method.
    The current thruster setpoint state is stored in the `current_thruster_setpoints`
    variable, this is done because the Pioneer does not report back its current thruster
    setpoint.
    """

    def __init__(self, parent_drone):
        self._parent_drone = parent_drone
        self._tcp_client = parent_drone._tcp_client
        self._state_watcher = parent_drone._state_watcher

        self.current_thruster_setpoints = {"surge": 0, "sway": 0, "heave": 0, "yaw": 0}

    @property
    def surge(self) -> float:
        """ Set force reference for the surge direction

        Arguments:

        * **surge** (float): Force set point in the surge direction in range <-1, 1>,
                             a positive set point makes the drone move forward
        """
        return self.current_thruster_setpoints["surge"]

    @surge.setter
    def surge(self, surge_value: float):
        self.current_thruster_setpoints["surge"] = surge_value
        self.update_setpoint()

    @property
    def sway(self) -> float:
        """ Set force reference for the sway direction

        Arguments:

        * **sway** (float): Force set point in the sway direction in range <-1, 1>,
                            a positive set point makes the drone move to the right
        """
        return self.current_thruster_setpoints["sway"]

    @sway.setter
    def sway(self, sway_value: float):
        self.current_thruster_setpoints["sway"] = sway_value
        self.update_setpoint()

    @property
    def heave(self) -> float:
        """ Set force reference for the heave direction

        Arguments:

        * **heave** (float): Force set point in the heave direction in range <-1, 1>,
                             a positive set point makes the drone move downwards
        """
        return self.current_thruster_setpoints["heave"]

    @heave.setter
    def heave(self, heave_value: float):
        self.current_thruster_setpoints["heave"] = heave_value
        self.update_setpoint()

    @property
    def yaw(self) -> float:
        """ Set force reference for the yaw direction

        Arguments:

        * **yaw** (float): Moment set point in the sway direction in range <-1, 1>,
                           a positive set point makes the drone rotate clockwise.
        """
        return self.current_thruster_setpoints["yaw"]

    @yaw.setter
    def yaw(self, yaw_value: float):
        self.current_thruster_setpoints["yaw"] = yaw_value
        self.update_setpoint()

    def update_setpoint(self):
        self.send_thruster_setpoint(*self.current_thruster_setpoints.values())

    def send_thruster_setpoint(self, surge, sway, heave, yaw):
        """Control the thrusters of the pioneer

        Set reference values between -1 and 1 for each controllable degree of freedom on the Pioneer.
        The reference values are mapped linearly to a thruster force, a set point of -1 correspons
        to maximum negative force and a set point of 1 corresponds to maximum positive force. For the
        yaw direction the reference is a moment not a force, as the yaw direction is rotational not
        translational.


        Arguments:

        * **surge** (float): Force set point in the surge direction in range <-1, 1>,
                             a positive set point makes the drone move forward
        * **sway** (float): Force set point in the sway direction in range <-1, 1>,
                             a positive set point makes the drone move to the right
        * **heave** (float): Force set point in the heave direction in range <-1, 1>,
                             a positive set point makes the drone move down.
        * **yaw** (float): Moment set point in the yaw direction in range <-1, 1>,
                             a positive set point makes the drone rotate clockwise.
        """
        self.current_thruster_setpoints["surge"] = surge
        self.current_thruster_setpoints["sway"] = sway
        self.current_thruster_setpoints["heave"] = heave
        self.current_thruster_setpoints["yaw"] = yaw
        self._tcp_client.motion_input(surge, sway, heave, yaw, 0, 0)

    @property
    def auto_depth_active(self) -> bool:
        """Enable or disable the auto depth control mode

        When auto depth is active, input for the heave direction to the thruster_setpoint function
        specifies a speed set point instead of a force set point. A control loop on the Pioneer will
        then attempt to maintain the wanted speed in the heave direction as long as auto depth is
        active.

        *Arguments*:

        * active (bool): Activate auto depth mode if active is true, de-activate if false

        *Returns*:

        * active (bool): Returns true if auto depth is active, false if it is not active
        """
        AUTO_DEPTH_MODE = 3
        AUTO_HEADING_AND_AUTO_DEPTH_MODE = 9
        state = self._state_watcher.general_state
        if (
            state["control_mode"] is AUTO_DEPTH_MODE
            or state["control_mode"] is AUTO_HEADING_AND_AUTO_DEPTH_MODE
        ):
            return True
        else:
            return False

    @auto_depth_active.setter
    def auto_depth_active(self, active: bool):
        if active:
            self._tcp_client.auto_depth_on()
        else:
            self._tcp_client.auto_depth_off()

    @property
    def auto_heading_active(self) -> bool:
        """Enable or disable the auto heading control mode

        When auto heading is active, input for the yaw direction to the thruster_setpoint function
        specifies a angular speed set point instead of a moment set point. A control loop on the
        Pioneer will then attempt to maintain the wanted angular velocity in the yaw direction as
        long as auto heading is active.

        *Arguments*:

        * active (bool): Activate auto heading mode if active is true, de-activate if false

        *Returns*:

        * active (bool): Returns true if auto heading mode is active, false if it is not active
        """
        AUTO_HEADING_MODE = 7
        AUTO_HEADING_AND_AUTO_DEPTH_MODE = 9
        state = self._state_watcher.general_state
        if (
            state["control_mode"] is AUTO_HEADING_MODE
            or state["control_mode"] is AUTO_HEADING_AND_AUTO_DEPTH_MODE
        ):
            return True
        else:
            return False

    @auto_heading_active.setter
    def auto_heading_active(self, active: bool):
        if active:
            self._tcp_client.auto_heading_on()
        else:
            self._tcp_client.auto_heading_off()

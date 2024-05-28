import threading
from typing import Optional

import blueye.protocol


class Motion:
    """Control the motion of the drone, and set automatic control modes

    Motion can be set one degree of freedom at a time by using the 4 motion properties
    (surge, sway, heave and yaw) or for all 4 degrees of freedom in one go through the
    `send_thruster_setpoint` method.
    """

    def __init__(self, parent_drone):
        self._parent_drone = parent_drone
        self.thruster_lock = threading.Lock()
        self._current_thruster_setpoints = {"surge": 0, "sway": 0, "heave": 0, "yaw": 0}
        self._current_boost_setpoints = {"slow": 0, "boost": 0}

    @property
    def current_thruster_setpoints(self):
        """Returns the current setpoints for the thrusters

        We maintain this state in the SDK since the drone expects to receive all of the setpoints at
        once.

        For setting the setpoints you should use the dedicated properties/functions for that, trying
        to set them directly with this property will raise an AttributeError.
        """

        return self._current_thruster_setpoints

    @current_thruster_setpoints.setter
    def current_thruster_setpoints(self, *args, **kwargs):
        raise AttributeError(
            "Do not set the setpoints directly, use the surge, sway, heave, yaw properties or the "
            "send_thruster_setpoint function for that."
        )

    def _send_motion_input_message(self):
        """Small helper function for building argument list to motion_input command"""
        thruster_setpoints = self.current_thruster_setpoints.values()
        boost_setpoints = self._current_boost_setpoints.values()
        self._parent_drone._ctrl_client.set_motion_input(*thruster_setpoints, *boost_setpoints)

    @property
    def surge(self) -> float:
        """Set force reference for the surge direction

        Arguments:

        * **surge** (float): Force set point in the surge direction in range <-1, 1>,
                             a positive set point makes the drone move forward
        """
        return self.current_thruster_setpoints["surge"]

    @surge.setter
    def surge(self, surge_value: float):
        with self.thruster_lock:
            self._current_thruster_setpoints["surge"] = surge_value
            self._send_motion_input_message()

    @property
    def sway(self) -> float:
        """Set force reference for the sway direction

        Arguments:

        * **sway** (float): Force set point in the sway direction in range <-1, 1>,
                            a positive set point makes the drone move to the right
        """
        return self.current_thruster_setpoints["sway"]

    @sway.setter
    def sway(self, sway_value: float):
        with self.thruster_lock:
            self._current_thruster_setpoints["sway"] = sway_value
            self._send_motion_input_message()

    @property
    def heave(self) -> float:
        """Set force reference for the heave direction

        Arguments:

        * **heave** (float): Force set point in the heave direction in range <-1, 1>,
                             a positive set point makes the drone move downwards
        """
        return self.current_thruster_setpoints["heave"]

    @heave.setter
    def heave(self, heave_value: float):
        with self.thruster_lock:
            self._current_thruster_setpoints["heave"] = heave_value
            self._send_motion_input_message()

    @property
    def yaw(self) -> float:
        """Set force reference for the yaw direction

        Arguments:

        * **yaw** (float): Moment set point in the sway direction in range <-1, 1>,
                           a positive set point makes the drone rotate clockwise.
        """
        return self.current_thruster_setpoints["yaw"]

    @yaw.setter
    def yaw(self, yaw_value: float):
        with self.thruster_lock:
            self._current_thruster_setpoints["yaw"] = yaw_value
            self._send_motion_input_message()

    def send_thruster_setpoint(self, surge, sway, heave, yaw):
        """Control the thrusters of the drone

        Set reference values between -1 and 1 for each controllable degree of freedom on the drone.
        The reference values are mapped linearly to a thruster force, a set point of -1 correspons
        to maximum negative force and a set point of 1 corresponds to maximum positive force. For
        the yaw direction the reference is a moment not a force, as the yaw direction is rotational
        not translational.


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
        with self.thruster_lock:
            self._current_thruster_setpoints["surge"] = surge
            self._current_thruster_setpoints["sway"] = sway
            self._current_thruster_setpoints["heave"] = heave
            self._current_thruster_setpoints["yaw"] = yaw
            self._send_motion_input_message()

    @property
    def boost(self) -> float:
        """Get or set the boost gain

        Arguments:

        * **boost_gain** (float): Range from 0 to 1.
        """
        return self._current_boost_setpoints["boost"]

    @boost.setter
    def boost(self, boost_gain: float):
        with self.thruster_lock:
            self._current_boost_setpoints["boost"] = boost_gain
            self._send_motion_input_message()

    @property
    def slow(self) -> float:
        """Get or set the "slow gain" (inverse of boost)

        Arguments:

        * **slow_gain** (float): Range from 0 to 1.
        """
        return self._current_boost_setpoints["slow"]

    @slow.setter
    def slow(self, slow_gain: float):
        with self.thruster_lock:
            self._current_boost_setpoints["slow"] = slow_gain
            self._send_motion_input_message()

    @property
    def auto_depth_active(self) -> Optional[bool]:
        """Enable or disable the auto depth control mode

        When auto depth is active, input for the heave direction to the thruster_setpoint function
        specifies a speed set point instead of a force set point. A control loop on the drone will
        then attempt to maintain the wanted speed in the heave direction as long as auto depth is
        active.

        *Arguments*:

        * Enable (bool): Activate auto depth mode if true, de-activate if false

        *Returns*:

        * Auto depth state (bool): True if auto depth is active, false if not
        """
        control_mode_tel = self._parent_drone.telemetry.get(blueye.protocol.ControlModeTel)
        if control_mode_tel is None:
            return None
        else:
            return control_mode_tel.state.auto_depth

    @auto_depth_active.setter
    def auto_depth_active(self, enable: bool):
        self._parent_drone._ctrl_client.set_auto_depth_state(enable)

    @property
    def auto_heading_active(self) -> Optional[bool]:
        """Enable or disable the auto heading control mode

        When auto heading is active, input for the yaw direction to the thruster_setpoint function
        specifies a angular speed set point instead of a moment set point. A control loop on the
        drone will then attempt to maintain the wanted angular velocity in the yaw direction as
        long as auto heading is active.

        *Arguments*:

        * Enable (bool): Activate auto heading mode if true, de-activate if false

        *Returns*:

        * Auto heading state (bool): True if auto heading mode is active, false if not
        """
        control_mode_tel = self._parent_drone.telemetry.get(blueye.protocol.ControlModeTel)
        if control_mode_tel is None:
            return None
        else:
            return control_mode_tel.state.auto_heading

    @auto_heading_active.setter
    def auto_heading_active(self, enable: bool):
        self._parent_drone._ctrl_client.set_auto_heading_state(enable)

    @property
    def auto_altitude_active(self) -> Optional[bool]:
        """Enable or disable the auto altitude control mode

        When auto altitude is active, the drone will attempt to maintain its current altitude above
        the seabed. Input for the heave direction to the thruster_setpoint function specifies a
        speed set point instead of a force set point. A control loop on the drone will then attempt
        to maintain the wanted speed in the heave direction as long as auto altitude is active.

        *Arguments*:
        * Enable (bool): Activate auto altitude mode if true, de-activate if false. If the drone
                         does not have a valid altitude reading this command will be ignored.

        *Returns*:

        * Auto altitude state (bool): True if auto altitude is active, false if not
        """
        control_mode_tel = self._parent_drone.telemetry.get(blueye.protocol.ControlModeTel)
        if control_mode_tel is None:
            return None
        else:
            return control_mode_tel.state.auto_altitude

    @auto_altitude_active.setter
    def auto_altitude_active(self, enable: bool):
        self._parent_drone._ctrl_client.set_auto_altitude_state(enable)

import threading
import warnings
from typing import Optional

import blueye.protocol

from .utils import deprecated_property


class Motion:
    """Control the motion of the drone, and set automatic control modes

    Motion can be set one degree of freedom at a time by using the motion setters (set_surge,
    set_sway, set_heave and set_yaw, and on the Blueye X7 also set_roll and set_pitch) or for all
    degrees of freedom in one go through the `send_thruster_setpoint` method.

    Only the Blueye X7 has thrusters that can produce roll and pitch moments. The other models
    ignore roll and pitch input, so the setters are safe to call on any drone.
    """

    def __init__(self, parent_drone):
        self._parent_drone = parent_drone
        self.thruster_lock = threading.Lock()
        self._current_thruster_setpoints = {
            "surge": 0,
            "sway": 0,
            "heave": 0,
            "yaw": 0,
            "roll": 0,
            "pitch": 0,
        }
        self._current_boost_setpoints = {"slow": 0, "boost": 0}

    def get_current_thruster_setpoints(self):
        """Returns the current setpoints for the thrusters

        We maintain this state in the SDK since the drone expects to receive all of the setpoints at
        once.

        For setting the setpoints you should use the dedicated setters/functions for that, trying
        to set them directly will raise an AttributeError.
        """

        return self._current_thruster_setpoints

    @property
    def current_thruster_setpoints(self):
        """Deprecated, use `get_current_thruster_setpoints` instead."""
        warnings.warn(
            "`Motion.current_thruster_setpoints` is deprecated and will be removed in the next "
            "major version. Use `Motion.get_current_thruster_setpoints()` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_current_thruster_setpoints()

    @current_thruster_setpoints.setter
    def current_thruster_setpoints(self, *args, **kwargs):
        raise AttributeError(
            "Do not set the setpoints directly, use the surge, sway, heave, yaw setters or the "
            "send_thruster_setpoint function for that."
        )

    def _send_motion_input_message(self):
        """Small helper function for building argument list to motion_input command"""
        setpoints = self._current_thruster_setpoints
        boost_setpoints = self._current_boost_setpoints
        self._parent_drone._ctrl_client.set_motion_input(
            setpoints["surge"],
            setpoints["sway"],
            setpoints["heave"],
            setpoints["yaw"],
            boost_setpoints["slow"],
            boost_setpoints["boost"],
            roll=setpoints["roll"],
            pitch=setpoints["pitch"],
        )

    def get_surge(self) -> float:
        """Get the force reference for the surge direction

        Returns:
            Force set point in the surge direction in range <-1, 1>.
        """
        return self._current_thruster_setpoints["surge"]

    def set_surge(self, surge_value: float):
        """Set force reference for the surge direction

        Args:
            surge_value (float): Force set point in the surge direction in range <-1, 1>,
                                 a positive set point makes the drone move forward.
        """
        with self.thruster_lock:
            self._current_thruster_setpoints["surge"] = surge_value
            self._send_motion_input_message()

    surge = deprecated_property("get_surge", "set_surge")

    def get_sway(self) -> float:
        """Get the force reference for the sway direction

        Returns:
            Force set point in the sway direction in range <-1, 1>.
        """
        return self._current_thruster_setpoints["sway"]

    def set_sway(self, sway_value: float):
        """Set force reference for the sway direction

        Args:
            sway_value (float): Force set point in the sway direction in range <-1, 1>,
                                a positive set point makes the drone move to the right.
        """
        with self.thruster_lock:
            self._current_thruster_setpoints["sway"] = sway_value
            self._send_motion_input_message()

    sway = deprecated_property("get_sway", "set_sway")

    def get_heave(self) -> float:
        """Get the force reference for the heave direction

        Returns:
            Force set point in the heave direction in range <-1, 1>.
        """
        return self._current_thruster_setpoints["heave"]

    def set_heave(self, heave_value: float):
        """Set force reference for the heave direction

        Args:
            heave_value (float): Force set point in the heave direction in range <-1, 1>,
                                 a positive set point makes the drone move downwards.
        """
        with self.thruster_lock:
            self._current_thruster_setpoints["heave"] = heave_value
            self._send_motion_input_message()

    heave = deprecated_property("get_heave", "set_heave")

    def get_yaw(self) -> float:
        """Get the moment reference for the yaw direction

        Returns:
            Moment set point in the yaw direction in range <-1, 1>.
        """
        return self._current_thruster_setpoints["yaw"]

    def set_yaw(self, yaw_value: float):
        """Set moment reference for the yaw direction

        Args:
            yaw_value (float): Moment set point in the yaw direction in range <-1, 1>,
                               a positive set point makes the drone rotate clockwise.
        """
        with self.thruster_lock:
            self._current_thruster_setpoints["yaw"] = yaw_value
            self._send_motion_input_message()

    yaw = deprecated_property("get_yaw", "set_yaw")

    def get_roll(self) -> float:
        """Get the moment reference for the roll direction

        Only the Blueye X7 acts on roll input, see `set_roll`.

        Returns:
            Moment set point in the roll direction in range <-1, 1>.
        """
        return self._current_thruster_setpoints["roll"]

    def set_roll(self, roll_value: float):
        """Set moment reference for the roll direction

        Only the Blueye X7 has thrusters that can produce a roll moment. Other models ignore this
        input.

        With auto heading off the value is an open-loop moment set point, like yaw, and nothing on
        the drone limits the resulting angle. The drone settles where the thruster moment is
        balanced by its righting moment, and a large input held for a few seconds can roll it over.
        The drone keeps acting on the last setpoint for as long as the SDK is connected, so set it
        back to 0 when the manoeuvre is done.

        With auto heading on the drone instead holds a roll angle. The value is then an angular
        speed set point for that angle, which is bounded to 45 degrees either side of level, and
        the drone keeps the angle it has reached when the input returns to 0. Engaging auto heading
        resets the held roll and pitch angles to level.

        While the autopilot is running a mission the drone holds level and ignores roll input.
        Starting the autopilot also switches auto heading off.

        Args:
            roll_value (float): Moment set point in the roll direction in range <-1, 1>,
                                a positive set point rolls the drone to the right.
        """
        with self.thruster_lock:
            self._current_thruster_setpoints["roll"] = roll_value
            self._send_motion_input_message()

    def get_pitch(self) -> float:
        """Get the moment reference for the pitch direction

        Only the Blueye X7 acts on pitch input, see `set_pitch`.

        Returns:
            Moment set point in the pitch direction in range <-1, 1>.
        """
        return self._current_thruster_setpoints["pitch"]

    def set_pitch(self, pitch_value: float):
        """Set moment reference for the pitch direction

        Only the Blueye X7 has thrusters that can produce a pitch moment. Other models ignore this
        input.

        With auto heading off the value is an open-loop moment set point, like yaw, and nothing on
        the drone limits the resulting angle. The drone settles where the thruster moment is
        balanced by its righting moment, and a large input held for a few seconds can tip it over.
        The drone keeps acting on the last setpoint for as long as the SDK is connected, so set it
        back to 0 when the manoeuvre is done.

        With auto heading on the drone instead holds a pitch angle. The value is then an angular
        speed set point for that angle, which is bounded to 45 degrees either side of level, and
        the drone keeps the angle it has reached when the input returns to 0. Engaging auto heading
        resets the held roll and pitch angles to level.

        While the autopilot is running a mission the drone holds level and ignores pitch input.
        Starting the autopilot also switches auto heading off.

        Args:
            pitch_value (float): Moment set point in the pitch direction in range <-1, 1>,
                                 a positive set point pitches the nose of the drone up.
        """
        with self.thruster_lock:
            self._current_thruster_setpoints["pitch"] = pitch_value
            self._send_motion_input_message()

    def zero_setpoints(self):
        """Set every setpoint to zero and send it.

        Covers surge, sway, heave, yaw, roll and pitch as well as slow and boost. The drone keeps
        the last motion input it received until a new one arrives or its watchdog times out, so
        this is what [`disconnect`][blueye.sdk.drone.Drone.disconnect] sends before letting go.
        """
        with self.thruster_lock:
            for axis in self._current_thruster_setpoints:
                self._current_thruster_setpoints[axis] = 0
            for gain in self._current_boost_setpoints:
                self._current_boost_setpoints[gain] = 0
            self._send_motion_input_message()

    def send_thruster_setpoint(self, surge, sway, heave, yaw, *, roll=0.0, pitch=0.0):
        """Control the thrusters of the drone

        Set reference values between -1 and 1 for each controllable degree of freedom on the drone.
        The reference values are mapped linearly to a thruster force, a set point of -1 corresponds
        to maximum negative force and a set point of 1 corresponds to maximum positive force. For
        the yaw, roll and pitch directions the reference is a moment not a force, as these
        directions are rotational not translational.

        Roll and pitch are keyword-only and default to 0, so a call that leaves them out clears any
        roll or pitch set earlier. Only the Blueye X7 acts on them, and with auto heading off they
        are open-loop moments that nothing on the drone limits. See `set_roll` and `set_pitch` for
        how auto heading changes their meaning and why the autopilot ignores them.

        Args:
            surge (float): Force set point in the surge direction in range <-1, 1>,
                           a positive set point makes the drone move forward.
            sway (float): Force set point in the sway direction in range <-1, 1>,
                          a positive set point makes the drone move to the right.
            heave (float): Force set point in the heave direction in range <-1, 1>,
                           a positive set point makes the drone move down.
            yaw (float): Moment set point in the yaw direction in range <-1, 1>,
                         a positive set point makes the drone rotate clockwise.
            roll (float): Moment set point in the roll direction in range <-1, 1>,
                          a positive set point rolls the drone to the right. X7 only.
            pitch (float): Moment set point in the pitch direction in range <-1, 1>,
                           a positive set point pitches the nose of the drone up. X7 only.
        """
        with self.thruster_lock:
            self._current_thruster_setpoints["surge"] = surge
            self._current_thruster_setpoints["sway"] = sway
            self._current_thruster_setpoints["heave"] = heave
            self._current_thruster_setpoints["yaw"] = yaw
            self._current_thruster_setpoints["roll"] = roll
            self._current_thruster_setpoints["pitch"] = pitch
            self._send_motion_input_message()

    def get_boost(self) -> float:
        """Get the boost gain

        Returns:
            The current boost gain, range from 0 to 1.
        """
        return self._current_boost_setpoints["boost"]

    def set_boost(self, boost_gain: float):
        """Set the boost gain

        Args:
            boost_gain (float): Range from 0 to 1.
        """
        with self.thruster_lock:
            self._current_boost_setpoints["boost"] = boost_gain
            self._send_motion_input_message()

    boost = deprecated_property("get_boost", "set_boost")

    def get_slow(self) -> float:
        """Get the "slow gain" (inverse of boost)

        Returns:
            The current slow gain, range from 0 to 1.
        """
        return self._current_boost_setpoints["slow"]

    def set_slow(self, slow_gain: float):
        """Set the "slow gain" (inverse of boost)

        Args:
            slow_gain (float): Range from 0 to 1.
        """
        with self.thruster_lock:
            self._current_boost_setpoints["slow"] = slow_gain
            self._send_motion_input_message()

    slow = deprecated_property("get_slow", "set_slow")

    def is_auto_depth_active(self) -> Optional[bool]:
        """Get the state of the auto depth control mode

        When auto depth is active, input for the heave direction to the thruster_setpoint function
        specifies a speed set point instead of a force set point. A control loop on the drone will
        then attempt to maintain the wanted speed in the heave direction as long as auto depth is
        active.

        Returns:
            Auto depth state (bool): True if auto depth is active, false if not. None if no
            telemetry message has been received.
        """
        control_mode_tel = self._parent_drone.telemetry.get(blueye.protocol.ControlModeTel)
        if control_mode_tel is None:
            return None
        else:
            return control_mode_tel.state.auto_depth

    def enable_auto_depth(self, enable: bool):
        """Enable or disable the auto depth control mode

        When auto depth is active, input for the heave direction to the thruster_setpoint function
        specifies a speed set point instead of a force set point. A control loop on the drone will
        then attempt to maintain the wanted speed in the heave direction as long as auto depth is
        active.

        Args:
            enable (bool): Activate auto depth mode if true, de-activate if false.
        """
        self._parent_drone._ctrl_client.set_auto_depth_state(enable)

    auto_depth_active = deprecated_property("is_auto_depth_active", "enable_auto_depth")

    def is_auto_heading_active(self) -> Optional[bool]:
        """Get the state of the auto heading control mode

        When auto heading is active, input for the yaw direction to the thruster_setpoint function
        specifies a angular speed set point instead of a moment set point. A control loop on the
        drone will then attempt to maintain the wanted angular velocity in the yaw direction as
        long as auto heading is active.

        Returns:
            Auto heading state (bool): True if auto heading mode is active, false if not. None if no
            telemetry message has been received.
        """
        control_mode_tel = self._parent_drone.telemetry.get(blueye.protocol.ControlModeTel)
        if control_mode_tel is None:
            return None
        else:
            return control_mode_tel.state.auto_heading

    def enable_auto_heading(self, enable: bool):
        """Enable or disable the auto heading control mode

        When auto heading is active, input for the yaw direction to the thruster_setpoint function
        specifies a angular speed set point instead of a moment set point. A control loop on the
        drone will then attempt to maintain the wanted angular velocity in the yaw direction as
        long as auto heading is active.

        Args:
            enable (bool): Activate auto heading mode if true, de-activate if false.
        """
        self._parent_drone._ctrl_client.set_auto_heading_state(enable)

    auto_heading_active = deprecated_property("is_auto_heading_active", "enable_auto_heading")

    def is_auto_altitude_active(self) -> Optional[bool]:
        """Get the state of the auto altitude control mode

        When auto altitude is active, the drone will attempt to maintain its current altitude above
        the seabed. Input for the heave direction to the thruster_setpoint function specifies a
        speed set point instead of a force set point. A control loop on the drone will then attempt
        to maintain the wanted speed in the heave direction as long as auto altitude is active.

        Returns:
            Auto altitude state (bool): True if auto altitude is active, false if not. None if no
            telemetry message has been received.
        """
        control_mode_tel = self._parent_drone.telemetry.get(blueye.protocol.ControlModeTel)
        if control_mode_tel is None:
            return None
        else:
            return control_mode_tel.state.auto_altitude

    def enable_auto_altitude(self, enable: bool):
        """Enable or disable the auto altitude control mode

        When auto altitude is active, the drone will attempt to maintain its current altitude above
        the seabed. Input for the heave direction to the thruster_setpoint function specifies a
        speed set point instead of a force set point. A control loop on the drone will then attempt
        to maintain the wanted speed in the heave direction as long as auto altitude is active.

        Args:
            enable (bool): Activate auto altitude mode if true, de-activate if false. If the drone
                           does not have a valid altitude reading this command will be ignored.
        """
        self._parent_drone._ctrl_client.set_auto_altitude_state(enable)

    auto_altitude_active = deprecated_property("is_auto_altitude_active", "enable_auto_altitude")

    def is_station_keeping_active(self) -> Optional[bool]:
        """Get the state of the station keeping control mode

        When station keeping is active, the drone will attempt to maintain its current position
        and orientation in the water as long as the mode is active.

        Returns:
            Station keeping state (bool): True if station keeping mode is active, false if not. None
            if no telemetry message has been received.
        """
        control_mode_tel = self._parent_drone.telemetry.get(blueye.protocol.ControlModeTel)
        if control_mode_tel is None:
            return None
        else:
            return control_mode_tel.state.station_keeping

    def enable_station_keeping(self, enable: bool):
        """Enable or disable the station keeping control mode

        When station keeping is active, the drone will attempt to maintain its current position
        and orientation in the water as long as the mode is active.

        Args:
            enable (bool): Activate station keeping mode if true, de-activate if false.
        """
        self._parent_drone._ctrl_client.set_station_keeping_state(enable)

    station_keeping_active = deprecated_property(
        "is_station_keeping_active", "enable_station_keeping"
    )

    def is_weather_vaning_active(self) -> Optional[bool]:
        """Get the state of the weather vaning control mode

        When weather vaning is active, the drone will attempt to maintain its current position
        in the water and orient itself parallel to the current.

        Returns:
            Weather vaning state (bool): True if weather vaning mode is active, false if not. None
            if no telemetry message has been received.
        """
        control_mode_tel = self._parent_drone.telemetry.get(blueye.protocol.ControlModeTel)
        if control_mode_tel is None:
            return None
        else:
            return control_mode_tel.state.weather_vaning

    def enable_weather_vaning(self, enable: bool):
        """Enable or disable the weather vaning control mode

        When weather vaning is active, the drone will attempt to maintain its current position
        in the water and orient itself parallel to the current.

        Args:
            enable (bool): Activate weather vaning mode if true, de-activate if false. If the drone
                           does not have a valid altitude reading this command will be ignored.
        """
        self._parent_drone._ctrl_client.set_weather_vaning_state(enable)

    weather_vaning_active = deprecated_property("is_weather_vaning_active", "enable_weather_vaning")

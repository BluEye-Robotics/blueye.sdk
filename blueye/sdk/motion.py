import threading
import warnings
from typing import Dict, Optional

import blueye.protocol

from .utils import deprecated_property


class Motion:
    """Control the motion of the drone, and set automatic control modes.

    Motion can be set one degree of freedom at a time by using the motion setters (set_surge,
    set_sway, set_heave and set_yaw, and on the Blueye X7 also set_roll and set_pitch) or for all
    degrees of freedom in one go through the `send_thruster_setpoint` method.

    A setpoint of 1 or -1 is full stick, not the most the thrusters can give. The force it asks
    for depends on [`set_boost`][blueye.sdk.motion.Motion.set_boost] and
    [`set_slow`][blueye.sdk.motion.Motion.set_slow]; see
    [Control from a Python script](../../../movement/from-the-CLI.md) for the levels per axis.
    The drone holds the last setpoint until it gets a new one, or until it zeroes the input 3
    seconds after the client in control stops sending its watchdog.

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
        # Set while disconnect() is leaving, see _stop_input
        self._input_stopped = False

    def get_current_thruster_setpoints(self) -> Dict[str, float]:
        """Get the setpoints the SDK last sent, per axis.

        The SDK keeps them because every motion message carries all axes at once.

        Returns:
            A dictionary with the surge, sway, heave, yaw, roll and pitch setpoints. Change them
            with the setters or `send_thruster_setpoint`, not through this dictionary.
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
        if self._input_stopped:
            return
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
            self._zero_setpoints()

    def _zero_setpoints(self):
        """zero_setpoints() for a caller that holds the thruster lock."""
        for axis in self._current_thruster_setpoints:
            self._current_thruster_setpoints[axis] = 0
        for gain in self._current_boost_setpoints:
            self._current_boost_setpoints[gain] = 0
        self._send_motion_input_message()

    def _stop_input(self, zero: bool):
        """Stop sending motion input, after a last zero when `zero` is set.

        For [`disconnect`][blueye.sdk.drone.Drone.disconnect]: until its threads have stopped, a
        control loop on another thread or a telemetry callback can still set motion, and input
        queued after the zero would reach the drone after it and stay in effect once the client
        has left. Setpoints set after this are dropped until `_resume_input`.
        """
        with self.thruster_lock:
            if zero:
                self._zero_setpoints()
            self._input_stopped = True

    def _resume_input(self):
        """Send motion input again, see `_stop_input`."""
        with self.thruster_lock:
            self._input_stopped = False

    def send_thruster_setpoint(self, surge, sway, heave, yaw, *, roll=0.0, pitch=0.0):
        """Set the setpoint of every axis in one message.

        Each setpoint is between -1 and 1 and scales the force (or, for yaw, roll and pitch, the
        moment) linearly. A setpoint of 1 or -1 is full stick, whose force depends on
        [`set_boost`][blueye.sdk.motion.Motion.set_boost] and
        [`set_slow`][blueye.sdk.motion.Motion.set_slow], not the most the thrusters can give.

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
        """Get the boost gain.

        Returns:
            The boost gain the SDK last sent, from 0 to 1.
        """
        return self._current_boost_setpoints["boost"]

    def set_boost(self, boost_gain: float):
        """Set the boost gain.

        Boost raises the force a full-stick setpoint asks for, up to the drone's boosted level at
        1. Values up to 0.1 count as 0 and 0.1 to 1 is stretched over the whole range, so 0.55 is
        halfway. The drone uses boost minus slow after that, so boost and slow at 1 together give
        the normal level.

        Args:
            boost_gain (float): Range from 0 to 1.
        """
        with self.thruster_lock:
            self._current_boost_setpoints["boost"] = boost_gain
            self._send_motion_input_message()

    boost = deprecated_property("get_boost", "set_boost")

    def get_slow(self) -> float:
        """Get the slow gain.

        Returns:
            The slow gain the SDK last sent, from 0 to 1.
        """
        return self._current_boost_setpoints["slow"]

    def set_slow(self, slow_gain: float):
        """Set the slow gain.

        Slow lowers the force a full-stick setpoint asks for, down to the drone's slow level at 1,
        for fine positioning. Values up to 0.1 count as 0, and the drone uses boost minus slow,
        see [`set_boost`][blueye.sdk.motion.Motion.set_boost].

        Args:
            slow_gain (float): Range from 0 to 1.
        """
        with self.thruster_lock:
            self._current_boost_setpoints["slow"] = slow_gain
            self._send_motion_input_message()

    slow = deprecated_property("get_slow", "set_slow")

    def is_auto_depth_active(self) -> Optional[bool]:
        """Get the state of the auto depth control mode

        When auto depth is active, heave input (`set_heave` or `send_thruster_setpoint`)
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

        When auto depth is active, heave input (`set_heave` or `send_thruster_setpoint`)
        specifies a speed set point instead of a force set point. A control loop on the drone will
        then attempt to maintain the wanted speed in the heave direction as long as auto depth is
        active.

        Auto depth needs no extra sensor. Enabling it turns auto altitude off, since the two hold
        the same axis.

        Args:
            enable (bool): Activate auto depth mode if true, de-activate if false.
        """
        self._parent_drone._ctrl_client.set_auto_depth_state(enable)

    auto_depth_active = deprecated_property("is_auto_depth_active", "enable_auto_depth")

    def is_auto_heading_active(self) -> Optional[bool]:
        """Get the state of the auto heading control mode

        When auto heading is active, yaw input (`set_yaw` or `send_thruster_setpoint`)
        specifies an angular speed set point instead of a moment set point. A control loop on the
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

        When auto heading is active, yaw input (`set_yaw` or `send_thruster_setpoint`)
        specifies an angular speed set point instead of a moment set point. A control loop on the
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
        the seabed. Heave input (`set_heave` or `send_thruster_setpoint`) specifies a
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
        the seabed. Heave input (`set_heave` or `send_thruster_setpoint`) specifies a
        speed set point instead of a force set point. A control loop on the drone will then attempt
        to maintain the wanted speed in the heave direction as long as auto altitude is active.

        Auto altitude needs a valid altitude, which comes from a DVL or a downward-facing Ping
        sonar on a guest port. `get_altitude()` returns `None` while there is none. Without it the
        drone drops the request and only logs it on its own side, so check
        `is_auto_altitude_active()` afterwards. Enabling auto altitude turns auto depth off, also
        when the auto altitude request itself is dropped. If the altitude becomes invalid while
        auto altitude is active, the drone switches to auto depth.

        Args:
            enable (bool): Activate auto altitude mode if true, de-activate if false.
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

        Station keeping needs a valid position from a DVL or from the drone's own Blueye GNSS.
        Topside positioning (UGPS, USBL or NMEA input over UDP) is used for the map position but
        does not count here: those fixes jump between samples, and the drone would chase every
        jump. Without a valid position the drone drops the request and only logs it on
        its own side, so check `is_station_keeping_active()` afterwards. An active hold is released
        when the position has been invalid for 3 seconds.
        `PositionEstimateTel.position_estimate.navigation_sensors` lists each sensor with its
        validity.

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

        Weather vaning is station keeping with a free heading, so it has the same requirement: a
        valid position from a DVL or the drone's own Blueye GNSS, see `enable_station_keeping`.
        Enabling it also turns station keeping on, and turning station keeping off turns weather
        vaning off. An altitude reading is not needed.

        Args:
            enable (bool): Activate weather vaning mode if true, de-activate if false.
        """
        self._parent_drone._ctrl_client.set_weather_vaning_state(enable)

    weather_vaning_active = deprecated_property("is_weather_vaning_active", "enable_weather_vaning")

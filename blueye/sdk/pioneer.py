#!/usr/bin/env python3
import threading
from typing import Iterator, Tuple

from .camera import Camera
from blueye.protocol import TcpClient, UdpClient


class _PioneerStateWatcher(threading.Thread):
    """
    Subscribes to UDP messages from the drone and stores the latest data
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self.general_state = None
        self.calibration_state = None
        self._udpclient = UdpClient()
        self._exit_flag = threading.Event()
        self.daemon = True

    def run(self):
        while not self._exit_flag.is_set():
            data_packet = self._udpclient.get_data_dict()
            if data_packet["command_type"] == 1:
                self.general_state = data_packet
            elif data_packet["command_type"] == 2:
                self.calibration_state = data_packet

    def stop(self):
        self._exit_flag.set()


class Pioneer:
    """A class providing a interface to the Blueye pioneer's basic functions
    """

    def __init__(self, ip="192.168.1.101", tcpPort=2011, autoConnect=True):
        self._ip = ip
        self._tcp_client = TcpClient(ip=ip, port=tcpPort, autoConnect=autoConnect)
        self._state_watcher = _PioneerStateWatcher()
        self.camera = Camera(self._tcp_client, self._state_watcher)
        if autoConnect is True:
            self.connect()

    def connect(self):
        """Start receiving telemetry info from the drone, and publishing watchdog messages

        When watchdog message are published the thrusters are armed, to stop the drone from moving
        unexpectedly when connecting all thruster set points are set to zero when connecting.
        """
        self._state_watcher.start()
        self._tcp_client.connect()
        self._tcp_client.start()
        self.thruster_setpoint(0, 0, 0, 0)

    @property
    def lights(self) -> int:
        """Get or set the brightness of the pioneers bottom canister lights

        *Arguments*:
            brightness (int): Set the brightness of the bottom canister LED's in the range <0, 255>

        *Returns*:
            brightness (int): The brightness of the bottom canister LED's in the range <0, 255>
        """
        state = self._state_watcher.general_state
        return state["lights_upper"]

    @lights.setter
    def lights(self, brightness: int):
        try:
            self._tcp_client.set_lights(brightness, 0)
        except ValueError as e:
            raise ValueError(
                "Error occured while trying to set lights to: " f"{brightness}"
            ) from e

    def thruster_setpoint(self, surge, sway, heave, yaw):
        """Control the thrusters of the pioneer

        Set reference values between -1 and 1 for each controllable degree of freedom on the Pioneer.
        The reference values are mapped linearly to a thruster force, a set point of -1 correspons
        to maximum negative force and a set point of 1 corresponds to maximum positive force. For the
        yaw direction the reference is a moment not a force, as the yaw direction is rotational not
        translational.


        Arguments:

        * **surge** (float): Force set point in the surge direction in range <-1, 1>, a positive set point makes the drone move forward
        * **sway** (float): Force set point in the sway direction in range <-1, 1>, a positive set point makes the drone move to the right
        * **heave** (float): Force set point in the heave direction in range <-1, 1>, a positive set point makes the drone move down.
        * **yaw** (float): Moment set point in the sway direction in range <-1, 1>, a positive set point makes the drone rotate clockwise.
        """
        self._tcp_client.motion_input(surge, sway, heave, yaw, 0, 0)

    @property
    def auto_depth_active(self) -> bool:
        """Enable or disable the auto depth control mode

        When auto depth is active, input for the heave direction to the thruster_setpoint function
        specifies a speed set point instead of a force set point. A control loop on the Pioneer will
        then attempt to maintain the wanted speed in the heave direction as long as auto depth is
        active.

        *Arguments*:
            active (bool): Activate auto depth mode if active is true, de-activte if false

        *Returns*:
            active (int): Returns true if auto depth is active, false if it is not active
        """
        AUTO_DEPTH_MODE = 3
        AUTO_HEADING_AND_AUTO_DEPTH_MODE = 9
        state = self._state_watcher.general_state
        if state["control_mode"] is AUTO_DEPTH_MODE or AUTO_HEADING_AND_AUTO_DEPTH_MODE:
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
            active (bool): Activate auto heading mode if active is true, de-activte if false

        *Returns*:
            active (int): Returns true if auto heading mode is active, false if it is not active
        """
        AUTO_HEADING_MODE = 7
        AUTO_HEADING_AND_AUTO_DEPTH_MODE = 9
        state = self._state_watcher.general_state
        if (
            state["control_mode"] is AUTO_HEADING_MODE
            or AUTO_HEADING_AND_AUTO_DEPTH_MODE
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

    def ping(self):
        """Ping drone, an exception is thrown by TcpClient if drone does not answer"""
        self._tcp_client.ping()


if __name__ == "__main__":
    pioneer = Pioneer()

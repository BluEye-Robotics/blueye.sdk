#!/usr/bin/env python3
import threading
from typing import Iterator, Tuple

from .camera import Camera
from blueye.protocol import TcpClient, UdpClient


class PioneerStateWatcher(threading.Thread):
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
        self._state_watcher = PioneerStateWatcher()
        self.camera = Camera(self._tcp_client, self._state_watcher)
        if autoConnect is True:
            self.connect()

    def connect(self):
        self._state_watcher.start()
        self.thruster_setpoint(0, 0, 0, 0)

    @property
    def lights(self) -> int:
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
        self._tcp_client.motion_input(surge, sway, heave, yaw, 0, 0)

    @property
    def auto_depth_active(self) -> bool:
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

#!/usr/bin/env python3
import threading
from typing import Iterator, Tuple

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


class Camera:
    def __init__(self, tcp_client, state_watcher):
        self._tcp_client = tcp_client
        self._state_watcher = state_watcher

    @property
    def is_recording(self) -> bool:
        state = self._state_watcher.general_state
        if state["camera_record_time"] != -1:
            return True
        else:
            return False

    @is_recording.setter
    def is_recording(self, start_recording: bool):
        if start_recording:
            self._tcp_client.start_recording()
        else:
            self._tcpc_lient.stop_recording()

    @property
    def exposure(self) -> int:
        camera_parameters = self._tcp_client.get_camera_parameters()
        exposure = camera_parameters[2]
        return exposure

    @exposure.setter
    def exposure(self, exposure: int):
        self._tcp_client.set_camera_exposure(exposure)

    @property
    def whitebalance(self) -> int:
        camera_parameters = self._tcp_client.get_camera_parameters()
        whitebalance = camera_parameters[3]
        return whitebalance

    @whitebalance.setter
    def whitebalance(self, whitebalance: int):
        self._tcp_client.set_camera_whitebalance(whitebalance)

    @property
    def hue(self) -> int:
        camera_parameters = self._tcp_client.get_camera_parameters()
        hue = camera_parameters[4]
        return hue

    @hue.setter
    def hue(self, hue: int):
        self._tcp_client.set_camera_hue(hue)

    @property
    def resolution(self) -> int:
        camera_parameters = self._tcp_client.get_camera_parameters()
        resolution = camera_parameters[5]
        return resolution

    @resolution.setter
    def resolution(self, resolution: int):
        self._tcp_client.set_camera_resolution(resolution)


class Pioneer:
    """A class providing a interface to the Blueye pioneer's basic functions

    Example of basic usage:
    >>> from blueye.sdk import Pioneer
    >>> from time import sleep
    >>> p = Pioneer()
    >>> p.lights = 10
    >>> sleep(3)
    >>> print(f"The current light intensity is: {p.lights}")
    >>> p.lights = 0
    """

    def __init__(self, ip="192.168.1.101", tcpPort=2011, autoConnect=True):
        self._ip = ip
        self._tcp_client = TcpClient(ip=ip, port=tcpPort, autoConnect=autoConnect)
        self._state_watcher = PioneerStateWatcher()
        self.camera = Camera(self._tcp_client, self._state_watcher)
        if autoConnect is True:
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

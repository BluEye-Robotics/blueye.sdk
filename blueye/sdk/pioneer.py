#!/usr/bin/env python3
import pprint
import threading
from typing import Iterator, Tuple

import cv2

from blueye.protocol import TcpClient, UdpClient
from blueye.sdk.diagnostics import get_diagnostic_data
from blueye.sdk.video import get_image, save_image


class PioneerStateWatcher(threading.Thread):
    """
    Subscribes to UDP messages from the drone and stores the latest data
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self.general_state = None
        self.calibration_state = None
        self._udpclient = UdpClient()
        self._stop_thread = False

    def run(self):
        while self._stop_thread is not True:
            data_packet = self._udpclient.get_data_dict()
            if data_packet["command_type"] == 1:
                self.general_state = data_packet
            elif data_packet["command_type"] == 2:
                self.calibration_state = data_packet


class Pioneer:
    def __init__(self, ip="192.168.1.101", tcpPort=2011, autoConnect=True):
        self._ip = ip
        self._tcpclient = TcpClient(
            ip=ip, port=tcpPort, autoConnect=autoConnect)
        self._stateWatcher = PioneerStateWatcher()
        if autoConnect is True:
            self._stateWatcher.start()

    @property
    def lights(self) -> (int, int):
        state = self._stateWatcher.general_state
        return (state["lights_upper"], state["lights_lower"])

    @lights.setter
    def lights(self, upper_lower_iterator: Iterator[Tuple[int, int]]):
        try:
            upper, lower = upper_lower_iterator
        except (TypeError, ValueError) as e:
            raise TypeError("Lights require a tuple with two values") from e
        try:
            self._tcpclient.set_lights(upper, lower)
        except ValueError as e:
            raise ValueError("Error occured while trying to set lights to"
                             f"({upper},{lower})") from e

    @property
    def depth(self):
        return self._pioneer_state["depth"]

    @property
    def drone_info(self):
        return get_diagnostic_data(self._ip, "drone_info")

    def print_drone_info(self):
        pprint.pprint(self.drone_info)

    def get_image(self):
        get_image(ip=self._ip)

    def save_image(self, filename):
        save_image(ip=self._ip, filename=filename)


if __name__ == "__main__":
    pioneer = Pioneer()
    pioneer.print_drone_info()
    pioneer.save_image("test.png")
    print(pioneer.depth)
    pioneer.show_video()

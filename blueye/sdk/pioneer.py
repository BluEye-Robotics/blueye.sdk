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


if __name__ == "__main__":
    pioneer = Pioneer()

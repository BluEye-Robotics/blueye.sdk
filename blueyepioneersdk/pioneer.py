#!/usr/bin/env python3
import cv2
import pprint
# import threading

from blueyepioneersdk.diagnostics import get_diagnostic_data
from blueyepioneersdk.video import get_image, save_image
from p2_app_protocol import UdpClient


class Pioneer:
    def __init__(self, ip="192.168.1.101"):
        self._ip = ip
        # self._cached_pioneer_state = None
        # self._pioneer_state_event = threading.Event()
        self._udpclient = UdpClient()

    @property
    def _pioneer_state(self):
        # self._pioneer_state_event.wait()
        # return self._cached_pioneer_state
        return self._udpclient.get_data_dict()

    # def _update_pineer_state(self, state):
    #    self._last_pioneer_state = state
    #    self._pioneer_state_event.set()

    def set_lights(self):
        pass

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

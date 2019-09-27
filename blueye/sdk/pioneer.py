#!/usr/bin/env python3
import threading
import time
import warnings
from typing import Iterator, Tuple

from blueye.protocol import TcpClient, UdpClient
from blueye.protocol.exceptions import ResponseTimeout

from .camera import Camera
from .motion import Motion


class _PioneerStateWatcher(threading.Thread):
    """Subscribes to UDP messages from the drone and stores the latest data
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self._general_state = None
        self._calibration_state = None
        self._udpclient = UdpClient()
        self._exit_flag = threading.Event()
        self.daemon = True

    @property
    def general_state(self) -> dict:
        start = time.time()
        while self._general_state is None:
            if time.time() - start > 3:
                raise TimeoutError("No state message received from drone")
        return self._general_state

    @property
    def calibration_state(self) -> dict:
        start = time.time()
        while self._calibration_state is None:
            if time.time() - start > 3:
                raise TimeoutError("No state message received from drone")
        return self._calibration_state

    def run(self):
        while not self._exit_flag.is_set():
            data_packet = self._udpclient.get_data_dict()
            if data_packet["command_type"] == 1:
                self._general_state = data_packet
            elif data_packet["command_type"] == 2:
                self._calibration_state = data_packet

    def stop(self):
        self._exit_flag.set()


class SlaveModeWarning(UserWarning):
    """Raised when trying to perform action not possible in slave mode"""


class slaveTcpClient:
    """A dummy TCP client that warns you if you use any of its functions"""

    def __getattr__(self, name):
        def method(*args):
            warnings.warn(
                f"Unable to call {name}{args} with client in slave mode",
                SlaveModeWarning,
                stacklevel=2,
            )

        return method


class Pioneer:
    """A class providing a interface to the Blueye pioneer's basic functions

    Automatically connects to the drone using the default ip and port when instantiated, this
    behaviour can be disabled by setting `autoConnect=False`.

    The drone only supports one client controlling it at a time, but if you pass
    `slaveModeEnabled=True` you will still be able to receive data from the drone.
    """

    def __init__(
        self, ip="192.168.1.101", tcpPort=2011, autoConnect=True, slaveModeEnabled=False
    ):
        self._ip = ip
        self._slaveModeEnabled = slaveModeEnabled
        if slaveModeEnabled:
            self._tcp_client = slaveTcpClient()
        else:
            self._tcp_client = TcpClient(ip=ip, port=tcpPort, autoConnect=autoConnect)
        self._state_watcher = _PioneerStateWatcher()
        self.camera = Camera(self._tcp_client, self._state_watcher)
        self.motion = Motion(self._tcp_client, self._state_watcher)

        if autoConnect is True:
            self.connect()

    def connect(self):
        """Start receiving telemetry info from the drone, and publishing watchdog messages

        When watchdog message are published the thrusters are armed, to stop the drone from moving
        unexpectedly when connecting all thruster set points are set to zero when connecting.
        """
        self._state_watcher.start()
        if self._slaveModeEnabled is False:
            if self._tcp_client._sock is None and not self._tcp_client.isAlive():
                self._tcp_client.connect()
                self._tcp_client.start()
            try:
                # Ensure that we are able to communicate with the drone
                self.ping()
            except ResponseTimeout as e:
                raise ConnectionError(
                    f"Found drone at {self._tcp_client._ip}:{self._tcp_client._port}, "
                    "but was unable to establish communication with it. "
                    "Is there another client connected?"
                ) from e
            self.motion.update_setpoint()

    @property
    def lights(self) -> int:
        """Get or set the brightness of the pioneers bottom canister lights

        *Arguments*:

        * brightness (int): Set the brightness of the bottom canister LED's in the range <0, 255>

        *Returns*:

        * brightness (int): The brightness of the bottom canister LED's in the range <0, 255>
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

    @property
    def depth(self) -> int:
        """Get the current depth in millimeters

        *Returns*:

        * depth (int): The depth in millimeters of water column.
        """

        return self._state_watcher.general_state["depth"]

    @property
    def pose(self) -> dict:
        """Get the current orientation of the drone

        *Returns*:

        * pose (dict): Dictionary with roll, pitch, and yaw in degrees, from 0 to 359.
        """
        pose = {
            "roll": (self._state_watcher.general_state["roll"] + 360) % 360,
            "pitch": (self._state_watcher.general_state["pitch"] + 360) % 360,
            "yaw": (self._state_watcher.general_state["yaw"] + 360) % 360,
        }
        return pose

    def ping(self):
        """Ping drone, an exception is thrown by TcpClient if drone does not answer"""
        self._tcp_client.ping()

#!/usr/bin/env python3
import socket
import threading
import time
import warnings
from json import JSONDecodeError

import requests
from blueye.protocol import TcpClient, UdpClient
from blueye.protocol.exceptions import MismatchedReply, NoConnectionToDrone, ResponseTimeout
from packaging import version

from .camera import Camera
from .constants import WaterDensities
from .logs import Logs
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


class _SlaveTcpClient:
    """A dummy TCP client that warns you if you use any of its functions"""

    def __getattr__(self, name):
        def method(*args):
            warnings.warn(
                f"Unable to call {name}{args} with client in slave mode",
                SlaveModeWarning,
                stacklevel=2,
            )

        return method


class _NoConnectionTcpClient:
    """A TCP client that raises a ConnectionError if you use any of its functions"""

    def __getattr__(self, name):
        def method(*args, **kwargs):
            raise ConnectionError(
                "The connection to the drone is not established, "
                "try calling the connect method before retrying"
            )

        return method


class Config:
    def __init__(self, parent_drone: "Pioneer"):
        self._parent_drone = parent_drone
        self._water_density = WaterDensities.salty

    @property
    def water_density(self):
        """Get or set the current water density for increased pressure sensor accuracy

        Setting the water density is only supported on drones with software version 1.5 or higher.
        Older software versions will assume a water density of 1025 grams per liter.

        The WaterDensities class contains typical densities for salty-, brackish-, and fresh water
        (these are the same values that the Blueye app uses).
        """
        return self._water_density

    @water_density.setter
    def water_density(self, density: int):
        if version.parse(self._parent_drone.software_version_short) < version.parse("1.5"):
            raise RuntimeError(
                "Drone software version is too old. Setting water density requires version 1.5"
                " or higher."
            )
        self._water_density = density
        self._parent_drone._tcp_client.set_water_density(density)

    def set_drone_time(self, time: int):
        """Set the system for the drone

        This method is used to set the system time for the drone. The argument `time` is expected to
        be a Unix timestamp (ie. the number of seconds since the epoch).
        """
        self._parent_drone._tcp_client.set_system_time(time)


class Pioneer:
    """A class providing a interface to the Blueye pioneer's basic functions

    Automatically connects to the drone using the default ip and port when instantiated, this
    behaviour can be disabled by setting `autoConnect=False`.

    The drone only supports one client controlling it at a time, but if you pass
    `slaveModeEnabled=True` you will still be able to receive data from the drone.
    """

    def __init__(self, ip="192.168.1.101", tcpPort=2011, autoConnect=True, slaveModeEnabled=False):
        self._ip = ip
        self._port = tcpPort
        self._slaveModeEnabled = slaveModeEnabled
        if slaveModeEnabled:
            self._tcp_client = _SlaveTcpClient()
        else:
            self._tcp_client = _NoConnectionTcpClient()
        self._state_watcher = _PioneerStateWatcher()
        self.camera = Camera(self)
        self.motion = Motion(self)
        self.logs = Logs(self)
        self.config = Config(self)

        if autoConnect is True:
            self.connect(timeout=3)

    @property
    def connection_established(self):
        if isinstance(self._tcp_client, _NoConnectionTcpClient):
            return False
        else:
            return True

    def _update_drone_info(self):
        """Request and store information about the connected drone"""
        try:
            response = requests.get(f"http://{self._ip}/diagnostics/drone_info", timeout=3).json()
        except (
            requests.ConnectTimeout,
            requests.ReadTimeout,
            requests.ConnectionError,
            JSONDecodeError,
        ):
            raise ConnectionError("Could not establish connection with drone")
        try:
            self.features = list(filter(None, response["features"].split(",")))
        except KeyError:
            # Drone versions older than 1.4.7 did not have this field.
            self.features = []
        self.software_version = response["sw_version"]
        self.software_version_short = self.software_version.split("-")[0]
        self.serial_number = response["serial_number"]
        self.uuid = response["hardware_id"]

    @staticmethod
    def _wait_for_udp_communication(timeout: int):
        """Simple helper for waiting for drone to come online

        Raises ConnectionError if no connection is established in the specified timeout.
        """
        temp_udp_client = UdpClient()
        temp_udp_client._sock.settimeout(timeout)
        try:
            temp_udp_client.get_data_dict()
        except socket.timeout as e:
            raise ConnectionError("Could not establish connection with drone") from e

    def _connect_to_tcp_socket(self):
        try:
            self._tcp_client.connect()
        except NoConnectionToDrone:
            raise ConnectionError("Could not establish connection with drone")

    def _start_watchdog(self):
        """Starts the thread for petting the watchdog

        _connect_to_tcp_socket() must be called first"""
        try:
            self._tcp_client.start()
        except RuntimeError:
            # Ignore multiple starts
            pass

    def _clean_up_tcp_client(self):
        """Stops the watchdog thread and closes the TCP socket"""
        self._tcp_client.stop()
        self._tcp_client._sock.close()
        self._tcp_client = _NoConnectionTcpClient()

    def _start_state_watcher_thread(self):
        try:
            self._state_watcher.start()
        except RuntimeError:
            # Ignore multiple starts
            pass

    def connect(self, timeout=None):
        """Start receiving telemetry info from the drone, and publishing watchdog messages

        When watchdog message are published the thrusters are armed, to stop the drone from moving
        unexpectedly when connecting all thruster set points are set to zero when connecting.
        """
        self._wait_for_udp_communication(timeout)
        self._update_drone_info()
        self._start_state_watcher_thread()
        if self._slaveModeEnabled:
            # No need to touch the TCP stuff if we're in slave mode so we return early
            return

        if not self.connection_established:
            self._tcp_client = TcpClient(ip=self._ip, port=self._port, autoConnect=False)
            self._connect_to_tcp_socket()

        try:
            self.ping()
            self.motion.send_thruster_setpoint(0, 0, 0, 0)

            # The drone runs from a read-only filesystem, and as such does not keep any state,
            # therefore when we connect to it we should send the current time
            self.config.set_drone_time(int(time.time()))

            self._start_watchdog()
        except ResponseTimeout as e:
            self._clean_up_tcp_client()
            raise ConnectionError(
                f"Found drone at {self._ip} but was unable to take control of it. "
                "Is there another client connected?"
            ) from e
        except MismatchedReply:
            # The connection is out of sync, likely due to a previous connection being
            # disconnected mid-transfer. Re-instantiating the connection should solve the issue
            self._clean_up_tcp_client()
            self.connect(timeout)
        except BrokenPipeError:
            # Have lost connection to drone, need to reestablish TCP client
            self._clean_up_tcp_client()
            self.connect(timeout)

    def disconnect(self):
        """Disconnects the TCP connection, allowing another client to take control of the drone"""
        if self.connection_established and not self._slaveModeEnabled:
            self._clean_up_tcp_client()

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
            raise ValueError("Error occured while trying to set lights to: " f"{brightness}") from e

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

    @property
    def battery_state_of_charge(self) -> int:
        """Get the battery state of charge

        *Returns*:

        * state_of_charge (int): Current state of charge of the drone battery in percent, from 0 to 100
        """
        return self._state_watcher.general_state["battery_state_of_charge_rel"]

    def ping(self):
        """Ping drone, an exception is thrown by TcpClient if drone does not answer"""
        self._tcp_client.ping()

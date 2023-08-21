#!/usr/bin/env python3
from __future__ import annotations

import logging
import time
from datetime import datetime
from json import JSONDecodeError
from typing import Callable, Dict, List, Optional

import blueye.protocol
import proto
import requests
from packaging import version

from .battery import Battery
from .camera import Camera
from .connection import CtrlClient, ReqRepClient, TelemetryClient, WatchdogPublisher
from .constants import WaterDensities
from .guestport import Peripheral, device_to_peripheral
from .logs import LegacyLogs, Logs
from .motion import Motion

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, parent_drone: "Drone"):
        self._parent_drone = parent_drone
        self._water_density = WaterDensities.salty

    @property
    def water_density(self):
        """Get or set the current water density for increased pressure sensor accuracy

        Older software versions will assume a water density of 1.025 kilograms per liter.

        The WaterDensities class contains typical densities for salty-, brackish-, and fresh water
        (these are the same values that the Blueye app uses).
        """
        return self._water_density

    @water_density.setter
    def water_density(self, density: float):
        self._water_density = density
        self._parent_drone._ctrl_client.set_water_density(density)

    def set_drone_time(self, time: int):
        """Set the system for the drone

        This method is used to set the system time for the drone. The argument `time` is expected to
        be a Unix timestamp (ie. the number of seconds since the epoch).
        """
        self._parent_drone._req_rep_client.sync_time(time)


class _NoConnectionClient:
    """A client that raises a ConnectionError if you use any of its functions"""

    def __getattr__(self, name):
        def method(*args, **kwargs):
            raise ConnectionError(
                "The connection to the drone is not established, "
                "try calling the connect method before retrying"
            )

        return method


class Telemetry:
    def __init__(self, parent_drone: "Drone"):
        self._parent_drone = parent_drone

    def set_msg_publish_frequency(self, msg: proto.message.Message, frequency: float):
        """Set the publishing frequency of a specific telemetry message

        Raises a RuntimeError if the drone fails to set the frequency. Possible causes could be a
        frequency outside the valid range, or an incorrect message type.

        *Arguments*:

        * msg (proto.message.Message): The message to set the frequency of. Needs to be one of the
                                       messages in blueye.protocol that end in Tel, eg.
                                       blueye.protocol.DepthTel
        * frequency (float): The frequency in Hz. Valid range is (0 .. 100).

        """
        resp = self._parent_drone._req_rep_client.set_telemetry_msg_publish_frequency(
            msg, frequency
        )
        if not resp.success:
            raise RuntimeError("Could not set telemetry message frequency")

    def add_msg_callback(
        self,
        msg_filter: List[proto.message.Message],
        callback: Callable[[str, proto.message.Message], None],
        raw: bool = False,
        **kwargs,
    ) -> str:
        """Register a telemetry message callback

        The callback is called each time a message of the type is received

        *Arguments*:

        * msg_filter: A list of message types to register the callback for.
                      Eg. `[blueye.protocol.DepthTel, blueye.protocol.Imu1Tel]`. If the list is
                      empty the callback will be registered for all message types
        * callback: The callback function. It should be minimal and return as fast as possible to
                    not block the telemetry communication. It is called with two arguments, the
                    message type name and the message object
        * raw: Pass the raw data instead of the deserialized message to the callback function
        * kwargs: Additional keyword arguments to pass to the callback function

        *Returns*:

        * uuid: Callback id. Can be used to remove callback in the future
        """
        uuid_hex = self._parent_drone._telemetry_watcher.add_callback(
            msg_filter, callback, raw, **kwargs
        )
        return uuid_hex

    def remove_msg_callback(self, callback_id: str) -> Optional[str]:
        """Remove a telemetry message callback

        *Arguments*:

        * callback_id: The callback id

        """
        self._parent_drone._telemetry_watcher.remove_callback(callback_id)

    def get(
        self, msg_type: proto.message.Message, deserialize=True
    ) -> Optional[proto.message.Message | bytes]:
        """Get the latest telemetry message of the specified type

        *Arguments*:


        * msg_type: The message type to get. Eg. blueye.protocol.DepthTel
        * deserialize: If True, the message will be deserialized before being returned. If False,
                       the raw bytes will be returned.

        *Returns*:

        * The latest message of the specified type, or None if no message has been received yet

        """
        try:
            msg = self._parent_drone._telemetry_watcher.get(msg_type)
        except KeyError:
            return None
        if deserialize:
            return msg_type.deserialize(msg)
        else:
            return msg


class Drone:
    """A class providing an interface to a Blueye drone's functions

    Automatically connects to the drone using the default ip when instantiated, this behaviour can
    be disabled by setting `auto_connect=False`.
    """

    def __init__(
        self,
        ip="192.168.1.101",
        auto_connect=True,
        timeout=3,
        disconnect_other_clients=False,
    ):
        self._ip = ip
        self.camera = Camera(self, is_guestport_camera=False)
        self.motion = Motion(self)
        self.logs = Logs(self)
        self.legacy_logs = LegacyLogs(self)
        self.config = Config(self)
        self.battery = Battery(self)
        self.telemetry = Telemetry(self)
        self.connected = False
        self.client_id: int = None
        self.in_control: bool = False
        self._watchdog_publisher = _NoConnectionClient()
        self._telemetry_watcher = _NoConnectionClient()
        self._req_rep_client = _NoConnectionClient()
        self._ctrl_client = _NoConnectionClient()

        self.peripherals: Optional[List[Peripheral]] = None
        """This list holds the peripherals connected to the drone. If it is `None`, then no
        Guestport telemetry message has been recieved yet."""

        if auto_connect is True:
            self.connect(timeout=timeout, disconnect_other_clients=disconnect_other_clients)

    def _verify_required_blunux_version(self, requirement: str):
        """Verify that Blunux version is higher than requirement

        requirement needs to be a string that's able to be parsed by version.parse()

        Raises a RuntimeError if the Blunux version of the connected drone does not match or exceed
        the requirement.
        """
        if version.parse(self.software_version_short) < version.parse(requirement):
            raise RuntimeError(
                f"Blunux version of connected drone is {self.software_version_short}. Version "
                f"{requirement} or higher is required."
            )

    def _update_drone_info(self, timeout: float = 3):
        """Request and store information about the connected drone"""
        try:
            response = requests.get(
                f"http://{self._ip}/diagnostics/drone_info", timeout=timeout
            ).json()
        except (
            requests.ConnectTimeout,
            requests.ReadTimeout,
            requests.ConnectionError,
            JSONDecodeError,
        ) as e:
            raise ConnectionError("Could not establish connection with drone") from e
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
    def _drone_info_callback(msg_type: str, msg: blueye.protocol.DroneInfoTel, drone: Drone):
        # Check if the GuestPortInfo has been initialized
        if msg.drone_info.gp._pb.ByteSize() != 0:
            drone._create_peripherals_from_drone_info(msg.drone_info.gp)

        # Remove the callback after the first message has been received
        drone.telemetry.remove_msg_callback(drone._drone_info_cb_id)

    def _create_peripherals_from_drone_info(self, gp_info: blueye.protocol.GuestPortInfo):
        self.peripherals = []
        for port in (gp_info.gp1, gp_info.gp2, gp_info.gp3):
            for device in port.device_list.devices:
                self.peripherals.append(device_to_peripheral(self, port.guest_port_number, device))

    def connect(
        self,
        client_info: blueye.protocol.ClientInfo = None,
        timeout: float = 4,
        disconnect_other_clients: bool = False,
    ):
        """Establish a connection to the drone

        Spawns of several threads for receiving telemetry, sending control messages and publishing
        watchdog messages.

        When a watchdog message is receieved by the drone the thrusters are armed, so to stop the
        drone from moving unexpectedly when connecting all thruster set points are set to zero when
        connecting.

        ** Arguments **
        - *client_info*: Information about the client connecting, if None the SDK will attempt to
                         read it from the environment
        - *timeout*: Seconds to wait for connection. The first connection on boot can be a little
                     slower than the following ones
        - *disconnect_other_clients*: If True, disconnect clients until drone reports that we are in
                                      control

        ** Raises **
        - *ConnectionError*: If the connection attempt fails
        - *RuntimeError*: If the Blunux version of the connected drone is too old
        """
        logger.info(f"Attempting to connect to drone at {self._ip}")
        self._update_drone_info(timeout=timeout)
        self._verify_required_blunux_version("3.2")

        self._telemetry_watcher = TelemetryClient(self)
        self._ctrl_client = CtrlClient(self)
        self._watchdog_publisher = WatchdogPublisher(self)
        self._req_rep_client = ReqRepClient(self)

        self._telemetry_watcher.start()
        self._req_rep_client.start()
        self._ctrl_client.start()
        self._watchdog_publisher.start()

        self.ping()
        connect_resp = self._req_rep_client.connect_client(client_info=client_info)
        logger.info(f"Connection successful, client id: {connect_resp.client_id}")
        logger.info(f"Client id in control: {connect_resp.client_id_in_control}")
        logger.info(f"There are {len(connect_resp.connected_clients)-1} other clients connected")
        self.client_id = connect_resp.client_id
        self.in_control = connect_resp.client_id == connect_resp.client_id_in_control
        self.connected = True
        if disconnect_other_clients and not self.in_control:
            self.take_control()
        self._drone_info_cb_id = self.telemetry.add_msg_callback(
            [blueye.protocol.DroneInfoTel],
            Drone._drone_info_callback,
            False,
            drone=self,
        )

        if self.in_control:
            # The drone runs from a read-only filesystem, and as such does not keep any state,
            # therefore when we connect to it we should send the current time
            current_time = int(time.time())
            time_formatted = datetime.fromtimestamp(current_time).strftime("%d. %b %Y %H:%M")
            logger.debug(f"Setting current time to {current_time} ({time_formatted})")
            self.config.set_drone_time(current_time)
            logger.debug(f"Disabling thrusters")
            self.motion.send_thruster_setpoint(0, 0, 0, 0)

    def disconnect(self):
        """Disconnects the connection, allowing another client to take control of the drone"""
        try:
            self._req_rep_client.disconnect_client(self.client_id)
        except blueye.protocol.exceptions.ResponseTimeout:
            # If there's no response the connection is likely already closed, so we can just
            # continue to stop threads and disconnect
            pass
        self._watchdog_publisher.stop()
        self._telemetry_watcher.stop()
        self._req_rep_client.stop()
        self._ctrl_client.stop()

        self._watchdog_publisher = _NoConnectionClient()
        self._telemetry_watcher = _NoConnectionClient()
        self._req_rep_client = _NoConnectionClient()
        self._ctrl_client = _NoConnectionClient()

        self.connected = False

    @property
    def connected_clients(self) -> Optional[List[blueye.protocol.ConnectedClient]]:
        """Get a list of connected clients"""
        clients_tel = self.telemetry.get(blueye.protocol.ConnectedClientsTel)
        if clients_tel is None:
            return None
        else:
            return list(clients_tel.connected_clients)

    @property
    def client_in_control(self) -> Optional[int]:
        """Get the client id of the client in control of the drone"""
        clients_tel = self.telemetry.get(blueye.protocol.ConnectedClientsTel)
        if clients_tel is None:
            return None
        else:
            return clients_tel.client_id_in_control

    def take_control(self, timeout=1):
        """Take control of the drone, disconnecting other clients

        Will disconnect other clients until the client is in control of the drone.
        Raises a RuntimeError if the client could not take control of the drone in the given time.
        """
        start_time = time.time()
        client_in_control = self.client_in_control
        while self.client_id != client_in_control:
            if time.time() - start_time > timeout:
                raise RuntimeError("Could not take control of the drone in the given time")
            resp = self._req_rep_client.disconnect_client(client_in_control)
            client_in_control = resp.client_id_in_control
        self.in_control = True

    @property
    def lights(self) -> Optional[float]:
        """Get or set the intensity of the drone lights

        *Arguments*:

        * brightness (float): Set the intensity of the drone light (0..1)

        *Returns*:

        * brightness (float): The intensity of the drone light (0..1)
        """
        return self.telemetry.get(blueye.protocol.LightsTel).lights.value

    @lights.setter
    def lights(self, brightness: float):
        if not 0 <= brightness <= 1:
            raise ValueError("Error occured while trying to set lights to: " f"{brightness}")
        self._ctrl_client.set_lights(brightness)

    @property
    def depth(self) -> Optional[float]:
        """Get the current depth in meters

        *Returns*:

        * depth (float): The depth in meters of water column.
        """
        depth_tel = self.telemetry.get(blueye.protocol.DepthTel)
        if depth_tel is None:
            return None
        else:
            return depth_tel.depth.value

    @property
    def pose(self) -> Optional[dict]:
        """Get the current orientation of the drone

        *Returns*:

        * pose (dict): Dictionary with roll, pitch, and yaw in degrees, from 0 to 359.
        """
        attitude_tel = self.telemetry.get(blueye.protocol.AttitudeTel)
        if attitude_tel is None:
            return None
        attitude = attitude_tel.attitude
        pose = {
            "roll": (attitude.roll + 360) % 360,
            "pitch": (attitude.pitch + 360) % 360,
            "yaw": (attitude.yaw + 360) % 360,
        }
        return pose

    @property
    def error_flags(self) -> Optional[Dict[str, bool]]:
        """Get the error flags

        *Returns*:

        * error_flags (dict): The error flags as bools in a dictionary
        """
        error_flags_tel = self.telemetry.get(blueye.protocol.ErrorFlagsTel)
        if error_flags_tel is None:
            return None
        error_flags_msg = error_flags_tel.error_flags
        error_flags = {}
        possible_flags = [attr for attr in dir(error_flags_msg) if not attr.startswith("__")]
        for flag in possible_flags:
            error_flags[flag] = getattr(error_flags_msg, flag)
        return error_flags

    @property
    def active_video_streams(self) -> Optional[Dict[str, int]]:
        """Get the number of currently active connections to the video stream

        Every client connected to the RTSP stream (does not matter if it's directly from GStreamer,
        or from the Blueye app) counts as one connection.

        """
        n_streamers_msg_tel = self.telemetry.get(blueye.protocol.NStreamersTel)
        if n_streamers_msg_tel is None:
            return None
        n_streamers_msg = n_streamers_msg_tel.n_streamers
        return {"main": n_streamers_msg.main, "guestport": n_streamers_msg.guestport}

    def ping(self, timeout: float = 1.0):
        """Ping drone

        Raises a ResponseTimeout exception if the drone does not respond within the timeout period.
        """
        self._req_rep_client.ping(timeout)

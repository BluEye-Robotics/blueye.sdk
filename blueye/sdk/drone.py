#!/usr/bin/env python3
import socket
import threading
import time
import warnings
from json import JSONDecodeError
from typing import Dict

import blueye.protocol
import requests
from packaging import version

from .camera import Camera
from .connection import CtrlClient, ReqRepClient, TelemetryClient, WatchdogPublisher
from .constants import WaterDensities
from .logs import Logs
from .motion import Motion


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


class Drone:
    """A class providing an interface to a Blueye drone's functions

    Automatically connects to the drone using the default ip when instantiated, this behaviour can
    be disabled by setting `autoConnect=False`.
    """

    def __init__(
        self,
        ip="192.168.1.101",
        autoConnect=True,
        timeout=3,
    ):
        self._ip = ip
        self.camera = Camera(self, is_guestport_camera=False)
        self.motion = Motion(self)
        self.logs = Logs(self)
        self.config = Config(self)
        self.connected = False
        self.client_id: int = None
        self.in_control: bool = False
        if autoConnect is True:
            self.connect(timeout=timeout)

    def _verify_required_blunux_version(self, requirement: str):
        """Verify that Blunux version is higher than requirement

        requirement needs to be a string that's able to be parsed by version.parse()

        Raises a RuntimeError if the Blunux version of the connected drone does not match or exceed
        the requirement.
        """

        if not self.connected:
            raise ConnectionError(
                "The connection to the drone is not established, try calling the connect method "
                "before retrying"
            )
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

    def connect(self, client_info: blueye.protocol.ClientInfo = None, timeout: float = 3):
        """Start receiving telemetry info from the drone, and publishing watchdog messages

        When watchdog message are published the thrusters are armed, to stop the drone from moving
        unexpectedly when connecting all thruster set points are set to zero when connecting.

        - *timeout* (float): Seconds to wait for connection
        """
        # TODO: Deal with exceptions
        self._update_drone_info(timeout=timeout)

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
        self.client_id = connect_resp.client_id
        self.in_control = connect_resp.client_id == connect_resp.client_id_in_control
        self.connected = True
        if self.in_control:
            # The drone runs from a read-only filesystem, and as such does not keep any state,
            # therefore when we connect to it we should send the current time
            self.config.set_drone_time(int(time.time()))
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

        self._watchdog_publisher = None
        self._telemetry_watcher = None
        self._req_rep_client = None
        self._ctrl_client = None

        self.connected = False

    @property
    def connected_clients(self) -> List[blueye.protocol.ConnectedClient]:
        """Get a list of connected clients"""
        tel_msg = blueye.protocol.ConnectedClientsTel.deserialize(
            self._telemetry_watcher.state["blueye.protocol.ConnectedClientsTel"]
        )
        return list(tel_msg.connected_clients)

    @property
    def lights(self) -> float:
        """Get or set the intensity of the drone lights

        *Arguments*:

        * brightness (float): Set the intensity of the drone light (0..1)

        *Returns*:

        * brightness (float): The intensity of the drone light (0..1)
        """
        lights_msg = self._telemetry_watcher.state["blueye.protocol.LightsTel"]
        value = blueye.protocol.LightsTel.deserialize(lights_msg).lights.value
        return value

    @lights.setter
    def lights(self, brightness: float):
        if not 0 <= brightness <= 1:
            raise ValueError("Error occured while trying to set lights to: " f"{brightness}")
        self._ctrl_client.set_lights(brightness)

    @property
    def depth(self) -> float:
        """Get the current depth in meters

        *Returns*:

        * depth (float): The depth in meters of water column.
        """
        depthTel = self._telemetry_watcher.state["blueye.protocol.DepthTel"]
        depthTel_msg = blueye.protocol.DepthTel.deserialize(depthTel)
        return depthTel_msg.depth.value

    @property
    def pose(self) -> dict:
        """Get the current orientation of the drone

        *Returns*:

        * pose (dict): Dictionary with roll, pitch, and yaw in degrees, from 0 to 359.
        """
        attitude_msg = self._telemetry_watcher.state["blueye.protocol.AttitudeTel"]
        attitude = blueye.protocol.AttitudeTel.deserialize(attitude_msg).attitude
        pose = {
            "roll": (attitude.roll + 360) % 360,
            "pitch": (attitude.pitch + 360) % 360,
            "yaw": (attitude.yaw + 360) % 360,
        }
        return pose

    @property
    def battery_state_of_charge(self) -> float:
        """Get the battery state of charge

        *Returns*:

        * State of charge (float): Current state of charge of the drone battery (0..1)
        """
        batteryTel = self._telemetry_watcher.state["blueye.protocol.BatteryTel"]
        batteryTel_msg = blueye.protocol.BatteryTel.deserialize(batteryTel)
        return batteryTel_msg.battery.level

    @property
    def error_flags(self) -> Dict[str, bool]:
        """Get the error flags

        *Returns*:

        * error_flags (dict): The error flags as bools in a dictionary
        """
        error_flags_tel = self._telemetry_watcher.state["blueye.protocol.ErrorFlagsTel"]
        error_flags_msg: blueye.protocol.ErrorFlags = blueye.protocol.ErrorFlagsTel.deserialize(
            error_flags_tel
        ).error_flags

        error_flags = {}
        possible_flags = [attr for attr in dir(error_flags_msg) if not attr.startswith("__")]
        for flag in possible_flags:
            error_flags[flag] = getattr(error_flags_msg, flag)
        return error_flags

    @property
    def active_video_streams(self) -> Dict[str, int]:
        """Get the number of currently active connections to the video stream

        Every client connected to the RTSP stream (does not matter if it's directly from GStreamer,
        or from the Blueye app) counts as one connection.

        """
        NStreamersTel = self._telemetry_watcher.state["blueye.protocol.NStreamersTel"]
        n_streamers_msg = blueye.protocol.NStreamersTel.deserialize(NStreamersTel).n_streamers
        return {"main": n_streamers_msg.main, "guestport": n_streamers_msg.guestport}

    def ping(self, timeout: float = 1.0):
        """Ping drone

        Raises a ResponseTimeout exception if the drone does not respond within the timeout period.
        """
        self._req_rep_client.ping(timeout)

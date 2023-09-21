import logging
from typing import TYPE_CHECKING, Optional

import blueye.protocol as bp
from packaging import version

from .camera import Camera

if TYPE_CHECKING:
    from .drone import Drone

logger = logging.getLogger(__name__)


class Peripheral:
    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        self.parent_drone = parent_drone
        self.port_number: bp.GuestPortNumber = port_number
        self.name: str = device.name
        self.manufacturer: str = device.manufacturer
        self.serial_number: str = device.serial_number
        self.depth_rating: float = device.depth_rating
        self.required_blunux_version: str = device.required_blunux_version
        self.device_id: bp.GuestPortDeviceID = device.device_id
        if self.required_blunux_version != "":
            if version.parse(self.required_blunux_version) > version.parse(
                parent_drone.software_version_short
            ):
                logger.warning(
                    f"Peripheral {self.name} requires Blunux version "
                    f"{self.required_blunux_version}, but the drone is running "
                    f"{parent_drone.software_version_short}"
                )


class GuestPortCamera(Camera, Peripheral):
    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        Camera.__init__(self, parent_drone, is_guestport_camera=True)
        Peripheral.__init__(self, parent_drone, port_number, device)


class GuestPortLight(Peripheral):
    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        Peripheral.__init__(self, parent_drone, port_number, device)

    def set_intensity(self, intensity: float):
        self.parent_drone._ctrl_client.set_guest_port_lights(intensity)

    def get_intensity(self) -> Optional[float]:
        return self.parent_drone.telemetry.get(bp.GuestPortLightsTel).lights.value


class Gripper(Peripheral):
    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        Peripheral.__init__(self, parent_drone, port_number, device)
        self.grip_velocity = 0
        self.rotation_velocity = 0

    @property
    def grip_velocity(self) -> float:
        return self.grip_velocity

    @grip_velocity.setter
    def grip_velocity(self, value: float):
        self.grip_velocity = value
        self.parent_drone._ctrl_client.set_gripper_velocities(value, self.rotation_velocity)

    @property
    def rotation_velocity(self) -> float:
        return self.rotation_velocity

    @rotation_velocity.setter
    def rotation_velocity(self, value: float):
        self.rotation_velocity = value
        self.parent_drone._ctrl_client.set_gripper_velocities(self.grip_velocity, value)


def device_to_peripheral(
    parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
) -> Peripheral:
    logger.debug(f"Found a {device.name} at port {port_number}")
    if device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_CAM:
        peripheral = GuestPortCamera(parent_drone, port_number, device)
    elif (
        device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_LIGHT
        or device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_LIGHT_PAIR
        or device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUE_ROBOTICS_LUMEN
    ):
        peripheral = GuestPortLight(parent_drone, port_number, device)
    elif (
        device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUE_ROBOTICS_NEWTON
        or device.device_id
        == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUE_ROBOTICS_DETACHABLE_NEWTON
        or device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEPRINT_LAB_REACH_ALPHA
    ):
        peripheral = Gripper(parent_drone, port_number, device)
    else:
        peripheral = Peripheral(parent_drone, port_number, device)
    return peripheral

import logging
from typing import TYPE_CHECKING

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
        if self.required_blunux_version != "":
            if version.parse(self.required_blunux_version) > version.parse(
                parent_drone.software_version_short
            ):
                logger.warning(
                    f"Peripheral {self.name} requires Blunux version "
                    f"{self.required_blunux_version}, but the drone is running "
                    f"{parent_drone.software_version_short}"
                )


class GuestportCamera(Camera, Peripheral):
    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        Camera.__init__(self, parent_drone, is_guestport_camera=True)
        Peripheral.__init__(self, parent_drone, port_number, device)


def device_to_peripheral(
    parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
) -> Peripheral:
    logger.debug(f"Found a {device.name} at port {port_number}")
    if device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_CAM:
        peripheral = GuestportCamera(parent_drone, port_number, device)
    else:
        peripheral = Peripheral(parent_drone, port_number, device)
    return peripheral
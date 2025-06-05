import logging
from typing import TYPE_CHECKING, Optional

import blueye.protocol as bp
from packaging import version

from .camera import Camera

if TYPE_CHECKING:
    from .drone import Drone

logger = logging.getLogger(__name__)


class Peripheral:
    """
    Represents a peripheral device connected to a guest port on the Blueye drone.
    """

    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        """Initialize the Peripheral class.

        Args:
            parent_drone (Drone): The parent drone instance.
            port_number (bp.GuestPortNumber): The guest port number.
            device (bp.GuestPortDevice): The guest port device.
        """
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
    """
    Represents a camera connected to a guest port on the Blueye drone.
    """

    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        """Initialize the GuestPortCamera class.

        Args:
            parent_drone (Drone): The parent drone instance.
            port_number (bp.GuestPortNumber): The guest port number.
            device (bp.GuestPortDevice): The guest port device.
        """
        Camera.__init__(self, parent_drone, is_guestport_camera=True)
        Peripheral.__init__(self, parent_drone, port_number, device)


class GuestPortLight(Peripheral):
    """
    Represents a light connected to a guest port on the Blueye drone.
    """

    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        """Initialize the GuestPortLight class.

        Args:
            parent_drone (Drone): The parent drone instance.
            port_number (bp.GuestPortNumber): The guest port number.
            device (bp.GuestPortDevice): The guest port device.
        """
        Peripheral.__init__(self, parent_drone, port_number, device)

    def set_intensity(self, intensity: float):
        """Set the intensity of the guest port light.

        Args:
            intensity (float): The intensity of the light (0..1).
        """
        self.parent_drone._ctrl_client.set_guest_port_lights(intensity)

    def get_intensity(self) -> Optional[float]:
        """Get the intensity of the guest port light.

        Returns:
            The intensity of the light (0..1).
        """
        return self.parent_drone.telemetry.get(bp.GuestPortLightsTel).lights.value


class Gripper(Peripheral):
    """
    Represents a gripper connected to a guest port on the Blueye drone.
    """

    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        """Initialize the Gripper class.

        Args:
            parent_drone (Drone): The parent drone instance.
            port_number (bp.GuestPortNumber): The guest port number.
            device (bp.GuestPortDevice): The guest port device.
        """
        Peripheral.__init__(self, parent_drone, port_number, device)
        self._grip_velocity = 0
        self._rotation_velocity = 0

    @property
    def grip_velocity(self) -> float:
        """Get or set the current grip velocity of the Gripper.

        Args:
            value (float): The new grip velocity to set. Must be a float between -1.0 and 1.0.

        Returns:
            The current grip velocity of the Gripper.

        Raises:
            ValueError: If the grip velocity is not between -1.0 and 1.0.
        """
        return self._grip_velocity

    @grip_velocity.setter
    def grip_velocity(self, value: float):
        if value < -1.0 or value > 1.0:
            raise ValueError("Grip velocity must be between -1.0 and 1.0.")
        self._grip_velocity = value
        self.parent_drone._ctrl_client.set_gripper_velocities(
            self._grip_velocity, self._rotation_velocity
        )

    @property
    def rotation_velocity(self) -> float:
        """Get or set the current rotation velocity of the Gripper.

        Args:
            value (float): The new rotation velocity to set. Must be a float between -1.0 and 1.0.

        Returns:
            The current rotation velocity of the Gripper.

        Raises:
            ValueError: If the rotation velocity is not between -1.0 and 1.0.
        """
        return self._rotation_velocity

    @rotation_velocity.setter
    def rotation_velocity(self, value: float):
        if value < -1.0 or value > 1.0:
            raise ValueError("Rotation velocity must be between -1.0 and 1.0.")
        self._rotation_velocity = value
        self.parent_drone._ctrl_client.set_gripper_velocities(
            self._grip_velocity, self._rotation_velocity
        )


class Laser(Peripheral):
    """
    Represents a laser connected to a guest port on the Blueye drone.
    """

    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        """Initialize the Laser class.

        Args:
            parent_drone (Drone): The parent drone instance.
            port_number (bp.GuestPortNumber): The guest port number.
            device (bp.GuestPortDevice): The guest port device.
        """
        Peripheral.__init__(self, parent_drone, port_number, device)

    def set_intensity(self, intensity: float):
        """Set the intensity of the laser.

        If the laser does not support dimming but only on and off, a value of 0 turns the laser off,
        and any value above 0 turns the laser on.

        Args:
            intensity (float): The intensity of the laser (0..1).

        Raises:
            ValueError: If the intensity is not between 0 and 1.
        """
        if intensity < 0 or intensity > 1:
            raise ValueError("Laser intensity must be between 0 and 1.")
        self.parent_drone._ctrl_client.set_laser_intensity(intensity)

    def get_intensity(self) -> Optional[float]:
        """Get the current intensity of the laser.

        Returns:
            The current intensity of the laser.
        """
        telemetry_msg = self.parent_drone.telemetry.get(bp.LaserTel)
        if telemetry_msg is None:
            return None
        else:
            return telemetry_msg.laser.value


class SkidServo(Peripheral):
    """
    Represents the servo on the skid (typically used for multibeams)
    """

    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        """Initialize the SkidServo class.

        Args:
            parent_drone (Drone): The parent drone instance.
            port_number (bp.GuestPortNumber): The guest port number.
            device (bp.GuestPortDevice): The guest port device.
        """
        self.max_angle = 28
        self.min_angle = -28
        Peripheral.__init__(self, parent_drone, port_number, device)

    def set_angle(self, angle: float) -> None:
        """Set the angle of the skid servo.

        Args:
            angle (float): The angle to set for the servo (-28 to 28 degrees).

        Raises:
            ValueError: If the angle is not within the allowed range.
        """
        if angle < self.min_angle or angle > self.max_angle:
            raise ValueError(
                f"Angle must be between {self.min_angle} and {self.max_angle} degrees."
            )
        self.parent_drone._ctrl_client.set_multibeam_servo_angle(angle)

    def get_angle(self) -> float | None:
        """Get the current angle of the skid servo.

        Returns:
            The current angle of the skid servo in degrees. None if telemetry is not available.
        """
        telemetry_msg = self.parent_drone.telemetry.get(bp.MultibeamServoTel)
        if telemetry_msg is None:
            return None
        else:
            return telemetry_msg.servo.angle


def device_to_peripheral(
    parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
) -> Peripheral:
    """Convert a device to its corresponding peripheral class.

    Args:
        parent_drone (Drone): The parent drone instance.
        port_number (bp.GuestPortNumber): The guest port number.
        device (bp.GuestPortDevice): The guest port device.

    Returns:
        The corresponding peripheral class instance.
    """
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
    elif (
        device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_LASER_TOOLS_SEA_BEAM
        or device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_SPOT_X_LASER_SCALERS
    ):
        peripheral = Laser(parent_drone, port_number, device)
    elif device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_MULTIBEAM_SERVO:
        peripheral = SkidServo(parent_drone, port_number, device)
    else:
        peripheral = Peripheral(parent_drone, port_number, device)
    return peripheral

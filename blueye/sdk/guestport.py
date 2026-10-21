import logging
import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

import blueye.protocol as bp
from packaging import version

from .camera import Camera
from .utils import deprecated_property, describe_enum

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
        self._detach_status: bp.GuestPortDetachStatus = device.detach_status
        self.required_capabilities: List[bp.GuestPortCapability] = list(
            device.required_capabilities
        )
        """Interfaces the device requires from the port it is connected to."""
        self.compatible_guest_ports: List[bp.GuestPortNumber] = list(device.compatible_guest_ports)
        """Ports on this drone where the device is fully supported, as computed by the drone from
        the port capabilities and the device requirements."""
        if self.required_blunux_version != "":
            if version.parse(self.required_blunux_version) > version.parse(
                parent_drone.software_version_short
            ):
                logger.warning(
                    f"Peripheral {self.name} requires Blunux version "
                    f"{self.required_blunux_version}, but the drone is running "
                    f"{parent_drone.software_version_short}"
                )

    def get_detach_status(self) -> bp.GuestPortDetachStatus:
        """Get the current attach state of a detachable device.

        The state is read from the latest drone info telemetry so it follows the device being
        attached or detached during a session. If no newer telemetry is available, the state
        reported when the peripheral was discovered is returned.

        Returns:
            The detach status. `GUEST_PORT_DETACH_STATUS_UNSPECIFIED` for devices that cannot be
            detached.
        """
        drone_info_tel = self.parent_drone.telemetry.get(bp.DroneInfoTel)
        if drone_info_tel is not None:
            device = _find_device(drone_info_tel.drone_info.gp, self)
            if device is not None:
                return device.detach_status
        return self._detach_status


def _find_device(gp_info: bp.GuestPortInfo, peripheral: Peripheral) -> Optional[bp.GuestPortDevice]:
    """Find the device entry for a peripheral in a `GuestPortInfo` message.

    Matches on port, device id and serial number. Returns `None` if the port slot is not set or
    the device is no longer listed on it.
    """
    port_index = int(peripheral.port_number)
    if not 1 <= port_index <= 6:
        return None
    slot = f"gp{port_index}"
    if slot not in gp_info:
        return None
    for device in getattr(gp_info, slot).device_list.devices:
        if (
            device.device_id == peripheral.device_id
            and device.serial_number == peripheral.serial_number
        ):
            return device
    return None


@dataclass
class GuestPort:
    """State of one guest port connector on the drone.

    A port either carries a list of devices or reports a connector error, never both. A port with
    nothing plugged in reports `GUEST_PORT_ERROR_NOT_CONNECTED`.
    """

    number: bp.GuestPortNumber
    """Which guest port this is."""
    capabilities: List[bp.GuestPortCapability] = field(default_factory=list)
    """Interfaces this port provides."""
    error: Optional[bp.GuestPortError] = None
    """Connector error reported by the drone, or `None` when the port carries a device list."""
    devices: List[Peripheral] = field(default_factory=list)
    """Peripherals discovered on this port. Empty when the port reports an error."""


def connector_info_to_guest_port(
    parent_drone: "Drone", connector_info: bp.GuestPortConnectorInfo
) -> GuestPort:
    """Build a [GuestPort][blueye.sdk.guestport.GuestPort] from the drone's connector info.

    Args:
        parent_drone (Drone): The parent drone instance.
        connector_info (bp.GuestPortConnectorInfo): The per-port message from `GuestPortInfo`.

    Returns:
        The guest port with its capabilities, connector error, and discovered peripherals.
    """
    port = GuestPort(
        number=connector_info.guest_port_number,
        capabilities=list(connector_info.capabilities),
    )
    if "error" in connector_info:
        port.error = connector_info.error
        if port.error == bp.GuestPortError.GUEST_PORT_ERROR_NOT_CONNECTED:
            logger.debug(f"Nothing connected to {describe_enum(port.number)}")
        else:
            logger.warning(
                f"Guest port {describe_enum(port.number)} reports connector error "
                f"{describe_enum(port.error)}"
            )
    else:
        for device in connector_info.device_list.devices:
            port.devices.append(device_to_peripheral(parent_drone, port.number, device))
    return port


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

        The drone applies the value to every light on its guest ports at once.

        Args:
            intensity (float): The intensity of the light (0..1).

        Raises:
            ValueError: If the intensity is not between 0 and 1.
        """
        if not 0 <= intensity <= 1:
            raise ValueError("Light intensity must be between 0 and 1.")
        self.parent_drone._ctrl_client.set_guest_port_lights(intensity)

    def get_intensity(self) -> Optional[float]:
        """Get the intensity of the guest port light.

        The drone only publishes the guest port light state after the lights have been set once
        in the session, so this can be `None` for a while after connecting.

        Returns:
            The intensity of the light (0..1), or `None` if the drone has not reported it yet.
        """
        telemetry_msg = self.parent_drone.telemetry.get(bp.GuestPortLightsTel)
        if telemetry_msg is None:
            return None
        return telemetry_msg.lights.value


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

    def get_grip_velocity(self) -> float:
        """Get the current grip velocity of the Gripper.

        Returns:
            The current grip velocity of the Gripper.
        """
        return self._grip_velocity

    def set_grip_velocity(self, value: float):
        """Set the current grip velocity of the Gripper.

        Args:
            value (float): The new grip velocity to set. Must be a float between -1.0 and 1.0.

        Raises:
            ValueError: If the grip velocity is not between -1.0 and 1.0.
        """
        if value < -1.0 or value > 1.0:
            raise ValueError("Grip velocity must be between -1.0 and 1.0.")
        self._grip_velocity = value
        self.parent_drone._ctrl_client.set_gripper_velocities(
            self._grip_velocity, self._rotation_velocity
        )

    grip_velocity = deprecated_property("get_grip_velocity", "set_grip_velocity")

    def get_rotation_velocity(self) -> float:
        """Get the current rotation velocity of the Gripper.

        Returns:
            The current rotation velocity of the Gripper.
        """
        return self._rotation_velocity

    def set_rotation_velocity(self, value: float):
        """Set the current rotation velocity of the Gripper.

        Args:
            value (float): The new rotation velocity to set. Must be a float between -1.0 and 1.0.

        Raises:
            ValueError: If the rotation velocity is not between -1.0 and 1.0.
        """
        if value < -1.0 or value > 1.0:
            raise ValueError("Rotation velocity must be between -1.0 and 1.0.")
        self._rotation_velocity = value
        self.parent_drone._ctrl_client.set_gripper_velocities(
            self._grip_velocity, self._rotation_velocity
        )

    rotation_velocity = deprecated_property("get_rotation_velocity", "set_rotation_velocity")


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
        if not 0 <= intensity <= 1:
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


class GenericServo(Peripheral):
    """
    Represents a Blueye generic servo connected to a guest port on the Blueye drone.

    The servo takes a position between 0 and 1, where 0 and 1 are the end stops. What that is in
    degrees depends on the servo. The drone drives generic servos on guest ports 1 to 3 and
    reports each one in its own `GenericServoTel`, which the SDK keeps per port.
    """

    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        """Initialize the Servo class.

        Args:
            parent_drone (Drone): The parent drone instance.
            port_number (bp.GuestPortNumber): The guest port number.
            device (bp.GuestPortDevice): The guest port device.
        """

        self.max_angle = 90
        self.min_angle = -90
        Peripheral.__init__(self, parent_drone, port_number, device)

    def set_position(self, position: float) -> None:
        """Set the position of the servo.

        Args:
            position (float): The position (0..1), where 0 and 1 are the end stops.

        Raises:
            ValueError: If the position is not between 0 and 1.
        """
        if not 0 <= position <= 1:
            raise ValueError(f"Position must be between 0 and 1, got {position}")
        self.parent_drone._ctrl_client.set_generic_servo_position(position, self.port_number)

    def _get_telemetry(self) -> Optional[bp.GenericServoTel]:
        """The last `GenericServoTel` the drone sent for this port.

        The drone publishes one message per port under the same type, so the generic telemetry
        store would only keep the last of them. The drone keeps a copy per port instead, filled
        by a callback. Before the first message has arrived the drone is asked, and the reply
        is used if it is about this port.
        """
        telemetry_msg = self.parent_drone._generic_servo_tel.get(self.port_number)
        if telemetry_msg is None:
            telemetry_msg = self.parent_drone.telemetry.get(bp.GenericServoTel)
            if telemetry_msg is None or telemetry_msg.servo.guest_port_number != self.port_number:
                return None
        return telemetry_msg

    def get_position(self) -> Optional[float]:
        """Get the current position of the servo.

        Returns:
            The position (0..1), or None if the drone has not reported it.
        """
        telemetry_msg = self._get_telemetry()
        if telemetry_msg is None:
            return None
        return telemetry_msg.servo.value

    def get_set_point(self) -> Optional[float]:
        """Get the position the servo is moving towards.

        Returns:
            The commanded position (0..1), or None if the drone has not reported it.
        """
        telemetry_msg = self._get_telemetry()
        if telemetry_msg is None:
            return None
        return telemetry_msg.set_point

    def set_angle(self, angle: float) -> None:
        """Set the position of the servo from an angle in degrees.

        Deprecated, the servo takes a position and not an angle. Use
        [`set_position`][blueye.sdk.guestport.GenericServo.set_position]. -90 maps to 0, 0 to
        0.5 and 90 to 1, which is what the old degree calls drove the servo to.

        Args:
            angle (float): The angle (-90..90), mapped linearly onto the 0..1 position.

        Raises:
            ValueError: If the angle is not within the allowed range.
        """
        warnings.warn(
            "`GenericServo.set_angle` is deprecated and will be removed in the next major "
            "version. Use `GenericServo.set_position()` with a 0..1 position instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not self.min_angle <= angle <= self.max_angle:
            raise ValueError(
                f"Angle must be between {self.min_angle} and {self.max_angle} degrees."
            )
        self.set_position((angle - self.min_angle) / (self.max_angle - self.min_angle))

    def get_angle(self) -> Optional[float]:
        """Get the current position of the servo as an angle in degrees.

        Deprecated, the servo reports a position and not an angle. Use
        [`get_position`][blueye.sdk.guestport.GenericServo.get_position]. Position 0 maps to
        -90, 0.5 to 0 and 1 to 90.

        Returns:
            The angle (-90..90), or None if the drone has not reported the position.
        """
        warnings.warn(
            "`GenericServo.get_angle` is deprecated and will be removed in the next major "
            "version. Use `GenericServo.get_position()`, which returns the 0..1 position.",
            DeprecationWarning,
            stacklevel=2,
        )
        position = self.get_position()
        if position is None:
            return None
        return self.min_angle + position * (self.max_angle - self.min_angle)


class SkidServo(Peripheral):
    """
    Represents the tilt servo for a multibeam sonar.

    Covers the skid-mounted servo (first and second generation), which tilts ±28 degrees, and the
    head-mounted multibeam servo, which tilts ±45 degrees. The drone drives all of them through
    the same control message, so one class serves all three; `min_angle` and `max_angle` give
    the range of the connected servo.
    """

    _ANGLE_LIMITS = {
        bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_MULTIBEAM_SERVO: 28,
        bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_MULTIBEAM_SERVO_V2: 28,
        bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_MULTIBEAM_HEAD_SERVO: 45,
    }

    def __init__(
        self, parent_drone: "Drone", port_number: bp.GuestPortNumber, device: bp.GuestPortDevice
    ):
        """Initialize the SkidServo class.

        Args:
            parent_drone (Drone): The parent drone instance.
            port_number (bp.GuestPortNumber): The guest port number.
            device (bp.GuestPortDevice): The guest port device.
        """
        limit = self._ANGLE_LIMITS.get(device.device_id, 28)
        self.max_angle = limit
        self.min_angle = -limit
        Peripheral.__init__(self, parent_drone, port_number, device)

    def set_angle(self, angle: float) -> None:
        """Set the angle of the multibeam servo.

        Args:
            angle (float): The angle to set for the servo in degrees, within `min_angle` and
                `max_angle` (±28 for the skid servos, ±45 for the head servo).

        Raises:
            ValueError: If the angle is not within the allowed range.
        """
        if not self.min_angle <= angle <= self.max_angle:
            raise ValueError(
                f"Angle must be between {self.min_angle} and {self.max_angle} degrees."
            )
        self.parent_drone._ctrl_client.set_multibeam_servo_angle(angle)

    def get_angle(self) -> float | None:
        """Get the current angle of the multibeam servo.

        Returns:
            The current angle of the servo in degrees. None if telemetry is not available.
        """
        telemetry_msg = self.parent_drone.telemetry.get(bp.MultibeamServoTel)
        if telemetry_msg is None:
            return None
        else:
            return telemetry_msg.servo.angle

    def get_set_point(self) -> float | None:
        """Get the angle the multibeam servo is moving towards.

        Returns:
            The commanded angle in degrees. None if telemetry is not available.
        """
        telemetry_msg = self.parent_drone.telemetry.get(bp.MultibeamServoTel)
        if telemetry_msg is None:
            return None
        else:
            return telemetry_msg.set_point


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
        device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_SCALING_LASER
        or device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_LASER_TOOLS_SEA_BEAM
        or device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_SPOT_X_LASER_SCALERS
    ):
        peripheral = Laser(parent_drone, port_number, device)
    elif device.device_id == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_GENERIC_SERVO:
        peripheral = GenericServo(parent_drone, port_number, device)
    elif device.device_id in SkidServo._ANGLE_LIMITS:
        peripheral = SkidServo(parent_drone, port_number, device)
    else:
        peripheral = Peripheral(parent_drone, port_number, device)
    return peripheral

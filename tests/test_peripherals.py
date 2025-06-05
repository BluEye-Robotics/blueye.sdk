import blueye.protocol as bp
import pytest

import blueye.sdk
from blueye.sdk.guestport import GenericServo, SkidServo


def test_peripheral_attribute_setter(mocked_drone):
    gp_cam = bp.GuestPortDevice({"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_CAM})
    gp_light = bp.GuestPortDevice(
        {"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_LIGHT}
    )
    gp_info = bp.GuestPortInfo()
    gp_info.gp1 = bp.GuestPortConnectorInfo()
    gp_info.gp1.device_list = bp.GuestPortDeviceList()
    gp_info.gp1.device_list.devices.append(gp_light)
    gp_info.gp3 = bp.GuestPortConnectorInfo()
    gp_info.gp3.device_list = bp.GuestPortDeviceList()
    gp_info.gp3.device_list.devices.append(gp_cam)

    mocked_drone._create_peripherals_from_drone_info(gp_info)
    assert isinstance(mocked_drone.external_camera, blueye.sdk.guestport.GuestPortCamera)
    assert isinstance(mocked_drone.external_light, blueye.sdk.guestport.GuestPortLight)


def test_laser_peripheral(mocked_drone):
    spotx_laser = bp.GuestPortDevice(
        {"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_SPOT_X_LASER_SCALERS}
    )
    gp_info = bp.GuestPortInfo()
    gp_info.gp1 = bp.GuestPortConnectorInfo()
    gp_info.gp1.device_list = bp.GuestPortDeviceList()
    gp_info.gp1.device_list.devices.append(spotx_laser)

    mocked_drone._create_peripherals_from_drone_info(gp_info)
    assert isinstance(mocked_drone.laser, blueye.sdk.guestport.Laser)
    mocked_drone.laser.set_intensity(0.5)
    mocked_drone._ctrl_client.set_laser_intensity.assert_called_once_with(0.5)
    laser_tel = bp.LaserTel(laser=bp.Laser(value=1))
    laser_tel_msg = bp.LaserTel.serialize(laser_tel)
    mocked_drone._telemetry_watcher._state[bp.LaserTel] = laser_tel_msg
    assert mocked_drone.laser.get_intensity() == 1
    with pytest.raises(ValueError):
        mocked_drone.laser.set_intensity(2)


def test_generic_servo_set_angle(mocked_drone):
    # Create a GenericServo instance
    generic_servo = GenericServo(
        parent_drone=mocked_drone,
        port_number=bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1,
        device=bp.GuestPortDevice(
            {"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_GENERIC_SERVO}
        ),
    )

    # Test valid angle
    generic_servo.set_angle(45)
    mocked_drone._ctrl_client.set_generic_servo_angle.assert_called_once_with(
        45, bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1
    )

    # Test invalid angle
    with pytest.raises(ValueError, match="Angle must be between -90 and 90 degrees."):
        generic_servo.set_angle(100)


def test_generic_servo_get_angle(mocked_drone):
    # Create a GenericServo instance
    generic_servo = GenericServo(
        parent_drone=mocked_drone,
        port_number=bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1,
        device=bp.GuestPortDevice(
            {"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_GENERIC_SERVO}
        ),
    )

    # Mock telemetry data
    telemetry_msg = bp.GenericServoTel.serialize(
        bp.GenericServoTel(servo=bp.GenericServo(value=30))
    )
    mocked_drone._telemetry_watcher._state[bp.GenericServoTel] = telemetry_msg

    # Test getting angle
    assert generic_servo.get_angle() == 30

    # Test when telemetry is not available
    mocked_drone._telemetry_watcher._state = {}

    assert generic_servo.get_angle() is None


def test_skid_servo_set_angle(mocked_drone):
    # Create a SkidServo instance
    skid_servo = SkidServo(
        parent_drone=mocked_drone,
        port_number=bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_2,
        device=bp.GuestPortDevice(
            {"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_MULTIBEAM_SERVO}
        ),
    )

    # Test valid angle
    skid_servo.set_angle(20)
    mocked_drone._ctrl_client.set_multibeam_servo_angle.assert_called_once_with(20)

    # Test invalid angle
    with pytest.raises(ValueError, match="Angle must be between -28 and 28 degrees."):
        skid_servo.set_angle(50)


def test_skid_servo_get_angle(mocked_drone):
    # Create a SkidServo instance
    skid_servo = SkidServo(
        parent_drone=mocked_drone,
        port_number=bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_2,
        device=bp.GuestPortDevice(
            {"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_MULTIBEAM_SERVO}
        ),
    )

    # Mock telemetry data
    telemetry_msg = bp.MultibeamServoTel.serialize(
        bp.MultibeamServoTel(servo=bp.MultibeamServo(angle=15))
    )
    mocked_drone._telemetry_watcher._state[bp.MultibeamServoTel] = telemetry_msg

    # Test getting angle
    assert skid_servo.get_angle() == 15

    # Test when telemetry is not available
    mocked_drone._telemetry_watcher._state = {}
    assert skid_servo.get_angle() is None

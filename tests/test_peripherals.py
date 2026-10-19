import warnings

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


def _port(number, devices=None, error=None, capabilities=()):
    info = bp.GuestPortConnectorInfo(guest_port_number=number, capabilities=list(capabilities))
    if error is not None:
        info.error = error
    else:
        info.device_list = bp.GuestPortDeviceList(devices=devices or [])
    return info


def test_peripheral_discovered_on_gp4(mocked_drone):
    gp_light = bp.GuestPortDevice(
        {"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_LIGHT}
    )
    gp_info = bp.GuestPortInfo(
        gp1=_port(
            bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1,
            error=bp.GuestPortError.GUEST_PORT_ERROR_NOT_CONNECTED,
        ),
        gp4=_port(bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_4, devices=[gp_light]),
    )

    mocked_drone._create_peripherals_from_drone_info(gp_info)

    assert len(mocked_drone.peripherals) == 1
    assert isinstance(mocked_drone.external_light, blueye.sdk.guestport.GuestPortLight)
    assert mocked_drone.external_light.port_number == bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_4


@pytest.mark.parametrize(
    "slot, number",
    [
        ("gp5", bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_5),
        ("gp6", bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_6),
    ],
)
def test_peripheral_discovered_on_gp5_and_gp6(mocked_drone, slot, number):
    gripper = bp.GuestPortDevice(
        {"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUE_ROBOTICS_NEWTON}
    )
    gp_info = bp.GuestPortInfo(**{slot: _port(number, devices=[gripper])})

    mocked_drone._create_peripherals_from_drone_info(gp_info)

    assert isinstance(mocked_drone.gripper, blueye.sdk.guestport.Gripper)
    assert mocked_drone.gripper.port_number == number


def test_get_guest_ports_reports_every_set_port(mocked_drone, caplog):
    gp_cam = bp.GuestPortDevice({"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_CAM})
    gp_info = bp.GuestPortInfo(
        gp1=_port(
            bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1,
            devices=[gp_cam],
            capabilities=[
                bp.GuestPortCapability.GUEST_PORT_CAPABILITY_ETHERNET,
                bp.GuestPortCapability.GUEST_PORT_CAPABILITY_I2C,
            ],
        ),
        gp2=_port(
            bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_2,
            error=bp.GuestPortError.GUEST_PORT_ERROR_NOT_CONNECTED,
            capabilities=[bp.GuestPortCapability.GUEST_PORT_CAPABILITY_RS485],
        ),
        gp4=_port(
            bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_4,
            error=bp.GuestPortError.GUEST_PORT_ERROR_READ_ERROR,
        ),
    )

    with caplog.at_level("DEBUG", logger="blueye.sdk.guestport"):
        mocked_drone._create_peripherals_from_drone_info(gp_info)

    ports = mocked_drone.get_guest_ports()
    assert [p.number for p in ports] == [
        bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1,
        bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_2,
        bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_4,
    ]
    gp1, gp2, gp4 = ports

    assert gp1.error is None
    assert gp1.capabilities == [
        bp.GuestPortCapability.GUEST_PORT_CAPABILITY_ETHERNET,
        bp.GuestPortCapability.GUEST_PORT_CAPABILITY_I2C,
    ]
    assert len(gp1.devices) == 1
    assert gp1.devices[0] is mocked_drone.external_camera

    assert gp2.error == bp.GuestPortError.GUEST_PORT_ERROR_NOT_CONNECTED
    assert gp2.capabilities == [bp.GuestPortCapability.GUEST_PORT_CAPABILITY_RS485]
    assert gp2.devices == []

    assert gp4.error == bp.GuestPortError.GUEST_PORT_ERROR_READ_ERROR
    assert gp4.devices == []

    # A real connector error is worth a warning, an empty port is not
    warnings = [r for r in caplog.records if r.levelname == "WARNING"]
    assert len(warnings) == 1
    assert "GUEST_PORT_NUMBER_PORT_4" in warnings[0].message
    assert "GUEST_PORT_ERROR_READ_ERROR" in warnings[0].message
    assert not any("PORT_2" in r.message for r in warnings)


def test_unknown_connector_error_does_not_abort_discovery(mocked_drone, caplog):
    """A drone running a newer Blunux can report an error value this SDK does not know.

    proto-plus hands that back as a plain int. Discovery must still log it and carry on to the
    remaining ports instead of raising.
    """
    gp_light = bp.GuestPortDevice(
        {"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_LIGHT}
    )
    gp_info = bp.GuestPortInfo(
        gp1=_port(bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1, error=1),
        gp2=_port(bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_2, devices=[gp_light]),
    )
    gp_info.gp1._pb.error = 999

    # proto-plus emits a UserWarning every time it reads an unrecognized enum value
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with caplog.at_level("WARNING", logger="blueye.sdk.guestport"):
            mocked_drone._create_peripherals_from_drone_info(gp_info)
        gp1, gp2 = mocked_drone.get_guest_ports()
        assert gp1.error == 999

    assert gp1.devices == []
    assert gp2.devices == [mocked_drone.external_light]
    assert any("connector error UNKNOWN(999)" in r.message for r in caplog.records)


def test_get_guest_ports_is_none_before_drone_info(mocked_drone):
    # No DroneInfoTel has been received by the mocked drone, so nothing is known yet
    assert mocked_drone.get_guest_ports() is None
    assert mocked_drone.peripherals is None


def test_peripheral_exposes_port_metadata(mocked_drone):
    device = bp.GuestPortDevice(
        device_id=bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUE_ROBOTICS_DETACHABLE_NEWTON,
        detach_status=bp.GuestPortDetachStatus.GUEST_PORT_DETACH_STATUS_DETACHED,
        required_capabilities=[bp.GuestPortCapability.GUEST_PORT_CAPABILITY_RS485],
        compatible_guest_ports=[
            bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1,
            bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_4,
        ],
    )
    gp_info = bp.GuestPortInfo(
        gp4=_port(bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_4, devices=[device])
    )

    mocked_drone._create_peripherals_from_drone_info(gp_info)

    gripper = mocked_drone.gripper
    assert gripper.get_detach_status() == bp.GuestPortDetachStatus.GUEST_PORT_DETACH_STATUS_DETACHED
    assert gripper.required_capabilities == [bp.GuestPortCapability.GUEST_PORT_CAPABILITY_RS485]
    assert gripper.compatible_guest_ports == [
        bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1,
        bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_4,
    ]


def test_peripheral_metadata_defaults_for_bare_device(mocked_drone):
    peripheral = blueye.sdk.guestport.Peripheral(
        mocked_drone, bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1, bp.GuestPortDevice()
    )
    assert (
        peripheral.get_detach_status()
        == bp.GuestPortDetachStatus.GUEST_PORT_DETACH_STATUS_UNSPECIFIED
    )
    assert peripheral.required_capabilities == []
    assert peripheral.compatible_guest_ports == []


def _seed_drone_info(mocked_drone, gp_info):
    tel = bp.DroneInfoTel(drone_info=bp.DroneInfo(gp=gp_info))
    mocked_drone._telemetry_watcher._state[bp.DroneInfoTel] = bp.DroneInfoTel.serialize(tel)


def _detachable_gripper(detach_status, serial="NG-1"):
    return bp.GuestPortDevice(
        device_id=bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUE_ROBOTICS_DETACHABLE_NEWTON,
        serial_number=serial,
        detach_status=detach_status,
    )


def test_detach_status_follows_drone_info_telemetry(mocked_drone):
    attached = bp.GuestPortDetachStatus.GUEST_PORT_DETACH_STATUS_ATTACHED
    detached = bp.GuestPortDetachStatus.GUEST_PORT_DETACH_STATUS_DETACHED
    port = bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_4

    mocked_drone._create_peripherals_from_drone_info(
        bp.GuestPortInfo(gp4=_port(port, devices=[_detachable_gripper(attached)]))
    )
    gripper = mocked_drone.gripper
    assert gripper.get_detach_status() == attached

    # The operator pulls the gripper off: the drone reports DETACHED in the next DroneInfoTel
    _seed_drone_info(
        mocked_drone, bp.GuestPortInfo(gp4=_port(port, devices=[_detachable_gripper(detached)]))
    )
    assert gripper.get_detach_status() == detached

    # A different unit with the same device id on the port does not count as ours
    _seed_drone_info(
        mocked_drone,
        bp.GuestPortInfo(gp4=_port(port, devices=[_detachable_gripper(attached, serial="NG-2")])),
    )
    assert gripper.get_detach_status() == attached  # last known state at discovery

    # The port now reports a connector error: fall back to the discovery-time state as well
    _seed_drone_info(
        mocked_drone,
        bp.GuestPortInfo(gp4=_port(port, error=bp.GuestPortError.GUEST_PORT_ERROR_NOT_CONNECTED)),
    )
    assert gripper.get_detach_status() == attached


def _laser_info():
    laser = bp.GuestPortDevice(
        {"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_SPOT_X_LASER_SCALERS}
    )
    return bp.GuestPortInfo(gp1=_port(bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1, devices=[laser]))


def _light_info():
    light = bp.GuestPortDevice(
        {"device_id": bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_LIGHT}
    )
    return bp.GuestPortInfo(gp2=_port(bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_2, devices=[light]))


def test_peripheral_attributes_are_none_before_discovery(mocked_drone):
    assert mocked_drone.peripherals is None
    assert mocked_drone.get_guest_ports() is None
    for name in ("external_camera", "external_light", "gripper", "laser", "servo", "skid_servo"):
        assert getattr(mocked_drone, name) is None


def test_discovery_does_not_depend_on_the_gpdrone_feature(mocked_drone):
    # The mocked drone info lists no "gpdrone" feature, yet connect() must still wait for the
    # guest port information from the drone instead of settling on an empty list.
    assert "gpdrone" not in mocked_drone.features
    mocked_drone._telemetry_watcher.add_callback.assert_called_once()
    args, _ = mocked_drone._telemetry_watcher.add_callback.call_args
    assert args[0] == [bp.DroneInfoTel]


def test_rediscovery_drops_devices_that_are_gone(mocked_drone):
    mocked_drone._create_peripherals_from_drone_info(_laser_info())
    assert isinstance(mocked_drone.laser, blueye.sdk.guestport.Laser)

    mocked_drone._create_peripherals_from_drone_info(_light_info())

    assert mocked_drone.laser is None
    assert isinstance(mocked_drone.external_light, blueye.sdk.guestport.GuestPortLight)
    assert len(mocked_drone.peripherals) == 1
    assert [port.number for port in mocked_drone.get_guest_ports()] == [
        bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_2
    ]


def test_disconnect_forgets_peripherals(mocked_drone):
    mocked_drone._create_peripherals_from_drone_info(_laser_info())

    mocked_drone.disconnect()

    assert mocked_drone.peripherals is None
    assert mocked_drone.get_guest_ports() is None
    assert mocked_drone.laser is None


def test_drone_info_without_guest_ports_keeps_waiting(mocked_drone):
    mocked_drone._drone_info_cb_id = "cb"
    without_gp = bp.DroneInfoTel(drone_info=bp.DroneInfo())
    with_gp = bp.DroneInfoTel(drone_info=bp.DroneInfo(gp=_laser_info()))

    blueye.sdk.Drone._drone_info_callback("DroneInfoTel", without_gp, mocked_drone)
    assert mocked_drone.peripherals == []
    assert mocked_drone.get_guest_ports() == []
    mocked_drone._telemetry_watcher.remove_callback.assert_not_called()

    blueye.sdk.Drone._drone_info_callback("DroneInfoTel", with_gp, mocked_drone)
    assert isinstance(mocked_drone.laser, blueye.sdk.guestport.Laser)
    mocked_drone._telemetry_watcher.remove_callback.assert_called_once_with("cb")


def test_drone_info_callback_is_ignored_after_disconnect(mocked_drone):
    with_gp = bp.DroneInfoTel(drone_info=bp.DroneInfo(gp=_laser_info()))
    mocked_drone.disconnect()

    blueye.sdk.Drone._drone_info_callback("DroneInfoTel", with_gp, mocked_drone)

    assert mocked_drone.peripherals is None
    assert mocked_drone.laser is None


def test_connect_with_a_cached_report_without_guest_ports(
    mocked_drone_not_connected, mocked_req_rep_client, mocked_telemetry_client
):
    drone = mocked_drone_not_connected
    mocked_req_rep_client.return_value.connect_client.return_value = bp.ConnectClientRep(
        client_id=1, client_id_in_control=1
    )
    mocked_telemetry_client.return_value._state[bp.DroneInfoTel] = bp.DroneInfoTel.serialize(
        bp.DroneInfoTel(drone_info=bp.DroneInfo())
    )

    drone.connect()

    # Reported, but no guest ports yet: empty lists, and the callback keeps waiting for them
    assert drone.peripherals == []
    assert drone.get_guest_ports() == []
    args, _ = drone._telemetry_watcher.add_callback.call_args
    assert args[0] == [bp.DroneInfoTel]


def test_connect_with_a_cached_report_with_guest_ports(
    mocked_drone_not_connected, mocked_req_rep_client, mocked_telemetry_client
):
    drone = mocked_drone_not_connected
    mocked_req_rep_client.return_value.connect_client.return_value = bp.ConnectClientRep(
        client_id=1, client_id_in_control=1
    )
    mocked_telemetry_client.return_value._state[bp.DroneInfoTel] = bp.DroneInfoTel.serialize(
        bp.DroneInfoTel(drone_info=bp.DroneInfo(gp=_laser_info()))
    )

    drone.connect()

    assert isinstance(drone.laser, blueye.sdk.guestport.Laser)
    drone._telemetry_watcher.add_callback.assert_not_called()

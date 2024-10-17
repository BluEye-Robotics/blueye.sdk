import blueye.protocol as bp
import pytest

import blueye.sdk


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

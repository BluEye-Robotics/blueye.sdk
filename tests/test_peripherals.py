import blueye.protocol as bp

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

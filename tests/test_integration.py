from time import time

import pytest


def polling_assert_with_timeout(cls, property_name, value_to_wait_for, timeout):
    """Waits for a property to change on the given class"""
    start_time = time()
    property_getter = type(cls).__dict__[property_name].__get__
    value = property_getter(cls)
    while value != value_to_wait_for:
        if time() - start_time > timeout:
            assert value == value_to_wait_for
        value = property_getter(cls)


@pytest.mark.connected_to_drone
class TestFunctionsWhenConnectedToDrone:
    @pytest.mark.parametrize("new_state", [True, False])
    def test_auto_heading(self, real_drone, new_state):
        real_drone.motion.auto_heading_active = new_state
        polling_assert_with_timeout(real_drone.motion, "auto_heading_active", new_state, 3)

    @pytest.mark.parametrize("new_state", [True, False])
    def test_auto_depth(self, real_drone, new_state):
        real_drone.motion.auto_depth_active = new_state
        polling_assert_with_timeout(real_drone.motion, "auto_depth_active", new_state, 3)

    def test_run_ping(self, real_drone):
        real_drone.ping()

    @pytest.mark.skip(
        reason="a camera stream must have been run before camera recording is possible"
    )
    def test_camera_recording(self, real_drone):
        _ = real_drone.camera.is_recording
        real_drone.camera.is_recording = True
        polling_assert_with_timeout(real_drone.camera, "is_recording", True, 1)
        real_drone.camera.is_recording = False
        polling_assert_with_timeout(real_drone.camera, "is_recording", False, 1)

    @pytest.mark.skip(
        reason="a camera stream must have been run before camera recording is possible"
    )
    def test_camera_record_time(self, real_drone):
        _ = real_drone.camera.record_time
        real_drone.camera.is_recording = True
        polling_assert_with_timeout(real_drone.camera, "record_time", 1, 3)

    def test_camera_bitrate(self, real_drone):
        _ = real_drone.camera.bitrate
        real_drone.camera.bitrate = 2000000
        polling_assert_with_timeout(real_drone.camera, "bitrate", 2000000, 1)
        real_drone.camera.bitrate = 3000000
        polling_assert_with_timeout(real_drone.camera, "bitrate", 3000000, 1)

    def test_camera_exposure(self, real_drone):
        _ = real_drone.camera.exposure
        real_drone.camera.exposure = 1200
        polling_assert_with_timeout(real_drone.camera, "exposure", 1200, 1)
        real_drone.camera.exposure = 1400
        polling_assert_with_timeout(real_drone.camera, "exposure", 1400, 1)

    def test_camera_whitebalance(self, real_drone):
        _ = real_drone.camera.whitebalance
        real_drone.camera.whitebalance = 3200
        polling_assert_with_timeout(real_drone.camera, "whitebalance", 3200, 1)
        real_drone.camera.whitebalance = 3400
        polling_assert_with_timeout(real_drone.camera, "whitebalance", 3400, 1)

    def test_camera_hue(self, real_drone):
        _ = real_drone.camera.hue
        real_drone.camera.hue = 20
        polling_assert_with_timeout(real_drone.camera, "hue", 20, 1)
        real_drone.camera.hue = 30
        polling_assert_with_timeout(real_drone.camera, "hue", 30, 1)

    def test_camera_resolution(self, real_drone):
        _ = real_drone.camera.resolution
        real_drone.camera.resolution = 480
        polling_assert_with_timeout(real_drone.camera, "resolution", 480, 1)
        real_drone.camera.resolution = 720
        polling_assert_with_timeout(real_drone.camera, "resolution", 720, 1)

    def test_camera_framerate(self, real_drone):
        _ = real_drone.camera.framerate
        real_drone.camera.framerate = 25
        polling_assert_with_timeout(real_drone.camera, "framerate", 25, 1)
        real_drone.camera.framerate = 30
        polling_assert_with_timeout(real_drone.camera, "framerate", 30, 1)

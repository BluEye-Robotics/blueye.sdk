from time import time

import pytest


def polling_assert_with_timeout(getter, value_to_wait_for, timeout):
    """Waits for a getter to return the value we are waiting for"""
    start_time = time()
    value = getter()
    while value != value_to_wait_for:
        if time() - start_time > timeout:
            assert value == value_to_wait_for
        value = getter()


@pytest.mark.connected_to_drone
class TestFunctionsWhenConnectedToDrone:
    @pytest.mark.parametrize("new_state", [True, False])
    def test_auto_heading(self, real_drone, new_state):
        real_drone.motion.enable_auto_heading(new_state)
        polling_assert_with_timeout(real_drone.motion.is_auto_heading_active, new_state, 3)

    @pytest.mark.parametrize("new_state", [True, False])
    def test_auto_depth(self, real_drone, new_state):
        real_drone.motion.enable_auto_depth(new_state)
        polling_assert_with_timeout(real_drone.motion.is_auto_depth_active, new_state, 3)

    def test_run_ping(self, real_drone):
        real_drone.ping()

    @pytest.mark.skip(
        reason="a camera stream must have been run before camera recording is possible"
    )
    def test_camera_recording(self, real_drone):
        _ = real_drone.camera.is_recording_active()
        real_drone.camera.set_recording(True)
        polling_assert_with_timeout(real_drone.camera.is_recording_active, True, 1)
        real_drone.camera.set_recording(False)
        polling_assert_with_timeout(real_drone.camera.is_recording_active, False, 1)

    @pytest.mark.skip(
        reason="a camera stream must have been run before camera recording is possible"
    )
    def test_camera_record_time(self, real_drone):
        _ = real_drone.camera.get_record_time()
        real_drone.camera.set_recording(True)
        polling_assert_with_timeout(real_drone.camera.get_record_time, 1, 3)

    def test_camera_bitrate(self, real_drone):
        _ = real_drone.camera.get_bitrate()
        real_drone.camera.set_bitrate(2000000)
        polling_assert_with_timeout(real_drone.camera.get_bitrate, 2000000, 1)
        real_drone.camera.set_bitrate(3000000)
        polling_assert_with_timeout(real_drone.camera.get_bitrate, 3000000, 1)

    def test_camera_exposure(self, real_drone):
        _ = real_drone.camera.get_exposure()
        real_drone.camera.set_exposure(1200)
        polling_assert_with_timeout(real_drone.camera.get_exposure, 1200, 1)
        real_drone.camera.set_exposure(1400)
        polling_assert_with_timeout(real_drone.camera.get_exposure, 1400, 1)

    def test_camera_whitebalance(self, real_drone):
        _ = real_drone.camera.get_whitebalance()
        real_drone.camera.set_whitebalance(3200)
        polling_assert_with_timeout(real_drone.camera.get_whitebalance, 3200, 1)
        real_drone.camera.set_whitebalance(3400)
        polling_assert_with_timeout(real_drone.camera.get_whitebalance, 3400, 1)

    def test_camera_hue(self, real_drone):
        _ = real_drone.camera.get_hue()
        real_drone.camera.set_hue(20)
        polling_assert_with_timeout(real_drone.camera.get_hue, 20, 1)
        real_drone.camera.set_hue(30)
        polling_assert_with_timeout(real_drone.camera.get_hue, 30, 1)

    def test_camera_resolution(self, real_drone):
        _ = real_drone.camera.get_resolution()
        real_drone.camera.set_resolution(720)
        polling_assert_with_timeout(real_drone.camera.get_resolution, 720, 1)
        real_drone.camera.set_resolution(1080)
        polling_assert_with_timeout(real_drone.camera.get_resolution, 1080, 1)

    def test_camera_framerate(self, real_drone):
        _ = real_drone.camera.get_framerate()
        real_drone.camera.set_framerate(25)
        polling_assert_with_timeout(real_drone.camera.get_framerate, 25, 1)
        real_drone.camera.set_framerate(30)
        polling_assert_with_timeout(real_drone.camera.get_framerate, 30, 1)

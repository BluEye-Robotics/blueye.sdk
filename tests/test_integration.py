from time import time

import blueye.protocol as bp
import pytest
from packaging import version

ALL_RESOLUTIONS = [
    bp.Resolution.RESOLUTION_VGA_480P,
    bp.Resolution.RESOLUTION_HD_720P,
    bp.Resolution.RESOLUTION_FULLHD_1080P,
    bp.Resolution.RESOLUTION_QHD_2K,
    bp.Resolution.RESOLUTION_UHD_4K,
]


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

    def test_camera_bitrate(self, real_drone, drone_model):
        if drone_model == bp.Model.MODEL_X3_ULTRA:
            pytest.xfail(
                "The Ultra applies the stream bitrate but always reports it as 0. The drone "
                "fills h264_bitrate from the camera control node, and the Ultra camera does not "
                "encode H264 - the RTSP server does, and its bitrate never reaches the reply"
            )
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

    def test_camera_hue(self, real_drone, drone_model):
        if drone_model == bp.Model.MODEL_X3_ULTRA:
            pytest.skip(
                "Hue is only available on Pioneer/Pro/X1/X3, the Ultra camera has no hue control"
            )
        _ = real_drone.camera.get_hue()
        real_drone.camera.set_hue(20)
        polling_assert_with_timeout(real_drone.camera.get_hue, 20, 1)
        real_drone.camera.set_hue(30)
        polling_assert_with_timeout(real_drone.camera.get_hue, 30, 1)

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_camera_resolution(self, real_drone):
        if version.parse(real_drone.software_version_short) >= version.parse("4.4"):
            pytest.xfail(
                "Drones running Blunux 4.4 or newer ignore the deprecated resolution field when "
                "camera parameters are set, use the stream/recording resolution methods instead"
            )
        _ = real_drone.camera.get_resolution()
        real_drone.camera.set_resolution(720)
        polling_assert_with_timeout(real_drone.camera.get_resolution, 720, 1)
        real_drone.camera.set_resolution(1080)
        polling_assert_with_timeout(real_drone.camera.get_resolution, 1080, 1)

    @pytest.mark.parametrize("resolution", ALL_RESOLUTIONS, ids=lambda r: r.name)
    def test_camera_stream_resolution(self, real_drone, resolution):
        original_resolution = real_drone.camera.get_stream_resolution()
        try:
            real_drone.camera.set_stream_resolution(resolution)
            polling_assert_with_timeout(real_drone.camera.get_stream_resolution, resolution, 3)
        finally:
            real_drone.camera.set_stream_resolution(original_resolution)

    @pytest.mark.parametrize("resolution", ALL_RESOLUTIONS, ids=lambda r: r.name)
    def test_camera_recording_resolution(self, real_drone, resolution):
        original_resolution = real_drone.camera.get_recording_resolution()
        try:
            real_drone.camera.set_recording_resolution(resolution)
            polling_assert_with_timeout(real_drone.camera.get_recording_resolution, resolution, 3)
        finally:
            real_drone.camera.set_recording_resolution(original_resolution)

    def test_camera_framerate(self, real_drone, drone_model):
        if drone_model == bp.Model.MODEL_X3_ULTRA:
            pytest.skip(
                "The Ultra only applies 25 fps to the recording pipeline, and the reported frame "
                "rate comes from the stream pipeline, which stays at 30. See "
                "test_camera_framerate_60_fps for the frame rate the Ultra does support"
            )
        _ = real_drone.camera.get_framerate()
        real_drone.camera.set_framerate(25)
        polling_assert_with_timeout(real_drone.camera.get_framerate, 25, 1)
        real_drone.camera.set_framerate(30)
        polling_assert_with_timeout(real_drone.camera.get_framerate, 30, 1)

    def test_camera_framerate_60_fps(self, real_drone, drone_model):
        """60 fps is only supported on the Ultra, and only at 1440p or lower.

        The drone caps the frame rate against the highest of the stream and recording
        resolution, so both must be lowered before requesting 60 fps.
        """
        if drone_model != bp.Model.MODEL_X3_ULTRA:
            pytest.skip("60 fps is only supported on the Ultra")
        original_stream_resolution = real_drone.camera.get_stream_resolution()
        original_recording_resolution = real_drone.camera.get_recording_resolution()
        original_framerate = real_drone.camera.get_framerate()
        try:
            real_drone.camera.set_stream_resolution(bp.Resolution.RESOLUTION_FULLHD_1080P)
            real_drone.camera.set_recording_resolution(bp.Resolution.RESOLUTION_FULLHD_1080P)
            real_drone.camera.set_framerate(60)
            polling_assert_with_timeout(real_drone.camera.get_framerate, 60, 3)
        finally:
            real_drone.camera.set_framerate(original_framerate)
            real_drone.camera.set_stream_resolution(original_stream_resolution)
            real_drone.camera.set_recording_resolution(original_recording_resolution)

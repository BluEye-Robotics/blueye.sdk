from time import sleep, time

import blueye.protocol as bp
import pytest
from packaging import version

from blueye.sdk.constants import JETSON_MODELS

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

    def test_drone_info(self, real_drone, drone_model):
        drone_info = real_drone.get_drone_info()
        assert drone_info is not None
        assert drone_info.model == drone_model
        assert real_drone.get_model() == drone_model
        assert real_drone.is_jetson_platform() is (drone_model in JETSON_MODELS)
        assert isinstance(real_drone.get_power_source(), bp.PowerSource)
        assert isinstance(real_drone.get_depth_sensor_type(), bp.PressureSensorType)

    def test_camera_calibration(self, real_drone, drone_model):
        calibration = real_drone.camera.get_calibration()
        if drone_model not in JETSON_MODELS:
            assert calibration is None
            pytest.skip("Only the X3 Ultra and X7 publish a camera calibration")
        assert calibration is not None
        assert calibration.image_width > 0 and calibration.image_height > 0
        assert len(calibration.distortion_coefficients) == 5
        scaled = real_drone.camera.get_scaled_calibration((1280, 720))
        assert scaled.image_width == 1280 and scaled.image_height == 720
        assert scaled.fx == pytest.approx(calibration.fx * 1280 / calibration.image_width)
        external_camera = getattr(real_drone, "external_camera", None)
        if external_camera is not None:
            assert external_camera.get_calibration() is None

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
        if drone_model in JETSON_MODELS:
            pytest.xfail(
                "The 4K camera models apply the stream bitrate but always report it as 0. The "
                "drone fills h264_bitrate from the camera control node, and the 4K camera does not "
                "encode H264 - the RTSP server does, and its bitrate never reaches the reply"
            )
        _ = real_drone.camera.get_bitrate()
        real_drone.camera.set_bitrate(2000000)
        polling_assert_with_timeout(real_drone.camera.get_bitrate, 2000000, 1)
        real_drone.camera.set_bitrate(3000000)
        polling_assert_with_timeout(real_drone.camera.get_bitrate, 3000000, 1)

    def test_camera_exposure(self, real_drone):
        # Both values fit in one frame at 30 fps, which the 4K camera shortens longer shutter
        # times to.
        _ = real_drone.camera.get_exposure()
        real_drone.camera.set_exposure(100)
        polling_assert_with_timeout(real_drone.camera.get_exposure, 100, 1)
        real_drone.camera.set_exposure(200)
        polling_assert_with_timeout(real_drone.camera.get_exposure, 200, 1)

    def test_camera_whitebalance(self, real_drone):
        _ = real_drone.camera.get_whitebalance()
        real_drone.camera.set_whitebalance(3200)
        polling_assert_with_timeout(real_drone.camera.get_whitebalance, 3200, 1)
        real_drone.camera.set_whitebalance(3400)
        polling_assert_with_timeout(real_drone.camera.get_whitebalance, 3400, 1)

    def test_camera_hue(self, real_drone, drone_model):
        if drone_model in JETSON_MODELS:
            pytest.skip(
                "Hue is only available on Pioneer/Pro/X1/X3, the 4K camera has no hue control"
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
        if drone_model in JETSON_MODELS:
            pytest.skip(
                "The 4K camera only applies 25 fps to the recording pipeline, and the reported "
                "frame rate comes from the stream pipeline, which stays at 30. See "
                "test_camera_framerate_60_fps for the frame rate they do support"
            )
        _ = real_drone.camera.get_framerate()
        real_drone.camera.set_framerate(25)
        polling_assert_with_timeout(real_drone.camera.get_framerate, 25, 1)
        real_drone.camera.set_framerate(30)
        polling_assert_with_timeout(real_drone.camera.get_framerate, 30, 1)

    def test_camera_framerate_60_fps(self, real_drone, drone_model):
        """60 fps is only supported on the 4K camera, and only at 1440p or lower.

        The drone caps the frame rate against the highest of the stream and recording
        resolution, so both must be lowered before requesting 60 fps.
        """
        if drone_model not in JETSON_MODELS:
            pytest.skip("60 fps is only supported on the X3 Ultra and X7")
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

    @pytest.mark.parametrize(
        "getter, setter",
        [
            ("get_turbidity_filter", "set_turbidity_filter"),
            ("get_color_correction", "set_color_correction"),
        ],
    )
    def test_camera_filters(self, real_drone, drone_model, getter, setter):
        """The filter telemetry is published on change, so a set must show up in the getter."""
        if drone_model not in JETSON_MODELS:
            pytest.skip("The image filters are only available on the X3 Ultra and X7")
        if version.parse(real_drone.software_version_short) < version.parse("5.0.0"):
            pytest.skip("The image filters need Blunux 5.0.0")
        original = getattr(real_drone.camera, getter)()

        def reported():
            settings = getattr(real_drone.camera, getter)()
            if settings is None:
                return None
            return (settings.enabled, round(settings.intensity, 2))

        try:
            getattr(real_drone.camera, setter)(True, 0.5)
            deadline = time() + 10
            while reported() is None and time() < deadline:
                sleep(0.1)
            if reported() is None:
                # The drone only reports a filter it has in its video pipeline. Color correction
                # came to gst_rtsp_record in July 2026, so earlier Blunux 5.0 builds have the
                # turbidity filter but not this one.
                pytest.skip(f"This drone build does not report {setter[4:]}")
            polling_assert_with_timeout(reported, (True, 0.5), 10)
            getattr(real_drone.camera, setter)(False, 0.25)
            polling_assert_with_timeout(reported, (False, 0.25), 10)
        finally:
            if original is not None:
                getattr(real_drone.camera, setter)(original.enabled, original.intensity)

    def test_camera_pan_tilt_zoom(self, real_drone, drone_model):
        if drone_model not in JETSON_MODELS:
            pytest.skip("Digital pan, tilt and zoom is only available on the X3 Ultra and X7")
        if version.parse(real_drone.software_version_short) < version.parse("5.0.0"):
            pytest.skip("Digital pan, tilt and zoom needs Blunux 5.0.0")
        original = real_drone.camera.get_pan_tilt_zoom()

        def rounded_state():
            state = real_drone.camera.get_pan_tilt_zoom()
            if state is None:
                return None
            return (round(state.pan, 1), round(state.tilt, 1), round(state.zoom, 1))

        try:
            real_drone.camera.set_pan_tilt_zoom(pan=0.5, tilt=-0.5, zoom=0.5)
            polling_assert_with_timeout(rounded_state, (0.5, -0.5, 0.5), 2)
            real_drone.camera.set_pan_tilt_zoom(zoom=0.0)
            polling_assert_with_timeout(lambda: rounded_state()[2], 0.0, 2)
        finally:
            if original is not None:
                real_drone.camera.set_pan_tilt_zoom(original.pan, original.tilt, original.zoom)

import blueye.protocol as bp
import pytest

from blueye.sdk import Drone


@pytest.fixture
def mocked_camera(mocked_drone: Drone):
    from blueye.sdk.camera import Camera

    # Set the version to a value that supports setting stream and recording resolution
    # independently.
    mocked_drone.software_version_short = "4.4.1"
    camera = Camera(mocked_drone)
    return camera


def test_stream_resolution_getter(mocked_camera):
    mocked_camera_parameters = bp.CameraParameters(
        stream_resolution=bp.Resolution.RESOLUTION_FULLHD_1080P
    )
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        mocked_camera_parameters
    )
    assert mocked_camera.get_stream_resolution() == bp.Resolution.RESOLUTION_FULLHD_1080P


def test_stream_resolution_setter(mocked_camera):
    old_camera_parameters = bp.CameraParameters(stream_resolution=bp.Resolution.RESOLUTION_HD_720P)

    new_camera_parameters = bp.CameraParameters(
        stream_resolution=bp.Resolution.RESOLUTION_FULLHD_1080P,
        resolution=bp.Resolution.RESOLUTION_FULLHD_1080P,
    )
    mocked_camera._camera_parameters = old_camera_parameters

    mocked_camera.set_stream_resolution(bp.Resolution.RESOLUTION_FULLHD_1080P)
    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once_with(
        new_camera_parameters
    )
    assert (
        mocked_camera._camera_parameters.stream_resolution == bp.Resolution.RESOLUTION_FULLHD_1080P
    )


def test_stream_resolution_invalid_type(mocked_camera):
    with pytest.raises(ValueError):
        mocked_camera.set_stream_resolution("invalid_resolution")


def test_recording_resolution_getter(mocked_camera):
    mocked_camera_parameters = bp.CameraParameters(
        recording_resolution=bp.Resolution.RESOLUTION_FULLHD_1080P
    )
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        mocked_camera_parameters
    )
    assert mocked_camera.get_recording_resolution() == bp.Resolution.RESOLUTION_FULLHD_1080P


def test_recording_resolution_setter(mocked_camera):
    old_camera_parameters = bp.CameraParameters(
        recording_resolution=bp.Resolution.RESOLUTION_HD_720P
    )

    new_camera_parameters = bp.CameraParameters(
        recording_resolution=bp.Resolution.RESOLUTION_FULLHD_1080P,
        resolution=bp.Resolution.RESOLUTION_FULLHD_1080P,
    )
    mocked_camera._camera_parameters = old_camera_parameters

    mocked_camera.set_recording_resolution(bp.Resolution.RESOLUTION_FULLHD_1080P)
    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once_with(
        new_camera_parameters
    )
    assert (
        mocked_camera._camera_parameters.recording_resolution
        == bp.Resolution.RESOLUTION_FULLHD_1080P
    )


def test_recording_resolution_invalid_type(mocked_camera):
    with pytest.raises(ValueError):
        mocked_camera.set_recording_resolution("invalid_resolution")


@pytest.mark.parametrize(
    "enum_value, expected",
    [
        (bp.Resolution.RESOLUTION_VGA_480P, 480),
        (bp.Resolution.RESOLUTION_HD_720P, 720),
        (bp.Resolution.RESOLUTION_FULLHD_1080P, 1080),
        (bp.Resolution.RESOLUTION_QHD_2K, 1440),
        (bp.Resolution.RESOLUTION_UHD_4K, 2160),
    ],
)
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_resolution_getter(mocked_camera, enum_value, expected):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(resolution=enum_value)
    )
    assert mocked_camera.get_resolution() == expected


@pytest.mark.parametrize(
    "value, expected_enum",
    [
        (480, bp.Resolution.RESOLUTION_VGA_480P),
        (720, bp.Resolution.RESOLUTION_HD_720P),
        (1080, bp.Resolution.RESOLUTION_FULLHD_1080P),
        (1440, bp.Resolution.RESOLUTION_QHD_2K),
        (2160, bp.Resolution.RESOLUTION_UHD_4K),
    ],
)
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_resolution_setter(mocked_camera, value, expected_enum):
    mocked_camera._camera_parameters = bp.CameraParameters()
    mocked_camera.set_resolution(value)
    assert mocked_camera._camera_parameters.resolution == expected_enum
    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once_with(
        mocked_camera._camera_parameters
    )


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_resolution_setter_invalid_value(mocked_camera):
    with pytest.raises(ValueError):
        mocked_camera.set_resolution(600)


def test_streaming_protocol_getter(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(streaming_protocol=bp.StreamingProtocol.STREAMING_PROTOCOL_RTSP_H264)
    )
    assert (
        mocked_camera.get_streaming_protocol() == bp.StreamingProtocol.STREAMING_PROTOCOL_RTSP_H264
    )


def test_streaming_protocol_setter(mocked_camera):
    mocked_camera._camera_parameters = bp.CameraParameters()
    mocked_camera.set_streaming_protocol(bp.StreamingProtocol.STREAMING_PROTOCOL_RTSP_MJPEG)
    assert (
        mocked_camera._camera_parameters.streaming_protocol
        == bp.StreamingProtocol.STREAMING_PROTOCOL_RTSP_MJPEG
    )
    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once_with(
        mocked_camera._camera_parameters
    )


def test_streaming_protocol_invalid_type(mocked_camera):
    with pytest.raises(ValueError):
        mocked_camera.set_streaming_protocol("invalid_protocol")


def test_old_drones_use_resolution_field(mocked_camera):
    # Set the version to a value that does not support separate recording resolution
    mocked_camera._parent_drone.software_version_short = "4.3"

    mocked_camera_parameters = bp.CameraParameters(resolution=bp.Resolution.RESOLUTION_FULLHD_1080P)
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        mocked_camera_parameters
    )

    assert mocked_camera.get_recording_resolution() == bp.Resolution.RESOLUTION_FULLHD_1080P
    assert mocked_camera.get_stream_resolution() == bp.Resolution.RESOLUTION_FULLHD_1080P


def test_configure_batches_changes(mocked_camera):
    """configure() should fetch current params, accumulate changes, and send once on exit."""
    initial_params = bp.CameraParameters(
        stream_resolution=bp.Resolution.RESOLUTION_HD_720P,
        framerate=bp.Framerate.FRAMERATE_FPS_25,
    )
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = initial_params

    with mocked_camera.configure() as params:
        params.stream_resolution = bp.Resolution.RESOLUTION_FULLHD_1080P
        params.framerate = bp.Framerate.FRAMERATE_FPS_30

    # Should have called get once (on enter) and set once (on exit)
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.assert_called_once()
    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once()

    # The sent params should contain both changes
    sent_params = mocked_camera._parent_drone._req_rep_client.set_camera_parameters.call_args[0][0]
    assert sent_params.stream_resolution == bp.Resolution.RESOLUTION_FULLHD_1080P
    assert sent_params.framerate == bp.Framerate.FRAMERATE_FPS_30


def test_configure_discards_on_exception(mocked_camera):
    """configure() should not send changes if an exception occurs inside the block."""
    initial_params = bp.CameraParameters(
        stream_resolution=bp.Resolution.RESOLUTION_HD_720P,
    )
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = initial_params

    with pytest.raises(ValueError):
        with mocked_camera.configure() as params:
            params.stream_resolution = bp.Resolution.RESOLUTION_FULLHD_1080P
            raise ValueError("abort")

    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_not_called()


def test_configure_passes_timeout(mocked_camera):
    """configure(timeout=X) should pass the timeout to both get and set calls."""
    initial_params = bp.CameraParameters()
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = initial_params

    with mocked_camera.configure(timeout=5.0) as params:
        params.framerate = bp.Framerate.FRAMERATE_FPS_30

    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.assert_called_once_with(
        camera=mocked_camera._camera_type, timeout=5.0
    )
    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once()
    assert (
        mocked_camera._parent_drone._req_rep_client.set_camera_parameters.call_args[1]["timeout"]
        == 5.0
    )


@pytest.fixture
def mocked_ultra_camera(mocked_drone: Drone):
    """A camera on a drone running a Blunux version that supports all camera parameters."""
    from blueye.sdk.camera import Camera

    mocked_drone.software_version_short = "5.1.0"
    return Camera(mocked_drone)


def test_get_resolution_warns_deprecation(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(resolution=bp.Resolution.RESOLUTION_HD_720P)
    )
    with pytest.warns(DeprecationWarning, match="get_stream_resolution"):
        assert mocked_camera.get_resolution() == 720


def test_set_resolution_warns_deprecation(mocked_camera):
    mocked_camera._camera_parameters = bp.CameraParameters()
    with pytest.warns(DeprecationWarning, match="set_stream_resolution"):
        mocked_camera.set_resolution(720)


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_resolution_getter_raises_on_unknown_resolution(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(resolution=bp.Resolution.RESOLUTION_UNSPECIFIED)
    )
    with pytest.raises(RuntimeError):
        mocked_camera.get_resolution()


@pytest.mark.parametrize(
    "enum_value, expected",
    [
        (bp.Framerate.FRAMERATE_FPS_25, 25),
        (bp.Framerate.FRAMERATE_FPS_30, 30),
        (bp.Framerate.FRAMERATE_FPS_60, 60),
    ],
)
def test_framerate_getter(mocked_camera, enum_value, expected):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(framerate=enum_value)
    )
    assert mocked_camera.get_framerate() == expected


@pytest.mark.parametrize(
    "value, expected_enum",
    [
        (25, bp.Framerate.FRAMERATE_FPS_25),
        (30, bp.Framerate.FRAMERATE_FPS_30),
        (60, bp.Framerate.FRAMERATE_FPS_60),
    ],
)
def test_framerate_setter(mocked_camera, value, expected_enum):
    mocked_camera._camera_parameters = bp.CameraParameters()
    mocked_camera.set_framerate(value)
    assert mocked_camera._camera_parameters.framerate == expected_enum
    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once_with(
        mocked_camera._camera_parameters
    )


def test_framerate_setter_invalid_value(mocked_camera):
    with pytest.raises(ValueError):
        mocked_camera.set_framerate(24)


def test_framerate_getter_raises_on_unknown_framerate(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(framerate=bp.Framerate.FRAMERATE_UNSPECIFIED)
    )
    with pytest.raises(RuntimeError):
        mocked_camera.get_framerate()


# (getter, setter, CameraParameters field name, test value) for the Ultra-only image parameters
ULTRA_IMAGE_PARAMETERS = [
    ("get_brightness", "set_brightness", "brightness", 5),
    ("get_contrast", "set_contrast", "contrast", 20),
    ("get_saturation", "set_saturation", "saturation", 10),
    ("get_gamma", "set_gamma", "gamma", 30),
    ("get_sharpness", "set_sharpness", "sharpness", -10),
    ("get_backlight_compensation", "set_backlight_compensation", "backlight_compensation", 100),
    ("get_denoise", "set_denoise", "denoise", -5),
    ("is_ehdr_enabled", "enable_ehdr", "ehdr_enabled", True),
    (
        "get_ehdr_exposure_min_number",
        "set_ehdr_exposure_min_number",
        "ehdr_exposure_min_number",
        2,
    ),
    (
        "get_ehdr_exposure_max_number",
        "set_ehdr_exposure_max_number",
        "ehdr_exposure_max_number",
        3,
    ),
]


@pytest.mark.parametrize("getter, setter, field_name, value", ULTRA_IMAGE_PARAMETERS)
def test_ultra_image_parameter_getter(mocked_ultra_camera, getter, setter, field_name, value):
    mocked_ultra_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(**{field_name: value})
    )
    assert getattr(mocked_ultra_camera, getter)() == value


@pytest.mark.parametrize("getter, setter, field_name, value", ULTRA_IMAGE_PARAMETERS)
def test_ultra_image_parameter_setter(mocked_ultra_camera, getter, setter, field_name, value):
    mocked_ultra_camera._camera_parameters = bp.CameraParameters()
    getattr(mocked_ultra_camera, setter)(value)
    assert getattr(mocked_ultra_camera._camera_parameters, field_name) == value
    mocked_ultra_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once_with(
        mocked_ultra_camera._camera_parameters
    )


@pytest.mark.parametrize("getter, setter, field_name, value", ULTRA_IMAGE_PARAMETERS)
def test_ultra_image_parameter_setter_requires_blunux_5(
    mocked_camera, getter, setter, field_name, value
):
    # The mocked_camera fixture runs Blunux 4.4.1
    with pytest.raises(RuntimeError):
        getattr(mocked_camera, setter)(value)


def test_gain_getter(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(gain=0.5)
    )
    assert mocked_camera.get_gain() == pytest.approx(0.5)


def test_gain_setter(mocked_camera):
    mocked_camera._camera_parameters = bp.CameraParameters()
    mocked_camera.set_gain(0.5)
    assert mocked_camera._camera_parameters.gain == pytest.approx(0.5)
    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once_with(
        mocked_camera._camera_parameters
    )


def test_mtu_size_getter(mocked_ultra_camera):
    mocked_ultra_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(mtu_size=1400)
    )
    assert mocked_ultra_camera.get_mtu_size() == 1400


def test_mtu_size_setter(mocked_ultra_camera):
    mocked_ultra_camera._camera_parameters = bp.CameraParameters()
    mocked_ultra_camera.set_mtu_size(1200)
    assert mocked_ultra_camera._camera_parameters.mtu_size == 1200
    mocked_ultra_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once_with(
        mocked_ultra_camera._camera_parameters
    )


def test_mtu_size_setter_requires_blunux_5_1(mocked_camera):
    # The mocked_camera fixture runs Blunux 4.4.1
    with pytest.raises(RuntimeError):
        mocked_camera.set_mtu_size(1200)


def test_configure_rejects_ultra_image_parameters_on_old_drone(mocked_camera):
    """Batched changes should honour the same Blunux version requirements as the setters."""
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters()
    )
    with pytest.raises(RuntimeError):
        with mocked_camera.configure() as params:
            params.brightness = 5
    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_not_called()


def test_configure_rejects_mtu_size_on_blunux_5_0(mocked_drone: Drone):
    from blueye.sdk.camera import Camera

    mocked_drone.software_version_short = "5.0.0"
    camera = Camera(mocked_drone)
    camera._parent_drone._req_rep_client.get_camera_parameters.return_value = bp.CameraParameters()
    with pytest.raises(RuntimeError):
        with camera.configure() as params:
            params.mtu_size = 1200
    camera._parent_drone._req_rep_client.set_camera_parameters.assert_not_called()

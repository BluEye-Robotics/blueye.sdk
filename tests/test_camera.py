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


def test_recording_bitrate_getter(mocked_ultra_camera):
    mocked_ultra_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(recording_bitrate=24_000_000)
    )
    assert mocked_ultra_camera.get_recording_bitrate() == 24_000_000


def test_recording_bitrate_setter(mocked_ultra_camera):
    mocked_ultra_camera._camera_parameters = bp.CameraParameters(recording_bitrate=0)

    mocked_ultra_camera.set_recording_bitrate(24_000_000)

    mocked_ultra_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once_with(
        bp.CameraParameters(recording_bitrate=24_000_000)
    )
    assert mocked_ultra_camera._camera_parameters.recording_bitrate == 24_000_000


def test_recording_bitrate_setter_requires_blunux_5(mocked_camera):
    with pytest.raises(RuntimeError):
        mocked_camera.set_recording_bitrate(24_000_000)


def test_parameter_getter_refreshes_from_the_drone(mocked_ultra_camera):
    """A getter must ask the drone, never answer from the cache.

    Every getter method calls _update_camera_parameters() first, so a value
    that changed since the last request - because another client set it, or
    because the drone resolved an "automatic" request to a concrete number - is
    reported as it is now and not as it was last written.
    """
    mocked_ultra_camera._camera_parameters = bp.CameraParameters(recording_bitrate=0)
    mocked_ultra_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(recording_bitrate=14_000_000)
    )

    assert mocked_ultra_camera.get_recording_bitrate() == 14_000_000
    mocked_ultra_camera._parent_drone._req_rep_client.get_camera_parameters.assert_called_once()


def test_setter_on_a_cold_camera_fetches_current_parameters_first(mocked_ultra_camera):
    """A setter on a camera that has not talked to the drone yet must fetch the
    current parameters before it sends.

    set_camera_parameters carries the whole CameraParameters struct, so without
    the lazy fetch the first setter after construction would send a
    default-constructed one and zero every field the caller never touched -
    resolution, framerate and codec among them.
    """
    assert mocked_ultra_camera._camera_parameters is None
    mocked_ultra_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(
            stream_resolution=bp.Resolution.RESOLUTION_FULLHD_1080P,
            framerate=bp.Framerate.FRAMERATE_FPS_30,
        )
    )

    mocked_ultra_camera.set_recording_bitrate(24_000_000)

    mocked_ultra_camera._parent_drone._req_rep_client.get_camera_parameters.assert_called_once()
    sent = mocked_ultra_camera._parent_drone._req_rep_client.set_camera_parameters.call_args[0][0]
    assert sent.recording_bitrate == 24_000_000
    assert sent.stream_resolution == bp.Resolution.RESOLUTION_FULLHD_1080P
    assert sent.framerate == bp.Framerate.FRAMERATE_FPS_30


# (SDK accessor name, protobuf field name) for the fields whose names diverge
BATCH_FIELD_ALIASES = [
    ("whitebalance", "white_balance", 3200),
    ("bitrate", "h264_bitrate", 3_000_000),
    ("bitrate_still_picture", "mjpg_bitrate", 500_000),
]


@pytest.mark.parametrize("sdk_name, field_name, value", BATCH_FIELD_ALIASES)
def test_configure_accepts_sdk_field_names(mocked_camera, sdk_name, field_name, value):
    """configure() should take the same names as the setters, not raw protobuf names."""
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters()
    )
    with mocked_camera.configure() as params:
        setattr(params, sdk_name, value)
    sent = mocked_camera._parent_drone._req_rep_client.set_camera_parameters.call_args[0][0]
    assert getattr(sent, field_name) == value


@pytest.mark.parametrize("sdk_name, field_name, value", BATCH_FIELD_ALIASES)
def test_configure_still_accepts_protobuf_field_names(mocked_camera, sdk_name, field_name, value):
    """The protobuf names shipped in 2.7.0, so they have to keep working."""
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters()
    )
    with mocked_camera.configure() as params:
        setattr(params, field_name, value)
    sent = mocked_camera._parent_drone._req_rep_client.set_camera_parameters.call_args[0][0]
    assert getattr(sent, field_name) == value


@pytest.mark.parametrize("sdk_name, field_name, value", BATCH_FIELD_ALIASES)
def test_configure_reads_back_through_sdk_names(mocked_camera, sdk_name, field_name, value):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(**{field_name: value})
    )
    with mocked_camera.configure() as params:
        assert getattr(params, sdk_name) == value


def test_configure_translates_framerate_int_to_enum(mocked_camera):
    """set_framerate() takes fps, so the batch must too - not a raw enum number."""
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters()
    )
    with mocked_camera.configure() as params:
        params.framerate = 60
    sent = mocked_camera._parent_drone._req_rep_client.set_camera_parameters.call_args[0][0]
    assert sent.framerate == bp.Framerate.FRAMERATE_FPS_60


def test_configure_still_accepts_framerate_enum(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters()
    )
    with mocked_camera.configure() as params:
        params.framerate = bp.Framerate.FRAMERATE_FPS_25
    sent = mocked_camera._parent_drone._req_rep_client.set_camera_parameters.call_args[0][0]
    assert sent.framerate == bp.Framerate.FRAMERATE_FPS_25


def test_configure_rejects_invalid_framerate(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters()
    )
    with pytest.raises(ValueError):
        with mocked_camera.configure() as params:
            params.framerate = 24
    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_not_called()


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_configure_translates_resolution_int_to_enum(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters()
    )
    with mocked_camera.configure() as params:
        params.resolution = 1440
    sent = mocked_camera._parent_drone._req_rep_client.set_camera_parameters.call_args[0][0]
    assert sent.resolution == bp.Resolution.RESOLUTION_QHD_2K


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_configure_rejects_invalid_resolution(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters()
    )
    with pytest.raises(ValueError):
        with mocked_camera.configure() as params:
            params.resolution = 600


def test_configure_warns_on_deprecated_resolution(mocked_camera):
    """The batch must not become the quiet way to keep using the deprecated field."""
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters()
    )
    with pytest.warns(DeprecationWarning, match="stream_resolution"):
        with mocked_camera.configure() as params:
            params.resolution = 1080


def test_configure_reads_back_framerate_and_resolution_as_ints(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters(
            framerate=bp.Framerate.FRAMERATE_FPS_60,
            resolution=bp.Resolution.RESOLUTION_UHD_4K,
        )
    )
    with mocked_camera.configure() as params:
        assert params.framerate == 60
        with pytest.warns(DeprecationWarning):
            assert params.resolution == 2160


def test_configure_rejects_unknown_field_name(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        bp.CameraParameters()
    )
    with pytest.raises(AttributeError):
        with mocked_camera.configure() as params:
            params.not_a_camera_parameter = 1


def camera_parameters_with_unknown_enum(field: str, value: int) -> bp.CameraParameters:
    """Build a CameraParameters reporting an enum value this SDK build does not know.

    proto-plus surfaces an unrecognized enum value as a plain int rather than an enum member,
    which is what a drone running a newer Blunux than the SDK would produce.
    """
    raw = bp.CameraParameters.pb(bp.CameraParameters())
    setattr(raw, field, value)
    return bp.CameraParameters.wrap(raw)


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_get_resolution_raises_runtime_error_on_unknown_enum(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        camera_parameters_with_unknown_enum("resolution", 42)
    )
    with pytest.raises(RuntimeError, match="42"):
        mocked_camera.get_resolution()


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_get_framerate_raises_runtime_error_on_unknown_enum(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        camera_parameters_with_unknown_enum("framerate", 42)
    )
    with pytest.raises(RuntimeError, match="42"):
        mocked_camera.get_framerate()


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_configure_raises_runtime_error_on_unknown_enum(mocked_camera):
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        camera_parameters_with_unknown_enum("framerate", 42)
    )
    with pytest.raises(RuntimeError, match="42"):
        with mocked_camera.configure() as params:
            params.framerate


class TestCalibration:
    CALIBRATION = bp.CameraCalibration(
        fx=1000.0,
        fy=1010.0,
        cx=960.0,
        cy=540.0,
        distortion_coefficients=[-0.1, 0.05, 0.001, -0.002, 0.01],
        image_width=1920,
        image_height=1080,
        is_default=True,
    )

    @staticmethod
    def _seed(camera, **drone_info):
        drone_info_tel = bp.DroneInfoTel(drone_info=bp.DroneInfo(**drone_info))
        camera._parent_drone._telemetry_watcher._state[bp.DroneInfoTel] = bp.DroneInfoTel.serialize(
            drone_info_tel
        )

    def _seed_calibration(self, camera):
        self._seed(camera, model=bp.Model.MODEL_X7, main_camera_calibration=self.CALIBRATION)

    def test_get_calibration_returns_published_calibration(self, mocked_camera):
        self._seed_calibration(mocked_camera)
        assert mocked_camera.get_calibration() == self.CALIBRATION

    @staticmethod
    def _no_telemetry(camera):
        # The fixture runs Blunux 4.4, where a missing telemetry message is fetched from the
        # drone with a request. Answer it with an empty payload, as a drone without the message
        # would.
        camera._parent_drone._req_rep_client.get_telemetry_msg.return_value = bp.GetTelemetryRep()

    def test_get_calibration_is_none_on_missing_telemetry(self, mocked_camera):
        self._no_telemetry(mocked_camera)
        assert mocked_camera.get_calibration() is None

    def test_get_calibration_is_none_when_not_published(self, mocked_camera):
        self._seed(mocked_camera, model=bp.Model.MODEL_X3)
        assert mocked_camera.get_calibration() is None

    def test_get_calibration_is_none_for_guestport_camera(self, mocked_drone):
        from blueye.sdk.camera import Camera

        guestport_camera = Camera(mocked_drone, is_guestport_camera=True)
        self._seed_calibration(guestport_camera)
        assert guestport_camera.get_calibration() is None

    def test_scaled_calibration_to_tuple(self, mocked_camera):
        self._seed_calibration(mocked_camera)
        scaled = mocked_camera.get_scaled_calibration((960, 540))
        assert scaled.fx == 500.0
        assert scaled.fy == 505.0
        assert scaled.cx == 480.0
        assert scaled.cy == 270.0
        assert scaled.image_width == 960
        assert scaled.image_height == 540
        assert scaled.is_default is True
        assert list(scaled.distortion_coefficients) == pytest.approx(
            list(self.CALIBRATION.distortion_coefficients)
        )

    def test_scaled_calibration_to_resolution_enum(self, mocked_camera):
        self._seed_calibration(mocked_camera)
        scaled = mocked_camera.get_scaled_calibration(bp.Resolution.RESOLUTION_UHD_4K)
        assert (scaled.image_width, scaled.image_height) == (3840, 2160)
        assert scaled.fx == 2000.0
        assert scaled.cy == 1080.0

    def test_scaled_calibration_to_480p_uses_the_4_by_3_frame(self, mocked_camera):
        # The drone streams 480p as 640x480, not as the 16:9 853x480 the calibration's aspect
        # ratio would suggest, so fx and cx must scale with the 640 width.
        self._seed_calibration(mocked_camera)
        scaled = mocked_camera.get_scaled_calibration(bp.Resolution.RESOLUTION_VGA_480P)
        assert (scaled.image_width, scaled.image_height) == (640, 480)
        assert scaled.fx == pytest.approx(1000.0 * 640 / 1920)
        assert scaled.cx == pytest.approx(960.0 * 640 / 1920)
        assert scaled.fy == pytest.approx(1010.0 * 480 / 1080)
        assert scaled.cy == pytest.approx(540.0 * 480 / 1080)

    def test_scaled_calibration_defaults_to_480p_stream_resolution(self, mocked_camera):
        self._seed_calibration(mocked_camera)
        mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
            bp.CameraParameters(stream_resolution=bp.Resolution.RESOLUTION_VGA_480P)
        )
        scaled = mocked_camera.get_scaled_calibration()
        assert (scaled.image_width, scaled.image_height) == (640, 480)
        assert scaled.fx == pytest.approx(1000.0 * 640 / 1920)

    @pytest.mark.parametrize(
        "resolution, size",
        [
            (bp.Resolution.RESOLUTION_VGA_480P, (640, 480)),
            (bp.Resolution.RESOLUTION_HD_720P, (1280, 720)),
            (bp.Resolution.RESOLUTION_FULLHD_1080P, (1920, 1080)),
            (bp.Resolution.RESOLUTION_QHD_2K, (2560, 1440)),
            (bp.Resolution.RESOLUTION_UHD_4K, (3840, 2160)),
        ],
        ids=lambda v: v.name if isinstance(v, bp.Resolution) else "",
    )
    def test_scaled_calibration_resolution_frame_sizes(self, mocked_camera, resolution, size):
        self._seed_calibration(mocked_camera)
        scaled = mocked_camera.get_scaled_calibration(resolution)
        assert (scaled.image_width, scaled.image_height) == size

    def test_scaled_calibration_defaults_to_stream_resolution(self, mocked_camera):
        self._seed_calibration(mocked_camera)
        mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
            bp.CameraParameters(stream_resolution=bp.Resolution.RESOLUTION_HD_720P)
        )
        scaled = mocked_camera.get_scaled_calibration()
        assert (scaled.image_width, scaled.image_height) == (1280, 720)
        assert scaled.fx == pytest.approx(1000.0 * 1280 / 1920)

    def test_scaled_calibration_keeps_the_published_calibration_untouched(self, mocked_camera):
        self._seed_calibration(mocked_camera)
        mocked_camera.get_scaled_calibration((960, 540))
        assert mocked_camera.get_calibration() == self.CALIBRATION

    def test_scaled_calibration_is_none_without_calibration(self, mocked_camera):
        self._no_telemetry(mocked_camera)
        assert mocked_camera.get_scaled_calibration((960, 540)) is None

    @pytest.mark.parametrize("resolution", ["1080p", (1920,), (0, 1080), (1920, -1)])
    def test_scaled_calibration_rejects_invalid_resolution(self, mocked_camera, resolution):
        self._seed_calibration(mocked_camera)
        with pytest.raises(ValueError):
            mocked_camera.get_scaled_calibration(resolution)

    def test_scale_calibration_requires_calibration_resolution(self):
        from blueye.sdk.camera import scale_calibration

        with pytest.raises(ValueError):
            scale_calibration(bp.CameraCalibration(fx=1000.0), 1920, 1080)


class Test4kCameraFeatures:
    """The turbidity and color correction filters and digital pan, tilt and zoom.

    They are main-camera-only features of the X3 Ultra and X7 running Blunux 5.0.0 or newer,
    sent as control messages and read back from change-driven telemetry.
    """

    @staticmethod
    def _seed_model(drone, model):
        drone_info_tel = bp.DroneInfoTel(drone_info=bp.DroneInfo(model=model))
        drone._telemetry_watcher._state[bp.DroneInfoTel] = bp.DroneInfoTel.serialize(drone_info_tel)

    @staticmethod
    def _seed(camera, msg_type, msg):
        camera._parent_drone._telemetry_watcher._state[msg_type] = msg_type.serialize(msg)

    @pytest.fixture
    def jetson_camera(self, mocked_drone: Drone):
        """The main camera of an X7 running Blunux 5.0.0."""
        from blueye.sdk.camera import Camera

        mocked_drone.software_version_short = "5.0.0"
        self._seed_model(mocked_drone, bp.Model.MODEL_X7)
        return Camera(mocked_drone)

    @staticmethod
    def _no_telemetry(camera):
        camera._parent_drone._req_rep_client.get_telemetry_msg.return_value = bp.GetTelemetryRep()

    # Getters

    def test_get_turbidity_filter(self, jetson_camera):
        self._seed(
            jetson_camera,
            bp.TurbidityFilterTel,
            bp.TurbidityFilterTel(turbidity_filter={"enabled": True, "intensity": 0.4}),
        )
        settings = jetson_camera.get_turbidity_filter()
        assert settings.enabled is True
        assert settings.intensity == pytest.approx(0.4)

    def test_get_color_correction(self, jetson_camera):
        self._seed(
            jetson_camera,
            bp.ColorCorrectionTel,
            bp.ColorCorrectionTel(color_correction_filter={"enabled": False, "intensity": 0.9}),
        )
        settings = jetson_camera.get_color_correction()
        assert settings.enabled is False
        assert settings.intensity == pytest.approx(0.9)

    def test_get_pan_tilt_zoom(self, jetson_camera):
        self._seed(
            jetson_camera,
            bp.CameraPanTiltZoomTel,
            bp.CameraPanTiltZoomTel(camera_pan_tilt_zoom={"pan": 0.2, "tilt": -0.3, "zoom": 0.5}),
        )
        state = jetson_camera.get_pan_tilt_zoom()
        assert (state.pan, state.tilt, state.zoom) == pytest.approx((0.2, -0.3, 0.5))

    @pytest.mark.parametrize(
        "getter", ["get_turbidity_filter", "get_color_correction", "get_pan_tilt_zoom"]
    )
    def test_getters_are_none_without_telemetry(self, jetson_camera, getter):
        self._no_telemetry(jetson_camera)
        assert getattr(jetson_camera, getter)() is None

    @pytest.mark.parametrize(
        "getter", ["get_turbidity_filter", "get_color_correction", "get_pan_tilt_zoom"]
    )
    def test_getters_are_none_for_guestport_camera(self, mocked_drone, getter):
        from blueye.sdk.camera import Camera

        guestport_camera = Camera(mocked_drone, is_guestport_camera=True)
        assert getattr(guestport_camera, getter)() is None
        mocked_drone._req_rep_client.get_telemetry_msg.assert_not_called()

    # Setters

    def test_set_turbidity_filter(self, jetson_camera):
        jetson_camera.set_turbidity_filter(True, 0.6)
        jetson_camera._parent_drone._ctrl_client.set_turbidity_filter.assert_called_once_with(
            True, 0.6
        )

    def test_set_color_correction(self, jetson_camera):
        jetson_camera.set_color_correction(False, 1.0)
        jetson_camera._parent_drone._ctrl_client.set_color_correction.assert_called_once_with(
            False, 1.0
        )

    def test_set_pan_tilt_zoom(self, jetson_camera):
        jetson_camera.set_pan_tilt_zoom(pan=-0.5, tilt=0.25, zoom=1.0)
        jetson_camera._parent_drone._ctrl_client.set_camera_pan_tilt_zoom.assert_called_once_with(
            -0.5, 0.25, 1.0
        )

    def test_set_pan_tilt_zoom_keeps_omitted_values(self, jetson_camera):
        self._seed(
            jetson_camera,
            bp.CameraPanTiltZoomTel,
            bp.CameraPanTiltZoomTel(camera_pan_tilt_zoom={"pan": 0.2, "tilt": -0.3, "zoom": 0.5}),
        )
        jetson_camera.set_pan_tilt_zoom(zoom=0.8)
        ctrl = jetson_camera._parent_drone._ctrl_client
        (pan, tilt, zoom), _ = ctrl.set_camera_pan_tilt_zoom.call_args
        assert (pan, tilt, zoom) == pytest.approx((0.2, -0.3, 0.8))

    def test_set_pan_tilt_zoom_defaults_to_centre_without_telemetry(self, jetson_camera):
        self._no_telemetry(jetson_camera)
        jetson_camera.set_pan_tilt_zoom(zoom=0.8)
        jetson_camera._parent_drone._ctrl_client.set_camera_pan_tilt_zoom.assert_called_once_with(
            0.0, 0.0, 0.8
        )

    def test_set_pan_tilt_zoom_with_all_values_does_not_read_telemetry(self, jetson_camera):
        jetson_camera.set_pan_tilt_zoom(0.0, 0.0, 0.0)
        jetson_camera._parent_drone._req_rep_client.get_telemetry_msg.assert_not_called()

    # Validation

    @pytest.mark.parametrize("intensity", [-0.1, 1.1, float("nan")])
    def test_filters_reject_out_of_range_intensity(self, jetson_camera, intensity):
        with pytest.raises(ValueError):
            jetson_camera.set_turbidity_filter(True, intensity)
        with pytest.raises(ValueError):
            jetson_camera.set_color_correction(True, intensity)
        jetson_camera._parent_drone._ctrl_client.set_turbidity_filter.assert_not_called()
        jetson_camera._parent_drone._ctrl_client.set_color_correction.assert_not_called()

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"pan": -1.1},
            {"pan": 1.1},
            {"tilt": -1.1},
            {"tilt": 1.1},
            {"zoom": -0.1},
            {"zoom": 1.1},
            {"zoom": float("nan")},
        ],
    )
    def test_pan_tilt_zoom_rejects_out_of_range_values(self, jetson_camera, kwargs):
        with pytest.raises(ValueError):
            jetson_camera.set_pan_tilt_zoom(**kwargs)
        jetson_camera._parent_drone._ctrl_client.set_camera_pan_tilt_zoom.assert_not_called()

    # Gating

    SETTERS = [
        ("set_turbidity_filter", (True, 0.5)),
        ("set_color_correction", (True, 0.5)),
        ("set_pan_tilt_zoom", (0.0, 0.0, 0.5)),
    ]

    @pytest.mark.parametrize("setter, args", SETTERS)
    def test_setters_require_blunux_5(self, mocked_drone, setter, args):
        from blueye.sdk.camera import Camera

        mocked_drone.software_version_short = "4.5.10"
        self._seed_model(mocked_drone, bp.Model.MODEL_X7)
        with pytest.raises(RuntimeError, match="5.0.0"):
            getattr(Camera(mocked_drone), setter)(*args)

    @pytest.mark.parametrize("setter, args", SETTERS)
    def test_setters_require_a_jetson_model(self, mocked_drone, setter, args):
        from blueye.sdk.camera import Camera

        mocked_drone.software_version_short = "5.0.0"
        self._seed_model(mocked_drone, bp.Model.MODEL_X3)
        with pytest.raises(RuntimeError, match="X3 Ultra and X7"):
            getattr(Camera(mocked_drone), setter)(*args)

    @pytest.mark.parametrize("setter, args", SETTERS)
    def test_setters_pass_when_the_model_is_unknown(self, mocked_drone, setter, args):
        from blueye.sdk.camera import Camera

        mocked_drone.software_version_short = "5.0.0"
        mocked_drone._req_rep_client.get_telemetry_msg.return_value = bp.GetTelemetryRep()
        getattr(Camera(mocked_drone), setter)(*args)

    @pytest.mark.parametrize("setter, args", SETTERS)
    def test_setters_reject_the_guestport_camera(self, mocked_drone, setter, args):
        from blueye.sdk.camera import Camera

        mocked_drone.software_version_short = "5.0.0"
        self._seed_model(mocked_drone, bp.Model.MODEL_X7)
        with pytest.raises(RuntimeError, match="main camera"):
            getattr(Camera(mocked_drone, is_guestport_camera=True), setter)(*args)

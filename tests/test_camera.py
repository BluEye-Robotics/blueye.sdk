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
    assert mocked_camera.stream_resolution == bp.Resolution.RESOLUTION_FULLHD_1080P


def test_stream_resolution_setter(mocked_camera):
    old_camera_parameters = bp.CameraParameters(stream_resolution=bp.Resolution.RESOLUTION_HD_720P)

    new_camera_parameters = bp.CameraParameters(
        stream_resolution=bp.Resolution.RESOLUTION_FULLHD_1080P,
        resolution=bp.Resolution.RESOLUTION_FULLHD_1080P,
    )
    mocked_camera._camera_parameters = old_camera_parameters

    mocked_camera.stream_resolution = bp.Resolution.RESOLUTION_FULLHD_1080P
    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once_with(
        new_camera_parameters
    )
    assert (
        mocked_camera._camera_parameters.stream_resolution == bp.Resolution.RESOLUTION_FULLHD_1080P
    )


def test_stream_resolution_invalid_type(mocked_camera):
    with pytest.raises(ValueError):
        mocked_camera.stream_resolution = "invalid_resolution"


def test_recording_resolution_getter(mocked_camera):
    mocked_camera_parameters = bp.CameraParameters(
        recording_resolution=bp.Resolution.RESOLUTION_FULLHD_1080P
    )
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        mocked_camera_parameters
    )
    assert mocked_camera.recording_resolution == bp.Resolution.RESOLUTION_FULLHD_1080P


def test_recording_resolution_setter(mocked_camera):
    old_camera_parameters = bp.CameraParameters(
        recording_resolution=bp.Resolution.RESOLUTION_HD_720P
    )

    new_camera_parameters = bp.CameraParameters(
        recording_resolution=bp.Resolution.RESOLUTION_FULLHD_1080P,
        resolution=bp.Resolution.RESOLUTION_FULLHD_1080P,
    )
    mocked_camera._camera_parameters = old_camera_parameters

    mocked_camera.recording_resolution = bp.Resolution.RESOLUTION_FULLHD_1080P
    mocked_camera._parent_drone._req_rep_client.set_camera_parameters.assert_called_once_with(
        new_camera_parameters
    )
    assert (
        mocked_camera._camera_parameters.recording_resolution
        == bp.Resolution.RESOLUTION_FULLHD_1080P
    )


def test_recording_resolution_invalid_type(mocked_camera):
    with pytest.raises(ValueError):
        mocked_camera.recording_resolution = "invalid_resolution"


def test_old_drones_use_resolution_field(mocked_camera):
    # Set the version to a value that does not support separate recording resolution
    mocked_camera._parent_drone.software_version_short = "4.3"

    mocked_camera_parameters = bp.CameraParameters(resolution=bp.Resolution.RESOLUTION_FULLHD_1080P)
    mocked_camera._parent_drone._req_rep_client.get_camera_parameters.return_value = (
        mocked_camera_parameters
    )

    assert mocked_camera.recording_resolution == bp.Resolution.RESOLUTION_FULLHD_1080P
    assert mocked_camera.stream_resolution == bp.Resolution.RESOLUTION_FULLHD_1080P

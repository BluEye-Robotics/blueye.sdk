import blueye.protocol as bp
import pytest

from blueye.sdk import Drone


@pytest.fixture
def mocked_camera(mocked_drone: Drone):
    from blueye.sdk.camera import Camera

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
        stream_resolution=bp.Resolution.RESOLUTION_FULLHD_1080P
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

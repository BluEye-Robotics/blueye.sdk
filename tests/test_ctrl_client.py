import blueye.protocol as bp
import pytest

from blueye.sdk.connection import CtrlClient


@pytest.fixture
def ctrl_client(mocked_drone_not_connected):
    """A control client whose thread is never started, so the queue keeps what is sent."""
    return CtrlClient(mocked_drone_not_connected)


def test_set_turbidity_filter_queues_message(ctrl_client):
    ctrl_client.set_turbidity_filter(True, 0.5)
    msg = ctrl_client._messages_to_send.get_nowait()
    assert isinstance(msg, bp.SetTurbidityFilterCtrl)
    assert msg.turbidity_filter.enabled is True
    assert msg.turbidity_filter.intensity == pytest.approx(0.5)


def test_set_color_correction_queues_message(ctrl_client):
    ctrl_client.set_color_correction(False, 0.25)
    msg = ctrl_client._messages_to_send.get_nowait()
    assert isinstance(msg, bp.SetColorCorrectionCtrl)
    assert msg.color_correction_filter.enabled is False
    assert msg.color_correction_filter.intensity == pytest.approx(0.25)


def test_set_camera_pan_tilt_zoom_queues_message(ctrl_client):
    ctrl_client.set_camera_pan_tilt_zoom(-0.5, 0.25, 1.0)
    msg = ctrl_client._messages_to_send.get_nowait()
    assert isinstance(msg, bp.CameraPanTiltZoomCtrl)
    ptz = msg.camera_pan_tilt_zoom
    assert (ptz.pan, ptz.tilt, ptz.zoom) == pytest.approx((-0.5, 0.25, 1.0))

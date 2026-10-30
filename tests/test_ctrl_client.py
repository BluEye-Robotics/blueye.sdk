import time

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


def test_rescan_cv_models_queues_message(ctrl_client):
    ctrl_client.rescan_cv_models()
    assert isinstance(ctrl_client._messages_to_send.get_nowait(), bp.RescanCvModelsCtrl)


class TestFlush:
    @pytest.fixture
    def running_client(self, mocker, mocked_drone_not_connected):
        """A control client whose thread runs against a mocked socket."""
        client = CtrlClient(mocked_drone_not_connected, context=mocker.MagicMock())
        client.start()
        yield client
        client._exit_flag.set()
        client.join(timeout=1)

    def test_flush_waits_until_the_thread_has_sent(self, running_client):
        running_client.rescan_cv_models()
        assert running_client.flush(timeout=2) is True
        (frames,), _ = running_client._drone_pub_socket.send_multipart.call_args
        assert frames[0] == b"blueye.protocol.RescanCvModelsCtrl"

    def test_flush_gives_up_when_nothing_sends(self, ctrl_client):
        # The thread is not running, so the message stays queued
        ctrl_client.rescan_cv_models()
        assert ctrl_client.flush(timeout=0.2) is False

    def test_stop_sends_what_is_queued_first(self, running_client):
        # A slow socket keeps messages queued when stop() is called, so they are only all
        # sent if stop() waits for them
        running_client._drone_pub_socket.send_multipart.side_effect = lambda *_: time.sleep(0.05)
        for _ in range(3):
            running_client.rescan_cv_models()
        running_client.stop()
        running_client.join(timeout=1)
        assert not running_client.is_alive()
        assert running_client._drone_pub_socket.send_multipart.call_count == 3

    def test_stop_on_a_thread_that_never_ran_does_not_wait(self, ctrl_client):
        ctrl_client.rescan_cv_models()
        start = time.monotonic()
        ctrl_client.stop()
        assert time.monotonic() - start < 0.5

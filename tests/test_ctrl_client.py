from queue import Queue

from blueye.sdk.connection import CtrlClient


def test_set_recording_state_includes_multibeam():
    client = CtrlClient.__new__(CtrlClient)
    client._messages_to_send = Queue()

    client.set_recording_state(True, False, True)

    message = client._messages_to_send.get_nowait()
    assert message.record_on.main is True
    assert message.record_on.guestport is False
    assert message.record_on.multibeam is True

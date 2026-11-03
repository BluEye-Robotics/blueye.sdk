import blueye.protocol as bp
import pytest

import blueye.sdk


@pytest.fixture
def telemetry_client():
    class OnlyIpDrone:
        _ip = "localhost"

    telemetry_client = blueye.sdk.connection.TelemetryClient(parent_drone=OnlyIpDrone())
    telemetry_client.start()
    yield telemetry_client
    telemetry_client.stop()
    telemetry_client.join()


def test_telemetry_getter(telemetry_client):
    depth_tel = bp.DepthTel.serialize(bp.DepthTel(depth={"value": 1.0}))
    msg = (bytes("blueye.protocol.DepthTel", "utf-8"), depth_tel)
    telemetry_client._handle_message(msg)
    assert telemetry_client.get(bp.DepthTel) == depth_tel


def test_unknown_telemetry_messages_are_ignored(mocker, telemetry_client):
    msg = (bytes("blueye.protocol.UnknownTel", "utf-8"), b"")
    mocked_logger = mocker.patch("blueye.sdk.connection.logger")
    telemetry_client._handle_message(msg)
    assert mocked_logger.info.called


def test_callback_is_called(mocker, telemetry_client):
    callback = mocker.MagicMock()
    telemetry_client.add_callback([bp.DepthTel], callback, raw=False)
    depth_tel = bp.DepthTel.serialize(bp.DepthTel(depth={"value": 1.0}))
    msg = (bytes("blueye.protocol.DepthTel", "utf-8"), depth_tel)
    telemetry_client._handle_message(msg)
    callback.assert_called_with("DepthTel", bp.DepthTel.deserialize(depth_tel))


def test_callback_return_raw(mocker, telemetry_client):
    callback = mocker.MagicMock()
    telemetry_client.add_callback([bp.DepthTel], callback, raw=True)
    depth_tel = bp.DepthTel.serialize(bp.DepthTel(depth={"value": 1.0}))
    msg = (bytes("blueye.protocol.DepthTel", "utf-8"), depth_tel)
    telemetry_client._handle_message(msg)
    callback.assert_called_with("DepthTel", depth_tel)


def test_remove_callback_warns_nonexistant_callback(mocker, telemetry_client):
    mocked_logger = mocker.patch("blueye.sdk.connection.logger")
    telemetry_client.remove_callback("not a uuid")
    mocked_logger.warning.assert_called_once()


def _depth_msg(depth: float):
    depth_tel = bp.DepthTel.serialize(bp.DepthTel(depth={"value": depth}))
    return (bytes("blueye.protocol.DepthTel", "utf-8"), depth_tel)


def test_raising_callback_does_not_stop_other_callbacks_or_later_messages(mocker, telemetry_client):
    mocked_logger = mocker.patch("blueye.sdk.connection.logger")
    raising = mocker.MagicMock(side_effect=RuntimeError("boom"))
    well_behaved = mocker.MagicMock()
    telemetry_client.add_callback([bp.DepthTel], raising, raw=False)
    telemetry_client.add_callback([bp.DepthTel], well_behaved, raw=False)

    first = _depth_msg(1.0)
    second = _depth_msg(2.0)
    telemetry_client._handle_message(first)
    telemetry_client._handle_message(second)

    assert raising.call_count == 2
    assert well_behaved.call_count == 2
    assert mocked_logger.exception.call_count == 2
    assert telemetry_client.get(bp.DepthTel) == second[1]


def test_raising_raw_callback_is_isolated(mocker, telemetry_client):
    mocked_logger = mocker.patch("blueye.sdk.connection.logger")
    raising = mocker.MagicMock(side_effect=ValueError("boom"))
    telemetry_client.add_callback([bp.DepthTel], raising, raw=True)

    telemetry_client._handle_message(_depth_msg(1.0))

    raising.assert_called_once()
    mocked_logger.exception.assert_called_once()


def test_callback_removing_itself_does_not_skip_the_next_callback(mocker, telemetry_client):
    second = mocker.MagicMock()

    def remove_self(msg_type, msg):
        telemetry_client.remove_callback(self_id)

    self_id = telemetry_client.add_callback([bp.DepthTel], remove_self, raw=False)
    telemetry_client.add_callback([bp.DepthTel], second, raw=False)

    telemetry_client._handle_message(_depth_msg(1.0))
    assert second.call_count == 1
    assert [cb.function for cb in telemetry_client._callbacks] == [second]

    telemetry_client._handle_message(_depth_msg(2.0))
    assert second.call_count == 2


def test_callback_added_during_dispatch_runs_from_the_next_message(mocker, telemetry_client):
    late = mocker.MagicMock()

    def add_late(msg_type, msg):
        telemetry_client.add_callback([bp.DepthTel], late, raw=False)
        telemetry_client.remove_callback(adder_id)

    adder_id = telemetry_client.add_callback([bp.DepthTel], add_late, raw=False)

    telemetry_client._handle_message(_depth_msg(1.0))
    late.assert_not_called()
    telemetry_client._handle_message(_depth_msg(2.0))
    late.assert_called_once()

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

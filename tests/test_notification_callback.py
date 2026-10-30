"""Tests for `Drone.notification_callback`, the logger enabled by `log_notifications=True`."""

import datetime
from types import SimpleNamespace

import blueye.protocol as bp
import pytest

from blueye.sdk import Drone


def _notification_tel(type_, level=bp.NotificationLevel.NOTIFICATION_LEVEL_WARNING):
    notification = {
        "timestamp": datetime.datetime(2026, 10, 19, 12, 0, tzinfo=datetime.timezone.utc),
        "level": level,
        "type_": type_,
    }
    tel = bp.NotificationTel(notification=notification)
    # Round-trip through the wire format so an unknown enum value arrives the same way as it does
    # from the drone: as a plain int instead of an enum member.
    return bp.NotificationTel.deserialize(bp.NotificationTel.serialize(tel))


@pytest.fixture
def fake_drone():
    return SimpleNamespace(_last_notification_timestamp=None)


def test_known_notification_type_is_logged_by_name(mocker, fake_drone):
    mocked_logger = mocker.patch("blueye.sdk.drone.logger")
    msg = _notification_tel(bp.NotificationType.NOTIFICATION_TYPE_DRONE_IS_STUCK)

    Drone.notification_callback("NotificationTel", msg, fake_drone)

    mocked_logger.warning.assert_called_once()
    assert "NOTIFICATION_TYPE_DRONE_IS_STUCK" in mocked_logger.warning.call_args.args[0]


@pytest.mark.filterwarnings("ignore:Unrecognized NotificationType enum value")
def test_unknown_notification_type_is_logged_instead_of_raising(mocker, fake_drone):
    mocked_logger = mocker.patch("blueye.sdk.drone.logger")
    unknown_type = max(member.value for member in bp.NotificationType) + 1
    msg = _notification_tel(unknown_type, level=bp.NotificationLevel.NOTIFICATION_LEVEL_ERROR)
    assert not hasattr(msg.notification.type_, "name")

    Drone.notification_callback("NotificationTel", msg, fake_drone)

    mocked_logger.error.assert_called_once()
    assert f"UNKNOWN({unknown_type})" in mocked_logger.error.call_args.args[0]


def test_repeated_notification_is_logged_once(mocker, fake_drone):
    mocked_logger = mocker.patch("blueye.sdk.drone.logger")
    msg = _notification_tel(bp.NotificationType.NOTIFICATION_TYPE_DRONE_IS_STUCK)

    Drone.notification_callback("NotificationTel", msg, fake_drone)
    Drone.notification_callback("NotificationTel", msg, fake_drone)

    mocked_logger.warning.assert_called_once()

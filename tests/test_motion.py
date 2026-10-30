from unittest.mock import Mock

import blueye.protocol as bp
import pytest

from blueye.sdk.connection import CtrlClient


def test_boost_getter_returns_expected_value(mocked_drone):
    mocked_drone.motion._current_boost_setpoints["boost"] = 1
    assert mocked_drone.motion.get_boost() == 1


def test_boost_setter_produces_correct_motion_input_arguments(mocked_drone):
    boost_gain = 0.5
    mocked_drone.motion.set_boost(boost_gain)
    mocked_drone._ctrl_client.set_motion_input.assert_called_with(
        0, 0, 0, 0, 0, boost_gain, roll=0, pitch=0
    )


def test_slow_getter_returns_expected_value(mocked_drone):
    mocked_drone.motion._current_boost_setpoints["slow"] = 1
    assert mocked_drone.motion.get_slow() == 1


def test_slow_setter_produces_correct_motion_input_arguments(mocked_drone):
    slow_gain = 0.3
    mocked_drone.motion.set_slow(slow_gain)
    mocked_drone._ctrl_client.set_motion_input.assert_called_with(
        0, 0, 0, 0, slow_gain, 0, roll=0, pitch=0
    )


def test_roll_getter_returns_expected_value(mocked_drone):
    mocked_drone.motion._current_thruster_setpoints["roll"] = 0.25
    assert mocked_drone.motion.get_roll() == 0.25


def test_roll_setter_produces_correct_motion_input_arguments(mocked_drone):
    mocked_drone.motion.set_roll(0.5)
    mocked_drone._ctrl_client.set_motion_input.assert_called_with(
        0, 0, 0, 0, 0, 0, roll=0.5, pitch=0
    )


def test_pitch_getter_returns_expected_value(mocked_drone):
    mocked_drone.motion._current_thruster_setpoints["pitch"] = -0.25
    assert mocked_drone.motion.get_pitch() == -0.25


def test_pitch_setter_produces_correct_motion_input_arguments(mocked_drone):
    mocked_drone.motion.set_pitch(-0.5)
    mocked_drone._ctrl_client.set_motion_input.assert_called_with(
        0, 0, 0, 0, 0, 0, roll=0, pitch=-0.5
    )


def test_other_setters_keep_roll_and_pitch(mocked_drone):
    """Every setter resends the full setpoint, so roll and pitch must survive a surge change."""
    mocked_drone.motion.set_roll(0.5)
    mocked_drone.motion.set_pitch(-0.5)
    mocked_drone.motion.set_surge(0.1)
    mocked_drone._ctrl_client.set_motion_input.assert_called_with(
        0.1, 0, 0, 0, 0, 0, roll=0.5, pitch=-0.5
    )


def test_roll_and_pitch_are_part_of_the_current_setpoints(mocked_drone):
    mocked_drone.motion.set_roll(0.5)
    mocked_drone.motion.set_pitch(-0.5)
    setpoints = mocked_drone.motion.get_current_thruster_setpoints()
    assert setpoints["roll"] == 0.5
    assert setpoints["pitch"] == -0.5


def test_send_thruster_setpoint_with_roll_and_pitch(mocked_drone):
    mocked_drone.motion.send_thruster_setpoint(0.1, 0.2, 0.3, 0.4, roll=0.5, pitch=0.6)
    mocked_drone._ctrl_client.set_motion_input.assert_called_with(
        0.1, 0.2, 0.3, 0.4, 0, 0, roll=0.5, pitch=0.6
    )
    assert mocked_drone.motion.get_roll() == 0.5
    assert mocked_drone.motion.get_pitch() == 0.6


def test_send_thruster_setpoint_without_roll_and_pitch_clears_them(mocked_drone):
    mocked_drone.motion.set_roll(0.5)
    mocked_drone.motion.set_pitch(-0.5)
    mocked_drone.motion.send_thruster_setpoint(0.1, 0.2, 0.3, 0.4)
    mocked_drone._ctrl_client.set_motion_input.assert_called_with(
        0.1, 0.2, 0.3, 0.4, 0, 0, roll=0.0, pitch=0.0
    )


def test_send_thruster_setpoint_rejects_positional_roll_and_pitch(mocked_drone):
    with pytest.raises(TypeError):
        mocked_drone.motion.send_thruster_setpoint(0.1, 0.2, 0.3, 0.4, 0.5, 0.6)


def test_ctrl_client_motion_input_message_carries_roll_and_pitch():
    """The wire message must carry roll and pitch, not just the SDK's cached setpoints."""
    parent_drone = Mock()
    parent_drone._ip = "192.168.1.101"
    client = CtrlClient(parent_drone, context=Mock())
    client.set_motion_input(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, roll=0.7, pitch=0.8)
    msg = client._messages_to_send.get_nowait()
    assert isinstance(msg, bp.MotionInputCtrl)
    assert msg.motion_input.surge == pytest.approx(0.1)
    assert msg.motion_input.sway == pytest.approx(0.2)
    assert msg.motion_input.heave == pytest.approx(0.3)
    assert msg.motion_input.yaw == pytest.approx(0.4)
    assert msg.motion_input.slow == pytest.approx(0.5)
    assert msg.motion_input.boost == pytest.approx(0.6)
    assert msg.motion_input.roll == pytest.approx(0.7)
    assert msg.motion_input.pitch == pytest.approx(0.8)


def test_ctrl_client_motion_input_defaults_roll_and_pitch_to_zero():
    """Callers that predate roll and pitch keep sending a level setpoint."""
    parent_drone = Mock()
    parent_drone._ip = "192.168.1.101"
    client = CtrlClient(parent_drone, context=Mock())
    client.set_motion_input(0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
    msg = client._messages_to_send.get_nowait()
    assert msg.motion_input.roll == 0
    assert msg.motion_input.pitch == 0


def test_auto_heading_returns_expected_value(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.ControlModeTel] = bp.ControlModeTel.serialize(
        bp.ControlModeTel(state=bp.ControlMode(auto_heading=True))
    )
    assert mocked_drone.motion.is_auto_heading_active() is True


def test_auto_heading_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.motion.is_auto_heading_active() is None


def test_auto_heading_produces_correct_control_message(mocked_drone):
    mocked_drone.motion.enable_auto_heading(True)
    mocked_drone._ctrl_client.set_auto_heading_state.assert_called_with(True)


def test_auto_depth_returns_expected_value(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.ControlModeTel] = bp.ControlModeTel.serialize(
        bp.ControlModeTel(state=bp.ControlMode(auto_depth=True))
    )
    assert mocked_drone.motion.is_auto_depth_active() is True


def test_auto_depth_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.motion.is_auto_depth_active() is None


def test_auto_depth_production_correct_control_message(mocked_drone):
    mocked_drone.motion.enable_auto_depth(True)
    mocked_drone._ctrl_client.set_auto_depth_state.assert_called_with(True)


def test_auto_altitude_returns_expected_value(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.ControlModeTel] = bp.ControlModeTel.serialize(
        bp.ControlModeTel(state=bp.ControlMode(auto_altitude=True))
    )
    assert mocked_drone.motion.is_auto_altitude_active() is True


def test_auto_altitude_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.motion.is_auto_altitude_active() is None


def test_auto_altitude_produces_correct_control_message(mocked_drone):
    mocked_drone.motion.enable_auto_altitude(True)
    mocked_drone._ctrl_client.set_auto_altitude_state.assert_called_with(True)


def test_station_keeping_returns_expected_value(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.ControlModeTel] = bp.ControlModeTel.serialize(
        bp.ControlModeTel(state=bp.ControlMode(station_keeping=True))
    )
    assert mocked_drone.motion.is_station_keeping_active() is True


def test_station_keeping_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.motion.is_station_keeping_active() is None


def test_station_keeping_produces_correct_control_message(mocked_drone):
    mocked_drone.motion.enable_station_keeping(True)
    mocked_drone._ctrl_client.set_station_keeping_state.assert_called_with(True)


def test_weather_vaning_returns_expected_value(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.ControlModeTel] = bp.ControlModeTel.serialize(
        bp.ControlModeTel(state=bp.ControlMode(weather_vaning=True))
    )
    assert mocked_drone.motion.is_weather_vaning_active() is True


def test_weather_vaning_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.motion.is_weather_vaning_active() is None


def test_weather_vaning_produces_correct_control_message(mocked_drone):
    mocked_drone.motion.enable_weather_vaning(True)
    mocked_drone._ctrl_client.set_weather_vaning_state.assert_called_with(True)


def test_zero_setpoints_clears_every_axis_and_gain(mocked_drone):
    mocked_drone.motion.send_thruster_setpoint(0.5, -0.5, 0.2, 0.1, roll=0.3, pitch=-0.3)
    mocked_drone.motion.set_boost(0.8)
    mocked_drone.motion.set_slow(0.4)
    mocked_drone.motion.zero_setpoints()
    assert all(v == 0 for v in mocked_drone.motion.get_current_thruster_setpoints().values())
    assert mocked_drone.motion.get_boost() == 0
    assert mocked_drone.motion.get_slow() == 0
    mocked_drone._ctrl_client.set_motion_input.assert_called_with(0, 0, 0, 0, 0, 0, roll=0, pitch=0)

import blueye.protocol as bp


def test_boost_getter_returns_expected_value(mocked_drone):
    mocked_drone.motion._current_boost_setpoints["boost"] = 1
    assert mocked_drone.motion.boost == 1


def test_boost_setter_produces_correct_motion_input_arguments(mocked_drone):
    boost_gain = 0.5
    mocked_drone.motion.boost = boost_gain
    mocked_drone._ctrl_client.set_motion_input.assert_called_with(0, 0, 0, 0, 0, boost_gain)


def test_slow_getter_returns_expected_value(mocked_drone):
    mocked_drone.motion._current_boost_setpoints["slow"] = 1
    assert mocked_drone.motion.slow == 1


def test_slow_setter_produces_correct_motion_input_arguments(mocked_drone):
    slow_gain = 0.3
    mocked_drone.motion.slow = slow_gain
    mocked_drone._ctrl_client.set_motion_input.assert_called_with(0, 0, 0, 0, slow_gain, 0)


def test_auto_heading_returns_expected_value(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.ControlModeTel] = bp.ControlModeTel.serialize(
        bp.ControlModeTel(state=bp.ControlMode(auto_heading=True))
    )
    assert mocked_drone.motion.auto_heading_active is True


def test_auto_heading_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.motion.auto_heading_active is None


def test_auto_heading_produces_correct_control_message(mocked_drone):
    mocked_drone.motion.auto_heading_active = True
    mocked_drone._ctrl_client.set_auto_heading_state.assert_called_with(True)


def test_auto_depth_returns_expected_value(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.ControlModeTel] = bp.ControlModeTel.serialize(
        bp.ControlModeTel(state=bp.ControlMode(auto_depth=True))
    )
    assert mocked_drone.motion.auto_depth_active is True


def test_auto_depth_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.motion.auto_depth_active is None


def test_auto_depth_production_correct_control_message(mocked_drone):
    mocked_drone.motion.auto_depth_active = True
    mocked_drone._ctrl_client.set_auto_depth_state.assert_called_with(True)


def test_auto_altitude_returns_expected_value(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.ControlModeTel] = bp.ControlModeTel.serialize(
        bp.ControlModeTel(state=bp.ControlMode(auto_altitude=True))
    )
    assert mocked_drone.motion.auto_altitude_active is True


def test_auto_altitude_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.motion.auto_altitude_active is None


def test_auto_altitude_produces_correct_control_message(mocked_drone):
    mocked_drone.motion.auto_altitude_active = True
    mocked_drone._ctrl_client.set_auto_altitude_state.assert_called_with(True)


def test_station_keeping_returns_expected_value(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.ControlModeTel] = bp.ControlModeTel.serialize(
        bp.ControlModeTel(state=bp.ControlMode(station_keeping=True))
    )
    assert mocked_drone.motion.station_keeping_active is True


def test_station_keeping_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.motion.station_keeping_active is None


def test_station_keeping_produces_correct_control_message(mocked_drone):
    mocked_drone.motion.station_keeping_active = True
    mocked_drone._ctrl_client.set_station_keeping_state.assert_called_with(True)


def test_weather_vaning_returns_expected_value(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.ControlModeTel] = bp.ControlModeTel.serialize(
        bp.ControlModeTel(state=bp.ControlMode(weather_vaning=True))
    )
    assert mocked_drone.motion.weather_vaning_active is True


def test_weather_vaning_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.motion.weather_vaning_active is None


def test_weather_vaning_produces_correct_control_message(mocked_drone):
    mocked_drone.motion.weather_vaning_active = True
    mocked_drone._ctrl_client.set_weather_vaning_state.assert_called_with(True)

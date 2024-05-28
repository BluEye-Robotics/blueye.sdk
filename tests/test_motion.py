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


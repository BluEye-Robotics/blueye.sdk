"""The IMU error flags, which drones report from Blunux 5.2."""

import blueye.protocol as bp
import pytest

from blueye.sdk.constants import IMU_ERROR_FLAGS


def _seed_error_flags(drone, **flags):
    msg = bp.ErrorFlagsTel(error_flags=flags)
    drone._telemetry_watcher._state[bp.ErrorFlagsTel] = bp.ErrorFlagsTel.serialize(msg)


def test_the_imu_flags_are_fields_of_the_installed_protocol():
    assert IMU_ERROR_FLAGS <= set(bp.ErrorFlags.meta.fields)


@pytest.mark.parametrize("mocked_drone", ["5.2.0", "5.2.225", "6.0.0"], indirect=True)
def test_drones_on_blunux_5_2_report_the_imu_flags(mocked_drone):
    _seed_error_flags(mocked_drone, imu_hp=True, depth_read=True)
    flags = mocked_drone.get_error_flags()
    assert {flag: flags[flag] for flag in IMU_ERROR_FLAGS} == {
        "imu_1": False,
        "imu_2": False,
        "imu_hp": True,
        "imu_attitude": False,
    }
    assert flags["depth_read"] is True


@pytest.mark.parametrize("mocked_drone", ["3.2.62", "5.1.7", "5.1.17"], indirect=True)
def test_older_drones_leave_the_imu_flags_out(mocked_drone):
    # An older drone never sets them, so they would read as false rather than missing
    _seed_error_flags(mocked_drone, depth_read=True)
    flags = mocked_drone.get_error_flags()
    assert IMU_ERROR_FLAGS.isdisjoint(flags)
    assert flags["depth_read"] is True
    assert set(flags) == set(bp.ErrorFlags.meta.fields) - IMU_ERROR_FLAGS


@pytest.mark.parametrize("mocked_drone", ["5.2.0"], indirect=True)
@pytest.mark.parametrize("attitude_failed, expected", [(False, True), (True, False)])
def test_has_attitude_follows_the_imu_attitude_flag(mocked_drone, attitude_failed, expected):
    _seed_error_flags(mocked_drone, imu_attitude=attitude_failed)
    assert mocked_drone.has_attitude() is expected


@pytest.mark.parametrize("mocked_drone", ["5.2.0"], indirect=True)
def test_has_attitude_is_none_before_the_drone_reports(mocked_drone):
    # On Blunux 3.3 and newer a missing message is asked for, and the mock answers empty
    assert mocked_drone.has_attitude() is None


@pytest.mark.parametrize("mocked_drone", ["3.2.62", "5.1.7"], indirect=True)
def test_has_attitude_needs_blunux_5_2(mocked_drone):
    _seed_error_flags(mocked_drone, imu_attitude=False)
    with pytest.raises(RuntimeError, match="5.2 or higher is required"):
        mocked_drone.has_attitude()

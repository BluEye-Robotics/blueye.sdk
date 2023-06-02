import json
from time import time
from unittest.mock import Mock, PropertyMock

import blueye.protocol as bp
import pytest
import requests
from freezegun import freeze_time

import blueye.sdk
from blueye.sdk import Drone
from blueye.sdk.camera import Camera


class TestLights:
    def test_lights_returns_value(self, mocked_drone):
        lights_tel = bp.LightsTel(lights={"value": 0})
        lights_tel_serialized = lights_tel.__class__.serialize(lights_tel)
        mocked_drone._telemetry_watcher._state[bp.LightsTel] = lights_tel_serialized
        assert mocked_drone.lights == 0


class TestPose:
    @pytest.mark.parametrize("old_angle, new_angle", [(0, 0), (180, 180), (-180, 180), (-1, 359)])
    def test_angle_conversion(self, mocked_drone, old_angle, new_angle):
        attitude_tel = bp.AttitudeTel(
            attitude={"roll": old_angle, "pitch": old_angle, "yaw": old_angle}
        )
        attitude_tel_serialized = attitude_tel.__class__.serialize(attitude_tel)
        mocked_drone._telemetry_watcher._state[bp.AttitudeTel] = attitude_tel_serialized
        pose = mocked_drone.pose
        assert pose["roll"] == new_angle
        assert pose["pitch"] == new_angle
        assert pose["yaw"] == new_angle


def test_documentation_opener(mocker):
    mocked_webbrowser_open = mocker.patch("webbrowser.open", autospec=True)
    import os

    blueye.sdk.__file__ = os.path.abspath("/root/blueye/sdk/__init__.py")

    blueye.sdk.open_local_documentation()

    mocked_webbrowser_open.assert_called_with(os.path.abspath("/root/blueye.sdk_docs/README.html"))


def test_feature_list(mocked_drone):
    mocked_drone._update_drone_info()
    assert mocked_drone.features == ["lasers", "harpoon"]


def test_feature_list_is_empty_on_old_versions(mocked_drone, requests_mock):
    dummy_drone_info = {
        "commit_id_csys": "299238949a",
        "hardware_id": "ea9ac92e1817a1d4",
        "manufacturer": "Blueye Robotics",
        "model_description": "Blueye Pioneer Underwater Drone",
        "model_name": "Blueye Pioneer",
        "model_url": "https://www.blueyerobotics.com",
        "operating_system": "blunux",
        "serial_number": "BYEDP123456",
        "sw_version": "1.3.2-rocko-master",
    }
    requests_mock.get(
        "http://192.168.1.101/diagnostics/drone_info",
        content=json.dumps(dummy_drone_info).encode(),
    )
    mocked_drone._update_drone_info()
    assert mocked_drone.features == []


def test_software_version(mocked_drone):
    mocked_drone._update_drone_info()
    assert mocked_drone.software_version == "3.1.52-honister-master"
    assert mocked_drone.software_version_short == "3.1.52"


def test_connect_fails_on_old_versions(mocked_drone, requests_mock):
    mocked_drone.software_version_short = "1.3.2"
    dummy_drone_info = {
        "commit_id_csys": "299238949a",
        "hardware_id": "ea9ac92e1817a1d4",
        "manufacturer": "Blueye Robotics",
        "model_description": "Blueye Pioneer Underwater Drone",
        "model_name": "Blueye Pioneer",
        "model_url": "https://www.blueyerobotics.com",
        "operating_system": "blunux",
        "serial_number": "BYEDP123456",
        "sw_version": "1.3.2-rocko-master",
    }
    requests_mock.get(
        "http://192.168.1.101/diagnostics/drone_info",
        content=json.dumps(dummy_drone_info).encode(),
    )
    with pytest.raises(RuntimeError):
        mocked_drone.connect()


def test_depth_reading(mocked_drone):
    depth = 10
    depthTel = bp.DepthTel(depth={"value": depth})
    depthTel_serialized = depthTel.__class__.serialize(depthTel)
    mocked_drone._telemetry_watcher._state[bp.DepthTel] = depthTel_serialized
    assert mocked_drone.depth == depth


def test_error_flags(mocked_drone):
    error_flags_tel = bp.ErrorFlagsTel(error_flags={"depth_read": True})
    error_flags_serialized = error_flags_tel.__class__.serialize(error_flags_tel)
    mocked_drone._telemetry_watcher._state[bp.ErrorFlagsTel] = error_flags_serialized
    assert mocked_drone.error_flags["depth_read"] == True


def test_battery_state_of_charge_reading(mocked_drone):
    SoC = 0.77
    batteryTel = bp.BatteryTel(battery={"level": SoC})
    batteryTel_msg = batteryTel.__class__.serialize(batteryTel)
    mocked_drone._telemetry_watcher._state[bp.BatteryTel] = batteryTel_msg
    assert mocked_drone.battery.state_of_charge == pytest.approx(SoC)


def test_still_picture_works(mocked_drone):
    mocked_drone.camera.take_picture()
    mocked_drone._ctrl_client.take_still_picture.assert_called_once()


@pytest.mark.parametrize(
    "exception",
    [
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout,
        requests.exceptions.ConnectionError,
    ],
)
def test_update_drone_info_raises_ConnectionError_when_not_connected(
    requests_mock, mocked_drone, exception
):
    requests_mock.get("http://192.168.1.101/diagnostics/drone_info", exc=exception)
    with pytest.raises(ConnectionError):
        mocked_drone._update_drone_info()


def test_active_video_streams_return_correct_number(mocked_drone: Drone):
    NStreamersTel = bp.NStreamersTel(n_streamers={"main": 1, "guestport": 2})
    NStreamersTel_serialized = NStreamersTel.__class__.serialize(NStreamersTel)
    mocked_drone._telemetry_watcher._state[bp.NStreamersTel] = NStreamersTel_serialized

    assert mocked_drone.active_video_streams["main"] == 1
    assert mocked_drone.active_video_streams["guestport"] == 2


class TestTilt:
    def test_tilt_fails_on_drone_without_tilt(self, mocked_drone: Drone):
        mocked_drone.features = []
        with pytest.raises(RuntimeError):
            mocked_drone.camera.tilt.set_velocity(0)
        with pytest.raises(RuntimeError):
            _ = mocked_drone.camera.tilt.angle
        with pytest.raises(RuntimeError):
            _ = mocked_drone.camera.tilt.stabilization_enabled
        with pytest.raises(RuntimeError):
            mocked_drone.camera.tilt.stabilization_enabled = True

    @pytest.mark.parametrize(
        "tilt_velocity",
        [
            0,
            1,
            -1,
            0.5,
        ],
    )
    def test_setting_tilt_velocity_works(self, mocked_drone, tilt_velocity):
        mocked_drone.features = ["tilt"]
        mocked_drone.camera.tilt.set_velocity(tilt_velocity)
        mocked_drone._ctrl_client.set_tilt_velocity.assert_called_with(tilt_velocity)

    @pytest.mark.parametrize(
        "expected_angle",
        [
            34.0,
            0.0,
            -33.0,
        ],
    )
    def test_tilt_returns_expected_angle(self, mocked_drone, expected_angle):
        mocked_drone.features = ["tilt"]
        TiltAngleTel = bp.TiltAngleTel(angle={"value": expected_angle})
        TiltAngleTel_serialized = bp.TiltAngleTel.serialize(TiltAngleTel)
        mocked_drone._telemetry_watcher._state[bp.TiltAngleTel] = TiltAngleTel_serialized
        assert mocked_drone.camera.tilt.angle == expected_angle

    @pytest.mark.parametrize(
        "expected_state",
        [
            True,
            False,
        ],
    )
    def test_tilt_stabilization_state(self, mocked_drone: Drone, expected_state):
        mocked_drone.features = ["tilt"]
        TiltStabilizationTel = bp.TiltStabilizationTel(state={"enabled": expected_state})
        TiltStabilizationTel_serialized = bp.TiltStabilizationTel.serialize(TiltStabilizationTel)
        mocked_drone._telemetry_watcher._state[
            bp.TiltStabilizationTel
        ] = TiltStabilizationTel_serialized
        assert mocked_drone.camera.tilt.stabilization_enabled == expected_state

    def test_set_tilt_stabilization(self, mocked_drone: Drone):
        mocked_drone.features = ["tilt"]
        mocked_drone.camera.tilt.stabilization_enabled = True
        assert mocked_drone._ctrl_client.set_tilt_stabilization.call_count == 1


class TestConfig:
    def test_water_density_property_returns_correct_value(self, mocked_drone: Drone):
        mocked_drone.config._water_density = 1.0
        assert mocked_drone.config.water_density == 1.0

    def test_setting_density(self, mocked_drone: Drone):
        old_value = mocked_drone.config.water_density
        new_value = old_value + 0.010
        mocked_drone.config.water_density = new_value
        assert mocked_drone.config.water_density == new_value
        mocked_drone._ctrl_client.set_water_density.assert_called_once()

    def test_set_drone_time_is_called_on_connection(self, mocked_drone: Drone):
        with freeze_time("2019-01-01"):
            expected_time = int(time())
            mocked_drone.connect()
            mocked_drone._req_rep_client.sync_time.assert_called_with(expected_time)


class TestMotion:
    def test_boost_getter_returns_expected_value(self, mocked_drone):
        mocked_drone.motion._current_boost_setpoints["boost"] = 1
        assert mocked_drone.motion.boost == 1

    def test_boost_setter_produces_correct_motion_input_arguments(self, mocked_drone):
        boost_gain = 0.5
        mocked_drone.motion.boost = boost_gain
        mocked_drone._ctrl_client.set_motion_input.assert_called_with(0, 0, 0, 0, 0, boost_gain)

    def test_slow_getter_returns_expected_value(self, mocked_drone):
        mocked_drone.motion._current_boost_setpoints["slow"] = 1
        assert mocked_drone.motion.slow == 1

    def test_slow_setter_produces_correct_motion_input_arguments(self, mocked_drone):
        slow_gain = 0.3
        mocked_drone.motion.slow = slow_gain
        mocked_drone._ctrl_client.set_motion_input.assert_called_with(0, 0, 0, 0, slow_gain, 0)


def test_gp_cam_recording(mocked_drone):
    mocked_drone.gp_cam = Camera(mocked_drone, is_guestport_camera=True)
    record_state_tel = bp.RecordStateTel(
        record_state={"main_is_recording": False, "guestport_is_recording": False}
    )
    mocked_drone._telemetry_watcher._state[bp.RecordStateTel] = bp.RecordStateTel.serialize(
        record_state_tel
    )
    mocked_drone.gp_cam.is_recording = True
    mocked_drone._ctrl_client.set_recording_state.assert_called_with(False, True)

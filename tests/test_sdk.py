import json
from time import time
from unittest.mock import Mock, PropertyMock

import blueye.protocol as bp
import pytest
import requests
from freezegun import freeze_time

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


def test_zmq_connection_error(mocked_drone):
    mocked_drone._req_rep_client.ping.side_effect = bp.exceptions.ResponseTimeout
    with pytest.raises(ConnectionError):
        mocked_drone.connect()


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
    assert mocked_drone.software_version == "3.2.62-honister-master"
    assert mocked_drone.software_version_short == "3.2.62"


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
        mocked_drone._telemetry_watcher._state[bp.TiltStabilizationTel] = (
            TiltStabilizationTel_serialized
        )
        assert mocked_drone.camera.tilt.stabilization_enabled == expected_state

    def test_set_tilt_stabilization(self, mocked_drone: Drone):
        mocked_drone.features = ["tilt"]
        mocked_drone.camera.tilt.stabilization_enabled = True
        assert mocked_drone._ctrl_client.set_tilt_stabilization.call_count == 1


class TestConfig:
    def test_water_density_property_returns_correct_value(self, mocked_drone: Drone):
        mocked_drone.config._water_density = 1000.0
        assert mocked_drone.config.water_density == 1000.0

    def test_setting_density(self, mocked_drone: Drone):
        old_value = mocked_drone.config.water_density
        new_value = old_value + 10
        mocked_drone.config.water_density = new_value
        assert mocked_drone.config.water_density == new_value
        mocked_drone._ctrl_client.set_water_density.assert_called_once()

    def test_set_drone_time_is_called_on_connection(self, mocked_drone: Drone):
        with freeze_time("2019-01-01"):
            expected_time = int(time())
            mocked_drone.connect()
            mocked_drone._req_rep_client.sync_time.assert_called_with(expected_time)


def test_altitude_is_none_on_invalid_readings(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.AltitudeTel] = bp.AltitudeTel.serialize(
        bp.AltitudeTel(altitude={"value": 10, "is_valid": False})
    )
    assert mocked_drone.altitude is None


def test_altitude_is_none_on_missing_readings(mocked_drone):
    assert mocked_drone.altitude is None


def test_altitude_is_correct_on_valid_readings(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.AltitudeTel] = bp.AltitudeTel.serialize(
        bp.AltitudeTel(altitude={"value": 10.5, "is_valid": True})
    )
    assert mocked_drone.altitude == 10.5


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


class TestTelemetry:
    def test_get(self, mocked_drone):
        depth_tel = bp.DepthTel(depth={"value": 10})
        mocked_drone._telemetry_watcher._state[bp.DepthTel] = bp.DepthTel.serialize(depth_tel)
        assert mocked_drone.telemetry.get(bp.DepthTel) == depth_tel

    def test_get_returns_none_if_not_available(self, mocked_drone):
        mocked_drone._telemetry_watcher._state = {}
        assert mocked_drone.telemetry.get(bp.DepthTel) is None

    def test_get_sends_request_if_blunux_newer_than_3_3(self, mocked_drone):
        mocked_drone.software_version_short = "3.3.0"
        mocked_drone._telemetry_watcher._state = {}

        mocked_drone._req_rep_client.get_telemetry_msg.return_value = bp.GetTelemetryRep(
            payload={"value": b""}
        )
        mocked_drone.telemetry.get(bp.DepthTel)
        mocked_drone._req_rep_client.get_telemetry_msg.assert_called_once()

    def test_get_no_request_for_blunux_older_than_3_3(self, mocked_drone):
        mocked_drone.software_version_short = "3.2.0"
        mocked_drone._telemetry_watcher._state = {}
        assert mocked_drone.telemetry.get(bp.DepthTel) is None
        mocked_drone._req_rep_client.get_telemetry_msg.assert_not_called()

    def test_get_deserializer(self, mocked_drone):
        depth_tel = bp.DepthTel(depth={"value": 10})
        depth_tel_serialized = bp.DepthTel.serialize(depth_tel)
        mocked_drone._telemetry_watcher._state[bp.DepthTel] = depth_tel_serialized
        assert mocked_drone.telemetry.get(bp.DepthTel, deserialize=True) == depth_tel
        assert mocked_drone.telemetry.get(bp.DepthTel, deserialize=False) == depth_tel_serialized


def test_water_temperature_returns_expected_value(mocked_drone):
    water_temp = 10.5
    water_temp_tel = bp.WaterTemperatureTel(temperature={"value": water_temp})
    water_temp_tel_serialized = bp.WaterTemperatureTel.serialize(water_temp_tel)
    mocked_drone._telemetry_watcher._state[bp.WaterTemperatureTel] = water_temp_tel_serialized
    assert mocked_drone.water_temperature == water_temp


def test_water_temperature_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.water_temperature is None


def test_dive_time_returns_expected_value(mocked_drone):
    dive_time_tel = bp.DiveTimeTel(dive_time={"value": 10})
    dive_time_tel_serialized = bp.DiveTimeTel.serialize(dive_time_tel)
    mocked_drone._telemetry_watcher._state[bp.DiveTimeTel] = dive_time_tel_serialized
    assert mocked_drone.dive_time == 10


def test_dive_time_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.dive_time is None


def test_connect_as_observer(mocked_drone_not_connected):
    mocked_drone_not_connected.connect(connect_as_observer=True)
    mocked_drone_not_connected._req_rep_client.connect_client.assert_called_with(
        client_info=None, is_observer=True
    )


def test_connect_as_observer_ignores_diconnect_other_clients(mocked_drone_not_connected):
    mocked_drone_not_connected.connect(disconnect_other_clients=True, connect_as_observer=True)
    mocked_drone_not_connected._req_rep_client.disconnect_client.assert_not_called()

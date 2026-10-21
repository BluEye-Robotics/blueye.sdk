import json
from time import time
from unittest.mock import Mock, NonCallableMock, PropertyMock

import blueye.protocol as bp
import pytest
from unittest.mock import call
import requests
from freezegun import freeze_time

from blueye.sdk import Drone
from blueye.sdk.camera import Camera


class TestLights:
    def test_lights_returns_value(self, mocked_drone):
        lights_tel = bp.LightsTel(lights={"value": 0})
        lights_tel_serialized = lights_tel.__class__.serialize(lights_tel)
        mocked_drone._telemetry_watcher._state[bp.LightsTel] = lights_tel_serialized
        assert mocked_drone.get_lights() == 0


class TestPose:
    @pytest.mark.parametrize("old_angle, new_angle", [(0, 0), (180, 180), (-180, 180), (-1, 359)])
    def test_angle_conversion(self, mocked_drone, old_angle, new_angle):
        attitude_tel = bp.AttitudeTel(
            attitude={"roll": old_angle, "pitch": old_angle, "yaw": old_angle}
        )
        attitude_tel_serialized = attitude_tel.__class__.serialize(attitude_tel)
        mocked_drone._telemetry_watcher._state[bp.AttitudeTel] = attitude_tel_serialized
        pose = mocked_drone.get_pose()
        assert pose["roll"] == new_angle
        assert pose["pitch"] == new_angle
        assert pose["yaw"] == new_angle

    def test_pose_is_none_without_telemetry(self, mocked_drone):
        assert mocked_drone.get_pose() is None


class TestAttitude:
    @pytest.mark.parametrize("roll, pitch, yaw", [(0, 0, 0), (-1.5, 2.5, -179), (180, -180, 90)])
    def test_angles_keep_their_sign(self, mocked_drone, roll, pitch, yaw):
        attitude_tel = bp.AttitudeTel(attitude={"roll": roll, "pitch": pitch, "yaw": yaw})
        mocked_drone._telemetry_watcher._state[bp.AttitudeTel] = bp.AttitudeTel.serialize(
            attitude_tel
        )
        attitude = mocked_drone.get_attitude()
        assert attitude["roll"] == pytest.approx(roll)
        assert attitude["pitch"] == pytest.approx(pitch)
        assert attitude["yaw"] == pytest.approx(yaw)

    def test_attitude_is_none_without_telemetry(self, mocked_drone):
        assert mocked_drone.get_attitude() is None


def test_mocked_drone_is_isolated_from_live_telemetry(mocked_drone):
    """Unit tests must never read telemetry off the network.

    `mocked_drone` used to build a real TelemetryClient, which subscribes to the drone IP. With
    a drone on the same network that fills the state within a few hundred milliseconds, and the
    tests asserting that a getter returns None when no telemetry has been received start failing
    at random.
    """
    # A spec'd mock passes isinstance() against the class it specs, so check for the mock
    # itself rather than asserting the watcher is not a TelemetryClient.
    assert isinstance(mocked_drone._telemetry_watcher, NonCallableMock)
    assert mocked_drone.telemetry.get(bp.ControlModeTel) is None


def test_zmq_connection_error(mocked_drone):
    mocked_drone._req_rep_client.ping.side_effect = bp.exceptions.ResponseTimeout
    with pytest.raises(ConnectionError):
        mocked_drone.connect()


def test_feature_list(mocked_drone):
    mocked_drone._update_drone_info()
    assert mocked_drone.features == ["tilt"]


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
    assert mocked_drone.get_depth() == depth


def test_error_flags(mocked_drone):
    error_flags_tel = bp.ErrorFlagsTel(error_flags={"depth_read": True})
    error_flags_serialized = error_flags_tel.__class__.serialize(error_flags_tel)
    mocked_drone._telemetry_watcher._state[bp.ErrorFlagsTel] = error_flags_serialized
    assert mocked_drone.get_error_flags()["depth_read"] == True


def test_battery_state_of_charge_reading(mocked_drone):
    SoC = 0.77
    batteryTel = bp.BatteryTel(battery={"level": SoC})
    batteryTel_msg = batteryTel.__class__.serialize(batteryTel)
    mocked_drone._telemetry_watcher._state[bp.BatteryTel] = batteryTel_msg
    assert mocked_drone.battery.get_state_of_charge() == pytest.approx(SoC)


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

    assert mocked_drone.get_active_video_streams()["main"] == 1
    assert mocked_drone.get_active_video_streams()["guestport"] == 2


class TestTilt:
    def test_tilt_fails_on_drone_without_tilt(self, mocked_drone: Drone):
        mocked_drone.features = []
        with pytest.raises(RuntimeError):
            mocked_drone.camera.tilt.set_velocity(0)
        with pytest.raises(RuntimeError):
            _ = mocked_drone.camera.tilt.get_angle()
        with pytest.raises(RuntimeError):
            _ = mocked_drone.camera.tilt.is_stabilization_enabled()
        with pytest.raises(RuntimeError):
            mocked_drone.camera.tilt.enable_stabilization(True)

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
        assert mocked_drone.camera.tilt.get_angle() == expected_angle

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
        assert mocked_drone.camera.tilt.is_stabilization_enabled() == expected_state

    def test_set_tilt_stabilization(self, mocked_drone: Drone):
        mocked_drone.features = ["tilt"]
        mocked_drone.camera.tilt.enable_stabilization(True)
        assert mocked_drone._ctrl_client.set_tilt_stabilization.call_count == 1


class TestConfig:
    def test_water_density_returns_correct_value(self, mocked_drone: Drone):
        mocked_drone.config._water_density = 1000.0
        assert mocked_drone.config.get_water_density() == 1000.0

    def test_setting_density(self, mocked_drone: Drone):
        old_value = mocked_drone.config.get_water_density()
        new_value = old_value + 10
        mocked_drone.config.set_water_density(new_value)
        assert mocked_drone.config.get_water_density() == new_value
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
    assert mocked_drone.get_altitude() is None


def test_altitude_is_none_on_missing_readings(mocked_drone):
    assert mocked_drone.get_altitude() is None


def test_altitude_is_correct_on_valid_readings(mocked_drone):
    mocked_drone._telemetry_watcher._state[bp.AltitudeTel] = bp.AltitudeTel.serialize(
        bp.AltitudeTel(altitude={"value": 10.5, "is_valid": True})
    )
    assert mocked_drone.get_altitude() == 10.5


def test_gp_cam_recording(mocked_drone):
    mocked_drone.gp_cam = Camera(mocked_drone, is_guestport_camera=True)
    record_state_tel = bp.RecordStateTel(
        record_state={"main_is_recording": False, "guestport_is_recording": False}
    )
    mocked_drone._telemetry_watcher._state[bp.RecordStateTel] = bp.RecordStateTel.serialize(
        record_state_tel
    )
    mocked_drone.gp_cam.set_recording(True)
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
    assert mocked_drone.get_water_temperature() == water_temp


def test_water_temperature_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.get_water_temperature() is None


def test_dive_time_returns_expected_value(mocked_drone):
    dive_time_tel = bp.DiveTimeTel(dive_time={"value": 10})
    dive_time_tel_serialized = bp.DiveTimeTel.serialize(dive_time_tel)
    mocked_drone._telemetry_watcher._state[bp.DiveTimeTel] = dive_time_tel_serialized
    assert mocked_drone.get_dive_time() == 10


def test_dive_time_returns_none_on_missing_telemetry(mocked_drone):
    assert mocked_drone.get_dive_time() is None


def test_connect_as_observer(mocked_drone_not_connected):
    mocked_drone_not_connected.connect(connect_as_observer=True)
    mocked_drone_not_connected._req_rep_client.connect_client.assert_called_with(
        client_info=None, is_observer=True
    )


def test_connect_as_observer_ignores_diconnect_other_clients(mocked_drone_not_connected):
    mocked_drone_not_connected.connect(disconnect_other_clients=True, connect_as_observer=True)
    mocked_drone_not_connected._req_rep_client.disconnect_client.assert_not_called()


class TestDroneInfo:
    @staticmethod
    def _seed(mocked_drone, **drone_info):
        drone_info_tel = bp.DroneInfoTel(drone_info=bp.DroneInfo(**drone_info))
        mocked_drone._telemetry_watcher._state[bp.DroneInfoTel] = bp.DroneInfoTel.serialize(
            drone_info_tel
        )

    def test_get_drone_info_returns_message(self, mocked_drone):
        self._seed(mocked_drone, model=bp.Model.MODEL_X7, serial_number=b"BYEDP230000")
        drone_info = mocked_drone.get_drone_info()
        assert drone_info.model == bp.Model.MODEL_X7
        assert drone_info.serial_number == b"BYEDP230000"

    def test_getters_return_none_on_missing_telemetry(self, mocked_drone):
        assert mocked_drone.get_drone_info() is None
        assert mocked_drone.get_model() is None
        assert mocked_drone.get_power_source() is None
        assert mocked_drone.get_depth_sensor_type() is None
        assert mocked_drone.is_jetson_platform() is None

    def test_get_model(self, mocked_drone):
        self._seed(mocked_drone, model=bp.Model.MODEL_X3_ULTRA)
        assert mocked_drone.get_model() == bp.Model.MODEL_X3_ULTRA

    def test_get_power_source(self, mocked_drone):
        self._seed(mocked_drone, power_source=bp.PowerSource.POWER_SOURCE_PARALLEL_BATTERIES)
        assert mocked_drone.get_power_source() == bp.PowerSource.POWER_SOURCE_PARALLEL_BATTERIES

    def test_get_depth_sensor_type(self, mocked_drone):
        self._seed(
            mocked_drone, depth_sensor=bp.PressureSensorType.PRESSURE_SENSOR_TYPE_KELLER_PA7LD
        )
        assert (
            mocked_drone.get_depth_sensor_type()
            == bp.PressureSensorType.PRESSURE_SENSOR_TYPE_KELLER_PA7LD
        )

    @pytest.mark.parametrize("model", list(bp.Model), ids=lambda m: m.name)
    def test_is_jetson_platform(self, mocked_drone, model):
        self._seed(mocked_drone, model=model)
        expected = model in (bp.Model.MODEL_X3_ULTRA, bp.Model.MODEL_X7)
        assert mocked_drone.is_jetson_platform() is expected

    def test_jetson_models_excludes_retired_prototype(self):
        from blueye.sdk.constants import JETSON_MODELS

        assert JETSON_MODELS == {bp.Model.MODEL_X3_ULTRA, bp.Model.MODEL_X7}
        assert bp.Model.MODEL_NEXT not in JETSON_MODELS


class TestMockedDroneX7:
    """The X7 fixture models what the unit tests need from the newest drone."""

    def test_http_drone_info(self, mocked_drone_x7):
        assert mocked_drone_x7.software_version_short == "5.0.0"
        assert mocked_drone_x7.features == ["gpdrone"]
        assert mocked_drone_x7.serial_number == "BYEDP260000"

    def test_model(self, mocked_drone_x7):
        assert mocked_drone_x7.get_model() == bp.Model.MODEL_X7
        assert mocked_drone_x7.is_jetson_platform() is True
        assert mocked_drone_x7.get_power_source() == bp.PowerSource.POWER_SOURCE_PARALLEL_BATTERIES

    def test_two_battery_packs(self, mocked_drone_x7):
        battery_tel = mocked_drone_x7.telemetry.get(bp.BatteryTel)
        assert battery_tel.battery.level == pytest.approx(0.8)
        assert battery_tel.second_battery.level == pytest.approx(0.7)

    def test_six_guest_ports(self, mocked_drone_x7):
        gp = mocked_drone_x7.get_drone_info().gp
        assert (
            gp.gp1.device_list.devices[0].device_id
            == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_GNSS_DEVICE
        )
        assert (
            gp.gp2.device_list.devices[0].device_id
            == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_WATERLINKED_DVL_A50
        )
        assert (
            gp.gp4.device_list.devices[0].device_id
            == bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_LIGHT
        )
        for port in (gp.gp3, gp.gp5, gp.gp6):
            assert port.error == bp.GuestPortError.GUEST_PORT_ERROR_NOT_CONNECTED

    def test_peripherals_discovered_on_connect(self, mocked_drone_x7):
        assert [p.port_number for p in mocked_drone_x7.peripherals] == [
            bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1,
            bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_2,
            bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_4,
        ]
        from blueye.sdk.guestport import GuestPortLight

        assert isinstance(mocked_drone_x7.external_light, GuestPortLight)


class TestFailedConnect:
    """A connect() that fails must not leave threads behind.

    A watchdog thread that outlives a failed connect() pets the drone as client 0, which the
    drone takes as the client in control whenever nobody is, so the drone's failsafe never trips.
    """

    @staticmethod
    def _clients(drone):
        return (
            drone._telemetry_watcher,
            drone._req_rep_client,
            drone._ctrl_client,
            drone._watchdog_publisher,
        )

    def _assert_torn_down(self, drone, started):
        from blueye.sdk.drone import _NoConnectionClient

        for client in started:
            client.stop.assert_called_once()
        for client in self._clients(drone):
            assert isinstance(client, _NoConnectionClient)
        assert drone.connected is False
        assert drone.in_control is False

    def test_failed_ping_stops_the_threads(
        self,
        mocked_drone_not_connected,
        mocked_req_rep_client,
        mocked_telemetry_client,
        mocked_ctrl_client,
        mocked_watchdog_publisher,
    ):
        drone = mocked_drone_not_connected
        mocked_req_rep_client.return_value.ping.side_effect = bp.exceptions.ResponseTimeout
        with pytest.raises(ConnectionError):
            drone.connect()
        started = [
            m.return_value
            for m in (mocked_req_rep_client, mocked_telemetry_client, mocked_ctrl_client)
        ]
        self._assert_torn_down(drone, started)
        mocked_watchdog_publisher.return_value.start.assert_not_called()

    def test_failed_connect_request_stops_the_threads(
        self,
        mocked_drone_not_connected,
        mocked_req_rep_client,
        mocked_telemetry_client,
        mocked_ctrl_client,
        mocked_watchdog_publisher,
    ):
        drone = mocked_drone_not_connected
        req_rep = mocked_req_rep_client.return_value
        req_rep.connect_client.side_effect = bp.exceptions.ResponseTimeout
        with pytest.raises(ConnectionError):
            drone.connect()
        started = [
            m.return_value
            for m in (mocked_req_rep_client, mocked_telemetry_client, mocked_ctrl_client)
        ]
        self._assert_torn_down(drone, started)
        mocked_watchdog_publisher.return_value.start.assert_not_called()

    def test_failure_after_the_connect_request_stops_everything(
        self,
        mocked_drone_not_connected,
        mocked_req_rep_client,
        mocked_telemetry_client,
        mocked_ctrl_client,
        mocked_watchdog_publisher,
    ):
        drone = mocked_drone_not_connected
        req_rep = mocked_req_rep_client.return_value
        req_rep.connect_client.return_value = bp.ConnectClientRep(
            client_id=1, client_id_in_control=1
        )
        req_rep.sync_time.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError, match="boom"):
            drone.connect()
        started = [
            m.return_value
            for m in (
                mocked_req_rep_client,
                mocked_telemetry_client,
                mocked_ctrl_client,
                mocked_watchdog_publisher,
            )
        ]
        self._assert_torn_down(drone, started)

    def test_watchdog_starts_once_the_client_id_is_known(
        self, mocked_drone_not_connected, mocked_req_rep_client, mocked_watchdog_publisher
    ):
        drone = mocked_drone_not_connected
        watchdog = mocked_watchdog_publisher.return_value

        def connect_client(**kwargs):
            watchdog.start.assert_not_called()
            assert drone.client_id is None
            return bp.ConnectClientRep(client_id=7, client_id_in_control=7)

        mocked_req_rep_client.return_value.connect_client.side_effect = connect_client
        drone.connect()
        watchdog.start.assert_called_once()
        assert drone.client_id == 7

    def test_disconnect_after_a_failed_connect_is_harmless(
        self, mocked_drone_not_connected, mocked_req_rep_client
    ):
        drone = mocked_drone_not_connected
        mocked_req_rep_client.return_value.ping.side_effect = bp.exceptions.ResponseTimeout
        with pytest.raises(ConnectionError):
            drone.connect()
        with pytest.raises(ConnectionError):
            drone.disconnect()


class TestZeroThrustOnDisconnect:
    """The drone keeps the last motion input until a new one arrives, so leaving sends zeros.

    The fixture's own connect() ran before its connect reply was mocked, so the tests that need
    control connect again first. After disconnect() the client attributes are placeholders, so
    the mocks are taken before.
    """

    def test_connect_zeroes_every_setpoint(self, mocked_drone):
        mocked_drone.connect()
        assert mocked_drone.in_control is True
        mocked_drone._ctrl_client.set_motion_input.assert_called_with(
            0, 0, 0, 0, 0, 0, roll=0, pitch=0
        )

    def test_connect_zeroes_and_flushes_before_the_first_pet(
        self,
        mocked_drone_not_connected,
        mocked_req_rep_client,
        mocked_ctrl_client,
        mocked_watchdog_publisher,
    ):
        drone = mocked_drone_not_connected
        mocked_req_rep_client.return_value.connect_client.return_value = bp.ConnectClientRep(
            client_id=1, client_id_in_control=1
        )
        ctrl = mocked_ctrl_client.return_value

        def start():
            ctrl.set_motion_input.assert_called_once_with(0, 0, 0, 0, 0, 0, roll=0, pitch=0)
            ctrl.flush.assert_called_once()

        mocked_watchdog_publisher.return_value.start.side_effect = start
        drone.connect()
        mocked_watchdog_publisher.return_value.start.assert_called_once()

    @staticmethod
    def _drone_reports_controller(drone, client_id_in_control):
        """Answer the fresh request disconnect() makes on Blunux 3.3+ with this controller."""
        drone.software_version_short = "5.0.0"
        tel = bp.ConnectedClientsTel(client_id_in_control=client_id_in_control)
        drone._req_rep_client.get_telemetry_msg.return_value = bp.GetTelemetryRep(
            payload={
                "type_url": "type.googleapis.com/blueye.protocol.ConnectedClientsTel",
                "value": bp.ConnectedClientsTel.serialize(tel),
            }
        )

    def test_disconnect_zeroes_when_promoted_to_control_meanwhile(self, mocked_drone):
        # Connected behind another client, then that client left and the drone promoted us
        mocked_drone._req_rep_client.connect_client.return_value = bp.ConnectClientRep(
            client_id=2, client_id_in_control=1
        )
        mocked_drone.connect()
        assert mocked_drone.in_control is False
        ctrl = mocked_drone._ctrl_client
        ctrl.set_motion_input.assert_not_called()
        self._drone_reports_controller(mocked_drone, 2)
        mocked_drone.disconnect()
        ctrl.set_motion_input.assert_called_once_with(0, 0, 0, 0, 0, 0, roll=0, pitch=0)

    def test_disconnect_zeroes_when_the_flag_says_so_and_the_report_says_nobody(self, mocked_drone):
        # For a moment after a handover the drone reports nobody in control
        mocked_drone.connect()
        assert mocked_drone.in_control is True
        ctrl = mocked_drone._ctrl_client
        ctrl.set_motion_input.reset_mock()
        self._drone_reports_controller(mocked_drone, 0)
        mocked_drone.disconnect()
        ctrl.set_motion_input.assert_called_once_with(0, 0, 0, 0, 0, 0, roll=0, pitch=0)

    def test_displaced_client_does_not_zero_the_new_pilot(self, mocked_drone):
        # We had control, another client took it. Motion input carries no client id, so a zero
        # from us would cut the new pilot's input
        mocked_drone.connect()
        assert mocked_drone.in_control is True
        ctrl = mocked_drone._ctrl_client
        ctrl.set_motion_input.reset_mock()
        self._drone_reports_controller(mocked_drone, 5)
        mocked_drone.disconnect()
        ctrl.set_motion_input.assert_not_called()

    def test_disconnect_falls_back_to_the_flag_without_a_report(self, mocked_drone):
        mocked_drone.connect()
        mocked_drone.software_version_short = "5.0.0"
        ctrl = mocked_drone._ctrl_client
        ctrl.set_motion_input.reset_mock()
        mocked_drone._req_rep_client.get_telemetry_msg.side_effect = bp.exceptions.ResponseTimeout
        mocked_drone.disconnect()
        ctrl.set_motion_input.assert_called_once_with(0, 0, 0, 0, 0, 0, roll=0, pitch=0)

    def test_old_drones_use_the_cached_report(self, mocked_drone):
        # Blunux before 3.3 cannot be asked for a telemetry message, the cache is all there is
        mocked_drone.connect()
        assert mocked_drone.software_version_short == "3.2.62"
        ctrl = mocked_drone._ctrl_client
        req_rep = mocked_drone._req_rep_client
        ctrl.set_motion_input.reset_mock()
        mocked_drone._telemetry_watcher._state[bp.ConnectedClientsTel] = (
            bp.ConnectedClientsTel.serialize(bp.ConnectedClientsTel(client_id_in_control=5))
        )
        mocked_drone.disconnect()
        ctrl.set_motion_input.assert_not_called()
        req_rep.get_telemetry_msg.assert_not_called()

    def test_connect_zeroes_again_at_the_end(self, mocked_drone):
        # Once before the watchdog thread starts, once after the setup, see connect()
        ctrl = mocked_drone._ctrl_client
        ctrl.set_motion_input.reset_mock()
        mocked_drone.connect()
        zeros = [
            c
            for c in ctrl.set_motion_input.call_args_list
            if c == call(0, 0, 0, 0, 0, 0, roll=0, pitch=0)
        ]
        assert len(zeros) == 2

    def test_disconnect_in_control_zeroes_flushes_then_leaves(self, mocked_drone):
        mocked_drone.connect()
        ctrl = mocked_drone._ctrl_client
        req_rep = mocked_drone._req_rep_client
        ctrl.set_motion_input.reset_mock()
        ctrl.flush.reset_mock()  # connect() flushed its own zero setpoint
        mocked_drone.motion.set_surge(0.7)
        assert mocked_drone.in_control is True

        def disconnect_client(client_id):
            ctrl.set_motion_input.assert_called_with(0, 0, 0, 0, 0, 0, roll=0, pitch=0)
            ctrl.flush.assert_called_once_with(1.0)
            return bp.DisconnectClientRep()

        req_rep.disconnect_client.side_effect = disconnect_client
        mocked_drone.disconnect()
        req_rep.disconnect_client.assert_called_once_with(1)
        assert mocked_drone.connected is False

    def test_disconnect_passes_the_flush_timeout(self, mocked_drone):
        mocked_drone.connect()
        ctrl = mocked_drone._ctrl_client
        ctrl.flush.reset_mock()  # connect() flushed its own zero setpoint
        mocked_drone.disconnect(timeout=2.5)
        ctrl.flush.assert_called_once_with(2.5)

    def test_disconnect_warns_when_the_zero_setpoint_did_not_go_out(self, mocked_drone, caplog):
        mocked_drone.connect()
        mocked_drone._ctrl_client.flush.return_value = False
        with caplog.at_level("WARNING", logger="blueye.sdk.drone"):
            mocked_drone.disconnect()
        assert "did not go out" in caplog.text

    def test_observer_disconnect_sends_no_motion_input(
        self, mocked_drone_not_connected, mocked_req_rep_client, mocked_ctrl_client
    ):
        drone = mocked_drone_not_connected
        mocked_req_rep_client.return_value.connect_client.return_value = bp.ConnectClientRep(
            client_id=2, client_id_in_control=1
        )
        drone.connect(connect_as_observer=True)
        assert drone.in_control is False
        ctrl = mocked_ctrl_client.return_value
        ctrl.set_motion_input.assert_not_called()
        drone.disconnect()
        ctrl.set_motion_input.assert_not_called()
        ctrl.flush.assert_not_called()


class TestContextManagerAndExit:
    def test_with_block_disconnects(self, mocked_drone, mocker):
        disconnect = mocker.spy(mocked_drone, "disconnect")
        with mocked_drone as drone:
            assert drone is mocked_drone
            disconnect.assert_not_called()
        disconnect.assert_called_once()
        assert mocked_drone.connected is False

    def test_with_block_disconnects_on_an_exception(self, mocked_drone, mocker):
        disconnect = mocker.spy(mocked_drone, "disconnect")
        with pytest.raises(ValueError):
            with mocked_drone:
                raise ValueError("boom")
        disconnect.assert_called_once()

    def test_with_block_on_a_disconnected_drone_does_nothing(self, mocked_drone, mocker):
        mocked_drone.disconnect()
        disconnect = mocker.spy(mocked_drone, "disconnect")
        with mocked_drone:
            pass
        disconnect.assert_not_called()

    def test_exit_hook_disconnects_connected_drones_only(self, mocked_drone, mocker):
        from blueye.sdk.drone import _connected_drones, _disconnect_at_exit

        assert mocked_drone in _connected_drones
        disconnect = mocker.spy(mocked_drone, "disconnect")
        _disconnect_at_exit()
        disconnect.assert_called_once()
        assert mocked_drone not in _connected_drones
        _disconnect_at_exit()
        disconnect.assert_called_once()

    def test_exit_hook_survives_a_failing_disconnect(self, mocked_drone, mocker, caplog):
        from blueye.sdk.drone import _disconnect_at_exit

        mocker.patch.object(mocked_drone, "disconnect", side_effect=RuntimeError("gone"))
        with caplog.at_level("WARNING", logger="blueye.sdk.drone"):
            _disconnect_at_exit()
        assert "Could not disconnect" in caplog.text

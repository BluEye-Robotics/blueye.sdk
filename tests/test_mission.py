from pathlib import Path

import blueye.protocol as bp
import pytest

import blueye.sdk
import blueye.sdk.mission
from blueye.sdk.mission import prepare_new_mission

tilt_camera_center = bp.Instruction(tilt_main_camera_command={"tilt_angle": {"value": 0.0}})
tilt_camera_top = bp.Instruction(tilt_main_camera_command={"tilt_angle": {"value": 30.0}})
tilt_camera_bottom = bp.Instruction(tilt_main_camera_command={"tilt_angle": {"value": -30.0}})
wait = bp.Instruction(wait_for_command={"wait_for_seconds": 4})

example_mission = prepare_new_mission(
    instruction_list=[tilt_camera_top, wait, tilt_camera_bottom, wait, tilt_camera_center],
    mission_id=0,
    mission_name="Example mission",
)


@pytest.fixture
def mocked_drone(mocked_drone: blueye.sdk.Drone, mocker):
    mocked_drone.software_version_short = "4.0.5"
    mocked_drone.telemetry = mocker.patch("blueye.sdk.drone.Telemetry")
    return mocked_drone


@pytest.fixture
def mocked_open(mocker):
    return mocker.patch("blueye.sdk.mission.open", mocker.mock_open())


def test_mission_planning_on_old_versions_raises_exception(mocked_drone):
    mocked_drone.software_version_short = "3.2.62"
    with pytest.raises(RuntimeError):
        mocked_drone.mission.get_status()
    with pytest.raises(RuntimeError):
        mocked_drone.mission.get_active()
    with pytest.raises(RuntimeError):
        mocked_drone.mission.send_new(example_mission)
    with pytest.raises(RuntimeError):
        mocked_drone.mission.run()
    with pytest.raises(RuntimeError):
        mocked_drone.mission.pause()
    with pytest.raises(RuntimeError):
        mocked_drone.mission.clear()


def test_get_status_returns_none_on_missing_telemetry(mocked_drone):
    mocked_drone.telemetry.get.return_value = None
    assert mocked_drone.mission.get_status() is None


def test_get_status_returns_mission_status(mocked_drone):
    mission_status = bp.MissionStatus({"state": bp.MissionState.MISSION_STATE_READY})
    mission_status_tel = bp.MissionStatusTel(mission_status=mission_status)
    mocked_drone.telemetry.get.return_value = mission_status_tel

    assert mocked_drone.mission.get_status() == mission_status


def test_get_active_returns_active_mission(mocked_drone):
    mocked_drone._req_rep_client.get_active_mission.return_value = bp.GetMissionRep(
        mission=example_mission
    )
    active_mission = mocked_drone.mission.get_active()
    assert active_mission == example_mission


def test_send_new_sends_mission(mocked_drone):
    mocked_drone.mission.send_new(example_mission)
    mocked_drone._req_rep_client.set_mission.assert_called_once_with(example_mission)


def test_run_calls_run_mission(mocked_drone):
    mocked_drone.mission.run()
    mocked_drone._ctrl_client.run_mission.assert_called_once()


def test_pause_calls_pause_mission(mocked_drone):
    mocked_drone.mission.pause()
    mocked_drone._ctrl_client.pause_mission.assert_called_once()


def test_clear_calls_clear_mission(mocked_drone):
    mocked_drone.mission.clear()
    mocked_drone._ctrl_client.clear_mission.assert_called_once()


def test_export_to_json_with_no_path(mocked_open):
    blueye.sdk.mission.export_to_json(example_mission)
    mocked_open.assert_called_once_with(Path("BlueyeMission.json"), "w")


def test_export_to_json_with_directory(mocked_open):
    blueye.sdk.mission.export_to_json(example_mission, output_path=Path("/tmp/"))
    mocked_open.assert_called_once_with(Path("/tmp/BlueyeMission.json"), "w")


def test_export_to_json_with_path(mocked_open):
    path = Path("/tmp/something_else.json")
    blueye.sdk.mission.export_to_json(example_mission, output_path=path)
    mocked_open.assert_called_once_with(path, "w")

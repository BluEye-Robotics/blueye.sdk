import blueye.protocol as bp
import pytest

import blueye.sdk
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


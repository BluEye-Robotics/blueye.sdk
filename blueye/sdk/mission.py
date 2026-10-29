import copy
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import blueye.protocol as bp
from google.protobuf.json_format import MessageToJson, Parse

# Necessary to avoid cyclic imports
if TYPE_CHECKING:
    from .drone import Drone

logger = logging.getLogger(__name__)


def create_waypoint_instruction(
    waypoint_name: str,
    latitude: float,
    longitude: float,
    depth: float,
    speed_to_target: float = 0.6,
    speed_to_depth: float = 0.3,
    circle_of_acceptance: float = 1,
    waypoint_id: int = 0,
) -> bp.Instruction:
    """
    Helper function to create waypoint instructions.

    Args:
        waypoint_name (str): The name of the waypoint.
        latitude (float): The latitude of the waypoint (WGS 84 decimal format). Needs to be in the
                          range [-90, 90].
        longitude (float): The longitude of the waypoint (WGS 84 decimal format). Needs to be in the
                           range [-180, 180].
        depth (float): The depth of the waypoint (meters below surface).
        circle_of_acceptance: The radius of the circle of acceptance (meters).
        speed_to_target: The speed to the waypoint (m/s).
        waypoint_id: The ID of the waypoint.

    Raises:
        ValueError: If latitude or longitude are out of bounds.

    Returns:
        Instruction: An Instruction object with the specified waypoint details.
    """
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Latitude must be between -90 and 90 degrees, got {latitude}")
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Longitude must be between -180 and 180 degrees, got {longitude}")
    global_position = bp.LatLongPosition()
    global_position.latitude = latitude
    global_position.longitude = longitude

    depth_set_point = bp.DepthSetPoint()
    depth_set_point.depth = depth
    depth_set_point.depth_zero_reference = bp.DepthZeroReference.DEPTH_ZERO_REFERENCE_SURFACE
    depth_set_point.speed_to_depth = speed_to_depth

    waypoint = bp.Waypoint()
    waypoint.id = waypoint_id
    waypoint.name = waypoint_name
    waypoint.global_position = global_position
    waypoint.circle_of_acceptance = circle_of_acceptance
    waypoint.speed_to_target = speed_to_target
    waypoint.depth_set_point = depth_set_point

    waypoint_command = bp.WaypointCommand(waypoint=waypoint)

    instruction = bp.Instruction({"waypoint_command": waypoint_command})
    return instruction


def prepare_new_mission(
    instruction_list: List[bp.Instruction],
    mission_id: int = 0,
    mission_name: str = "",
) -> bp.Mission:
    """Creates a mission from a list of instructions

    The instructions are copied and numbered 1 to n in list order, which is the numbering the
    Blueye app uses. The drone executes the instructions in list order and reports progress by
    these ids: `MissionStatus.completed_instruction_ids` and
    `ReferenceAutoPilot.active_instruction_id` refer to them. The instructions passed in are left
    unchanged, so the same instruction object can appear more than once in the list.

    Args:
        mission_id: ID of the mission
        mission_name: Name of the mission
        instruction_list: List of instructions to create the mission from

    Raises:
        ValueError: If the number of instructions exceeds 50, which is the maximum allowed.

    Returns:
        A mission object with the instructions and their respective IDs
    """
    if len(instruction_list) > 50:
        raise ValueError(
            "A mission can only contain up to 50 instructions. "
            f"Received {len(instruction_list)} instructions."
        )
    logger.debug(
        f'Preparing the "{mission_name}" mission, with ID {mission_id} and '
        f"{len(instruction_list)} instructions"
    )

    # Copy the instructions so the caller's objects keep their ids. Number from 1: the drone
    # reports progress by id, and 0 is also what an unset id reads back as.
    instructions = []
    for position, instruction in enumerate(instruction_list, start=1):
        instruction_copy = copy.deepcopy(instruction)
        instruction_copy.id = position
        instructions.append(instruction_copy)
    return bp.Mission(id=mission_id, name=mission_name, instructions=instructions)


def import_from_json(input_path: Path | str) -> bp.Mission:
    """Import a mission from a JSON file

    This allows you to load a mission from a file that was previously exported.

    Args:
        input_path: The path to the JSON file to import

    Returns:
        The imported mission
    """
    if type(input_path) == str:
        input_path = Path(input_path)
    logger.debug(f"Importing mission from {input_path}")

    with open(input_path, "r") as f:
        json_data = f.read()
        mission = bp.Mission()
        Parse(json_data, mission._pb)
        return mission


def export_to_json(mission: bp.Mission, output_path: Optional[Path | str] = None):
    """Export the mission to a JSON file

    This allows you to save the mission to a file for later use or to share it with others.

    Args:
        mission: The mission to export
        output_path: The path to write the JSON file to. If `None` the mission will be written to
                     the current directory with the name `BlueyeMission.json`. If the path is a
                     directory, the mission will be written to that directory with the name
                     `BlueyeMission.json`. Else the mission will be written to the specified file.
    """
    if output_path is None:
        output_path = Path("BlueyeMission.json")
    else:
        if type(output_path) == str:
            output_path = Path(output_path)
        if output_path.is_dir():
            output_path = output_path.joinpath("BlueyeMission.json")

    logger.debug(f'Exporting mission "{mission.name}" to {output_path}')
    with open(output_path, "w") as f:
        f.write(MessageToJson(mission._pb))


class Mission:
    """Class for handling mission planning with the drone

    Example usage:
        1. Create some instructions
            ```python
            import blueye.protocol as bp
            go_to_seabed = bp.Instruction(go_to_seabed_command={"desired_speed": 0.3})
            take_picture = bp.Instruction(camera_command={
                "camera_action": bp.CameraAction.CAMERA_ACTION_TAKE_PHOTO
            })
            go_to_surface = bp.Instruction(go_to_surface_command={"desired_speed": 0.3})
            ```

        2. Create a mission with the instructions
            ```python
            from blueye.sdk.mission import prepare_new_mission
            mission = prepare_new_mission(
                instruction_list = [go_to_seabed, take_picture, go_to_surface],
                mission_id = 0,
                mission_name = "Go to seabed and take a picture",)
            ```

        3. Load and run the new mission
            ```python
            drone.mission.load_and_run(mission)
            ```
    """

    def __init__(self, parent_drone: "Drone"):
        """Initialize the Mission class.

        Args:
            parent_drone: The parent drone instance.
        """
        self._parent_drone = parent_drone

    def get_status(self) -> Optional[bp.MissionStatus]:
        """Get the current mission status.

        Returns:
            The current mission status, or None if no telemetry data has been received.

        Raises:
            RuntimeError: If the connected drone does not meet the required Blunux version.
        """
        self._parent_drone._verify_required_blunux_version("4.0.5")
        msg = self._parent_drone.telemetry.get(bp.MissionStatusTel)
        if msg is None:
            return None
        else:
            return msg.mission_status

    def get_active(self) -> bp.Mission:
        """Get the current active mission.

        Returns:
            The current active mission. The mission will be empty if no mission is running.

        Raises:
            RuntimeError: If the connected drone does not meet the required Blunux version.
        """
        self._parent_drone._verify_required_blunux_version("4.0.5")
        return self._parent_drone._req_rep_client.get_active_mission().mission

    def send_new(self, mission: bp.Mission):
        """Send a new mission to the drone.

        Args:
            mission: The mission to send to the drone.

        Raises:
            RuntimeError: If the connected drone does not meet the required Blunux version.
        """
        self._parent_drone._verify_required_blunux_version("4.0.5")
        self._parent_drone._req_rep_client.set_mission(mission)

    def run(self):
        """Run the currently loaded mission.

        The mission state must be MISSION_STATE_READY before calling this method.

        Raises:
            RuntimeError: If the connected drone does not meet the required Blunux version.
        """
        self._parent_drone._verify_required_blunux_version("4.0.5")
        self._parent_drone._ctrl_client.run_mission()

    def pause(self):
        """Pause the currently running mission.

        Raises:
            RuntimeError: If the connected drone does not meet the required Blunux version.
        """
        self._parent_drone._verify_required_blunux_version("4.0.5")
        self._parent_drone._ctrl_client.pause_mission()

    def clear(self):
        """Clear the currently loaded mission.

        Raises:
            RuntimeError: If the connected drone does not meet the required Blunux version.
        """
        self._parent_drone._verify_required_blunux_version("4.0.5")
        self._parent_drone._ctrl_client.clear_mission()

    def _get_state(self) -> Optional[bp.MissionState]:
        """The mission state from the latest status, or `None` when no status has arrived."""
        status = self.get_status()
        if status is None:
            return None
        return status.state

    def _wait_for_state(
        self,
        wanted: tuple[bp.MissionState, ...],
        timeout: float,
        description: str,
        load_failure_is_error: bool = False,
        poll_interval: float = 0.1,
    ) -> bp.MissionState:
        """Poll the mission state until it is one of `wanted`.

        A missing status counts as not there yet, like any state other than the wanted ones. The
        drone has no status to give until its mission node has published the first one after boot.

        Args:
            wanted: The states to wait for.
            timeout: Seconds to wait before giving up.
            description: Names the wanted states in the `TimeoutError` message.
            load_failure_is_error: Raise on `MISSION_STATE_FAILED_TO_LOAD_MISSION` instead of
                waiting on. Set while waiting for the mission that was sent. Before that, a
                failed load left over from an earlier mission is cleared like any other state.
            poll_interval: Seconds between two reads of the state.

        Returns:
            The state that ended the wait.

        Raises:
            RuntimeError: If `load_failure_is_error` is set and the drone reports
                `MISSION_STATE_FAILED_TO_LOAD_MISSION`.
            TimeoutError: If none of the wanted states is reported within the timeout.
        """
        deadline = time.monotonic() + timeout
        while True:
            state = self._get_state()
            if state in wanted:
                return state
            if (
                load_failure_is_error
                and state == bp.MissionState.MISSION_STATE_FAILED_TO_LOAD_MISSION
            ):
                raise RuntimeError("Failed to load the mission. Check the mission instructions.")
            if time.monotonic() >= deadline:
                if state is None:
                    raise TimeoutError(
                        f"No mission status received from the drone within {timeout} s."
                    )
                raise TimeoutError(
                    f"Mission status did not become {description} within {timeout} s, "
                    f"last state was {state.name}."
                )
            time.sleep(poll_interval)

    def load_and_run(self, mission: bp.Mission, timeout: float = 2.0):
        """Clears any previous mission, loads the given mission, and runs it.

        The method returns once the drone has been told to run the mission. Use
        [`get_status`][blueye.sdk.mission.Mission.get_status] to follow it from there.

        For about a second after the drone boots there is no mission status to read. The method
        waits for it like for any other state, within the same timeout.

        Args:
            mission: The mission to load and run.
            timeout: Seconds to wait for each step: for a mission status to arrive, for the drone to
                clear a previous mission, and for the new mission to become ready.

        Raises:
            RuntimeError: If the connected drone does not meet the required Blunux version, or the
                drone fails to load the mission.
            TimeoutError: If no mission status arrives, or the mission does not become inactive or
                ready, within the timeout.
        """
        self._parent_drone._verify_required_blunux_version("4.0.5")

        # Wait for a status to know whether a previous mission has to be cleared first
        state = self._wait_for_state(tuple(bp.MissionState), timeout, "known")
        if state not in (
            bp.MissionState.MISSION_STATE_INACTIVE,
            bp.MissionState.MISSION_STATE_COMPLETED,
        ):
            self.clear()
            self._wait_for_state((bp.MissionState.MISSION_STATE_INACTIVE,), timeout, "inactive")

        self.send_new(mission)
        self._wait_for_state(
            (bp.MissionState.MISSION_STATE_READY,), timeout, "ready", load_failure_is_error=True
        )
        self.run()

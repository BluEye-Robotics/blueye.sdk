import copy
import logging
from typing import TYPE_CHECKING, List, Optional

import blueye.protocol

# Necessary to avoid cyclic imports
if TYPE_CHECKING:
    from .drone import Drone

logger = logging.getLogger(__name__)


def prepare_new_mission(
    instruction_list: List[blueye.protocol.Instruction],
    mission_id: int = 0,
    mission_name: str = "",
) -> blueye.protocol.Mission:
    """Creates a mission from a list of instructions

    Automatically assigns an ID to each instruction based on the order they are in the list.

    Args:
        mission_id: ID of the mission
        mission_name: Name of the mission
        instruction_list: List of instructions to create the mission from

    Returns:
        A mission object with the instructions and their respective IDs
    """
    logger.debug(
        f"Preparing the {mission_name} mission, with ID {mission_id} and "
        f"{len(instruction_list)} instructions"
    )
    instruction_id = 0

    # Deep copy the instructions to avoid modifying the original ones
    for instruction in instruction_list:
        instruction_copy = copy.deepcopy(instruction)
        instruction_copy.id = instruction_id
        instruction_id += 1
        instruction_list[instruction_list.index(instruction)] = instruction_copy
    return blueye.protocol.Mission(id=mission_id, name=mission_name, instructions=instruction_list)


class Mission:
    """Class for handling mission planning with the drone

    The flow is a follows:
    1. Create some instructions
        import blueye.protocol as bp
        go_to_seabed = bp.Instruction(go_to_seabed_command={"desired_speed": 0.3})
        take_picture = bp.Instruction(camera_command={
            "camera_action": bp.CameraAction.CAMERA_ACTION_TAKE_PHOTO
        })
        go_to_surface = bp.Instruction(go_to_surface_command={"desired_speed": 0.3})

    2. Create a mission with the instructions
        from blueye.sdk.mission import prepare_new_mission
        mission = prepare_new_mission(
            instruction_list = [go_to_seabed, take_picture, go_to_surface],
            mission_id = 0,
            mission_name = "Go to seabed and take a picture",)

    3. Clear any previous missions
        drone.mission.clear()

    4. Wait for the drone to be ready to receive a new mission
        while drone.mission.get_status().state != bp.MissionState.MISSION_STATE_INACTIVE:
            time.sleep(0.1)

    5. Send the mission to the drone
        drone.mission.send_new(mission)

    6. Wait for the drone to be ready to run the mission
        while drone.mission.get_status().state != bp.MissionState.MISSION_STATE_READY:
            time.sleep(0.1)

    7. Run the mission
        drone.mission.run()
    """

    def __init__(self, parent_drone: "Drone"):
        self._parent_drone = parent_drone

    def get_status(self) -> Optional[blueye.protocol.MissionStatus]:
        """Returns the current mission status

        Returns None if no telemetry data has been received yet
        """
        msg = self._parent_drone.telemetry.get(blueye.protocol.MissionStatusTel)
        if msg is None:
            return None
        else:
            return msg.mission_status

    def get_active(self) -> blueye.protocol.Mission:
        """Returns the current active mission

        The mission will be empty if no mission is running."""
        return self._parent_drone._req_rep_client.get_active_mission().mission

    def send_new(self, mission: blueye.protocol.Mission) -> None:
        """Sends a new mission to the drone."""
        self._parent_drone._req_rep_client.set_mission(mission)

    def run(self) -> None:
        """Runs the currently loaded mission"""
        self._parent_drone._ctrl_client.run_mission()

    def pause(self) -> None:
        """Pauses the currently running mission"""
        self._parent_drone._ctrl_client.pause_mission()

    def clear(self) -> None:
        """Clears the currently loaded mission"""
        self._parent_drone._ctrl_client.clear_mission()

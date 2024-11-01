import blueye.protocol
from typing import TYPE_CHECKING, Optional

# Necessary to avoid cyclic imports
if TYPE_CHECKING:
    from .drone import Drone


class Mission:
    """Class for handling mission planning with the drone

    The flow is a follows:
    1. Create some instructions
        import blueye.protocol as bp
        go_to_seabed = bp.Instruction(go_to_seabed_command={"desired_speed": 0.5})
        take_picture = bp.Instruction(camera_command={
            "camera_action": bp.CameraAction.CAMERA_ACTION_TAKE_PHOTO
        })
        go_to_surface = bp.Instruction(go_to_surface_command={"desired_speed": 0.5})

    2. Create a mission with the instructions
        mission = bp.Mission(instructions=[go_to_seabed, take_picture, go_to_surface])

    3. Check if the drone is ready receive a new mission
        ready = drone.mission.get_status().state == bp.MissionState.MISSION_STATE_INACTIVE

    4. If ready, send the mission to the drone
        if ready:
            drone.mission.send_new(mission)

    5. Run the mission
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

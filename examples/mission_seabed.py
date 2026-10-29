import logging
import logging.handlers
import time

import blueye.protocol as bp

from blueye.sdk import Drone
from blueye.sdk.mission import prepare_new_mission

# Set up logging
logger = logging.getLogger("blueye.sdk")
logger.setLevel(logging.DEBUG)
socket_handler = logging.handlers.SocketHandler(
    "localhost", logging.handlers.DEFAULT_TCP_LOGGING_PORT
)
logger.addHandler(socket_handler)

# Create some instructions for the mission
go_to_seabed = bp.Instruction(go_to_seabed_command={"desired_speed": 0.3})
take_picture = bp.Instruction(
    camera_command={"camera_action": bp.CameraAction.CAMERA_ACTION_TAKE_PHOTO}
)
go_to_surface = bp.Instruction(go_to_surface_command={"desired_speed": 0.3})

# Create a mission with the instructions
mission = prepare_new_mission(
    instruction_list=[go_to_seabed, take_picture, go_to_surface],
    mission_id=0,
    mission_name="Go to seabed and take a picture",
)

# Establish a connection to the drone
d = Drone(log_notifications=True)

# Send the mission to the drone and start it
d.mission.load_and_run(mission)

# Stay connected until the mission has ended. If the script exits, the SDK stops petting the
# drone's watchdog and the drone aborts the mission about 3 seconds later. The status is None
# until the drone has reported one, and a mission can end aborted or failed as well as completed.
end_states = (
    bp.MissionState.MISSION_STATE_COMPLETED,
    bp.MissionState.MISSION_STATE_ABORTED,
    bp.MissionState.MISSION_STATE_FAILED_TO_START_MISSION,
)
status = d.mission.get_status()
while status is None or status.state not in end_states:
    time.sleep(0.1)
    status = d.mission.get_status()
print(f"Mission ended with state {status.state.name}")

d.disconnect()

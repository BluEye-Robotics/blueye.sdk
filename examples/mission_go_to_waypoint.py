import logging
import logging.handlers
import time

import blueye.protocol as bp

from blueye.sdk import Drone
from blueye.sdk.mission import create_waypoint_instruction, prepare_new_mission

# Publish runtime logs over TCP (including mission status notifications)
logger = logging.getLogger("blueye.sdk")
logger.setLevel(logging.DEBUG)
socket_handler = logging.handlers.SocketHandler(
    "localhost", logging.handlers.DEFAULT_TCP_LOGGING_PORT
)
logger.addHandler(socket_handler)

# Create some waypoints in a (roughly) square pattern
#    10.4174°E           10.4176°E
#    B ------------------ C 63.4418°N
#    |                    |
#    |                    |
#    |                    |
#    A ------------------ D 63.4415°N
wp_a = create_waypoint_instruction("Point A", 63.4415, 10.4174, 0)
wp_b = create_waypoint_instruction("Point B", 63.4418, 10.4174, 0)
wp_c = create_waypoint_instruction("Point C", 63.4418, 10.4176, 0)
wp_d = create_waypoint_instruction("Point D", 63.4415, 10.4176, 0)


# Create a mission with the instructions
mission = prepare_new_mission(
    instruction_list=[wp_a, wp_b, wp_c, wp_d, wp_a],
    mission_id=0,
    mission_name="Go to waypoints",
)

# Establish a connection to the drone
d = Drone(log_notifications=True)

# Send the mission to the drone and start it
d.mission.load_and_run(mission)

# Stay connected until the mission has ended. If the script exits, the SDK stops petting the
# drone's watchdog and the drone aborts the mission about 3 seconds later. The status is None
# until the drone has reported one, and a mission can end aborted or failed as well as completed.
# It is also over when another client clears it (INACTIVE) or loads its own in its place
# (INACTIVE, then READY or FAILED_TO_LOAD_MISSION).
end_states = (
    bp.MissionState.MISSION_STATE_COMPLETED,
    bp.MissionState.MISSION_STATE_ABORTED,
    bp.MissionState.MISSION_STATE_FAILED_TO_START_MISSION,
    bp.MissionState.MISSION_STATE_FAILED_TO_LOAD_MISSION,
    bp.MissionState.MISSION_STATE_INACTIVE,
)
status = d.mission.get_status()
while status is None or status.state not in end_states:
    time.sleep(0.1)
    status = d.mission.get_status()
print(f"Mission ended with state {status.state.name}")

d.disconnect()

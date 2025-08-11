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
#    10.3840°E           10.3841°E
#    B ------------------ C 63.4612°N
#    |                    |
#    |                    |
#    |                    |
#    A ------------------ D 63.4610°N
wp_a = create_waypoint_instruction("Point A", 63.4415, 10.4174, 0)
wp_b = create_waypoint_instruction("Point B", 63.4418, 10.4176, 0)
wp_c = create_waypoint_instruction("Point C", 63.4418, 10.4174, 0)
wp_d = create_waypoint_instruction("Point D", 63.4415, 10.4176, 0)
wp_e = create_waypoint_instruction("Point E", 63.4415, 10.4175, 0)


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

# Wait until the mission state becomes MISSION_STATE_COMPLETED
while d.mission.get_status().state != bp.MissionState.MISSION_STATE_COMPLETED:
    time.sleep(0.1)
print("Mission completed successfully!")

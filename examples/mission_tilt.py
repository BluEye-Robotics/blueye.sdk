import time

import blueye.protocol as bp

from blueye.sdk import Drone
from blueye.sdk.mission import prepare_new_mission

# Create some instructions for the mission
tilt_camera_center = bp.Instruction(tilt_main_camera_command={"tilt_angle": {"value": 0.0}})
tilt_camera_top = bp.Instruction(tilt_main_camera_command={"tilt_angle": {"value": 30.0}})
tilt_camera_bottom = bp.Instruction(tilt_main_camera_command={"tilt_angle": {"value": -30.0}})
wait = bp.Instruction(wait_for_command={"wait_for_seconds": 4})

# Create a mission with the instructions
mission = prepare_new_mission(
    instruction_list=[tilt_camera_top, wait, tilt_camera_bottom, wait, tilt_camera_center, wait],
    mission_id=0,
    mission_name="Tilt camera",
)

# Establish a connection to the drone
d = Drone(log_notifications=True)

# Check if the drone is ready to receive a new mission
if not d.mission.get_status().state == bp.MissionState.MISSION_STATE_INACTIVE:
    d.mission.clear()
    # Wait until the mission state becomes MISSION_STATE_INACTIVE
    while d.mission.get_status().state != bp.MissionState.MISSION_STATE_INACTIVE:
        time.sleep(0.1)

# Send the mission to the drone
d.mission.send_new(mission)

# Wait until the mission state becomes MISSION_STATE_READY
while d.mission.get_status().state != bp.MissionState.MISSION_STATE_READY:
    time.sleep(0.1)

# Run the mission
d.mission.run()

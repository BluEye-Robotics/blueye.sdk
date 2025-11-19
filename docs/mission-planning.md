# Mission planning with the SDK

The SDK supports creating and running missions on the drone using the [`mission`][blueye.sdk.mission.Mission] attribute of the [`Drone`][blueye.sdk.drone.Drone] class. Missions are created using a set of instructions that define the actions the drone should perform.

## Creating a mission
As an example we will create a mission that goes to the seabed, takes a picture with the main camera, and returns to the surface.

First we define the instructions we want to use. The available instructions are outlined in the [`Instruction`][blueye.protocol.types.mission_planning.Instruction] class.

```python
import blueye.protocol as bp

go_to_seabed = bp.Instruction(go_to_seabed_command={"desired_speed": 0.3})
take_picture = bp.Instruction(camera_command={
    "camera_action": bp.CameraAction.CAMERA_ACTION_TAKE_PHOTO
})
go_to_surface = bp.Instruction(go_to_surface_command={"desired_speed": 0.3})
```

Next we create the mission using these instructions. The mission is created by passing a list of instructions to the [`prepare_new_mission`][blueye.sdk.mission.prepare_new_mission] function.

```python
from blueye.sdk.mission import prepare_new_mission
go_to_seabed_mission = prepare_new_mission(
    instruction_list = [go_to_seabed, take_picture, go_to_surface],
    mission_id = 0,
    mission_name = "Go to seabed and take a picture",
)
```

## Loading and running the mission
With the mission created we can now transfer it to the drone and run it. The easiest way to do this is to use the [`load_and_run`][blueye.sdk.mission.Mission.load_and_run] method, which will transfer the mission the drone, wait for it to become ready and then start the mission.

```python
from blueye.sdk import Drone

d = Drone()

d.mission.load_and_run(go_to_seabed_mission)
```

## Getting status updates from the mission
The mission progress is published through the [`NotificationTel`][blueye.protocol.types.telemetry.NotificationTel] messages. These messages can be read manually with the usual telemetry methods, ie. [`telemetry.get`][blueye.sdk.drone.Telemetry.get] or [`telemetry.add_msg_callback`][blueye.sdk.drone.Telemetry.add_msg_callback].

Alternatively, if one initializes the Drone object with `log_notifications=True`, the notifications will be logged with pythons `logging` module. This is the recommended way to get notified about mission progress.

```python
from blueye.sdk import Drone

d = Drone(log_notifications=True)
```

The termial output can however quickly become cluttered when the logs are being printed inbetween the program output. In such cases, it can be useful to run the program in one terminal and then run a separate terminal to read the logs. This can be accomplished by configuring a simple TCP server to listen for log messages. See the [Receiving logs in another terminal](logs/runtime-logs.md#receiving-logs-in-another-terminal) section for an example of how to do this.

## Exporting to JSON
The mission can be exported to a JSON file using the [`export_to_json`][blueye.sdk.mission.export_to_json] method. This allows you to save the mission for later use or share it with others. It is also possible to load the json file in the Blueye App.

```python
import blueye.protocol as bp
from blueye.sdk.mission import export_to_json, prepare_new_mission

# Create a mission
mission = prepare_new_mission(
    instruction_list=[bp.Instruction(go_to_seabed_command={"desired_speed": 0.3})]
)

# Export the mission to a JSON file
export_to_json(mission, "exported_mission.json")
```

## Importing from JSON
You can also import a mission from a JSON file using the [`import_from_json`][blueye.sdk.mission.import_from_json] method. This allows you to load a previously saved mission and run it on the drone.

```python
from blueye.sdk import Drone
from blueye.sdk.mission import import_from_json

mission = import_from_json("exported_mission.json")

d = Drone()
d.mission.load_and_run(mission)

```

## Examples
Here are some examples outlining how to use some of the mission planning features


/// details | Tilt camera
    type: example

This is a simple example that tilts the camera up and down. Useful for testing with the drone out of the water.

{{code_from_file("../examples/mission_tilt.py", flavor= "python")}}
///

/// details | Go to seabed
    type: example

Another simple example outlining how to create some simple instructions and run them on the drone. This example goes to the seabed, takes a picture with the main camera, and returns to the surface.

{{code_from_file("../examples/mission_seabed.py", flavor= "python")}}
///


/// details | Go to waypoints
    type: example

This example shows how one can create multiple waypoints and have the drone go to each of them in sequence.
{{code_from_file("../examples/mission_go_to_waypoint.py", flavor= "python")}}
///

# Blueye drone models

The SDK works with every Blueye model. What a script can do depends on the hardware:

| Model | Camera | Camera tilt | Guest ports | CV models and laser tracking | Batteries |
| --- | --- | --- | --- | --- | --- |
| Pioneer | Up to 1080p | None | None | No | 1 |
| Pro | Up to 1080p | ±30° | None | No | 1 |
| X1 | Up to 1080p | ±30° | 1 | No | 1 |
| X3 | Up to 1080p | ±30° | 3 | No | 1 |
| X3 Ultra | 4K, 60 fps up to 1440p | ±30° | 3 | Yes | 1 |
| X7 | 4K, 60 fps up to 1440p | ±90° | 6 | Yes | 2 |

The X3 Ultra and X7 run on the NVIDIA Jetson platform. Their 4K camera has image settings, image filters and a digital pan, tilt and zoom that the older camera lacks, and no hue control. See [Configure drone parameters](configuration.md).

## Telling the models apart from a script

[`get_model`][blueye.sdk.drone.Drone.get_model] returns the model as a `blueye.protocol.Model`, and [`is_jetson_platform`][blueye.sdk.drone.Drone.is_jetson_platform] says whether the drone is an X3 Ultra or X7. Both read the drone's `DroneInfoTel`, and ask the drone for it if it has not arrived since connecting. `Drone.features` lists `"tilt"` on drones with a camera tilt. See [Drone model and hardware](drone-info.md).

```python
import blueye.protocol as bp
from blueye.sdk import Drone

with Drone(connect_as_observer=True) as drone:
    if drone.get_model() == bp.Model.MODEL_X7:
        print("X7: the camera tilts ±90°")
```

Methods for hardware a model does not have behave in one of three ways; each method's reference says which. Some raise `RuntimeError`, such as the [`Tilt`][blueye.sdk.camera.Tilt] methods without `"tilt"` and the image filters on the older camera. Some are ignored by the drone, such as roll and pitch input on models other than the X7. Peripheral attributes such as [`gripper`][blueye.sdk.drone.Drone.gripper] are `None` when no such device is attached.

## X7 notes

- **Camera tilt.** The camera tilts from -90° to +90°, and mission tilt instructions are limited to that range. [`enable_stabilization`][blueye.sdk.camera.Tilt.enable_stabilization] is accepted and [`is_stabilization_enabled`][blueye.sdk.camera.Tilt.is_stabilization_enabled] reports it, but the tilt servo does not compensate for the drone's pitch.
- **Lights.** Each side has three LEDs aimed up, ahead and down. The drone aims the light at the commanded camera tilt by dimming the LEDs that point away from it, so changing the tilt changes which lights are on.
- **Roll and pitch.** The X7 is the only model that acts on roll and pitch input, see [Control from a Python script](movement/from-the-CLI.md).
- **Batteries.** The X7 runs two batteries in parallel. [`get_power_source`][blueye.sdk.drone.Drone.get_power_source] reports how the drone is powered.

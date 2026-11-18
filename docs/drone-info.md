# Drone model and hardware
The drone publishes its identity and hardware configuration in the `DroneInfoTel` telemetry
message. The `Drone` class exposes the most useful fields through getters, so a script can adapt
to the drone it is connected to without parsing the message itself. If `DroneInfoTel` has not
arrived since connecting, the getters ask the drone for it.

```python
import blueye.protocol as bp
from blueye.sdk import Drone

drone = Drone()

# The model as a blueye.protocol.Model enum, e.g. bp.Model.MODEL_X7
model = drone.get_model()

# True for the X3 Ultra and X7, which have the 4K camera
if drone.is_jetson_platform():
    drone.camera.set_framerate(60)

# bp.PowerSource.POWER_SOURCE_PARALLEL_BATTERIES on the X7, SINGLE_BATTERY on the others
power_source = drone.get_power_source()

# E.g. bp.PressureSensorType.PRESSURE_SENSOR_TYPE_KELLER_PA7LD for the extended depth sensor
depth_sensor = drone.get_depth_sensor_type()
```

The full [`DroneInfo`][blueye.protocol.DroneInfo] message is available through
[`get_drone_info`][blueye.sdk.drone.Drone.get_drone_info]. It also carries the component serial
numbers, the guest port configuration and the installed computer vision models.

```python
drone_info = drone.get_drone_info()
print(drone_info.blunux_version)
print(drone_info.serial_number.decode())
```

The main camera calibration published by the X3 Ultra and X7 is covered in
[Camera calibration](video/camera-calibration.md).

## Error flags
[`get_error_flags`][blueye.sdk.drone.Drone.get_error_flags] returns the drone's error flags as a
dictionary of bools, true while the error is present. The flags are the fields of the
[`ErrorFlags`][blueye.protocol.types.message_formats.ErrorFlags] message, which the drone
publishes once a second.

```python
flags = drone.get_error_flags()
if flags and flags["depth_read"]:
    print("The depth sensor cannot be read")
```

Drones running Blunux 5.2 or newer also report the state of their IMUs. The drone sets and
clears these flags as an IMU stops or recovers:

| Flag | Set when | Models |
| --- | --- | --- |
| `imu_1` | IMU 1 is not delivering data | All |
| `imu_2` | IMU 2 is not delivering data | All |
| `imu_hp` | The high-precision IMU is not delivering data | X3 Ultra and X7 |
| `imu_attitude` | No IMU works, so the drone has no attitude estimate | All |

Older drones do not report these flags, so `get_error_flags` leaves them out there rather than
reporting them as false.

One working IMU is enough for the drone to estimate its attitude. Without one it can only be
driven by hand: it switches every auto mode off and refuses to turn one on, aborts a running
mission, reports its roll, pitch and yaw as NaN and turns camera tilt stabilization off. When an
IMU recovers the flag clears, but the drone does not turn the auto modes or tilt stabilization
back on by itself.
[`has_attitude`][blueye.sdk.drone.Drone.has_attitude] checks for this, and raises
`RuntimeError` on drones older than Blunux 5.2:

```python
if drone.has_attitude() is False:
    print("No attitude estimate: auto modes and missions are unavailable")
```

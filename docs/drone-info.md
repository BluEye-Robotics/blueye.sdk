# Drone model and hardware
The drone publishes its identity and hardware configuration in the `DroneInfoTel` telemetry
message. The `Drone` class exposes the most useful fields through getters, so a script can adapt
to the drone it is connected to without parsing the message itself. The getters return `None`
until the first `DroneInfoTel` message has been received, which normally happens during
[`connect`][blueye.sdk.drone.Drone.connect].

```python
import blueye.protocol as bp
from blueye.sdk import Drone

drone = Drone()

# The model as a blueye.protocol.Model enum, e.g. bp.Model.MODEL_X7
model = drone.get_model()

# True for the X3 Ultra and X7, which share the Jetson camera pipeline
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

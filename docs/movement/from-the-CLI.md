# Controlling from the Command Line Interface

This is a super simple example showing how you make the drone move from the command line interface:

```python
import time
from blueye.sdk import Drone
myDrone = Drone()
myDrone.motion.set_surge(0.4)
time.sleep(1)
myDrone.motion.set_surge(0)
```

## Auto modes and what they need

The auto modes are enabled with the `enable_*` methods on [`motion`][blueye.sdk.motion.Motion]. The drone checks its sensors when a mode is requested. A request the drone cannot meet is dropped with a log line on the drone and nothing else, so read the matching `is_*_active()` method afterwards. [`ControlModeTel`][blueye.protocol.types.telemetry.ControlModeTel] carries the same flags.

| Mode | Needs | When the requirement is lost |
| --- | --- | --- |
| Auto depth | Nothing beyond the built-in depth sensor. Turns auto altitude off. | |
| Auto heading | Nothing beyond the built-in IMU. | |
| Auto altitude | A valid altitude from a DVL or a downward-facing Ping sonar on a guest port. Turns auto depth off. | The drone switches to auto depth. |
| Station keeping | A valid position from a DVL or the drone's own Blueye GNSS. Topside positioning (UGPS, USBL, NMEA input) does not count. | Released after 3 seconds without a valid position. |
| Weather vaning | The same as station keeping, which it turns on. | As for station keeping. |

The position sensors and their validity are listed in `PositionEstimateTel.position_estimate.navigation_sensors`, and [`get_altitude`][blueye.sdk.drone.Drone.get_altitude] returns `None` while the altitude is not valid. See [Navigation sensors](../peripherals.md#navigation-sensors) for which guest-port devices provide what.

```python
import time
from blueye.sdk import Drone

myDrone = Drone()
myDrone.motion.enable_station_keeping(True)
time.sleep(1)
if not myDrone.motion.is_station_keeping_active():
    print("Station keeping did not engage: no valid DVL or GNSS position")
```

All auto modes are switched off when the client in control stops petting the drone's watchdog, see [Connecting to the drone](../connecting.md).

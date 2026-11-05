# Control from a Python script

A [`Drone`][blueye.sdk.drone.Drone] object has a `motion` attribute, an instance of [`Motion`][blueye.sdk.motion.Motion], with the methods that move the drone and switch its auto modes on and off. Each setter gives one axis a setpoint between -1 and 1, which the drone holds until it gets a new one:

```python
import time
from blueye.sdk import Drone

with Drone() as myDrone:
    myDrone.motion.set_surge(0.4)
    time.sleep(1)
    myDrone.motion.set_surge(0)
# Leaving the block zeroes every setpoint and disconnects
```

The drone drops motion input while nobody is in control, and an observer is never given control, so a script that pilots the drone should connect without `connect_as_observer=True`. See [Connecting to the drone](../connecting.md).

## Axes and directions

| Axis | Setter | A positive setpoint | Models |
| --- | --- | --- | --- |
| Surge | [`set_surge`][blueye.sdk.motion.Motion.set_surge] | moves forward | All |
| Sway | [`set_sway`][blueye.sdk.motion.Motion.set_sway] | moves right | All |
| Heave | [`set_heave`][blueye.sdk.motion.Motion.set_heave] | moves down | All |
| Yaw | [`set_yaw`][blueye.sdk.motion.Motion.set_yaw] | turns clockwise, seen from above | All |
| Roll | [`set_roll`][blueye.sdk.motion.Motion.set_roll] | rolls right | X7 |
| Pitch | [`set_pitch`][blueye.sdk.motion.Motion.set_pitch] | raises the nose | X7 |

Surge, sway and heave setpoints are forces. Yaw, roll and pitch setpoints are moments. The models other than the X7 ignore roll and pitch, so those setters are safe to call on any drone. On the X7, read [`set_roll`][blueye.sdk.motion.Motion.set_roll] before using them: with auto heading off nothing limits the resulting angle.

## How strong a setpoint is

A setpoint of ±1 is full stick. It does not ask for the most the thrusters can give: the force depends on boost and slow.

- **Normal**, with boost and slow at 0, is the drone's everyday level.
- **Boost**, [`set_boost(1)`][blueye.sdk.motion.Motion.set_boost], raises full stick to the drone's boosted force.
- **Slow**, [`set_slow(1)`][blueye.sdk.motion.Motion.set_slow], lowers it for fine positioning.

At full stick, as a share of the boosted force, with the drone's default force settings:

| Axis | Normal | Slow |
| --- | --- | --- |
| Surge | 27 % | 4 % |
| Sway | 39 % | 13 % |
| Heave | 44 % | 18 % |
| Yaw, roll and pitch | 52 % | 16 % |

Boost and slow each have a dead band of 0.1: values up to 0.1 count as 0, and 0.1 to 1 is stretched over the whole range, so a boost of 0.55 is halfway. The drone then takes boost minus slow and blends linearly toward the boosted level when the result is positive and toward the slow level when it is negative. Both at 1 give the normal level. A setpoint between 0 and 1 scales the force in proportion.

## One axis or all at once

The setters change one axis and keep the others. [`send_thruster_setpoint`][blueye.sdk.motion.Motion.send_thruster_setpoint] sets surge, sway, heave and yaw in one message, and roll and pitch as keyword arguments that default to 0. [`get_current_thruster_setpoints`][blueye.sdk.motion.Motion.get_current_thruster_setpoints] returns what the SDK last sent.

In a control loop, compute every axis and send them with one `send_thruster_setpoint` call per iteration:

```python
import time
from blueye.sdk import Drone

with Drone() as myDrone:
    end = time.monotonic() + 5
    while time.monotonic() < end:
        # Compute every axis here, for example from a controller
        myDrone.motion.send_thruster_setpoint(surge=0.3, sway=0, heave=-0.1, yaw=0)
        time.sleep(0.05)  # 20 Hz
```

## Auto modes and what they need

The auto modes are enabled with the `enable_*` methods on [`motion`][blueye.sdk.motion.Motion]. The drone checks its sensors when a mode is requested. The drone does not send a notification when it refuses a mode. It writes an error to its own log and leaves the mode off, so read the matching `is_*_active()` method afterwards. [`ControlModeTel`][blueye.protocol.types.telemetry.ControlModeTel] carries the same flags.

| Mode | Needs | When the requirement is lost |
| --- | --- | --- |
| Auto depth | Nothing beyond the built-in depth sensor. Turns auto altitude off. | |
| Auto heading | Nothing beyond the built-in IMU. | |
| Auto altitude | A valid altitude from a DVL or a downward-facing Ping sonar on a guest port. Turns auto depth off. | The drone switches to auto depth. |
| Station keeping | A valid position from a DVL or the drone's own Blueye GNSS. Topside positioning (UGPS, USBL, NMEA input) does not count. | Released after 3 seconds without a valid position. |
| Weather vaning | The same as station keeping, which it turns on. | As for station keeping. |

With auto depth or auto altitude on, the heave setpoint asks for a vertical speed instead of a force, and 0 holds the depth or altitude. With auto heading on, the yaw setpoint asks for a turn rate, and 0 holds the heading.

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

## Stopping safely

The drone keeps the last setpoint it received, so a script that stops sending does not stop the drone. Set every axis back to 0 with [`zero_setpoints`][blueye.sdk.motion.Motion.zero_setpoints] when a manoeuvre is done. [`disconnect`][blueye.sdk.drone.Drone.disconnect], and the end of a `with` block, zero the setpoints before leaving when the script is in control. When connecting, the SDK zeroes them only if it gets control.

If the client in control stops sending its watchdog for 3 seconds, the drone zeroes the input and switches the auto modes off, see [Connecting to the drone](../connecting.md#what-the-drone-does-when-the-client-in-control-goes-quiet).

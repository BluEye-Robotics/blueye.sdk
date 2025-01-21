# Upgrading to v2
Version 2 of the Blueye SDK (unfortunately) introduces a few breaking changes. The following guide outlines what has changed, and what you need to change to be compatible with the new version.

## Change of underlying communication protocol
The underlying communications protocol has been changed from UDP/TCP to protobuf messages sent over ZeroMQ sockets. This means that the drone now supports multiple simultaneous clients, and as such, the 'slave-mode' functionality is no longer necessary and has been removed.

Another added benefit is the ability to list and disconnect other clients connected to the drone.

## Requirement on Blunux v3.2 or newer
The SDK now requires v3.2 or newer of the Blunux operating system to be installed on the drone to able to connect to it.

## Dropped support Python 3.7
One or several of our subdependencies has dropped support for 3.7, and in an effort to reduce the maintenance burden we decided to drop support for 3.7 when adding support for 3.11.

## New range for lights control
Previously the valid range for the `lights` property was an `int` between 0 and 255, it has now been updated to a `float` in the range 0 to 1.

```python
# Previously
my_drone.lights = 64

# Updated
my_drone.lights = 0.25
```

## Error flags are a dictionary of bools
Error flags are now represented as a dictionary of bools instead of bitflags in an `int`. See the [ErrorFlags message][blueye.protocol.types.message_formats.ErrorFlags] for an overview of the possible error states.

```python
# Previously
depth_read_error: bool = my_drone.error_flags & (1 << 2)

# Updated
depth_read_error: bool = my_drone.error_flags["depth_read"]
```

## Changed return type in `active_video_streams` property
The `active_video_streams` property has been modified to return a dictionary containing `"main"` and `"guestport"` as keys. This change provides the option to be able to read the number of active video streams for both the main camera and (optinally) a guestport camera.
```python
# Previously
streams_on_main_camera = my_drone.active_video_streams

# Updated
streams_on_main_camera = my_drone.active_video_streams["main"]
```

## Water Density Unit changed from g/L to kg/L
The unit for water density has been updated from grams per liter (g/L) to kilograms per liter (kg/L). Make sure to adjust your calculations or conversions accordingly.

```python
# Previously
density: int = my_drone.config.water_density
print(density) # Will print 1025

# Updated
density: float = my_drone.config.water_density
print(density) # Will print 1.025
```

## Camera Stabilization uses on/off instead of toggle
The camera stabilization functionality now uses separate methods for enabling and disabling instead of a single toggle method. Update your code to use the appropriate methods based on the desired behavior.

```python
# Previously
my_drone.camera.toggle_stabilization()
print(my_drone.camera.stabilization_enabled)

# Updated
my_drone.camera.stabilization_enabled = True
print(my_drone.camera.stabilization_enabled)
```

## `tilt_speed` has been renamed to `tilt_velocity`
The function tilt_speed has been renamed to tilt_velocity to better reflect its purpose and usage. Update your code to use the new function name.
```python
# Previously
my_drone.camera.tilt.set_speed(1)

# Updated
my_drone.camera.tilt.set_velocity(1)
```

## New subclass for battery data
The `battery_state_of_charge` property has been moved to a subclass on the `Drone`-object. In addition the state of charge range for the battery has been adjusted to a scale of 0 to 1, instead of the previous 0 to 100 range.

```python
# Previously
state_of_charge: int = my_drone.battery_state_of_charge

# Updated
state_of_charge: float = my_drone.battery.state_of_charge
```

## Custom Overlay Classes Replaced with Enums
Custom overlay classes have been replaced with enums defined in the `blueye.protocol` package. Make sure to update your code to use the new enums for overlay functionality.

```python
# Previously
from blueye.sdk import DepthUnitOverlay, FontSizeOverlay, LogoOverlay, TemperatureUnitOverlay

my_drone.camera.overlay.depth_unit = DepthUnitOverlay.METERS
my_drone.camera.overlay.font_size = FontSizeOverlay.PX15
my_drone.camera.overlay.logo = LogoOverlay.BLUEYE
my_drone.camera.overlay.temperature_unit = TemperatureUnitOverlay.CELSIUS

# Updated
import blueye.protocol as bp

my_drone.camera.overlay.depth_unit = bp.DepthUnit.DEPTH_UNIT_METERS
my_drone.camera.overlay.font_size = bp.FontSize.FONT_SIZE_PX15
my_drone.camera.overlay.logo = bp.LogoType.LOGO_TYPE_DEFAULT
my_drone.camera.overlay.temperature_unit = bp.TemperatureUnit.TEMPERATURE_UNIT_CELSIUS
```

## Telemetry properties will now return `None` if no data exists
Properties that read telemetry data, such as `lights`, `tilt_angle`, `depth`, `pose`, `battery_state_of_charge`, `error_flags`, `active_video_streams`, `auto_depth_active`, and `auto_heading_active`, will now return `None` if no telemetry message has been received from the drone. Previously if a UDP message had not arrived, a `KeyError` exception would have been raised.

```python
# Previously
print(my_drone.pose) # If no state message has been received yet this could throw a KeyError

# Updated
print(my_drone.pose) # This will now print "None" if no AttitudeTel-message has been received.
```

## New initialization parameters to the `Drone` object
The `AutoConnect` parameter has been renamed to `auto_connect` for consistency and clarity.
```python
# Previously
my_drone = Drone(AutoConnect = False)

# Updated
my_drone = Drone(auto_connect = False)
```

The `udpTimeout` parameter has been renamed to `timeout` for consistency and clarity.
```python
# Previously
my_drone = Drone(udpTimeout = 5)

# Updated
my_drone = Drone(timeout = 5)
```

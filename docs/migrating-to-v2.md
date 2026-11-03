# Upgrading to v2
Version 2 of the Blueye SDK introduces a few breaking changes. The following guide outlines what has changed, and what you need to change to be compatible with the new version.

The examples below use the getter and setter methods introduced in v2.8.0. The v2.0 to v2.7 property names still work but emit a `DeprecationWarning`; the [deprecated properties](deprecations.md) page maps each of them to its replacement.

## Change of underlying communication protocol
The underlying communications protocol has been changed from UDP/TCP to protobuf messages sent over ZeroMQ sockets. This means that the drone now supports multiple simultaneous clients, and as such, the 'slave-mode' functionality is no longer necessary and has been removed.

Another added benefit is the ability to list and disconnect other clients connected to the drone.

## Requirement on Blunux v3.2 or newer
The SDK now requires v3.2 or newer of the Blunux operating system to be installed on the drone to able to connect to it.

## Dropped support Python 3.7
One or several of our subdependencies has dropped support for 3.7, and in an effort to reduce the maintenance burden we decided to drop support for 3.7 when adding support for 3.11.

## New range for lights control
Previously the valid range for the lights was an `int` between 0 and 255, it has now been updated to a `float` in the range 0 to 1.

```python
# Previously
my_drone.lights = 64

# Updated
my_drone.set_lights(0.25)
```

## Error flags are a dictionary of bools
Error flags are now represented as a dictionary of bools instead of bitflags in an `int`. See the [ErrorFlags message][blueye.protocol.types.message_formats.ErrorFlags] for an overview of the possible error states.

```python
# Previously
depth_read_error: bool = my_drone.error_flags & (1 << 2)

# Updated
depth_read_error: bool = my_drone.get_error_flags()["depth_read"]
```

## Changed return type for the active video streams
The active video streams are returned as a dictionary containing `"main"` and `"guestport"` as keys. This change provides the option to be able to read the number of active video streams for both the main camera and (optionally) a guestport camera.
```python
# Previously
streams_on_main_camera = my_drone.active_video_streams

# Updated
streams_on_main_camera = my_drone.get_active_video_streams()["main"]
```

## Water density is still in g/L
An earlier version of this guide said that the water density unit changed from grams per liter to kilograms per liter. It did not. The SDK, the protocol and the drone all use grams per liter, and salt water is `1025`, which is also [`WaterDensities.salty`][blueye.sdk.constants.WaterDensities]. Code that followed the old advice and sent `1.025` gave the drone a density a thousand times too low for its depth calculation.

```python
from blueye.sdk.constants import WaterDensities

my_drone.config.set_water_density(WaterDensities.salty)  # 1025 g/L
```

## Camera Stabilization uses on/off instead of toggle
The camera stabilization functionality now uses separate methods for enabling and disabling instead of a single toggle method. The methods live on `camera.tilt`.

```python
# Previously
my_drone.camera.toggle_stabilization()
print(my_drone.camera.stabilization_enabled)

# Updated
my_drone.camera.tilt.enable_stabilization(True)
print(my_drone.camera.tilt.is_stabilization_enabled())
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
The battery state of charge has been moved to a subclass on the `Drone`-object. In addition the state of charge range for the battery has been adjusted to a scale of 0 to 1, instead of the previous 0 to 100 range.

```python
# Previously
state_of_charge: int = my_drone.battery_state_of_charge

# Updated
state_of_charge: float = my_drone.battery.get_state_of_charge()
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

my_drone.camera.overlay.set_depth_unit(bp.DepthUnit.DEPTH_UNIT_METERS)
my_drone.camera.overlay.set_font_size(bp.FontSize.FONT_SIZE_PX15)
my_drone.camera.overlay.set_logo(bp.LogoType.LOGO_TYPE_DEFAULT)
my_drone.camera.overlay.set_temperature_unit(bp.TemperatureUnit.TEMPERATURE_UNIT_CELSIUS)
```

## Telemetry getters return `None` if no data exists
Getters that read telemetry data, such as `get_lights`, `camera.tilt.get_angle`, `get_depth`, `get_pose`, `battery.get_state_of_charge`, `get_error_flags`, `get_active_video_streams`, `motion.is_auto_depth_active`, and `motion.is_auto_heading_active`, return `None` if no telemetry message has been received from the drone. Previously if a UDP message had not arrived, a `KeyError` exception would have been raised.

```python
# Previously
print(my_drone.pose) # If no state message has been received yet this could throw a KeyError

# Updated
print(my_drone.get_pose()) # This will now print "None" if no AttitudeTel-message has been received.
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

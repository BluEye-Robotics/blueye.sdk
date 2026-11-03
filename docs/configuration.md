There are settings on the drone that are remotely configurable from the Blueye mobile app. These can also be set directly from the SDK.

### Configure time and date

The drone does not keep track of time internally. The SDK sets the time on the drone automatically when you connect initially. But you can also configure time and date manually like this

```python
import time
from blueye.sdk import Drone

myDrone = Drone()

time_to_set_on_drone = int(time.time()) # Unix Timestamp
myDrone.config.set_drone_time(time_to_set_on_drone)
```

or if we for example want to offset the drone time 5 hours relative to our current system time we can do something like this:

```python
from blueye.sdk import Drone
from datetime import timezone, timedelta, datetime

myDrone = Drone()

offset_in_hours = timedelta(hours=5)
equivalent_timezone = timezone(offset_in_hours)
unix_timestamp = datetime.now(tz=equivalent_timezone).timestamp()

myDrone.config.set_drone_time(int(unix_timestamp))
```

### Calibrate pressure sensor for water density

The water density on the drone default to a reasonable density for salt water: 1025 grams per liter. For more accurate depth readings, the water density can be configured manually to suit your local conditions

```python
from blueye.sdk import Drone, WaterDensities

myDrone = Drone()

# Salt water
myDrone.config.set_water_density(WaterDensities.salty)  # 1025 g/L

# Brackish water
myDrone.config.set_water_density(WaterDensities.brackish)  # 1011 g/L

# Fresh water
myDrone.config.set_water_density(WaterDensities.fresh)  # 997 g/L

# Can also be set to arbitrary values
myDrone.config.set_water_density(1234)
```

### Configure camera parameters

There are several camera parameters that can be set. For a full list of camera parameters and their possible values see the [`camera reference`](reference/blueye/sdk/camera.md) section.

To change a single parameter you can set it directly:

```python
from blueye.sdk import Drone

myDrone = Drone()

myDrone.camera.set_bitrate(8_000_000)  # 8 Mbit bitrate
```

To change multiple parameters at once, use the `configure()` context manager. This batches all changes into a single request, avoiding multiple pipeline restarts:

```python
import blueye.protocol as bp
from blueye.sdk import Drone

myDrone = Drone()

with myDrone.camera.configure(timeout=5.0) as params:
    params.stream_resolution = bp.Resolution.RESOLUTION_FULLHD_1080P
    params.framerate = bp.Framerate.FRAMERATE_FPS_30
    params.h264_bitrate = 4_000_000
# All changes are sent in one request when the block exits.
# If an exception occurs inside the block, changes are discarded.
```

The `timeout` parameter (default: 0.5s) controls how long to wait for the drone to respond. Increase it when changing parameters that trigger pipeline restarts (e.g. codec, resolution).

Due to a bug in the camera streaming on the drone a camera stream has to have been opened at least once before camera parameters can be set on the drone, see issue [#67](https://github.com/BluEye-Robotics/blueye.sdk/issues/67). For instructions on how to start a video stream see, the [`Quick Start Guide`](quick_start.md#watching-the-video-stream).

### Image filters and digital pan, tilt and zoom

The 4K camera in the X3 Ultra and X7 has two image filters and a digital pan, tilt and zoom. They are not camera parameters, each is sent as its own control message, and the drone reports the state it applied in a telemetry message. The setters raise `RuntimeError` on other models, on the guestport camera and on drones running Blunux older than 5.0.0.

```python
from blueye.sdk import Drone

myDrone = Drone()

# Turbidity filter: contrast enhancement (CLAHE) for murky water
myDrone.camera.set_turbidity_filter(enabled=True, intensity=0.5)

# Color correction: restores the red and blue the water absorbs with depth
myDrone.camera.set_color_correction(enabled=True, intensity=0.8)

# Digital pan, tilt and zoom. Values left out keep what was last sent from this object, so
# the second call keeps the zoom of the first.
myDrone.camera.set_pan_tilt_zoom(zoom=0.5)
myDrone.camera.set_pan_tilt_zoom(pan=-0.3, tilt=0.2)

print(myDrone.camera.get_turbidity_filter())  # FilterMessage with enabled and intensity
print(myDrone.camera.get_pan_tilt_zoom())  # CameraPanTiltZoom with pan, tilt and zoom
```

The drone publishes `TurbidityFilterTel`, `ColorCorrectionTel` and `CameraPanTiltZoomTel` when the state changes, not at a fixed rate. The getters return what the drone reported on the last change, and ask the drone directly if nothing has been received since connecting, so there is no need to wait for a periodic update. A drone that has never applied a filter has nothing to report, and the getter returns `None` until the first change.

The report arrives about 0.1 s after the command, so `set_pan_tilt_zoom` fills in the values you leave out from what it last sent, and from the drone's report only before the first call. A change made by the Blueye app after your last call is not picked up that way; pass all three values when that matters.

Laser dot tracking works on the full, unzoomed image, so [`enable_tracking`][blueye.sdk.guestport.Laser.enable_tracking] resets pan, tilt and zoom to 0 when it starts, as the Blueye app does.

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
myDrone.config.water_density = WaterDensities.salty  # 1025 g/L

# Brackish water
myDrone.config.water_density = WaterDensities.brackish  # 1011 g/L

# Fresh water
myDrone.config.water_density = WaterDensities.fresh  # 997 g/L

# Can also be set to arbitrary values
myDrone.config.water_density = 1234
```

### Configure camera parameters
There are 6 different camera parameters that can be set. For a full list of camera parameters and their possible values see the [`camera reference`](reference/blueye/sdk/camera.md) section. For example you could set the bit rate like this

```python
from blueye.sdk import Drone

myDrone = Drone()

myDrone.camera.bitrate = 8_000_000 # 8 Mbit bitrate
```

Due to a bug in the camera streaming on the drone a camera stream has to have been opened at least once before camera parameters can be set on the drone, see issue [#67](https://github.com/BluEye-Robotics/blueye.sdk/issues/67). For instructions on how to start a video stream see, the [`Quick Start Guide`](quick_start.md#watching-the-video-stream).

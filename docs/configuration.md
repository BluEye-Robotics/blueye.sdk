There are settings on the drone that are remotely configurable from the Blueye mobile app. These can be set directly from the SDK.

### Configure time and date
The drone does not keep track of time internally. The SDK sets the time on the drone automatically when you connect initially. But you can also configure time and date manually like this

```python
import time
from blueye.sdk import Pioneer

p = Pioneer()

time_to_set_on_drone = int(time.time()) # Unix Timestamp
p.config.set_drone_time(time_to_set_on_drone)
```

### Configure water density
The water density on the drone default to a reasonable density for salt water: 1025 grams per liter. For more accurate depth readings, the water density can be configured manually to suit your local conditions

```python
from blueye.sdk import Pioneer

p = Pioneer()

p.config.water_density = 997 # water density in grams per liter for fresh water
```

### Configure camera parameters
There are 6 different camera parameters that can be set. For a full list of camera parameters and their possible values see the [`camera reference`](https://blueye-robotics.github.io/blueye.sdk/reference/blueye/sdk/pioneer/) section. For example you could set the camera bit rate like this

```python
from blueye.sdk import Pioneer

p = Pioneer()

p.camera.bitrate = 8000000 # 8 Mbit bitrate

```
Due to a bug in the camera streaming on the drone a camera stream has to have been opened at least once before camera parameters can be set on the drone, see issue [#67](https://github.com/BluEye-Robotics/blueye.sdk/issues/67). For instructions on how to start a video stream see, the [`Quick Start Guide`](https://blueye-robotics.github.io/blueye.sdk/docs/quick_start/).

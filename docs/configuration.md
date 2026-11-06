There are settings on the drone that are remotely configurable from the Blueye mobile app. These can also be set directly from the SDK.

### Configure time and date

The drone does not keep track of time internally. When a client connects and is in control, the SDK sends the computer's current time to the drone. A connection made with `connect_as_observer=True`, or while another client holds control, leaves the drone's clock alone, unless it passes `disconnect_other_clients=True` and takes control. You can also set the time yourself:

```python
import time
from blueye.sdk import Drone

myDrone = Drone()

myDrone.config.set_drone_time(int(time.time()))  # Unix timestamp
```

The drone's clock runs in UTC and stamps its logs, so always set it to the current Unix time. To show local time in the video overlay, set the overlay's time zone offset in minutes instead. The overlay adds it to the drone's UTC time:

```python
myDrone.camera.overlay.set_timezone_offset(120)  # UTC+2
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
    params.framerate = 30
    params.bitrate = 4_000_000
# All changes are sent in one request when the block exits.
# If an exception occurs inside the block, changes are discarded.
```

The `timeout` parameter (default: 0.5s) controls how long to wait for the drone to respond. Increase it when changing parameters that trigger pipeline restarts (e.g. codec, resolution).

/// admonition | Setters send every parameter
    type: warning
Each camera setter sends the full set of camera parameters, not only the one it changes. It fills in the rest from the parameters the SDK read last: on the first setter call, or by the most recent getter. A change made from the Blueye app after that read is written back over, and two setters in a row can undo each other if a getter ran in between. `configure()` reads the parameters when the block starts and sends one request, so use it when changing several parameters. The overlay setters work the same way with the overlay parameters. Sending only the changed field is tracked in [#221](https://github.com/BluEye-Robotics/blueye.sdk/issues/221).
///

Exposure and white balance apply to every model, with -1 for automatic: [`set_exposure`][blueye.sdk.camera.Camera.set_exposure] and [`set_whitebalance`][blueye.sdk.camera.Camera.set_whitebalance]. [`set_gain`][blueye.sdk.camera.Camera.set_gain] differs per model: -1 keeps the current gain on the Pioneer, Pro, X1 and X3, and on the X3 Ultra and X7 a manual gain only takes effect with a manual exposure. [`set_hue`][blueye.sdk.camera.Camera.set_hue] only has an effect on the Pioneer, Pro, X1 and X3.

### Image settings (X3 Ultra and X7)

The 4K camera in the X3 Ultra and X7 has image settings the older cameras lack. The setters need Blunux 5.0.0 and raise `RuntimeError` on older versions. They do not check the model.

| Setter | Range | Default |
| --- | --- | --- |
| [`set_brightness`][blueye.sdk.camera.Camera.set_brightness] | -10..10 | 0 |
| [`set_contrast`][blueye.sdk.camera.Camera.set_contrast] | -50..50 | 0 |
| [`set_saturation`][blueye.sdk.camera.Camera.set_saturation] | 0..50 | 8 |
| [`set_gamma`][blueye.sdk.camera.Camera.set_gamma] | 4..79 | 22 |
| [`set_sharpness`][blueye.sdk.camera.Camera.set_sharpness] | -20..20 | -20 |
| [`set_backlight_compensation`][blueye.sdk.camera.Camera.set_backlight_compensation] | -150..150 | 10 |
| [`set_denoise`][blueye.sdk.camera.Camera.set_denoise] | -20..20 | -20 |
| [`enable_ehdr`][blueye.sdk.camera.Camera.enable_ehdr] | `True` or `False` | `True` |
| [`set_ehdr_exposure_min_number`][blueye.sdk.camera.Camera.set_ehdr_exposure_min_number] | 1..4 | 1 |
| [`set_ehdr_exposure_max_number`][blueye.sdk.camera.Camera.set_ehdr_exposure_max_number] | 1..4 | 2 |

More than 2 eHDR frames can lower the frame rate.

```python
with myDrone.camera.configure() as params:
    params.contrast = 10
    params.saturation = 12
    params.denoise = 0
```

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

### Recording and streaming

The settings for the recorded file, its resolution, codec and bitrate, are covered in [Recording video and taking pictures](video/recording-and-stills.md#resolution-frame-rate-codec-and-bitrate). The live stream has these:

- [`set_stream_resolution`][blueye.sdk.camera.Camera.set_stream_resolution] and [`set_framerate`][blueye.sdk.camera.Camera.set_framerate]. The frame rate applies to the recording too.
- [`set_bitrate`][blueye.sdk.camera.Camera.set_bitrate]: the H.264 stream bitrate, 1 to 16 Mbit/s.
- [`set_streaming_protocol`][blueye.sdk.camera.Camera.set_streaming_protocol]: `STREAMING_PROTOCOL_RTSP_H264` or `STREAMING_PROTOCOL_RTSP_MJPEG`. The Pioneer, Pro, X1 and X3 do not start a recording while they stream MJPEG. The X3 Ultra and X7 cap an MJPEG stream at 1080p.
- [`set_mtu_size`][blueye.sdk.camera.Camera.set_mtu_size]: the largest network packet the stream uses, in bytes. 0 uses the drone's default of 1400. Lower it for links that carry smaller packets, such as some VPNs. Needs Blunux 5.1.0.

```python
import blueye.protocol as bp

with myDrone.camera.configure(timeout=5.0) as params:
    params.streaming_protocol = bp.StreamingProtocol.STREAMING_PROTOCOL_RTSP_H264
    params.mtu_size = 1200
```

### Camera tilt

Every model except the original Pioneer can tilt the camera. [`Drone.features`][blueye.sdk.drone.Drone.features] contains `"tilt"` on those drones, and the [`Tilt`][blueye.sdk.camera.Tilt] methods raise `RuntimeError` without it.

```python
import time

myDrone.camera.tilt.set_velocity(0.5)  # 1 is full speed up, -1 full speed down
time.sleep(1)
myDrone.camera.tilt.set_velocity(0)
print(myDrone.camera.tilt.get_angle())  # Degrees

myDrone.camera.tilt.enable_stabilization(True)
```

The drone keeps the last velocity until it gets a new one, so the tilt runs to its end stop unless you set it back to 0. Stabilization tilts the camera against the drone's pitch. The X7 accepts the setting but its tilt servo does not compensate.

### Overlay and logo

The overlay is the text and logo the drone draws into its recordings. [`camera.overlay`][blueye.sdk.camera.Overlay] has an `enable_*` method for each field (depth, heading, tilt, date, temperature, altitude, distance and more), and setters for the title and subtitle, units, font size, margins, text shading, the date format and the time zone offset.

```python
import blueye.protocol as bp

overlay = myDrone.camera.overlay
overlay.enable_depth(True)
overlay.enable_date(True)
overlay.set_date_format("%Y-%m-%d %H:%M:%S")
overlay.set_title("Pier inspection")
overlay.set_depth_unit(bp.DepthUnit.DEPTH_UNIT_METERS)
overlay.set_font_size(bp.FontSize.FONT_SIZE_PX25)
```

Title, subtitle and date format take up to 63 ASCII characters. Longer text is cut to 63 characters and sent with a `RuntimeWarning`. Non-ASCII text, a value of the wrong type or one out of range is not sent: the setter warns with a `RuntimeWarning` and leaves the setting unchanged.

To show your own logo, upload a JPG or PNG of up to 2000 px and 5 MB, then select it:

```python
overlay.upload_logo("logo.png")
overlay.set_logo(bp.LogoType.LOGO_TYPE_CUSTOM)
```

`LOGO_TYPE_DEFAULT` shows the default logo and `LOGO_TYPE_NONE` none. [`download_logo`][blueye.sdk.camera.Overlay.download_logo] fetches the uploaded file and [`delete_logo`][blueye.sdk.camera.Overlay.delete_logo] removes it.

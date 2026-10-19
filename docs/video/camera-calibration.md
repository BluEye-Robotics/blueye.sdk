# Camera calibration
The X3 Ultra and X7 publish the intrinsic calibration of the main camera as part of the
`DroneInfoTel` telemetry message. The calibration uses the pinhole camera model with
[OpenCV](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html) distortion coefficients
(`k1, k2, p1, p2, k3`), which is what the Blueye app uses to undistort the video.

The SDK exposes it through
[`Camera.get_calibration`][blueye.sdk.camera.Camera.get_calibration], which returns a
[`CameraCalibration`][blueye.protocol.CameraCalibration] message, or `None` if the drone has not
published one. Older models (Pioneer, Pro, X1 and X3) and the guestport camera do not publish a
calibration.

```python
from blueye.sdk import Drone

drone = Drone()

calibration = drone.camera.get_calibration()
if calibration is None:
    print("The connected drone does not publish a camera calibration")
else:
    print(f"Calibrated at {calibration.image_width}x{calibration.image_height}")
    print(f"fx={calibration.fx:.1f} fy={calibration.fy:.1f} "
          f"cx={calibration.cx:.1f} cy={calibration.cy:.1f}")
    print(f"Distortion: {list(calibration.distortion_coefficients)}")
    if calibration.is_default:
        print("This is the built-in default for the model, not a per-drone calibration")
```

## Scaling to the video resolution
The focal lengths and principal point are in pixels at the resolution the calibration was computed
at. Before using them on a frame of a different size they have to be scaled: `fx` and `cx` with the
width ratio, `fy` and `cy` with the height ratio. The distortion coefficients are resolution
independent.

[`Camera.get_scaled_calibration`][blueye.sdk.camera.Camera.get_scaled_calibration] does this
for you. Without arguments it scales to the current stream resolution, and it also accepts a
[`Resolution`][blueye.protocol.Resolution] or a `(width, height)` tuple. A `Resolution` maps to
the frame size the drone's video pipeline produces for it, which is 640x480 for 480p and 16:9 for
the other resolutions.

```python
import blueye.protocol as bp

# Matches the frames you receive from the RTSP stream
calibration = drone.camera.get_scaled_calibration()

# Matches a recording made at 4K
calibration = drone.camera.get_scaled_calibration(bp.Resolution.RESOLUTION_UHD_4K)

# Matches a frame you have already resized
calibration = drone.camera.get_scaled_calibration((640, 360))
```

## Undistorting a frame with OpenCV
The message maps directly onto the arguments OpenCV expects.

```python
import cv2
import numpy as np

calibration = drone.camera.get_scaled_calibration((frame.shape[1], frame.shape[0]))

camera_matrix = np.array([
    [calibration.fx, 0.0, calibration.cx],
    [0.0, calibration.fy, calibration.cy],
    [0.0, 0.0, 1.0],
])
distortion = np.array(calibration.distortion_coefficients)

undistorted = cv2.undistort(frame, camera_matrix, distortion)
```

## Older models
Drones that do not publish a calibration have to be calibrated by hand, for example with OpenCV's
[chessboard calibration](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html). As a
starting point, Johan Kvalberg measured the following values for a Blueye Pioneer in his
[master thesis](https://ntnuopen.ntnu.no/ntnu-xmlui/handle/11250/2622900). The thesis does not state
the image resolution the values were computed at, and the camera, housing and water all affect the
result, so treat them as an example rather than a calibration of your drone.

```python
import numpy as np

# Blueye Pioneer, in water
camera_matrix = np.array([
    [1354.45761, 0.0, 891.069717],
    [0.0, 1379.97405, 756.192877],
    [0.0, 0.0, 1.0],
])
distortion = np.array([-0.2708139, 0.20052465, 0.0208302, 0.0002806, -0.10134601])

# Blueye Pioneer, in air
camera_matrix_air = np.array([
    [978.36617202, 0.0, 985.08473535],
    [0.0, 975.69987506, 541.52130078],
    [0.0, 0.0, 1.0],
])
distortion_air = np.array([-0.37370139, 0.26899755, -0.00120655, -0.00185788, -0.1411856])
```

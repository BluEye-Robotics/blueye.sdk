# Recording video and taking pictures

The drone records video and stores pictures on its own storage. This page covers starting and stopping a recording, taking a still, what the drone does with each command, and what can keep it from recording. [Downloading videos and images](downloading.md) covers getting the files off the drone afterwards.

## Recording

```python
import time

from blueye.sdk import Drone

myDrone = Drone()

try:
    deadline = time.monotonic() + 15
    while not myDrone.camera.is_recording_active():
        if time.monotonic() >= deadline:
            raise TimeoutError("The camera did not start recording")
        myDrone.camera.set_recording(True)
        time.sleep(1)

    time.sleep(10)
    print(f"Recording: {myDrone.camera.is_recording_active()}, {myDrone.camera.get_record_time()} s")
finally:
    myDrone.camera.set_recording(False)
```

[`set_recording`][blueye.sdk.camera.Camera.set_recording] starts or stops the main camera. The same methods on [`external_camera`][blueye.sdk.guestport.GuestPortCamera] do the same for a guest port camera. The drone has one record command for all of its recorders: the main camera, the guest port camera and the multibeam. The SDK fills in the current state of the recorders you are not changing from the latest [`RecordStateTel`][blueye.protocol.types.telemetry.RecordStateTel], which the drone publishes twice a second by default, so a recording started from the Blueye app keeps running when a script starts or stops another one. A recording that started after the last report can be missed, from another client or from your own previous call. When starting more than one recorder, wait until [`is_recording_active`][blueye.sdk.camera.Camera.is_recording_active] confirms the first before starting the next.

`set_recording` needs that telemetry to have arrived. Right after connecting it may not have, in which case the call logs a warning and sends nothing. [`is_recording_active`][blueye.sdk.camera.Camera.is_recording_active] returns `None` in the same case.

The camera service needs watchdog messages from a client in control before it accepts a recording start. The sender of the recording command can be an observer if another client holds control. After connecting or taking control, allow time for the watchdog and recording telemetry to arrive; the example retries for up to 15 seconds and checks that recording has started. An RTSP viewer is not required. The X3 Ultra's camera service has a 60-second timeout for stopping an ongoing recording without a control watchdog. See [Connecting to the drone](../connecting.md) for how control is assigned.

[`get_record_time`][blueye.sdk.camera.Camera.get_record_time] is the length of the current recording in seconds, and -1 while not recording.

### Resolution, frame rate, codec and bitrate

On Blunux 4.4.1 and newer the recording and the live stream have separate resolutions: [`set_recording_resolution`][blueye.sdk.camera.Camera.set_recording_resolution] and [`set_recording_codec`][blueye.sdk.camera.Camera.set_recording_codec] apply to the file, [`set_stream_resolution`][blueye.sdk.camera.Camera.set_stream_resolution] and [`set_bitrate`][blueye.sdk.camera.Camera.set_bitrate] to the stream, and [`set_framerate`][blueye.sdk.camera.Camera.set_framerate] sets the camera's frame rate. [`set_recording_bitrate`][blueye.sdk.camera.Camera.set_recording_bitrate] needs Blunux 5.0.0. On older Blunux the two share one resolution. See [Configure drone parameters](../configuration.md) for the ranges per model.

## Taking pictures

```python
myDrone.camera.take_picture()
```

[`take_picture`][blueye.sdk.camera.Camera.take_picture] requests a still picture to be stored on the drone. The picture command has no camera selector: the drone forwards the request to the main camera and, if a guest port camera is attached, to that camera too. `myDrone.external_camera.take_picture()` sends the same command. The app's Internal / External / Both camera setting applies to video recording, not this picture command. Mission camera instructions capture from the main camera only.

Pictures get EXIF GPS tags when the drone has a position. [`set_bitrate_still_picture`][blueye.sdk.camera.Camera.set_bitrate_still_picture] sets the bitrate of the still picture stream they are taken from.

## Storage settings

The drone's storage settings in the Blueye app have switches for videos, images, the multibeam and the dive log. With videos off the drone never starts a recording, and with images off it drops the picture, in both cases without a word to the client. `set_recording(True)` and `take_picture()` raise `RuntimeError` when the matching switch is off. The SDK reads the switches when it connects, and reads them again before refusing, so a switch turned on after connecting is picked up; a switch turned off after connecting is not, and the command is sent as before. Wrapping the request that changes the settings is tracked in [#252](https://github.com/BluEye-Robotics/blueye.sdk/issues/252).

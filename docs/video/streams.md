# Live video streams

The drone streams its camera live over RTSP. Any RTSP player can show it: VLC, GStreamer, OpenCV, or the Blueye Observer app. This page lists the streams and what a player needs to know about them.

## Stream URLs

| Stream | URL | Available on |
| --- | --- | --- |
| Main camera | `rtsp://192.168.1.101:8554/test` | Every model |
| Guest port camera | `rtsp://192.168.1.101:8555/guestport_cam` | Drones with a Blueye guest port camera attached |
| Multibeam sonar | `rtsp://192.168.1.101:8556/sonar` | X3 Ultra and X7 with a multibeam connected |

The main camera is also served at `/cam` on the same port. Change the address if the drone is reached through another IP.

[`get_stream_url`][blueye.sdk.camera.Camera.get_stream_url] returns the URL the drone reports for a camera:

```python
from blueye.sdk import Drone

with Drone(connect_as_observer=True) as drone:
    print(drone.camera.get_stream_url())  # rtsp://192.168.1.101:8554/test
    if drone.external_camera is not None:
        print(drone.external_camera.get_stream_url())
```

## What every player needs

- **UDP only.** The drone sends the stream over RTP on UDP and refuses RTSP over TCP with `461 Unsupported transport`. A player that asks for TCP gets no picture, and the computer must accept incoming UDP from the drone, so a firewall or VPN that blocks it blocks the stream.
- **Four sessions per stream.** Each stream accepts 4 RTSP sessions, including the Blueye app's. A fifth player is refused with `453 Not Enough Bandwidth`. The Blueye app always gets in, also when the other 4 are taken. [`get_active_video_streams`][blueye.sdk.drone.Drone.get_active_video_streams] returns the number of sessions on the main and guest port camera streams.
- **No overlay.** The text and logo overlay is drawn into recordings, not into the live stream.
- **H.264 by default.** The main camera can stream MJPEG instead, set with [`set_streaming_protocol`][blueye.sdk.camera.Camera.set_streaming_protocol]. An MJPEG stream needs a different decoder, see [GStreamer for video streaming](gstreamer-for-video-streaming.md).

## X3 Ultra and X7

- The live stream runs at 30 fps at most. With the camera at 60 fps the stream carries every other frame, while recordings keep all of them.
- The stream defaults to 1080p. An H.264 stream can be 4K with [`set_stream_resolution`][blueye.sdk.camera.Camera.set_stream_resolution], but takes more to decode, and the stream bitrate stays the same. An MJPEG stream is limited to 1080p.
- After the drone boots, the camera starts when the first client connects to the drone: the Blueye app or an SDK `Drone`, observers included. An RTSP player on its own does not start it, and gets no picture until a client has connected.

## Multibeam sonar stream

On the X3 Ultra and X7 with a multibeam connected, the drone renders the sonar image and streams it as H.264 at port 8556. It shows the sonar while the multibeam is running and black frames while it is not. The SDK has no method to start the multibeam, so start it from the Blueye app. The colours follow the palette last selected in the app, greyscale until one is.

## OpenCV

OpenCV's `VideoCapture` opens the stream with its FFmpeg backend, which takes a few seconds to start:

```python
import cv2
from blueye.sdk import Drone

with Drone(connect_as_observer=True) as drone:
    capture = cv2.VideoCapture(drone.camera.get_stream_url(), cv2.CAP_FFMPEG)
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            cv2.imshow("Blueye", frame)
            if cv2.waitKey(1) == ord("q"):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()
```

Install OpenCV with `pip install opencv-python`. `capture.read()` returns frames as NumPy arrays in BGR order. If the stream does not open, check that `OPENCV_FFMPEG_CAPTURE_OPTIONS` is not set to `rtsp_transport;tcp`: the drone refuses TCP.

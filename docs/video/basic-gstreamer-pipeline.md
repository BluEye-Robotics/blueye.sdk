First, install [`GStreamer`](https://gstreamer.freedesktop.org/documentation/installing/index.html?gi-language=c), then run this pipeline in your terminal:

``` shell
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.101:8554/test latency=0 \
    ! rtph264depay \
    ! avdec_h264 \
    ! videoconvert \
    ! fpsdisplaysink sync=false
```
This opens a new window with the camera stream and some meta information about packet loss and the camera frame rate.

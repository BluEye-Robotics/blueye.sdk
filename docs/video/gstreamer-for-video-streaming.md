GStreamer is the lowest latency alternative for streaming video from the drone to your laptop. See [Live video streams](streams.md) for the stream URLs and what the drone allows. On the X3 Ultra and X7, the camera only starts once the Blueye app or an SDK `Drone` has connected after the drone boots.

## Installing GStreamer

To run the streaming pipeline in the next section you will need a runtime installation of GStreamer.
The instructions below show the basic steps for installing GStreamer on the most common operating systems.
You can find more in depth instruction for your specific operating system in the [`GStreamer docs`](https://gstreamer.freedesktop.org/documentation/installing/?gi-language=c).


/// details | Windows
    type: abstract

On Windows the basic installation steps are:

1. Download the runtime installer for the latest stable release from https://gstreamer.freedesktop.org/download.
2. Run the installer. When asked to choose a setup type choose to do a __complete__ installation. This is because some plugins that are needed for the basic pipeline later are not included if you choose to install the typical setup
3. To run GStreamer commands form the terminal, GStreamer must be added to the PATH environment variable. This can be done from the advanced system settings. Add `%GSTREAMER_1_0_ROOT_X86_64%\bin` to path. Alternatively you can choose to run gst-launch-1.0.exe from the folder it is installed in, typically `C:\gstreamer\1.0\x86_64\bin`
///

/// details | Mac OS
    type: abstract

On Mac OS GStreamer and its plugins can be installed using [brew](https://brew.sh/)
```shell
brew install gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly gst-libav
```
///
/// details | Linux
    type: abstract

On Ubuntu and Debian GStreamer and its plugins can be installed using apt.
```shell
apt-get install libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc \
gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa
```
///
You can test the installation by trying the basic pipeline from the next section when connected to a drone. Or with

``` shell
gst-launch-1.0 videotestsrc ! autovideosink
```

## Basic streaming pipeline
After installing you can run this pipeline in your terminal:

/// details | Windows
    type: abstract
``` shell
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.101:8554/test latency=0 ! rtph264depay ! avdec_h264 ! videoconvert ! fpsdisplaysink sync=false
```
///
/// details | Linux and macOS
    type: abstract
``` shell
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.101:8554/test latency=0 \
    ! rtph264depay \
    ! avdec_h264 \
    ! videoconvert \
    ! fpsdisplaysink sync=false
```
///
Running the pipeline will open a window with the camera stream and information about packet loss and camera frame rate.

## External camera streaming pipeline
With a Blueye guest port camera attached you can use the following pipeline:

/// details | Windows
    type: abstract
``` shell
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.101:8555/guestport_cam latency=0 ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink sync=false
```
///
/// details | Linux and macOS
    type: abstract
``` shell
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.101:8555/guestport_cam latency=0 \
    ! rtph264depay \
    ! avdec_h264 \
    ! videoconvert \
    ! autovideosink sync=false
```
///
Running the pipeline will open a window with the external camera stream.

## MJPEG streaming pipeline
When the main camera streams MJPEG, set with
[`set_streaming_protocol`][blueye.sdk.camera.Camera.set_streaming_protocol], the H.264 decoder is
replaced by a JPEG one:

/// details | Windows
    type: abstract
``` shell
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.101:8554/test latency=0 ! rtpjpegdepay ! jpegdec ! videoconvert ! fpsdisplaysink sync=false
```
///
/// details | Linux and macOS
    type: abstract
``` shell
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.101:8554/test latency=0 \
    ! rtpjpegdepay \
    ! jpegdec \
    ! videoconvert \
    ! fpsdisplaysink sync=false
```
///

## Multibeam sonar pipeline
On the X3 Ultra and X7 with a multibeam connected, the sonar image is an H.264 stream on port
8556:

/// details | Windows
    type: abstract
``` shell
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.101:8556/sonar latency=0 ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink sync=false
```
///
/// details | Linux and macOS
    type: abstract
``` shell
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.101:8556/sonar latency=0 \
    ! rtph264depay \
    ! avdec_h264 \
    ! videoconvert \
    ! autovideosink sync=false
```
///

GStreamer is the lowest latency alternative for streaming video from the drone to your laptop.

## Installing GStreamer

To run the streaming pipeline in the next section you will need a runtime installation of GStreamer.
The instructions below show the basic steps for installing GStreamer on the most common operating systems.
You can find more in depth instruction for your specific operating system in the [`GStreamer docs`](https://gstreamer.freedesktop.org/documentation/installing/?gi-language=c).


??? abstract "Windows"

    On Windows the basic installation steps are:

    1. Download the relevant installer for your computer from https://gstreamer.freedesktop.org/download .
    Using the latest stable relase should be fine, at the time of writing that is `1.16.1 runtime installer`
    2. Run the installer. When asked to choose a setup type choose to do a __complete__ installation. This is because some plugins that are needed for the basic pipeline later are not included if you choose to install the typical setup
    3. To run GStreamer commands form the terminal, GStreamer must be added to the PATH environment variable. This can be done from the advanced system settings. Add `%GSTREAMER_1_0_ROOT_X86_64%\bin` to path. Alternatively you can choose to run gst-launch-1.0.exe from the folder it is installed in, typically `C:\gstreamer\1.0\x86_64\bin`


??? abstract "Mac OS"

    On Mac OS GStreamer and its plugins can be installed using [brew](https://brew.sh/)
    ```shell
    brew install gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly gst-libav
    ```

???+ abstract "Linux"

    On Ubuntu and Debian GStreamer and its plugins can be installed using apt.
    ```shell
    apt-get install libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc \
    gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa
    ```

You can test the installation by trying the basic pipeline from the next section when connected to a drone. Or with

``` shell
gst-launch-1.0 videotestsrc ! autovideosink
```

## Basic streaming pipeline
After installing you can run this pipeline in your terminal:

??? abstract "Windows"
    ``` shell
    gst-launch-1.0 rtspsrc location=rtsp://192.168.1.101:8554/test latency=0 ! rtph264depay ! avdec_h264 ! videoconvert ! fpsdisplaysink sync=false
    ```

???+ abstract "Linux and Mac OS"
    ``` shell
    gst-launch-1.0 rtspsrc location=rtsp://192.168.1.101:8554/test latency=0 \
        ! rtph264depay \
        ! avdec_h264 \
        ! videoconvert \
        ! fpsdisplaysink sync=false
    ```

Running the pipeline will open a window with the camera stream and information about packet loss and camera frame rate.

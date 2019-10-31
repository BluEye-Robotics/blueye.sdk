GStreamer is the lowest latency alternative for streaming video from the drone to your laptop.

## Installing GStreamer

The instructions below show the basic steps for installing gstreamer on the common operating systems.

??? abstract "Windows"
    ** Install GStreamer**

    To run the streaming pipeline below you will need a runtime installation of Gstreamer. You can find more in depth instruction
    in the [`gstreamer docs`](https://gstreamer.freedesktop.org/documentation/installing/on-windows.html?gi-language=c)

    The basic installation steps are:

    1. Download the relevant installer for your computer from https://gstreamer.freedesktop.org/download .
    Using the latest stable relase should be fine, at the time of writing that is `1.16.1 runtime installer`
    2. Run the installer. When asked to choose a setup type choose to do a __complete__ installation. This is because some plugins that are needed for the basic pipeline later are not included if you choose to install the typical setup
    3. To run gstreamer commands form the terminal, gstreamer must be added to the  PATH environment variable. This can be done from the advanved system settings. Add `%GSTREAMER_1_0_ROOT_X86_64%\bin` to path. Or you can run gst-launch-1.0.exe from the folder it is installed in, typically `C:\gstreamer\1.0\x86_64\bin`

    You can test the installation by trying the basic pipeline from the section below when connected to a drone.

??? abstract "Mac OS"

    ** Install GStreamer**

    To run the streaming pipeline below you will need a runtime installation of GStreamer. You can find more in depth instruction
    in the [`GStreamer docs`](https://gstreamer.freedesktop.org/documentation/installing/on-mac-osx.html?gi-language=c).

    GStreamer and its plugins can be installed with brew
    ```shell
    brew install gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly gst-libav
    ```

???+ abstract "Linux"
    ** Install GStreamer**

    To run the streaming pipeline below you will need a runtime installation of Gstreamer. You can find more in depth instruction
    for your linux distribution at the [`gstreamer docs`](https://gstreamer.freedesktop.org/documentation/installing/on-linux.html?gi-language=c)

    The basic steps for installing on Ubuntu or Debian are

    Install gstreamer and plugins
    ```shell
    apt-get install libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc \
    gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa
    ```
    Verify that gstreamer is installed
    ```shell
    which gst-launch-1.0
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

Running the pipeline will open a new window with the camera stream and some meta information about packet loss and the camera frame rate.

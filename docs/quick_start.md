## Installation
The SDK requires Python 3.7 or higher. We recommend setting up a virtual environment like
[`pyenv`](https://github.com/pyenv/pyenv) for managing your python version, see below for linux instructions.

### Virtual environment with pyenv
Install pyenv, for more instructions see the [pyenv-installer](https://github.com/pyenv/pyenv-installer)

``` shell
curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
pyenv update
```

Install the needed dependencies for building python 3.7.4
``` shell
apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev python-openssl
```
Then build python with pyenv
```
pyenv install 3.7.4
```

Create a virtual environment, and activate it
```
pyenv virtualenv 3.7.4 blueye_sdk
pyenv activate blueye_sdk
```

### Install
Install `blueye.sdk` into your virtual environment

``` python
pip3 install blueye.sdk
```

## Connect to the Pioneer
To use the SDK your computer must be connected to the Pioneer via the surface unit WiFi.
Turn on the drone and connect to the surface unit WiFi. For a how to on turning on the Pioneer
and surface unit you can watch the
[quick start video](https://support.blueye.no/hc/en-us/articles/360006901473-Quick-Start-Guide).

## Control the Pioneer

Most of the pioneers functionality is controlled using python properties,
we can illustrate the use of properties by showing how to control the lights through the `lights`
property of the Pioneer.

``` python
import time
from blueye.sdk import Pioneer
# when the pioneer object is instantiatied a connection to the drone is established
p = Pioneer()
# setting the lights property of the Pioneer object to 10
p.lights = 10
time.sleep(2)
# we can also get the current brightness of the lights through the lights property
print(f"Current light intensity: {p.lights}")
p.lights = 0

# properties can also be used for reading telemetry data from the drone
print(f"Current depth in millimeters: {p.depth}")
```
For a overview of all available properties and their valid input ranges see the
[`Reference section`](../../../reference/blueye/sdk/pioneer/) of the documentation.

### Watching the video stream
The easiest way to open the  RTSP video stream is using [`VLC media player`](https://www.videolan.org/vlc/index.html).
Once VLC is downloaded you can start the stream like this, the RTSP URL is: `rtsp://192.168.1.101:8554/test`
![text](./media/rtsp-in-vlc.gif)


For lower latency streaming (on a PC) you can see the [`Gstreamer instructions`](./video/basic-gstreamer-pipeline.md), or if you just want to watch a low latency stream you can download the Blueye Dive Buddy ([iOS](https://apps.apple.com/us/app/blueye-dive-buddy/id1453884806?ls=1)/[Android](https://play.google.com/store/apps/details?id=no.blueye.divebuddy))

Or you can use the buddy app ([`android`](https://play.google.com/store/apps/details?id=no.blueye.divebuddy&hl=en)/[`iOS`](https://apps.apple.com/no/app/blueye-dive-buddy/id1453884806?l=nb)). The normal blueye app can not be used to spectate when controlling the drone from the SDK because it will interfere with the commands sent from the SDK. But the Buddy app is only a spectator and can be used together with the SDK.
### Explore the examples
For further examples on how to use the SDK to control the Pioneer have a look at the
[motion examples](../movement/from-the-CLI/).

Remember to install the example dependencies before running the examples.

```shell
pip install "blueye.sdk[examples]"
```

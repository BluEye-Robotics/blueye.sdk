## Installation
The SDK requires Python 3.7 or higher. Since many operating systems do not package the newest
version of Python we recommend using [`pyenv`](https://github.com/pyenv/pyenv) or something similar
for configuring multiple python versions on the same system. Pyenv also has the added benefit of
managing your virtual environments for you, though you are of course free to use other tools for
that as well.

The instructions below show the necessary steps to get started with the SDK on a fresh install:

??? abstract "Windows"
    **Install Python**

    Install Python 3.7 or higher, you can find the latest python versions [here](https://www.python.org/downloads/).
    Remember to check the option "Add Python to path" when installing.

    **Install virtualenv for managing Python versions (optional)**

    Using a virtual environment is not strictly necessary, but it greatly simplifies the
    development of Python packages.
    ```shell
    # Upgrade pip version
    python -m pip install --upgrade pip
    pip install virtualenv
    ```

    Next, we create a virtual environment

    ```shell
    cd .\Desktop
    mkdir pioneer_project
    cd .\pioneer_project
    # Replace "C:\Program Files\Python37\python.exe" with the path
    # to the python version you want to use in the line below
    virtualenv blueye_sdk_env -p "C:\Program Files\Python37\python.exe"
    ```
    activate the virtual environment
    ```shell
    .\blueye_sdk_env\Scripts\activate.bat
    ```
    if you are not allowed to activate the virtual environment, you might have to allow running unsigned scripts,
    see [this link](http://tritoneco.com/2014/02/21/fix-for-powershell-script-not-digitally-signed/) for instructions.

    **Install the SDK**

    Now we're ready to install the SDK, which should be as simple as

    ```
    pip install blueye.sdk
    ```

    or, if you want to include the dependencies required for running the examples shown in this
    documentation you should run

    ```
    pip install "blueye.sdk[examples]"
    ```

??? abstract "Mac OS"
    ???+ Warning ""
        Currently there are no instructions for Mac OS, these will come later.

???+ abstract "Linux"
    These instructions are directed at Ubuntu, but the process should be similar for other
    distributions.

    **Install the necessary Python version**

    Install pyenv, for more instructions see the [pyenv-installer](https://github.com/pyenv/pyenv-installer)

    ```
    curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
    pyenv update
    ```

    Install the needed dependencies for building python 3.7.4

    ```
    apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
    xz-utils tk-dev libffi-dev liblzma-dev python-openssl
    ```
    Then build python with pyenv
    ```
    pyenv install 3.7.4
    ```

    **Create a virtual environment**

    Using a virtual environment is not strictly necessary, but it greatly simplifies the
    development of Python packages.

    Since we already have pyenv installed we'll use it to create a virtual environment,

    ```
    pyenv virtualenv 3.7.4 blueye.sdk
    pyenv activate blueye.sdk
    ```

    **Install the SDK**

    Now we're ready to install the SDK, which should be as simple as

    ```
    pip install blueye.sdk
    ```

    or, if you want to include the dependencies required for running the examples shown in this
    documentation you should run

    ```
    pip install "blueye.sdk[examples]"
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
For a overview of the properties that are availabe for controlling and reading data from the Pioneer, go to the
[`Reference section`](https://blueye-robotics.github.io/blueye.sdk/reference/blueye/sdk/pioneer/) of the documentation.The valid input ranges and descriptions of the different properties can also be found there.

### Watching the video stream
The easiest way to open the  RTSP video stream is using [`VLC media player`](https://www.videolan.org/vlc/index.html).
Once VLC is downloaded you can start the stream like this, the RTSP URL is: `rtsp://192.168.1.101:8554/test`
![text](./media/rtsp-in-vlc.gif)


For lower latency streaming (on a PC) you can see the
[`Gstreamer instructions`](./video/basic-gstreamer-pipeline.md), or if you just want to watch a low
latency stream you can download the Blueye Dive Buddy
([iOS](https://apps.apple.com/us/app/blueye-dive-buddy/id1453884806?ls=1) /
[Android](https://play.google.com/store/apps/details?id=no.blueye.divebuddy))

The normal Blueye app can not be used to spectate when controlling the drone from the SDK because
it will interfere with the commands sent from the SDK. The dive buddy app, however, is only a
spectator and can be used together with the SDK.

### Explore the examples
For further examples on how to use the SDK to control the Pioneer have a look at the
[motion examples](../movement/from-the-CLI/).

Remember to install the example dependencies before running the examples.

```shell
pip install "blueye.sdk[examples]"
```

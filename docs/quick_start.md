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
    mkdir drone_project
    cd .\drone_project
    # Replace "C:\Program Files\Python310\python.exe" with the path
    # to the python version you want to use in the line below
    virtualenv blueye_sdk_env -p "C:\Program Files\Python310\python.exe"
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

    ** Install the necessary Python version**

    Install pyenv, for more instructions see the [pyenv-installer](https://github.com/pyenv/pyenv-installer)

    ```
    curl https://pyenv.run | bash
    pyenv update
    ```

    If you want pyenv to be loaded each time you open a new terminal you can add this to your .zshrc or the equivalent for your terminal
    ```
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
    ```

    The [Pyenv wiki](https://github.com/pyenv/pyenv/wiki#suggested-build-environment) recommends installing some
    additional dependencies before building Python.


    ```shell
    # optional, but recommended:
    brew install openssl readline sqlite3 xz zlib
    ```

    When running Mojave or higher (10.14+) you will also need to install the additional SDK headers:
    ```shell
    sudo installer -pkg /Library/Developer/CommandLineTools/Packages/macOS_SDK_headers_for_macOS_10.14.pkg -target /
    ```
    Then build Python with pyenv

    ```
    pyenv install 3.10.1
    ```

    **Create a virtual environment**

    Using a virtual environment is not strictly necessary, but it greatly simplifies the
    development of Python packages.

    Since we already have pyenv installed we'll use it to create a virtual environment,

    ```
    pyenv virtualenv 3.10.1 blueye.sdk
    pyenv activate blueye.sdk
    ```

    **Install the SDK**

    Now we're ready to install the SDK, which should be as simple as.

    ```
    pip install blueye.sdk
    ```

    or, if you want to include the dependencies required for running the examples shown in this
    documentation you should run

    ```
    pip install "blueye.sdk[examples]"
    ```



??? abstract "Linux"
    These instructions are directed at Ubuntu, but the process should be similar for other
    distributions.

    **Install the necessary Python version**

    Install pyenv, for more instructions see the [pyenv-installer](https://github.com/pyenv/pyenv-installer)

    ```
    curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
    pyenv update
    ```

    Install the needed dependencies for building python 3.10.1

    ```
    apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
    xz-utils tk-dev libffi-dev liblzma-dev python-openssl
    ```
    Then build python with pyenv
    ```
    pyenv install 3.10.1
    ```

    **Create a virtual environment**

    Using a virtual environment is not strictly necessary, but it greatly simplifies the
    development of Python packages.

    Since we already have pyenv installed we'll use it to create a virtual environment,

    ```
    pyenv virtualenv 3.10.1 blueye.sdk
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

## Connect to the drone
To use the SDK your computer must be connected to the drone via the surface unit WiFi. For a how-to
on turning on the drone and surface unit you can watch the
[quick start video](https://support.blueye.no/hc/en-us/articles/360006901473-Quick-Start-Guide).

## Control the drone
Most of the functionality is controlled using Python properties and we will illustrate the use of
properties by showing how to control the lights:

``` python
import time
from blueye.sdk import Drone

# When the Drone object is instantiatied a connection to the drone is established
myDrone = Drone()

# Setting the lights property to 10
myDrone.lights = 10

time.sleep(2)

# We can also get the current brightness of the lights through the lights property
print(f"Current light intensity: {myDrone.lights}")
myDrone.lights = 0

# Properties can also be used for reading telemetry data from the drone
print(f"Current depth in millimeters: {myDrone.depth}")
```
For an overview of the properties that are available for controlling and reading data from the drone, go to the
[`Reference section`](../../reference/blueye/sdk/drone) of the documentation.
The valid input ranges and descriptions of the different properties can also be found there.


!!! Tip
    You can explore the properties of the drone interactively using an interactive python interpreter like
    [`iPython`](https://ipython.readthedocs.io/en/stable/interactive/tutorial.html), install it with:
    ```shell
    pip install ipython
    ```
    By instantiating a Drone object and using the completion key (normally the `tab-key ↹`) you can get a interactive list of
    the available properties on the drone, it is then easy to try setting and getting the different properties.
    ![`iPython`](https://blueyenostorage.blob.core.windows.net/sdkimages/ipython-exploration.gif)


### Watching the video stream
The easiest way to open the  RTSP video stream is using [`VLC media player`](https://www.videolan.org/vlc/index.html).
Once VLC is downloaded you can start the stream like this, the RTSP URL is: `rtsp://192.168.1.101:8554/test`
![text](https://blueyenostorage.blob.core.windows.net/sdkimages/rtsp-in-vlc.gif)


For lower latency streaming (on a PC) you can see the instructions on using
[`Gstreamer`](./video/gstreamer-for-video-streaming.md), or if you just want to watch a low
latency stream you can download the Blueye Dive Buddy
([iOS](https://apps.apple.com/us/app/blueye-dive-buddy/id1453884806?ls=1) /
[Android](https://play.google.com/store/apps/details?id=no.blueye.divebuddy))

The normal Blueye app can not be used to spectate when controlling the drone from the SDK because
it will interfere with the commands sent from the SDK. The dive buddy app, however, is only a
spectator and can be used together with the SDK.

### Explore the examples
For further examples on how to use the SDK to control the drone have a look at the
[motion examples](../movement/from-the-CLI/).

Remember to install the example dependencies before running the examples.

```shell
pip install "blueye.sdk[examples]"
```

### Local documentation
Since the drone surface unit (usually) does not have internet access it can be a bit tricky to
reference this documentation while developing on the drone. Luckily when you install the SDK from
PyPI it includes a pre-built, local copy of this documentation. This documentation can be viewed by
executing the following Python snippet:

```python
import blueye.sdk

blueye.sdk.open_local_documentation()
```

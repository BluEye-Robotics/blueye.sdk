# blueye.sdk
[![Tests](https://github.com/BluEye-Robotics/blueye.sdk/workflows/Tests/badge.svg)](https://github.com/BluEye-Robotics/blueye.sdk/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/BluEye-Robotics/blueye.sdk.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/BluEye-Robotics/blueye.sdk/context:python)
[![codecov](https://codecov.io/gh/BluEye-Robotics/blueye.sdk/branch/master/graph/badge.svg)](https://codecov.io/gh/BluEye-Robotics/blueye.sdk)
[![PyPi-version](https://img.shields.io/pypi/v/blueye.sdk.svg?maxAge=3600)](https://pypi.org/project/blueye.sdk/)
[![python-versions](https://img.shields.io/pypi/pyversions/blueye.sdk.svg?longCache=True)](https://pypi.org/project/blueye.sdk/)
_________________

[Read Latest Documentation](https://blueye-robotics.github.io/blueye.sdk/) - [Browse GitHub Code Repository](https://github.com/BluEye-Robotics/blueye.sdk)
_________________

**Note: This is a pre-release -- Please report any issues you might encounter**
_________________
A Python package for remote control of the Blueye Pioneer underwater drone.


![SDK demo](https://user-images.githubusercontent.com/8504604/66751230-d05c7e00-ee8e-11e9-91cb-d46b433aafa5.gif)

## About The Pioneer
The Blueye Pioneer is a underwater drone designed for inspections. It is produced and sold by the Norwegian company [`Blueye Robotics`](https://www.blueyerobotics.com/).
Here is a Youtube video  that gives a overview of the system and its specifications.

[![about the Pioneer video](https://img.youtube.com/vi/_-AEtr6xOP8/0.jpg)](https://www.youtube.com/watch?v=_-AEtr6xOP8)

## This SDK and the Pioneer
The Pioneer is normally controlled via a mobile device through the Blueye App ([iOS](https://apps.apple.com/no/app/blueye/id1369714041)/[Android](https://play.google.com/store/apps/details?id=no.blueye.blueyeapp)). The mobile device
is connected via WiFi to a surface unit, and the Pioneer is connected to the surface unit via a tether cable.

This python SDK exposes the functionality of the Blueye app through a Python object. The SDK enables remote control of the Pioneer as well as reading telemetry data and viewing video streams, it is not meant for executing code on the Pioneer.
To control the Pioneer you connect your laptop to the surface unit WiFi and run code that interfaces with the Pioneer through the Pioneer Python object.


Check out the [`Quick Start Guide`](https://blueye-robotics.github.io/blueye.sdk/docs/quick_start/) to get started with using the SDK.

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
A Python package for remote control of the Blueye Pioneer and Blueye Pro underwater drones.


![SDK demo](https://user-images.githubusercontent.com/8504604/66751230-d05c7e00-ee8e-11e9-91cb-d46b433aafa5.gif)

## About Blueye Underwater Drones
The Blueye Pioneer and Blueye Pro are underwater drones designed for inspections. It is produced and sold by the Norwegian company [`Blueye Robotics`](https://www.blueyerobotics.com/).
Here is a Youtube video  that gives a overview of the system and its specifications.

[![about the Blueye Pro video](https://images.ctfassets.net/qpo1z0ycuc50/2JLqOXRoSIMe370zfrtgQV/445995589cbdb4e6baa406d97bcbf667/DSC05337_3_Mathilde_edit.jpg?w=1920&q=80)](https://www.youtube.com/watch?v=HI2CQbnCsoU)

## This SDK and the Blueye drones
A Blueye drone is normally controlled via a mobile device through the Blueye App ([iOS](https://apps.apple.com/no/app/blueye/id1369714041)/[Android](https://play.google.com/store/apps/details?id=no.blueye.blueyeapp)). The mobile device
is connected via Wi-Fi to a surface unit, and the Pioneer or Pro is connected to the surface unit via a tether cable.

This python SDK exposes the functionality of the Blueye app through a Python object. The SDK enables remote control of the Blueye Pioneer and Blueye Pro as well as reading telemetry data and viewing video streams. It is not meant for executing code on the Pioneer.
To control the drone you connect your laptop to the surface unit Wi-Fi and run code that interfaces with the Blueye Pro or Blueye Pioneer through the Pioneer Python object.


Check out the [`Quick Start Guide`](https://blueye-robotics.github.io/blueye.sdk/docs/quick_start/) to get started with using the SDK.

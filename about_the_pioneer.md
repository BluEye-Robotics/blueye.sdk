# About The Pioneer
The Blueye Pioneer is a underwater drone designed for inspections. It is produced and sold by the Norwegian company [`Blueye Robotics`](https://www.blueyerobotics.com/).
Here is a [`youtube video`](https://www.youtube.com/watch?v=_-AEtr6xOP8) that gives a overview of the system and some specifications.


![Pioneer at the Tautra Reef](./docs/media/pioneer-at-reef.gif)

## This SDK and the Pioneer
The Pioneer is normally controlled via a mobile device through the [Blueye app](https://play.google.com/store/apps/details?id=no.blueye.blueyeapp). The mobile device
is connected via WiFi to a surface unit, and the Pioneer is connected to the surface unit via a tether cable.

![SDK demo](./docs/media/sdk-demo.gif)

This python SDK exposes the functionality of the Blueye app through a Python object. The SDK enables remote control of the Pioneer as well as reading telemetry data and viewing video streams, it is not meant for executing code on the Pioneer.
To control the Pioneer you connect your laptop to the surface unit WiFi and run code that interface with the Pioneer through the Pioneer Python object.


Check out the [`Quick Start Guide`](./docs/quick_start.md) to get started with using the SDK.

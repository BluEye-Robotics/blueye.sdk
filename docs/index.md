![SDK demo](https://user-images.githubusercontent.com/8504604/66751230-d05c7e00-ee8e-11e9-91cb-d46b433aafa5.gif)

Blueye produces and sells three models of underwater drones, the Blueye Pioneer, Blueye Pro, and Blueye X3. The Pioneer and the Pro are drones designed for inspection, while the X3 is extensible with three guest ports that allow attaching for example grippers or sonars.
Visit [blueyerobotics.com](https://www.blueyerobotics.com/products) for more information about the Blueye products.

## This SDK and the Blueye drones
A Blueye drone is normally controlled via a mobile device through the Blueye App ([iOS](https://apps.apple.com/no/app/blueye/id1369714041)/[Android](https://play.google.com/store/apps/details?id=no.blueye.blueyeapp)).
The mobile device is connected via Wi-Fi to a surface unit, and the drone is connected to the surface unit via a tether cable.

This python SDK exposes the functionality of the Blueye app through a Python object. The SDK enables remote control of a Blueye drone as well as reading telemetry data and viewing video streams. It is not meant for executing code on the drone itself.

To control the drone you connect your laptop to the surface unit Wi-Fi and run code that interfaces with the through the Python object.


Check out the [`Quick Start Guide`](quick_start.md) to get started with using the SDK.

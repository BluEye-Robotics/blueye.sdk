![SDK demo: connect with Drone(), set_lights(1.0), and motion.set_surge(0.3)](media/sdk-demo.gif)

The Blueye SDK is a Python package for controlling Blueye underwater drones from a computer. Your computer joins the drone's surface unit over Wi-Fi, the same way the Blueye app does, and a [`Drone`][blueye.sdk.drone.Drone] object connects to the drone through it.

New to the SDK? Start with the [Quick Start](quick_start.md), which installs the SDK and runs a first script, then read [Connecting to the drone](connecting.md) for how a script and the Blueye app share the drone.

## Supported drones

The SDK works with every Blueye model:

| Model | Camera | Camera tilt | Guest ports | CV models |
| --- | --- | --- | --- | --- |
| Pioneer | Up to 1080p | None | None | No |
| Pro | Up to 1080p | ±30° | None | No |
| X1 | Up to 1080p | ±30° | 1 | No |
| X3 | Up to 1080p | ±30° | 3 | No |
| X3 Ultra | 4K | ±30° | 3 | Yes |
| X7 | 4K | ±90° | 6 | Yes |

[Blueye drone models](models.md) has the full table and the differences that matter to a script, and [blueyerobotics.com](https://www.blueyerobotics.com/products) has more about the drones.

## What the documentation covers

- **Movement**: [moving the drone](movement/from-the-CLI.md) with thrust, boost and the auto modes, and [driving it with a gamepad](movement/with-a-gamepad.md).
- **Video**: [live streams](video/streams.md) and [GStreamer](video/gstreamer-for-video-streaming.md), [recording and taking pictures](video/recording-and-stills.md), [downloading media](video/downloading.md) and the [camera calibration](video/camera-calibration.md).
- **Logs**: [listing and downloading dive logs](logs/listing-and-downloading.md), [plotting them](logs/plotting.md) and [viewing them in Foxglove](logs/foxglove-bez-to-mcap.md).
- **Drone settings**: [camera, overlay and other parameters](configuration.md), and [the drone's model and hardware](drone-info.md).
- **Telemetry**: [subscribing to telemetry messages](telemetry-callback.md) and [visualizing live sensor data](foxglove-bridge.md).
- **Guest port tools**: [grippers, lights, lasers, servos and sensors](peripherals.md).
- **Missions**: [planning and running missions](mission-planning.md).
- **The blueye command**: [the CLI](cli.md) for logs, computer vision models and other tasks from the terminal.
- **Reference**: every class and method, starting with [`Drone`](reference/blueye/sdk/drone.md), and the [protocol messages](reference/blueye/protocol/overview.md).

A copy of the documentation matching the installed SDK ships with the package for use without internet access, see the [Quick Start](quick_start.md#local-documentation).

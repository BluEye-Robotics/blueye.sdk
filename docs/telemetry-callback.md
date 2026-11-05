# Subscribing to a telemetry message

The drone publishes all of its telemetry data as protobuf encoded messages transmitted via a ZeroMQ socket. You can find the protobuf message definitions in the [Protocol Definitions](https://github.com/BluEye-Robotics/ProtocolDefinitions/) repository, and the generated python definitions are located in the [blueye.protocol](https://github.com/BluEye-Robotics/blueye.protocol) repository.

Upon connection the [Drone object][blueye.sdk.drone.Drone] will instantiate an instance of the [Telemetry class][blueye.sdk.drone.Telemetry] as the `telemetry` attribute. Using this attribute one can control various telemetry function and add/remove new callbacks.

## Adding a callback
To add a callback we need to use the [`add_msg_callback`][blueye.sdk.drone.Telemetry.add_msg_callback] function, and provide it with a list of telemetry messages types we want it to trigger on, as well as a function handle to call. All available telemetry messages can be found in [telemetry.proto][blueye.protocol.types.telemetry]

## Removing a callback
A callback is removed with [`remove_msg_callback`][blueye.sdk.drone.Telemetry.remove_msg_callback] using the ID returned when creating the callback.

## Adjusting the publishing frequency of a telemetry message
[`set_msg_publish_frequency`][blueye.sdk.drone.Telemetry.set_msg_publish_frequency] changes how often the drone publishes a telemetry message. The frequency must be greater than 0 and at most 100 Hz.

The drone has a single telemetry publisher shared by every connected client, so the new rate also applies to the Blueye app and any other SDK client, and it stays in effect until the drone reboots. There is no request for restoring the default, so set the rate back yourself before your program exits if other clients depend on it, as the example at the bottom of this page does.

Not every message has a publish frequency. The messages in [`EVENT_DRIVEN_TELEMETRY`][blueye.sdk.constants.EVENT_DRIVEN_TELEMETRY] are published when their data arrives, such as a sonar ping or a detection, rather than on a timer. Messages from peripherals, like the thickness gauge, only exist while that peripheral is connected. The drone refuses to change the frequency in both cases, and the SDK raises a `RuntimeError` that names the message and the reason.

On Blunux versions older than 5.1, changing a rate could stop the drone from publishing that message until it restarts, while the request still reported success. If a message goes quiet after a rate change on such a drone, a reboot brings it back.

## Adjusting the logging frequency of a telemetry message
The drone writes telemetry to the dive log at its own rate, separate from the publish rate. [`set_msg_log_frequency`][blueye.sdk.drone.Telemetry.set_msg_log_frequency] changes how often a message is logged, for example to get IMU or DVL data at a higher rate in the log without sending it to every client at that rate. It requires Blunux 5.1 or newer and takes the same frequency range as the publish frequency.

On the X3 Ultra and X7 a multibeam recording raises the log rate of six messages while it runs (`PositionEstimateTel`, `AttitudeTel`, `CalibratedImuTel`, `CalibratedImuHpTel`, `DepthTel` and `AltitudeTel`) and restores their defaults when it stops. A rate set for one of those is replaced both times.

## IMU telemetry
The drone publishes raw and calibrated data from its inertial measurement units (IMUs):

| Message | Data | Models |
| --- | --- | --- |
| `Imu1Tel`, `Imu2Tel` | Raw data from the drone's two IMUs | All |
| `CalibratedImuTel` | Calibrated IMU data | All |
| `ImuHpTel` | Raw data from the high-precision IMU | X3 Ultra and X7 |
| `CalibratedImuHpTel` | Calibrated high-precision IMU data | X3 Ultra and X7 |

Each message carries an `imu` field with the accelerometer in g, the gyroscope in rad/s, the magnetometer in μT and the temperature in °C. The axes are the drone's body frame: x forward, y right and z down. A drone at rest reads about +1 g on z. The high-precision IMU has no magnetometer, and its magnetometer fields stay 0.

All five are published at 1 Hz by default. Raise the rate with [`set_msg_publish_frequency`](#adjusting-the-publishing-frequency-of-a-telemetry-message), which changes it for every client, or the log rate with [`set_msg_log_frequency`](#adjusting-the-logging-frequency-of-a-telemetry-message). This example prints all of them; on models without the high-precision IMU the high-precision callback never runs:

{{code_from_file("../examples/print_imu.py", "python")}}

## Example
The following example illustrates how can use a callback to print the depth reported by the drone.

{{code_from_file("../examples/print_depth.py", "python")}}

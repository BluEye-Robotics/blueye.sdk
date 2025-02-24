# Subscribing to a telemetry message

The drone publishes all of its telemetry data as protobuf encoded messages transmitted via a ZeroMQ socket. You can find the protobuf message definitions in the [Protocol Definitions](https://github.com/BluEye-Robotics/ProtocolDefinitions/) repository, and the generated python definitions are located in the [blueye.protocol](https://github.com/BluEye-Robotics/blueye.protocol) repository.

Upon connection the [Drone object][blueye.sdk.drone.Drone] will instantiate an instance of the [Telemetry class][blueye.sdk.drone.Telemetry] as the `telemetry` attribute. Using this attribute one can control various telemetry function and add/remove new callbacks.

## Adding a callback
To add a callback we need to use the [`add_msg_callback`][blueye.sdk.drone.Telemetry.add_msg_callback] function, and provide it with a list of telemetry messages types we want it to trigger on, as well as a function handle to call. All available telemetry messages can be found in [telemetry.proto][blueye.protocol.types.telemetry]

## Removing a callback
A callback is removed with [`remove_msg_callback`][blueye.sdk.drone.Telemetry.remove_msg_callback] using the ID returned when creating the callback.

## Adjusting the publishing frequency of a telemetry message
By using the [`set_msg_publish_frequency`][blueye.sdk.drone.Telemetry.set_msg_publish_frequency] function we can alter how often the drone should publish the specified telemetry message. The valid frequency range is 0 to 100 Hz.

## Example
The following example illustrates how can use a callback to print the depth reported by the drone.

{{code_from_file("../examples/print_depth.py", "python")}}

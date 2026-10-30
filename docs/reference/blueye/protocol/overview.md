# Message Types Overview

## Telemetry Messages
Telemetry messages are used to receive real-time data from the drone. Examples of telemetry messages include depth, altitude, attitude, and battery status. These messages are handled by the [TelemetryClient][blueye.sdk.connection.TelemetryClient] class. They are subscribed to and processed to update the state of the drone or trigger callbacks.

## Control Messages
Control messages are used to send commands to control the drone's behavior. Examples of control messages include setting light intensity, controlling thrusters, and taking pictures. These messages are handled by the [CtrlClient][blueye.sdk.connection.CtrlClient] class. They are sent to the drone to perform actions like adjusting lights, moving the drone, or starting/stopping recordings.

## Request-Reply (Req_Rep) Messages
Request-Reply messages are used for synchronous communication where a request is sent, and a response is expected. Examples of request-reply messages include getting camera parameters, setting overlay parameters, and synchronizing time. These messages are handled by the [ReqRepClient][blueye.sdk.connection.ReqRepClient] class. They are used to query the drone for information or to set configurations that require confirmation.

## Message Formats
Message formats define the structure and serialization of messages. These include Protobuf message definitions for telemetry, control, and request-reply messages. Message formats are used internally by the SDK to serialize and deserialize messages, ensuring consistent communication between the SDK and the drone. For example, the telemetry message "DepthTel" will have a "Depth" message from message formats.

Each message on the reference pages lists its fields under "Attributes", with the unit, range and frame of the field where the protocol defines one. Enums list their values the same way.

## Mission Planning Messages
Mission planning messages are used for planning and executing missions. Examples of mission planning messages include waypoints and mission start/stop commands. These messages are used to define and control autonomous missions for the drone, allowing for pre-programmed routes and actions to be executed by the drone.

## Aquatroll Messages
Aquatroll messages describe an In-Situ Aqua TROLL water quality probe connected to a guest port. The readings arrive as telemetry in [AquaTrollSensorParametersTel][blueye.protocol.types.telemetry.AquaTrollSensorParametersTel], one parameter block per sensor. [AquaTrollProbeMetadataTel][blueye.protocol.types.telemetry.AquaTrollProbeMetadataTel] and [AquaTrollSensorMetadataTel][blueye.protocol.types.telemetry.AquaTrollSensorMetadataTel] describe the probe and its sensors. Two control messages set the unit of a parameter and the connection status of the probe. There are no request messages for sensor data; read the telemetry instead.

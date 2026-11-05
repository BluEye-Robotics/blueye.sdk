# Connecting to the drone

A [`Drone`][blueye.sdk.drone.Drone] object connects when it is created and stays connected until you call [`disconnect`][blueye.sdk.drone.Drone.disconnect] or the script exits. This page covers what the drone does while a client is connected, when that client goes quiet, and when it leaves.

## Choosing how to connect

Connections require Blunux 3.2 or newer. Use an observer connection for telemetry, log downloads, or other work that should leave control with the pilot:

```python
import time
from blueye.sdk import Drone

with Drone(connect_as_observer=True, log_notifications=True) as drone:
    time.sleep(1)  # Allow the first telemetry messages to arrive.
    print(drone.get_depth())  # Can still be None if no depth message has arrived.
```

The default `Drone()` connection is eligible for control. If nobody holds control, it takes control, zeroes the thruster setpoints and synchronizes the drone's clock to the computer. If another client already holds control, it joins without displacing that client, but can inherit control when that client leaves.

| Argument | Effect |
| --- | --- |
| `ip="192.168.1.101"` | Drone address; change it for a routed network. |
| `connect_as_observer=True` | Exclude this connection from control assignment and handover. |
| `disconnect_other_clients=True` | Disconnect clients holding control until this non-observer connection has control. Ignored for an observer connection. |
| `log_notifications=True` | Log incoming drone notifications through Python's `logging` module. Configure logging to display them. |
| `client_info=...` | Supply a [`blueye.protocol.ClientInfo`][blueye.protocol.types.message_formats.ClientInfo]; otherwise the SDK identifies itself using its version, OS and hostname. |
| `auto_connect=False` | Construct the object without connecting; call `connect()` later. |

`connect_as_observer`, notification logging and the other connection options must be passed to `connect()` itself when using `auto_connect=False`; they are not saved for a later call.

### Using the Blueye app alongside a script

The Blueye app initially joins as an observer. When the pilot starts a dive, it requests control if nobody has it; otherwise it reports the client in control and refuses to start the dive. A plain `Drone()` script can therefore block the pilot even if the app connected first. Use `connect_as_observer=True` for read-only scripts.

An observer connection is not a read-only permission: setters still send commands. The depth callback example deliberately changes a shared telemetry rate to demonstrate the API; omit those changes when another client's rate must be preserved. See [telemetry subscriptions](telemetry-callback.md).

### Inspecting clients and taking control

[`get_connected_clients`][blueye.sdk.drone.Drone.get_connected_clients] and [`get_client_in_control`][blueye.sdk.drone.Drone.get_client_in_control] read the latest client-list telemetry. Both return `None` until it arrives. Once available, client id `0` means nobody holds control.

```python
with Drone(connect_as_observer=True) as drone:
    deadline = time.monotonic() + 5
    clients = drone.get_connected_clients()
    while clients is None and time.monotonic() < deadline:
        time.sleep(0.1)
        clients = drone.get_connected_clients()
    for client in clients or []:
        print(client.client_id, client.client_info.name, client.client_info.is_observer)
    print("Client in control:", drone.get_client_in_control())
```

[`take_control()`][blueye.sdk.drone.Drone.take_control] disconnects other clients until this client is in control; it is not a cooperative handover request. Coordinate with the pilot before calling it or connecting with `disconnect_other_clients=True`. An observer is excluded from promotion, so `take_control()` cannot turn an observer into a controller and may disconnect other clients before timing out. Disconnect and reconnect as a non-observer if control is needed.

## The watchdog

The drone expects a watchdog message from every connected client. The SDK sends one every second from a background thread for as long as the connection is open. The drone keeps two timers on these messages: a 3 second safety timer for the client in control, described below, and a client list that drops a client after about 4 seconds of silence.

The thread is a daemon thread, so it stops when the Python interpreter exits. A script that ends right after starting something on the drone, a mission for example, has stopped petting the watchdog 3 seconds before the drone notices.

## What the drone does when the client in control goes quiet

Only watchdog messages from the client in control count for the drone's safety timer. When they stop for 3 seconds, the drone runs its failsafe once:

- All auto modes are switched off: auto depth, auto heading, auto altitude, station keeping, weather vaning and the mission autopilot.
- The stick input is zeroed, boost and slow included.
- The main lights and a guest-port light are switched off.
- The laser is switched off and laser dot tracking stops.
- The multibeam stops.
- The gripper stops moving.
- Running computer vision models are stopped.
- A running mission is aborted and its state becomes `MISSION_STATE_ABORTED`.

The failsafe also runs 3 seconds after the client in control disconnects, unless another client has taken over control by then.

## Control handover

The first client to connect without `connect_as_observer=True` is in control. When the client in control disconnects, or is dropped from the client list after about 4 seconds of silence, the drone hands control to the client that has been connected the longest among those that did not connect as observers. If there is none, nobody is in control and the drone reports client id 0.

[`Drone.in_control`][blueye.sdk.drone.Drone] is set when the connection is made and by [`take_control`][blueye.sdk.drone.Drone.take_control]. It is not updated afterwards, so after a handover it is stale. Compare [`get_client_in_control`][blueye.sdk.drone.Drone.get_client_in_control] with `client_id` for the current answer:

```python
from blueye.sdk import Drone

d = Drone()
in_control_now = d.get_client_in_control() == d.client_id
```

## Observers

`Drone(connect_as_observer=True)` keeps a client out of the handover: it is never given control. It does not make the SDK read-only. Every setter still sends its message, and the drone acts on control messages from any client. An observer's watchdog messages do not count for the safety timer either, so an observer cannot keep the failsafe from running when the client in control goes away.

## Ending the connection

Call [`disconnect`][blueye.sdk.drone.Drone.disconnect] when the script is done. The drone removes the client at once and hands control over without waiting for the 3 second timeout. Scripts that start a mission should stay connected until the mission has ended, see [Mission planning](mission-planning.md#loading-and-running-the-mission).

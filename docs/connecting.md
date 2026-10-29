# Connecting to the drone

A [`Drone`][blueye.sdk.drone.Drone] object connects when it is created and stays connected until you call [`disconnect`][blueye.sdk.drone.Drone.disconnect] or the script exits. This page covers what the drone does while a client is connected, when that client goes quiet, and when it leaves.

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

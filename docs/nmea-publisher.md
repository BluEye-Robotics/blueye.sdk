# NMEA position and heading

This page includes example Python scripts for forwarding the drone's position and heading to NMEA receivers, and for sending an external positioning system's fixes to the drone. Each script is shown below with its filename linked to a copy bundled with this documentation version. These links also work in the SDK's installed, offline documentation.

[Download all examples](examples.zip) and extract the archive, or save the individual example and the shared `nmea_utils.py` helper shown at the end of this page in the same directory. Use the SDK version that matches these docs. If you need the example dependencies, install `"blueye.sdk[examples]==<version>"`, replacing `<version>` with that SDK version. This keeps the SDK pinned while adding the dependencies.

The scripts use NMEA 0183 sentences with an XOR checksum (`*hh`) and a CRLF terminator. Coordinates are decimal degrees in Python and unsigned degrees/minutes plus hemisphere letters in the sentences.

## Forwarding the drone's position

The `nmea_publisher.py` example below subscribes to `PositionEstimateTel` as an observer and sends GPGLL sentences to a chart plotter or other UDP receiver. It carries the position estimate's validity flag as `A` (valid) or `V` (invalid). Non-finite or out-of-range coordinates are skipped.

The default destination is the surface-unit subnet's broadcast address, `192.168.1.255`, on port **10111**. Change it to your receiver's address and port. Do not broadcast these estimates to port 10110: that is the drone's position input, and feeding its output back into that input creates a feedback loop. If a chart plotter requires port 10110, send directly to the plotter's IP address.

{{code_from_file("../examples/nmea_publisher.py", "python")}}

## Forwarding heading to a serial port

The `nmea_heading_publisher.py` example below sends the latest yaw as HDT at up to 10 Hz. Set `COM_PORT` and `BAUD_RATE` for your receiver. It connects as an observer without changing the drone-wide attitude publishing rate. It waits for an attitude message, skips non-finite values, and stops sending if no attitude has arrived for one second. Heading is wrapped and rounded to 0.0–359.9 degrees.

{{code_from_file("../examples/nmea_heading_publisher.py", "python")}}

## Feeding an external position to the drone

The drone listens on **UDP port 10110** for its own position, such as fixes from a topside USBL system. This is separate from the pilot's position. Send the ROV's measured latitude and longitude, not the boat's GPS coordinates and not the drone's own position estimate.

Blunux 4.2.6 and newer pass `GNGGA`, `GPGLL`, `PBLPLL` and `PSONLLD` sentences to the position estimator, and Blunux 5.1 adds `GPGGA` and `GNGLL`. Other sentence types are ignored. The example sends `GPGLL`, which all of these versions accept.

Send one checksummed, CRLF-terminated sentence per UDP datagram to the drone's IP address, normally `192.168.1.101`. Supply fresh fixes at **1 Hz or faster**. The NMEA navigation source expires after about three seconds without a valid fix. Mark unusable fixes invalid rather than repeatedly sending the last valid position with a new timestamp.

/// admonition | Position reset
    type: warning
The first valid NMEA fix resets the drone's local position frame and odometer. Do not inject test coordinates during a dive or a running mission.
///

The `nmea_position_input.py` example below reads `latitude longitude A|V` lines from standard input and unicasts a GPGLL sentence for each line. It needs no SDK connection or control of the drone. Connect it to an adapter for your positioning system that emits fresh fixes without buffering, for example:

```shell
python -u positioning_adapter.py | python examples/nmea_position_input.py --ip 192.168.1.101
```

`positioning_adapter.py` is your own adapter, not a supplied example. If it already produces NMEA, send those sentences directly instead. The supplied script does not repeat old fixes if its input stops.

{{code_from_file("../examples/nmea_position_input.py", "python")}}

### Checking that the drone receives the fixes

Inspect the NMEA entry in `PositionEstimateTel.position_estimate.navigation_sensors`. The overall estimate's `is_valid` flag alone does not tell you whether the NMEA source is valid.

```python
import time

import blueye.protocol as bp
from blueye.sdk import Drone


def show_nmea(msg_type, msg):
    for sensor in msg.position_estimate.navigation_sensors:
        if sensor.sensor_id == bp.NavigationSensorID.NAVIGATION_SENSOR_ID_NMEA:
            print(sensor.is_valid, sensor.global_position)


with Drone(connect_as_observer=True) as drone:
    drone.telemetry.add_msg_callback([bp.PositionEstimateTel], show_nmea)
    time.sleep(10)
```

Older firmware may not report the per-source status. The resulting global estimate can also incorporate other sensors, so it need not equal each incoming fix exactly.

NMEA position input does **not** enable station keeping. See [station keeping requirements][blueye.sdk.motion.Motion.enable_station_keeping] and [waypoint missions](mission-planning.md) for supported control modes. Waypoint mission legs are limited to 300 m.

## Shared sentence formatting

Both position scripts and the heading publisher use this helper:

{{code_from_file("../examples/nmea_utils.py", "python")}}

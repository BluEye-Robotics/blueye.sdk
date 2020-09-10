# Log file format
The log files from the Blueye drones are in essence a recording of the data that is
published over UDP stored as a comma-separated-value (CSV) file.

The rest of this page documents the most useful fields of the log files. The column
indices listed are zero-based. If you feel that some fields need more documentation,
feel free to open an issue
[on Github](https://github.com/BluEye-Robotics/blueye.sdk/issues/new), and we'll happily
supply the requested information.

### Time
Column | Type    | Unit                                                      | Description
-------|---------|-----------------------------------------------------------|--------------------------------------------
2      | Integer | Milliseconds                                              | The elapsed time since the start of the log
3      | Float   | [Unix timestamp](https://en.wikipedia.org/wiki/Unix_time) | Global time

### Position
The position is based on the user's phone's GPS at the start of the dive.

Column | Type  | Unit    | Description
-------|-------|---------|------------
6      | Float | Degrees | Latitude
7      | Float | Degrees | Longitude


### File storage
Column | Type    | Unit  | Description
-------|---------|-------|--------------------------------
8      | Integer | Bytes | Total file storage on the drone
9      | Integer | Bytes | Available free space

### Temperature
Note: All temperatures are in "deci-degrees Celsius", ie. to get °C you need to divide the value by 10.

Column | Type    | Unit         | Description
-------|---------|--------------|----------------------------
11     | Integer | Deci-Celsius | Bottom canister temperature
12     | Integer | Deci-Celsius | Water temperature
13     | Integer | Deci-Celsius | Top canister temperature
14     | Integer | Deci-Celsius | CPU temperature

### Internal humidity
Note: The unit is in deci-percent (ie. divide by 10 to get percent).

Column | Type    | Unit         | Description
-------|---------|--------------|---------------------------------
15     | Integer | Deci-percent | Humidity in the top canister.
16     | Integer | Deci-percent | Humidity in the bottom canister.

### Lights
Column | Type    | Unit | Description
-------|---------|------|------------------------------------------------
17     | Integer | -    | State of the on-board light. Range is 0 to 255.

### Depth
Column | Type    | Unit         | Description
-------|---------|--------------|--------------------------------------------------------------------------------------
22     | Integer | Milli-meters | Depth below water surface. Positive values are below the surface, negative are above.

### Control force
Control force is the force exerted on the drone by the control system.

Column | Type  | Unit   | Description
-------|-------|--------|------------------------------
29     | Float | Newton | Force in the surge direction.
30     | Float | Newton | Force in the sway direction.
31     | Float | Newton | Force in the heave direction.
32     | Float | Newton | Force in the yaw direction.

### Orientation (pose)
Column | Type  | Unit    | Description
-------|-------|---------|-------------------------------------
32     | Float | Degrees | Roll angle. Range from -180° - 180°
33     | Float | Degrees | Pitch angle. Range from -180° - 180°
34     | Float | Degrees | Yaw angle. Range from -180° - 180°

### Battery
Column | Type    | Unit          | Description
-------|---------|---------------|-------------------------------------------------------------------------------------
38     | Integer | Milli-volts   | Battery voltage
39     | Integer | Milli-amperes | Battery current. Negative values are drained from the battery, positive are charged.
41     | Integer | Percent       | Relative state of charge. Range from 0 - 100 %

# Deprecated properties

v2.8.0 replaced the properties that exposed drone state and control with explicit getter and setter methods. The old names still work but emit a `DeprecationWarning` on every read and write, and they will be removed in v3. Code written for v2.0 to v2.7 can be updated one name at a time with the tables below.

The warning names the replacement. Python shows each deprecation warning once per location by default; to see every use a script makes while it runs, turn them all on:

```shell
python -W always::DeprecationWarning my_script.py
```

`Motion.current_thruster_setpoints` is read-only, like the other properties without a setter below. Set the setpoints with [`send_thruster_setpoint()`][blueye.sdk.motion.Motion.send_thruster_setpoint] or the individual setters. Assigning to a read-only property raises `AttributeError`.

The tables are generated from the list the test suite checks, so every row has a test behind it.

{{deprecated_properties_table()}}

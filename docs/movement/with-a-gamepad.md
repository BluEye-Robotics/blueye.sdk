# Controlling the drone from a gamepad

To run the example remember to first install the optional dependencies needed for running the examples
``` shell
pip install "blueye.sdk[examples]"
```

The example below illustrates how one could use an Xbox controller and the SDK to control the drone.

The [inputs library](https://github.com/zeth/inputs) supports many other gamepads, so using a
different controller should be as simple as looking up the event codes for the buttons/axes and
mapping them to the functions you want.

{{code_from_file("../examples/gamepad_controller.py", "python")}}

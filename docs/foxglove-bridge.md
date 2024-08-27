# Visualize live sensor data from the drone with Foxglove
With some simple steps you can visualize live sensor data from the drone in Foxglove.

1. Download foxglove here and create an account.
2. Power on the drone and connect your computer to the Blueye wifi.
3. Run `pip install foxglove_websocket` and `pip install protobuf` in your pyenv.
4. In the examples folder you simply run the foxglove_bridge_ws.py.
5. Open foxglove and open a new `Foxglove WebSocket` connection and leave it on default (`ws://localhost:8765`).
6. Add panel, Raw message, or Plot and select the topic you want to display.

{{code_from_file("../examples/foxglove_bridge_ws.py", "python")}}

How it works. The `foxglove_bridge_ws.py` script is using the Blueye SDK to subscribe to the drone telemetry messages with `ZeroMQ`. Then the foxglove websocket server is forwarding the protobuf messages so they can be subscribed to in the `Foxglove GUI`.

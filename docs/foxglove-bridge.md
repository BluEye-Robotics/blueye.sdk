# Visualize live sensor data from the drone with Foxglove
With some simple steps you can visualize live sensor data from the drone in Foxglove.

1. Download foxglove [here](https://foxglove.dev/download) and create an account.
2. Power on the drone and connect your computer to the Blueye wifi.
3. Run `pip install "blueye.sdk[examples]"` to get the necessary dependencies, if you have not done so already.
4. Clone the [blueye.sdk repository](https://github.com/BluEye-Robotics/blueye.sdk) to get the examples, or copy the script below into a file. In the examples folder you simply run `python foxglove_bridge_ws.py` to start the bridge.
5. Open foxglove and open a new `Foxglove WebSocket` connection and leave it on default (`ws://localhost:8765`).
6. Add panel, Raw message, or Plot and select the topic you want to display.

### Alternative with Docker
We have also provided a docker container that you can use to automatically starts the blueye-foxglove server.

1. Pull the image: `docker pull blueyerobotics/foxglove-bridge`.
2. Run the image in a container with port 8765 open: `docker run --rm -p 8765:8765 blueyerobotics/foxglove-bridge`.
3. Connect as above in step 5.

### How it works
 The script below uses the Blueye SDK to subscribe to the drone telemetry messages with `ZeroMQ`. Then the foxglove websocket server is forwarding the protobuf messages so they can be subscribed to in the `Foxglove GUI`.

### Example of a websocket bridge
{{code_from_file("../examples/foxglove_bridge_ws.py", "python")}}

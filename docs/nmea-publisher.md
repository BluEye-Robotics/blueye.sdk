# NMEA Position Publisher

This example shows how one can use the blueye.sdk to forward position messages from the drone as NMEA 0183 messages, eg. to use in a chart plotter on a boat, etc.

The script performs the following steps:

1. **UDP Configuration**: Sets up the UDP IP and port for sending NMEA messages. If your receiver expects to receive data on a different port you need to change it here
2. **Drone Connection**: Establishes a connection to the Blueye drone.
3. **Callback Registration**: Registers a callback function to handle position estimate telemetry messages.
4. **Main Loop**: Keeps the script running to continuously receive and send messages.

{{code_from_file("../examples/nmea_publisher.py", "python")}}

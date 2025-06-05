# Odometer to Imagenex 831L Publisher

This example shows how one can use the blueye.sdk to forward the odometer distance from the position messages from the drone to the PipeSonarL software from Imagenex. The PipeSonarL software is used to operate the [Imagenex 831L Pipe Profiling sonar](https://imagenex.com/products/831l-pipe-profiling).

The PipeSonarL software accepts input from external cable counting systems, which is used to generate a 3D point cloud from a pipe inspection.

On a Blueye X3, we can use the odometer distance from the position messages to generate the cable count for the PipeSonarL software. The odometer distance is the distance the drone has traveled since the last reset.

The script performs the following steps:

1. **UDP Configuration**: Sets up the UDP IP and port for sending NMEA messages. If your receiver expects to receive data on a different port, you need to change it here.
2. **Increase publishing frequency**: Increases the publishing frequency of the position estimate message to 5 Hz.
3. **Drone Connection**: Establishes a connection to the Blueye drone.
4. **Callback Registration**: Registers a callback function to handle position estimate telemetry messages.
5. **Main Loop**: Keeps the script running to continuously receive and send messages.

{{code_from_file("../examples/publish_odometer_to_831l.py", "python")}}

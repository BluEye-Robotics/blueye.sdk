# Visualize dive log sensor data with Foxglove
With some simple steps you can visualize dive log data with ease in Foxglove. This is a great tool to play back and visualize control signals and estimated states and other sensor data from the dive.

1. Download foxglove [here](https://foxglove.dev/download) and create an account.
2. Download a divelog from the drone as shown [here](https://blueye-robotics.github.io/blueye.sdk/latest/logs/listing-and-downloading/).
3. Run `pip install "blueye.sdk[examples]"` to get the necessary dependencies, if you have not done so already.
4. Clone the [blueye.sdk repository](https://github.com/BluEye-Robotics/blueye.sdk) to get the examples, or copy the script below into a file. In the examples folder you simply run `python foxglove_bez_to_mcap.py <logfile.bez> [output_filename.mcap]` to convert your .bez-file.
5. Open foxglove, in the top left menu, click on `Open local file`, and pick your newly created .mcap-file.
6. Click on `Add panel`, and `Raw message`, or `Plot` and select the signal you want to display.
7. Start typing `DepthTel.depth.value` to get auto-complete on all available messages in the protocol.
8. You can also get a nice overview of the logged messages with this command: `mcap info logfile.mcap` in your terminal.

### The .bez to .mcap log file converter:
{{code_from_file("../examples/foxglove_bez_to_mcap.py", "python")}}

# Visualize dive log sensor data with Foxglove

With some simple steps you can visualize dive log data with ease in Foxglove. This is a great tool to play back and visualize control signals and estimated states and other sensor data from the dive.

1. Download Foxglove [here](https://foxglove.dev/download) and create an account.
2. Install the SDK with the `cli` extra to get the [`blueye` CLI](../cli.md) and the
   `.mcap` converter: `pip install "blueye.sdk[cli]"`.
3. Download a dive log from the drone and convert it in one step:

    ```shell
    blueye logs download --latest 1 --mcap
    ```

    Already have `.bez` files on disk? Convert them directly — no drone needed:

    ```shell
    blueye logs convert mydive.bez
    ```

4. Open Foxglove, in the top left menu, click on `Open local file`, and pick your newly created .mcap-file.
5. Click on `Add panel`, and `Raw message`, or `Plot` and select the signal you want to display.
6. Start typing `DepthTel.depth.value` to get auto-complete on all available messages in the protocol.
7. You can also get a nice overview of the logged messages with this command: `mcap info logfile.mcap` in your terminal.

For programmatic access to the log records (the converter is built on the same
parser), see [`LogStream`][blueye.sdk.logs.LogStream].

# Development

## Project structure and context
`blueye.sdk` is a Python package that exposes the functionality of the Blueye app.
The SDK depends on three projects:

* [`ProtocolDefinitons`](https://github.com/BluEye-Robotics/ProtocolDefinitions) : TCP commands are sent from a computer or mobile device to the drone, and UDP messages with telemetry data are sent from the drone back to the top side device. These TCP commands and UDP telemetry messages are defined as json files in this project.
* [`blueye.protocol`](https://github.com/BluEye-Robotics/blueye.protocol) : Implements a TCP client for connecting to a Blueye drone and sending the TCP commands defined in `ProtocolDefinitions`, and a UDP client for receiving and parsing the telemetry messages defined in `ProtocolDefinitions`
* [`blueye.sdk`](https://github.com/BluEye-Robotics/blueye.sdk) : Wraps the TCP and UDP client from `blueye.protocol` into an easy to use Python object. `blueye.sdk` also adds functionality for downloading log files from the drone.

## Tests
To run the tests when connected to a surface unit with an active drone, do:

```shell
pytest
```

To run tests when not connected to a drone, do:

``` shell
pytest -k "not connected_to_drone"
```

## Documentation
The documentation is written in markdown and converted to html with
[portray](https://timothycrosley.github.io/portray/). To generate and open the
documentation locally run

``` shell
portray in_browser
```

## Formatting
To keep the code style consistent [`Black`](https://pypi.org/project/black/) is used for code formatting.
To format code with black run `black .` in the project root directory.
Adding a pre-commit hook ensures black is run before every commit

```shell
pre-commit install
```
adds a pre-commit hook for black formatting.

## Can't find what you are looking for?
We're continuously improving this project and if you feel features are missing or something feels clunky, please open an [issue](https://github.com/BluEye-Robotics/blueye.sdk/issues) and suggest a change. Bug reports and fixes are of course always welcome!

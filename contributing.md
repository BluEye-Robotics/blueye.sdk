# Contributing to blueye.sdk

## Project structure and context
`blueye.sdk` is a Python package that exposes the functionality of the Blueye app.
The SDK depends on three projects:

* [`ProtocolDefinitons`](https://github.com/BluEye-Robotics/ProtocolDefinitions) : This repository contains the definitions for the Protobuf messages used to communicate with the drone.
* [`blueye.protocol`](https://github.com/BluEye-Robotics/blueye.protocol) : This is the generated python package from the definitions in `ProtocolDefinitions`.
* [`blueye.sdk`](https://github.com/BluEye-Robotics/blueye.sdk) : Defines [ZeroMQ](https://zeromq.org/) sockets for telemetry-, control-, and request-response messages. These sockets are then wrapped into an easy to use Python object. `blueye.sdk` also adds functionality for downloading log files from the drone.

## Tests
To run the tests when connected to a surface unit with an active drone, do:

```shell
uv run pytest
```

To run tests when not connected to a drone, do:

``` shell
uv run pytest -k "not connected_to_drone"
```

## Documentation
The documentation is written in markdown and converted to html with [mkdocs](https://www.mkdocs.org/). To generate and open the documentation locally run

``` shell
uv run mkdocs serve
```

## Formatting
To keep the code style consistent [`Black`](https://pypi.org/project/black/) is used for code formatting.
To format code with black run `black .` in the project root directory.
Adding a pre-commit hook ensures black is run before every commit

```shell
uv tool install pre-commit --with pre-commit-uv --force-reinstall
pre-commit install
```

## Can't find what you are looking for?
We're continuously improving this project and if you feel features are missing or something feels clunky, please open an [issue](https://github.com/BluEye-Robotics/blueye.sdk/issues) and suggest a change. Bug reports and fixes are of course always welcome!

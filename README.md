# blueye.sdk
[![Tests](https://github.com/BluEye-Robotics/blueye.sdk/workflows/Tests/badge.svg)](https://github.com/BluEye-Robotics/blueye.sdk/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

A Python package for remote control of the Blueye Pioneer underwater drone.

## Installation
```shell
pip install blueye.sdk
```

## Tests
To run the tests when connected to a surface unit with a active drone, do:

```shell
pytest
```

To run tests when not connected to a drone, do:

``` shell
pytest -k "not connected_to_drone"
```

## Documentation in portray
To generate the documentation locally run

``` shell
portray in_browser
```

## Formatting with black
Run `black .` to autoformat, or add the pre-commit hook

```shell
pre-commit install
```
to have it done done automatically on every commit.

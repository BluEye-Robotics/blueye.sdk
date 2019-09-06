# blueye.sdk
[![Tests](https://github.com/BluEye-Robotics/blueye.sdk/workflows/Tests/badge.svg)](https://github.com/BluEye-Robotics/blueye.sdk/actions)

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

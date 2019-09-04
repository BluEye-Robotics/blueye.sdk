# blueye.sdk
[![Tests](https://github.com/BluEye-Robotics/blueye.sdk/workflows/Tests/badge.svg)](https://github.com/BluEye-Robotics/blueye.sdk/actions)

A Python package for remote control of the Blueye Pioneer underwater drone.

## Installation
```shell
pip install blueye.sdk
```

## Tests
to run the tests do:

```shell
pytest
```

To run tests when not connected to a drone, i.e tests that uses mocks not drone hardware do:

``` shell
pytest -k "not connected_to_drone"
```

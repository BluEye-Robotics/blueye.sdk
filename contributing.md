# Development

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
This SDK is still very much a work in progress, if you feel features are missing or something feels clunky, please open an [issue](https://github.com/BluEye-Robotics/blueye.sdk/issues) and suggest a change. Bug reports and fixes are of course always welcome!

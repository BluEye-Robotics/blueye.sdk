"""Render the deprecated property table for docs/deprecations.md.

The list of shims lives in tests/test_deprecations.py, where every entry is exercised by the test
suite. The docs read the same list, so the page cannot drift from the code.
"""

import importlib.util
import os
from collections import defaultdict
from unittest import mock

_TEST_MODULE = os.path.join(os.path.dirname(__file__), "..", "tests", "test_deprecations.py")

# Reference path for every class that owns a shim. The table is grouped in this order.
_REFERENCE_PATHS = {
    "Drone": "blueye.sdk.drone.Drone",
    "Config": "blueye.sdk.drone.Config",
    "Battery": "blueye.sdk.battery.Battery",
    "Motion": "blueye.sdk.motion.Motion",
    "Gripper": "blueye.sdk.guestport.Gripper",
    "Tilt": "blueye.sdk.camera.Tilt",
    "Overlay": "blueye.sdk.camera.Overlay",
    "Camera": "blueye.sdk.camera.Camera",
}


def load_deprecated_properties():
    """The `DEPRECATED_PROPERTIES` list from the test module, loaded by path."""
    spec = importlib.util.spec_from_file_location("test_deprecations", _TEST_MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DEPRECATED_PROPERTIES


def owner_class_name(accessor) -> str:
    """The name of the class whose shim an accessor from the test list reaches.

    The accessor is called with a mock in place of the drone and the attribute chain it took,
    `drone.camera.overlay` say, is resolved through the classes the real objects would have, so
    the lambdas need no particular spelling. A helper function that builds a real object returns
    that object's class.
    """
    import blueye.sdk

    drone_mock = mock.MagicMock()
    result = accessor(drone_mock)
    if not isinstance(result, mock.Mock):
        return type(result).__name__
    if result is drone_mock:
        return "Drone"
    # Walk the attribute chain the lambda took on the mock, e.g. drone.camera.overlay, and
    # resolve each step through the class annotations or the type of the attribute on a real class.
    owner = blueye.sdk.Drone
    for attribute in result._extract_mock_name().split(".")[1:]:
        owner = _attribute_class(owner, attribute)
    return owner.__name__


def _attribute_class(owner, attribute):
    """The class of `owner.<attribute>`, found through the module the owner class is defined in."""
    import inspect

    source = inspect.getsource(owner.__init__)
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"self.{attribute} = ") or stripped.startswith(
            f"self.{attribute}: "
        ):
            expression = stripped.split("=", 1)[1].strip()
            class_name = expression.split("(")[0].strip()
            module = inspect.getmodule(owner)
            if hasattr(module, class_name):
                return getattr(module, class_name)
    raise LookupError(f"Cannot resolve the class of {owner.__name__}.{attribute}")


def render_table(deprecated_properties) -> str:
    """One markdown table per class: deprecated property, getter, setter."""
    by_owner = defaultdict(list)
    for accessor, prop, getter, setter in deprecated_properties:
        by_owner[owner_class_name(accessor)].append((prop, getter, setter))

    sections = []
    for name, path in _REFERENCE_PATHS.items():
        rows = by_owner.pop(name, [])
        if not rows:
            continue
        lines = [
            f"### [`{name}`][{path}]",
            "",
            "| Deprecated property | Read with | Write with |",
            "| --- | --- | --- |",
        ]
        for prop, getter, setter in rows:
            read = f"[`{getter}()`][{path}.{getter}]"
            write = f"[`{setter}()`][{path}.{setter}]" if setter else "read-only"
            lines.append(f"| `{prop}` | {read} | {write} |")
        sections.append("\n".join(lines))
    if by_owner:
        raise LookupError(f"No reference path for the classes {sorted(by_owner)}")
    return "\n\n".join(sections)


def define_env(env):
    @env.macro
    def deprecated_properties_table() -> str:
        """The deprecated property tables for docs/deprecations.md.

        Example usage in markdown:

            {{deprecated_properties_table()}}
        """
        return render_table(load_deprecated_properties())

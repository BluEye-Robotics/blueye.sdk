"""Tests for the mkdocs macro that renders docs/deprecations.md from the deprecation test list."""

import re

import pytest

from doc_utils import deprecated_properties
from tests.test_deprecations import DEPRECATED_PROPERTIES, _make_gripper


def test_every_shim_gets_a_row():
    table = deprecated_properties.render_table(DEPRECATED_PROPERTIES)

    rows = [line for line in table.splitlines() if line.startswith("| `")]
    assert len(rows) == len(DEPRECATED_PROPERTIES)
    for _, prop, getter, setter in DEPRECATED_PROPERTIES:
        row = next(line for line in rows if line.startswith(f"| `{prop}`"))
        assert f"`{getter}()`" in row
        assert (f"`{setter}()`" in row) if setter else ("read-only" in row)


def test_every_class_gets_a_section():
    table = deprecated_properties.render_table(DEPRECATED_PROPERTIES)

    sections = re.findall(r"^### \[`(\w+)`\]\[([\w.]+)\]$", table, re.MULTILINE)
    assert [name for name, _ in sections] == [
        "Drone",
        "Config",
        "Battery",
        "Motion",
        "Gripper",
        "Tilt",
        "Overlay",
        "Camera",
    ]
    for name, path in sections:
        assert path.endswith(f".{name}")


@pytest.mark.parametrize(
    "accessor, expected",
    [
        (lambda d: d, "Drone"),
        (lambda drone: drone.camera, "Camera"),
        (lambda d: (d.camera).overlay, "Overlay"),
        (lambda d: d.camera.tilt, "Tilt"),
        (_make_gripper, "Gripper"),
    ],
)
def test_owner_is_resolved_from_the_attribute_chain(accessor, expected):
    # The spelling of the lambda does not matter, only the attributes it reaches
    assert deprecated_properties.owner_class_name(accessor) == expected


def test_unknown_attribute_is_reported():
    with pytest.raises(LookupError, match="Drone.sonar"):
        deprecated_properties.owner_class_name(lambda d: d.sonar)


def test_class_without_reference_path_is_reported():
    class Unknown:
        pass

    with pytest.raises(LookupError, match="Unknown"):
        deprecated_properties.render_table([(lambda d: Unknown(), "x", "get_x", None)])


def test_the_test_list_loads_by_path():
    assert deprecated_properties.load_deprecated_properties() is not None
    assert len(deprecated_properties.load_deprecated_properties()) == len(DEPRECATED_PROPERTIES)

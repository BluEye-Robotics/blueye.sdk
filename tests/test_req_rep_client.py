import blueye.protocol as bp
import pytest

import blueye.sdk


@pytest.mark.parametrize("message", [bp.DepthTel, "blueye.protocol.DepthTel"])
def test_parse_to_type(message):
    assert blueye.sdk.connection.ReqRepClient._parse_type_to_string(message) == "DepthTel"

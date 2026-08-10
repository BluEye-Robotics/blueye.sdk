import pytest

from blueye.sdk.cli.external import metadata
from blueye.sdk.cli.external.metadata import (
    MetadataError,
    extract_script_block,
    parse_tool_metadata,
)

VALID_SCRIPT = """\
# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas"]
#
# [tool.blueye]
# name = "export-logs"
# description = "Export dive logs to CSV"
# min-sdk-version = "2.7.0"
# ///
import sys
"""

NO_DEPS_SCRIPT = """\
# /// script
# [tool.blueye]
# name = "net-check"
# description = "Ping the drone"
# ///
"""


class TestExtractScriptBlock:
    def test_block_extracted_and_uncommented(self):
        block = extract_script_block(VALID_SCRIPT)
        assert 'name = "export-logs"' in block
        assert "# " not in block.splitlines()[0]

    def test_no_block_returns_none(self):
        assert extract_script_block("import sys\n") is None

    def test_bare_hash_lines_handled(self):
        script = NO_DEPS_SCRIPT.replace("# [tool.blueye]", "#\n# [tool.blueye]")
        assert "[tool.blueye]" in extract_script_block(script)

    def test_multiple_script_blocks_rejected(self):
        with pytest.raises(MetadataError, match="multiple"):
            extract_script_block(NO_DEPS_SCRIPT + "\n" + NO_DEPS_SCRIPT)

    def test_other_block_types_ignored(self):
        script = NO_DEPS_SCRIPT.replace("# /// script", "# /// other", 1)
        assert extract_script_block(script) is None


class TestParseToolMetadata:
    def test_full_toml_path(self):
        parsed = parse_tool_metadata(VALID_SCRIPT)
        assert parsed.name == "export-logs"
        assert parsed.description == "Export dive logs to CSV"
        assert parsed.min_sdk_version == "2.7.0"
        assert parsed.has_dependencies is True
        assert parsed.parsed_with_fallback is False

    def test_no_dependencies_detected(self):
        assert parse_tool_metadata(NO_DEPS_SCRIPT).has_dependencies is False

    def test_missing_block_raises(self):
        with pytest.raises(MetadataError, match="no '# /// script'"):
            parse_tool_metadata("print('hi')\n")

    def test_missing_tool_blueye_table_raises(self):
        script = '# /// script\n# requires-python = ">=3.10"\n# ///\n'
        with pytest.raises(MetadataError, match=r"\[tool\.blueye\]"):
            parse_tool_metadata(script)

    def test_missing_name_raises(self):
        script = NO_DEPS_SCRIPT.replace('# name = "net-check"\n', "")
        with pytest.raises(MetadataError, match="'name'"):
            parse_tool_metadata(script)

    def test_missing_description_raises(self):
        script = NO_DEPS_SCRIPT.replace('# description = "Ping the drone"\n', "")
        with pytest.raises(MetadataError, match="'description'"):
            parse_tool_metadata(script)

    @pytest.mark.parametrize(
        "bad_name", ["UPPER", "1starts-with-digit", "-leading-dash", "has space", "a" * 33]
    )
    def test_invalid_names_rejected(self, bad_name):
        script = NO_DEPS_SCRIPT.replace("net-check", bad_name)
        with pytest.raises(MetadataError, match="invalid"):
            parse_tool_metadata(script)

    def test_invalid_toml_raises(self):
        script = NO_DEPS_SCRIPT.replace('"Ping the drone"', '"unclosed')
        with pytest.raises(MetadataError):
            parse_tool_metadata(script)


class TestFallbackParser:
    @pytest.fixture(autouse=True)
    def force_fallback(self, mocker):
        mocker.patch.object(metadata, "_load_toml", return_value=None)

    def test_fallback_parses_string_keys(self):
        parsed = parse_tool_metadata(VALID_SCRIPT)
        assert parsed.name == "export-logs"
        assert parsed.description == "Export dive logs to CSV"
        assert parsed.min_sdk_version == "2.7.0"
        assert parsed.parsed_with_fallback is True

    def test_fallback_detects_dependencies(self):
        assert parse_tool_metadata(VALID_SCRIPT).has_dependencies is True
        assert parse_tool_metadata(NO_DEPS_SCRIPT).has_dependencies is False

    def test_fallback_missing_table_raises(self):
        script = '# /// script\n# requires-python = ">=3.10"\n# ///\n'
        with pytest.raises(MetadataError, match=r"\[tool\.blueye\]"):
            parse_tool_metadata(script)

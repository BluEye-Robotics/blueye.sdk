"""Filename and version-local download links for included code."""

import subprocess
from types import SimpleNamespace

import pytest

from doc_utils.load_code_from_file import define_env, source_revision


@pytest.fixture(params=[b"\n", b"\r\n"], ids=["lf", "crlf"])
def macro_env(tmp_path, request):
    docs = tmp_path / "docs"
    docs.mkdir()
    examples = tmp_path / "examples"
    examples.mkdir()
    (examples / "demo.py").write_bytes(b"print('hello')" + request.param)
    macros = {}

    def register(fn):
        macros[fn.__name__] = fn
        return fn

    env = SimpleNamespace(
        variables={"docs_dir": str(docs)},
        conf={"config_file_path": str(tmp_path / "mkdocs.yml")},
        page=SimpleNamespace(file=SimpleNamespace(src_uri="guide.md")),
        macro=register,
    )
    define_env(env)
    return env, macros


def test_filename_links_to_bundled_source_without_repo_url(macro_env):
    _, macros = macro_env
    rendered = macros["code_from_file"]("../examples/demo.py", "python")
    assert rendered.startswith("[`examples/demo.py`](examples/demo.py)\n\n")
    assert "```python\nprint('hello')\n\n```" in rendered


def test_prefix_applies_to_filename_and_code(macro_env):
    _, macros = macro_env
    rendered = macros["code_from_file"]("../examples/demo.py", "python", "    ")
    assert all(line.startswith("    ") for line in rendered.splitlines() if line)


def test_source_url_encodes_special_characters(macro_env, tmp_path):
    _, macros = macro_env
    (tmp_path / "examples" / "with space#.py").write_text("pass", encoding="utf-8")
    rendered = macros["code_from_file"]("../examples/with space#.py", "python")
    assert "`examples/with space#.py`" in rendered
    assert "(examples/with%20space%23.py)" in rendered


@pytest.mark.parametrize("page", ["movement/guide.md", "movement/index.md"])
def test_nested_page_uses_source_relative_link(macro_env, page):
    env, macros = macro_env
    env.page.file.src_uri = page
    rendered = macros["code_from_file"]("../examples/demo.py", "python")
    assert "(../examples/demo.py)" in rendered


def test_file_outside_repository_gets_no_download_link(macro_env, tmp_path):
    env, macros = macro_env
    repo = tmp_path / "other-repository"
    repo.mkdir()
    env.conf["config_file_path"] = str(repo / "mkdocs.yml")
    rendered = macros["code_from_file"]("../examples/demo.py", "python")
    assert rendered.startswith("`demo.py`\n\n```python")


def test_non_example_source_gets_no_download_link(macro_env, tmp_path):
    _, macros = macro_env
    (tmp_path / "script.py").write_text("pass", encoding="utf-8")
    rendered = macros["code_from_file"]("../script.py", "python")
    assert rendered.startswith("`script.py`\n\n```python")


def test_missing_file_still_reports_error(macro_env):
    _, macros = macro_env
    rendered = macros["code_from_file"]("../examples/missing.py", "python")
    assert rendered.startswith("<b>File not found:")
    assert "missing.py" in rendered


def test_repository_root_uses_config_location(macro_env, tmp_path):
    env, macros = macro_env
    nested_docs = tmp_path / "documentation" / "pages"
    nested_docs.mkdir(parents=True)
    env.variables["docs_dir"] = str(nested_docs)
    rendered = macros["code_from_file"]("../../examples/demo.py", "python")
    assert "[`examples/demo.py`](examples/demo.py)" in rendered


@pytest.fixture
def committed_example(macro_env, tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    # Exercise Windows checkout normalization on every platform: the committed blob uses LF.
    subprocess.run(
        ["git", "-c", "core.autocrlf=true", "-c", "core.safecrlf=false", "add", "examples/demo.py"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "Example",
        ],
        cwd=tmp_path,
        check=True,
    )
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    env, macros = macro_env
    env.conf["repo_url"] = "https://github.com/BluEye-Robotics/blueye.sdk/"
    return macros, revision


def test_github_icon_follows_local_link_and_uses_full_commit(committed_example):
    macros, revision = committed_example
    rendered = macros["code_from_file"]("../examples/demo.py", "python")
    assert rendered.startswith(
        "[`examples/demo.py`](examples/demo.py) [:fontawesome-brands-github:]("
    )
    assert f"/blob/{revision}/examples/demo.py" in rendered
    assert f'"View source on GitHub at {revision[:8]}"' in rendered
    assert "/blob/master/" not in rendered


@pytest.mark.parametrize(
    "replacement", [b"print('changed')\n", b"print('hello') \n", b"\nprint('hello')\n"]
)
def test_changed_source_has_only_the_local_download(committed_example, tmp_path, replacement):
    macros, _ = committed_example
    (tmp_path / "examples" / "demo.py").write_bytes(replacement)
    rendered = macros["code_from_file"]("../examples/demo.py", "python")
    assert rendered.startswith("[`examples/demo.py`](examples/demo.py)\n\n")
    assert "github" not in rendered
    assert replacement.decode("utf-8") in rendered


def test_untracked_source_has_only_the_local_download(committed_example, tmp_path):
    macros, _ = committed_example
    (tmp_path / "examples" / "new.py").write_text("pass\n", encoding="utf-8")
    rendered = macros["code_from_file"]("../examples/new.py", "python")
    assert rendered.startswith("[`examples/new.py`](examples/new.py)\n\n")
    assert "github" not in rendered


def test_source_archive_without_git_keeps_local_link(macro_env):
    env, macros = macro_env
    env.conf["repo_url"] = "https://github.com/BluEye-Robotics/blueye.sdk"
    rendered = macros["code_from_file"]("../examples/demo.py", "python")
    assert rendered.startswith("[`examples/demo.py`](examples/demo.py)\n\n")
    assert "github" not in rendered


def test_git_unavailable_omits_github_link(tmp_path, mocker):
    (tmp_path / ".git").mkdir()
    mocker.patch(
        "doc_utils.load_code_from_file.subprocess.check_output", side_effect=FileNotFoundError
    )
    assert source_revision(tmp_path, "examples/demo.py", b"pass\n") is None

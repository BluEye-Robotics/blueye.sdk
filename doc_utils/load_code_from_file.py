import os
import posixpath
import subprocess
from pathlib import Path, PurePosixPath
from urllib.parse import quote


def source_revision(repo_root: Path, relative_path: str, content: bytes) -> str | None:
    """Return a commit containing the same source, allowing CRLF checkout conversion.

    An archive build may have no Git checkout, and a preview may include uncommitted edits.
    Neither should link to a different version of the file.
    """
    if not (repo_root / ".git").exists():
        return None
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        committed = subprocess.check_output(
            ["git", "show", f"{revision}:{relative_path}"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    # Git may store LF while core.autocrlf checks out CRLF on Windows. Ignore that conversion,
    # but keep all other whitespace significant so edited source cannot link to the wrong code.
    return (
        revision if committed.replace(b"\r\n", b"\n") == content.replace(b"\r\n", b"\n") else None
    )


def define_env(env):
    @env.macro
    def code_from_file(fn: str, flavor: str = "", line_prefix: str = ""):
        """
        Include a file as a fenced code block with its filename.
        Python examples link to downloads bundled with this docs build, including offline builds.
        A GitHub icon links to the build commit when it contains the same file contents.
        Other files get an unlinked filename. The flavor selects syntax highlighting.

        Example usage in markdown:

            {{code_from_file("code/myfile.py", "python", "    ")}}

        """
        docs_dir = env.variables.get("docs_dir", "docs")
        fn = os.path.abspath(os.path.join(docs_dir, fn))
        if not os.path.exists(fn):
            return f"""<b>File not found: {fn}</b>"""
        path = Path(fn)
        content = path.read_bytes()
        config_file = env.conf.get("config_file_path")
        repo_root = (
            Path(config_file).resolve().parent if config_file else Path(docs_dir).resolve().parent
        )
        try:
            relative_path = path.resolve().relative_to(repo_root).as_posix()
        except ValueError:
            label = f"`{path.name}`"
        else:
            label = f"`{relative_path}`"
            if (
                relative_path.startswith("examples/")
                and path.suffix == ".py"
                and "__pycache__" not in path.parts
            ):
                # MkDocs resolves this source-relative link for both directory URLs and the
                # flat HTML layout used by open_local_documentation().
                page_dir = PurePosixPath(env.page.file.src_uri).parent.as_posix()
                source_url = quote(posixpath.relpath(relative_path, page_dir))
                label = f"[{label}]({source_url})"
                repo_url = env.conf.get("repo_url")
                if repo_url:
                    revision = source_revision(repo_root, relative_path, content)
                    if revision:
                        github_url = (
                            f"{repo_url.rstrip('/')}/blob/{revision}/{quote(relative_path)}"
                        )
                        label += (
                            f" [:fontawesome-brands-github:]({github_url} "
                            f'"View source on GitHub at {revision[:8]}")'
                        )

        # Normalize only the rendered Markdown; downloadable copies keep the source bytes.
        text = content.decode("utf-8").replace("\r\n", "\n")
        formatted_lines = "".join(f"{line_prefix}{line}" for line in text.splitlines(keepends=True))
        return f"""{line_prefix}{label}

{line_prefix}```{flavor}
{formatted_lines}
{line_prefix}```"""

    @env.macro
    def external_markdown(fn: str):
        """
        Load markdown from files external to the mkdoGcs root path.
        Example usage in markdown:

            {{external_markdown("../../README.md")}}

        """
        docs_dir = env.variables.get("docs_dir", "docs")
        fn = os.path.abspath(os.path.join(docs_dir, fn))
        if not os.path.exists(fn):
            return f"""<b>File not found: {fn}</b>"""
        with open(fn, "r") as f:
            return f.read()

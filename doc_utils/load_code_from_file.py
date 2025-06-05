import os


def define_env(env):
    @env.macro
    def code_from_file(fn: str, flavor: str = "", line_prefix: str = ""):
        """
        Load code from a file and save as a markdown code block.
        If a flavor is specified, it's passed in as a hint for syntax
        highlighters.

        Example usage in markdown:

            {{code_from_file("code/myfile.py", "python", "    ")}}

        """
        docs_dir = env.variables.get("docs_dir", "docs")
        fn = os.path.abspath(os.path.join(docs_dir, fn))
        if not os.path.exists(fn):
            return f"""<b>File not found: {fn}</b>"""
        with open(fn, "r") as f:
            formatted_lines = "".join(f"{line_prefix}{line}" for line in f.readlines())
            return f"""{line_prefix}```{flavor}
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

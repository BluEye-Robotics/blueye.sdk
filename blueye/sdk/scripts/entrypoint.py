import click
import importlib
from pathlib import Path


class DynamicClickGroup(click.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cmd_dir = Path(__file__).parent

    def list_commands(self, ctx):
        """Dynamically find all commands."""
        rv = []
        for filename in self.cmd_dir.glob("*.py"):
            if filename.name.startswith("__") or filename.name == "entrypoint.py":
                continue
            rv.append(filename.stem.replace("_", "-"))
        rv.sort()
        return rv

    def get_command(self, ctx, cmd_name):
        """Dynamically get a command."""
        try:
            module_name = cmd_name.replace("-", "_")
            module = importlib.import_module(f"blueye.sdk.scripts.{module_name}")
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, click.Command):
                    return obj
        except ImportError:
            return


@click.command(cls=DynamicClickGroup)
def main():
    """
    Blueye SDK CLI
    """
    pass

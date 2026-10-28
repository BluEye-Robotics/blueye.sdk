"""Recreate the quick-start exploration GIF with current IPython completions.

Requires the SDK, IPython, FFmpeg with drawtext, and DejaVu Sans Mono.
Run from the repository root:

    uv run --with ipython python doc_utils/render_ipython_demo.py

The terminal animation uses completion candidates from the installed SDK. It
does not connect to a drone or execute the displayed control command. Pass
--font /path/to/DejaVuSansMono.ttf if fontconfig is unavailable.
"""

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

from IPython.core.interactiveshell import InteractiveShell

from blueye.sdk import Drone

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "docs/media/ipython-exploration.gif"
PREFIX = "d.motion.enable_auto_"
COMMAND = "d.motion.enable_auto_heading(True)"
DURATION = 16


def completion_names():
    shell = InteractiveShell()
    shell.Completer.use_jedi = False
    shell.user_ns["d"] = Drone(auto_connect=False)
    _, matches = shell.Completer.complete(PREFIX)
    names = [match.lstrip(".") for match in matches]
    if "enable_auto_heading" not in names:
        raise RuntimeError("The SDK completion list no longer contains enable_auto_heading")
    _, selected = shell.Completer.complete(PREFIX + "h")
    if selected != [".enable_auto_heading"]:
        raise RuntimeError("The heading prefix no longer has a unique completion")
    return names


def terminal_filters(directory, names):
    filters = []
    text_index = 0

    def text(value, x, y, start, end=DURATION, color="0xc2d2d6"):
        nonlocal text_index
        if not value:
            return
        filename = f"text-{text_index}.txt"
        text_index += 1
        (directory / filename).write_text(value, encoding="utf-8")
        filters.append(
            f"drawtext=fontfile=font.ttf:textfile={filename}:expansion=none:"
            f"fontsize=24:fontcolor={color}:x={x}:y={y}:y_align=font:"
            f"enable='gte(t,{start:.3f})*lt(t,{end:.3f})'"
        )

    def cursor(length, y, start, end):
        filters.append(
            f"drawbox=x={136 + length * 14}:y={y + 5}:w=13:h=25:"
            f"color=0x93a1a1:t=fill:enable='gte(t,{start:.3f})*lt(t,{end:.3f})'"
        )

    def typing(code, y, start, finish, submit, already=0):
        for count in range(already, len(code) + 1):
            at = start + (finish - start) * (count - already) / (len(code) - already)
            until = (
                start + (finish - start) * (count + 1 - already) / (len(code) - already)
                if count < len(code)
                else submit
            )
            text(code[:count], 136, y, at, until)
            cursor(count, y, at, until)

    text("In [1]:", 24, 20, 0, color="0x859900")
    typing("from blueye.sdk import Drone", 20, 0, 2.2, 2.5)
    text("from blueye.sdk import Drone", 136, 20, 2.5)

    text("In [2]:", 24, 68, 2.5, color="0x859900")
    typing("d = Drone()", 68, 2.5, 3.8, 4.2)
    text("d = Drone()", 136, 68, 4.2)

    text("In [3]:", 24, 116, 4.2, color="0x859900")
    typing(PREFIX, 116, 4.2, 6.5, 9.8)
    text("[Tab]", 848, 116, 6.7, 7.5, color="0x268bd2")
    # Show the real completion candidates beneath the active input line.
    menu_height = 16 + len(names) * 34
    filters.append(
        f"drawbox=x=136:y=158:w=364:h={menu_height}:color=0x073642:t=fill:"
        "enable='gte(t,6.7)*lt(t,10.2)'"
    )
    for row, name in enumerate(names):
        text(name, 150, 166 + row * 34, 6.7, 10.2)

    # Narrow the candidates with 'h', then expand the unique match with Tab.
    text(PREFIX + "h", 136, 116, 9.8, 10.2)
    cursor(len(PREFIX) + 1, 116, 9.8, 10.2)
    completed = "d.motion.enable_auto_heading"
    text(completed, 136, 116, 10.2, 10.8)
    cursor(len(completed), 116, 10.2, 10.8)
    text("[Tab]", 848, 116, 10.2, 10.8, color="0x268bd2")
    typing(COMMAND, 116, 10.8, 12.2, 12.6, already=len(completed))
    text(COMMAND, 136, 116, 12.6)
    text("In [4]:", 24, 164, 12.6, color="0x859900")
    cursor(0, 164, 12.6, DURATION)
    return ",\n".join(filters)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--font", type=Path, help="DejaVu Sans Mono TTF file")
    args = parser.parse_args()
    names = completion_names()
    font = args.font or Path(
        subprocess.check_output(["fc-match", "DejaVu Sans Mono", "-f", "%{file}"], text=True)
    )
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blueye-ipython-demo-") as temporary:
        directory = Path(temporary)
        shutil.copyfile(font, directory / "font.ttf")
        graph = (
            f"[0:v]{terminal_filters(directory, names)},split[video][colors];"
            "[colors]palettegen[palette];"
            "[video][palette]paletteuse=dither=none[out]"
        )
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c=0x002b36:s=1000x320:r=10:d={DURATION}",
                "-filter_complex",
                graph,
                "-map",
                "[out]",
                "-loop",
                "0",
                str(directory / "rendered.gif"),
            ],
            cwd=directory,
            check=True,
        )
        shutil.copyfile(directory / "rendered.gif", output)
    print(output)


if __name__ == "__main__":
    main()

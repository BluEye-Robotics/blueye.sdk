"""Rebuild the README demo's terminal track, keeping the original drone footage.

Requires Python 3.10+, FFmpeg with drawtext, ImageMagick 7, and DejaVu Sans Mono.
Run from the repository root:

    python doc_utils/render_sdk_demo.py

The original GIF is downloaded into a temporary directory. To work offline, pass
--source /path/to/original.gif (the generated sdk-demo.gif also works). Use
--font /path/to/DejaVuSansMono.ttf if fontconfig is unavailable.

Edit COMMANDS to update the code. Times are seconds in the original recording;
each next prompt coincides with Enter, keeping lights and motion synchronized.
This renders text only; it never connects to or sends commands to a drone.
"""

import argparse
import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import tokenize
import urllib.request

SOURCE_URL = (
    "https://user-images.githubusercontent.com/8504604/"
    "66751230-d05c7e00-ee8e-11e9-91cb-d46b433aafa5.gif"
)
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "docs/media/sdk-demo.gif"
# (command, prompt appears, typing starts, typing finishes)
# Submit the action commands just before their visible response in the footage:
# lights at about 11.2 s, forward motion at about 16.0 s.
COMMANDS = [
    ("from blueye.sdk import Drone", 0.0, 0.1, 4.2),
    ("d = Drone()", 4.5, 4.8, 7.4),
    ("d.set_lights(1.0)", 7.8, 8.1, 10.9),
    ("d.motion.set_surge(0.3)", 11.1, 11.5, 15.7),
    ("", 15.9, 15.9, 20.0),
]


def terminal_filters(directory):
    # Cover the old terminal, leaving the divider and all footage untouched.
    filters = ["drawbox=x=0:y=0:w=506:h=ih:color=0x002b36:t=fill"]
    text_index = 0

    def text(value, x, y, color, start):
        nonlocal text_index
        filename = f"text-{text_index}.txt"
        text_index += 1
        (directory / filename).write_text(value, encoding="utf-8")
        filters.append(
            f"drawtext=fontfile=font.ttf:textfile={filename}:expansion=none:"
            f"fontsize=20:fontcolor={color}:x={x}:y={y}:y_align=font:"
            f"enable='gte(t,{start:.3f})'"
        )

    for row, (code, prompt_at, start, finish) in enumerate(COMMANDS):
        y = 16 + row * 42
        text(f"In [{row + 1}]:", 0, y, "0x859900", prompt_at)
        colors = ["0xc2d2d6"] * len(code)
        for token in tokenize.generate_tokens(io.StringIO(code).readline):
            color = None
            if token.string in ("from", "import") or token.type == tokenize.NUMBER:
                color = "0x859900"
            elif token.string in ("blueye", "sdk"):
                color = "0x268bd2"
            if color:
                colors[token.start[1] : token.end[1]] = [color] * len(token.string)

        # DejaVu Sans Mono at 20 px has a 12 px advance. Reveal one glyph at a
        # time, on the original frame timestamps, without resampling the video.
        times = [start + (finish - start) * i / max(1, len(code) - 1) for i in range(len(code))]
        for i, (character, color, at) in enumerate(zip(code, colors, times)):
            if character != " ":
                text(character, 96 + i * 12, y, color, at)

        end = COMMANDS[row + 1][1] if row + 1 < len(COMMANDS) else 20.0
        boundaries = [prompt_at, *times, end]
        for i, (at, until) in enumerate(zip(boundaries, boundaries[1:])):
            if at == until:
                continue
            filters.append(
                f"drawbox=x={96 + i * 12}:y={y + 4}:w=11:h=21:"
                f"color=0x93a1a1:t=fill:enable='gte(t,{at:.3f})*lt(t,{until:.3f})'"
            )
    return ",\n".join(filters)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Local copy of the 20-second demo GIF")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--font", type=Path, help="DejaVu Sans Mono TTF file")
    args = parser.parse_args()
    font = args.font
    if font is None:
        font = Path(
            subprocess.check_output(["fc-match", "DejaVu Sans Mono", "-f", "%{file}"], text=True)
        )
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blueye-sdk-demo-") as temporary:
        directory = Path(temporary)
        source = directory / "source.gif"
        if args.source:
            shutil.copyfile(args.source, source)
        else:
            urllib.request.urlretrieve(SOURCE_URL, source)
        shutil.copyfile(font, directory / "font.ttf")
        graph = (
            f"[0:v]{terminal_filters(directory)},split[video][colors];\n"
            "[colors]palettegen=reserve_transparent=1[palette];\n"
            "[video][palette]paletteuse=dither=none:"
            "diff_mode=rectangle[out]"
        )
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(source),
                "-filter_complex",
                graph,
                "-map",
                "[out]",
                "-fps_mode",
                "passthrough",
                "-loop",
                "0",
                "-final_delay",
                "20",
                str(directory / "rendered.gif"),
            ],
            cwd=directory,
            check=True,
        )
        # Reuse nearly identical pixels between frames to keep the README asset
        # small. This is lossy temporal compression; dimensions and timing stay
        # unchanged, and the high-contrast terminal text stays legible.
        subprocess.run(
            [
                "magick",
                str(directory / "rendered.gif"),
                "-coalesce",
                "-fuzz",
                "10%",
                "-layers",
                "Optimize",
                str(directory / "optimized.gif"),
            ],
            check=True,
        )
        shutil.copyfile(directory / "optimized.gif", output)
    print(output)


if __name__ == "__main__":
    main()

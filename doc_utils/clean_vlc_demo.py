"""Remove the gray stream frames from the original VLC walkthrough.

Requires Python 3.10+ and gifsicle. Run from the repository root:

    python doc_utils/clean_vlc_demo.py

Use --source /path/to/original.gif to work offline. The frame ranges refer to
the original 167-frame recording, not the cleaned output.
"""

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request

SOURCE_URL = "https://blueyenostorage.blob.core.windows.net/sdkimages/rtsp-in-vlc.gif"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "docs/media/rtsp-in-vlc.gif"
# Zero-based, inclusive ranges: 10.5 <= t < 11.9 and 13.0 <= t < 14.1 seconds.
GRAY_FRAMES = ["#105-118", "#130-140"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Original, unfiltered VLC GIF")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--gifsicle", default="gifsicle", help="Path to the gifsicle executable")
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blueye-vlc-demo-") as temporary:
        directory = Path(temporary)
        source = directory / "original.gif"
        if args.source:
            shutil.copyfile(args.source, source)
        else:
            urllib.request.urlretrieve(SOURCE_URL, source)
        # Expand before deleting so retained frames do not depend on removed
        # frames for their pixels. Keep the source palettes intact.
        subprocess.run(
            [
                args.gifsicle,
                "--unoptimize",
                str(source),
                "--output",
                str(directory / "expanded.gif"),
            ],
            check=True,
        )
        subprocess.run(
            [
                args.gifsicle,
                str(directory / "expanded.gif"),
                "--delete",
                *GRAY_FRAMES,
                "--optimize=3",
                "--output",
                str(directory / "cleaned.gif"),
            ],
            check=True,
        )
        shutil.copyfile(directory / "cleaned.gif", output)
    print(output)


if __name__ == "__main__":
    main()

"""Include example downloads from this checkout in each documentation build.

Executed by mkdocs-gen-files, which registers the downloads as site assets before
Markdown links are resolved. The assets also go into the wheel's offline docs.
"""

from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import mkdocs_gen_files

examples_dir = Path(__file__).resolve().parents[1] / "examples"
bundle = BytesIO()
with ZipFile(bundle, "w", compression=ZIP_DEFLATED) as archive:
    for source in sorted(examples_dir.rglob("*.py")):
        if "__pycache__" in source.parts:
            continue
        destination = "examples/" + source.relative_to(examples_dir).as_posix()
        content = source.read_bytes()
        with mkdocs_gen_files.open(destination, "wb") as output:
            output.write(content)
        archive.writestr(destination, content)

with mkdocs_gen_files.open("examples.zip", "wb") as output:
    output.write(bundle.getvalue())

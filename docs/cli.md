# The blueye CLI

The SDK ships with a `blueye` command line interface for working with the drone from
the terminal. It is installed together with the SDK:

```shell
pip install blueye.sdk
```

Running `blueye --help` lists the available commands. Two features need the SDK's
`cli` extra:

- `blueye bundle-model` inspects ONNX files and needs the `onnx` package.
- `blueye logs download --mcap` and `blueye logs convert` write `.mcap` files and need
  `mcap-protobuf-support`.

```shell
pip install "blueye.sdk[cli]"
```

(Keep the quotes — most shells treat square brackets specially.) Everything else works
without the extra. When a command needs a package that is missing, it prints the install
command for your platform instead of failing with an import error; `bundle-model` then
exits with code 2, the `.mcap` paths of `logs` with code 1.

## Conventions

**Drone address.** Commands that talk to the drone take `--drone-ip` (default
`192.168.1.101`) and `--timeout` in seconds (default 10 for `logs`, 5 for `models`).
Give them after the action, as in `blueye logs list --drone-ip 192.168.1.102`; without
an action (the interactive session) they follow the command name. `bundle-model` only
contacts the drone with `--push` and takes `--drone-ip` for that.

**Interactive and scripted use.** `blueye logs` and `blueye models` run without an
action open an interactive session when stdin and stdout are a terminal; piped or
redirected, they print the list instead. `bundle-model` prompts for every value a flag
did not supply; `--yes` accepts the inferred defaults and asks nothing. Every prompt
names the flag that answers it.

**Exit codes.**

| Code | Meaning                                                                 |
| ---- | ----------------------------------------------------------------------- |
| 0    | Success                                                                 |
| 1    | A user-facing error: the drone could not be reached, a file is missing, invalid metadata, a declined confirmation |
| 2    | `bundle-model` needs the `cli` extra and it is missing, or the arguments were invalid |
| 130  | Interrupted with Ctrl-C                                                 |

Third-party tools (see [below](#third-party-tools-blueye-tools)) propagate their own
exit code.

## Bundling CV models — `blueye bundle-model`

The Blueye X3 Ultra can run your own computer vision models: object
detection, instance segmentation, and single-object tracking. The drone's vision
pipeline consumes **model packages** — a zip containing an ONNX model and a
`model_meta.json` file that describes how to preprocess frames and decode the model's
outputs.

The `blueye bundle-model` command turns an exported ONNX file into such a package. It

- validates that the model is of a supported type,
- auto-generates `model_meta.json` from the ONNX graph and any embedded metadata
  (Ultralytics exports carry their class names and input size along),
- interactively asks about anything that cannot be inferred, and
- writes a deployable zip.

### Interactive use

Point the command at your ONNX file and answer the prompts:

```shell
blueye bundle-model path/to/model.onnx
```

The CLI inspects the model, shows what it inferred (output format, class count, input
size, labels), and walks through the remaining choices with interactive prompts — model
name, tracking algorithm, and the runtime configuration for the drone:

- **Execution device** — the CLI analyzes the network and recommends the Jetson DLA
  cores (`tensorrt-dla0`/`tensorrt-dla1`) for convolution-style models, which frees the
  GPU for other work. Models with layers the DLA cannot run (NMS-in-graph,
  transformers) get `tensorrt` recommended instead. You can always pick any device.
- **Inference rate** — maximum rate in Hz, defaulting to unlimited.
- **Autolaunch** — whether the drone should start this model automatically. Defaults
  to enabled; pass `--no-runtime-enabled` to bundle the package disabled.
- **Package metadata** — a version string (default `1.0.0`) plus optional description,
  author, and license. These are informational fields carried inside
  `model_meta.json` so the package stays self-describing wherever it travels
  (drone web UI, Blueye App, Blueye Cloud). Use an [SPDX identifier](https://spdx.org/licenses/)
  for the license when you can (`MIT`, `Apache-2.0`, `AGPL-3.0`, `Proprietary`).

The result is a zip with `model.onnx` and `model_meta.json` at its root.

### Scripted use

Every prompt can be answered with a flag, and `--yes` accepts all inferred defaults:

```shell
blueye bundle-model yolov8n.onnx --yes \
    --name "YOLOv8n (COCO)" \
    --model-version 1.0.0 --author "Ultralytics" --license AGPL-3.0 \
    --description "YOLOv8n nano object detector trained on COCO (80 classes)" \
    --tracking byte_track \
    --runtime-device tensorrt-dla0 --runtime-hz 10 --runtime-enabled \
    --output yolov8n_package.zip
```

Use `--dry-run` to print the generated `model_meta.json` without writing anything, and
`--labels labels.txt` (one class name per line) when the model does not embed its class
names.

### Options

Package and output:

| Option                          | Meaning                                                                   |
| ------------------------------- | ------------------------------------------------------------------------- |
| `onnx_path`                     | The ONNX file. Prompted for when omitted.                                 |
| `--name NAME`                   | Human-readable model name. Default: the name embedded in the model, else the file stem. |
| `--model-version VERSION`       | Version string written to the metadata. Default `1.0.0`.                  |
| `--description`, `--author`, `--license` | Informational package fields. Passing any of them skips the "add package details?" prompt. |
| `-o`, `--output PATH`           | Output zip. Default `<name>_package.zip` in the current directory.         |
| `--force`                       | Overwrite an existing zip. Without it, interactive runs ask and scripted runs fail. |
| `--dry-run`                     | Print the generated `model_meta.json` and stop; nothing is written.       |
| `--push`                        | Upload the zip to the drone after writing it.                             |
| `--drone-ip IP`                 | Drone address used by `--push`. Default `192.168.1.101`.                  |
| `-y`, `--yes`                   | Accept every inferred default; never prompt.                              |
| `--strict`                      | Treat `onnx.checker` failures as fatal instead of asking whether to continue. |
| `--quiet`                       | Print only errors and the result path.                                    |

Model structure (all inferred from the ONNX graph when possible):

| Option                      | Meaning                                                                       |
| --------------------------- | ----------------------------------------------------------------------------- |
| `--format FORMAT`           | Decoder format; one of the values in the table below. Prompted for when inference is uncertain. |
| `--labels FILE`             | Class names, one per line. Default: the labels embedded in the model.         |
| `--num-classes N`           | Number of classes. Default: inferred from the output shape or the label count. |
| `--input-size WxH`          | Model input size, e.g. `640x640`. Needed when the model has dynamic dimensions. |
| `--anchors "W,H W,H ..."`   | Anchor pairs in grid-cell units, `yolov2_grid` only.                          |
| `--grid-size N`             | Feature-map grid size, `yolov2_grid` only. Default: inferred, else prompted (13). |
| `--one-indexed-classes`     | Class IDs start at 1 (TensorFlow SSD exports), `ssd_multi` only.              |
| `--template-size PX`, `--search-size PX` | Template and search crop sizes for single-object trackers. Defaults 128/256 (`ostrack`), 112/224 (`mixformerv2`). |

Preprocessing and decoding:

| Option                          | Meaning                                                                   |
| ------------------------------- | ------------------------------------------------------------------------- |
| `--color-order {rgb,bgr}`       | Channel order the model expects. Default `rgb`.                           |
| `--normalize-scale FLOAT`       | Pixel scale. Default `1/255` for most formats, `1.0` for `yolov2_grid` and `ssd_multi`. |
| `--normalize-mean R,G,B`, `--normalize-std R,G,B` | Per-channel normalization. Default: ImageNet values for `detr`, `ostrack` and `mixformerv2`, none otherwise. |
| `--confidence-threshold FLOAT`  | Detection confidence threshold, detection packages only. Default `0.3`. Trackers keep their package default (`0.5`). |
| `--nms-threshold FLOAT`         | NMS IoU threshold. Default `0.45`.                                        |
| `--tracking {none,iou,byte_track}` | Multi-object tracking algorithm for detection packages. Default `none`. |

Runtime configuration on the drone:

| Option                          | Meaning                                                                   |
| ------------------------------- | ------------------------------------------------------------------------- |
| `--runtime-device DEVICE`       | `cuda`, `tensorrt`, `tensorrt-dla0` or `tensorrt-dla1` on the drone. `cpu` and `coreml` are accepted for local desktop testing of the package. |
| `--runtime-hz HZ`               | Maximum inference rate in Hz, or `max` for unlimited (the default).        |
| `--runtime-enabled`, `--no-runtime-enabled` | Autolaunch the model on the drone. Default enabled.            |

### Supported model types

| Output format  | Model family                                    |
| -------------- | ----------------------------------------------- |
| `yolov2_grid`  | YOLOv2 / TinyYOLOv2 (grid + anchors)            |
| `yolov5_flat`  | YOLOv5 ONNX export                              |
| `yolov8_flat`  | YOLOv8 / YOLO11 ONNX export                     |
| `yolov8_seg`   | YOLOv8/v11 segmentation                         |
| `yolo_e2e`     | End-to-end YOLO with NMS in the model (YOLO26)  |
| `yolo_e2e_seg` | End-to-end YOLO segmentation                    |
| `ssd_multi`    | SSD (multi-output, e.g. TensorFlow exports)     |
| `detr`         | DETR transformer detectors                      |
| `ostrack`      | OSTrack single-object tracker                   |
| `mixformerv2`  | MixFormerV2 single-object tracker               |

The model must take float32 image input; models with a clearly unsupported structure
(image classifiers, float16 inputs, non-image inputs) are rejected with an explanation.

### Deploying to the drone

The easiest way is to push the package directly: interactive runs offer it after the
zip is written, and scripts pass `--push` (with `--drone-ip` if the drone is not at
the default `192.168.1.101`):

```shell
blueye bundle-model yolov8n.onnx --yes --push
```

If the drone cannot be reached, the command fails with a clear message — the zip is
still written and can be pushed later with `blueye models upload`.

The same operations are available programmatically through the SDK:

```python
import blueye.sdk

drone = blueye.sdk.Drone(auto_connect=False)  # HTTP only, takes no control
model = drone.cv_models.upload("yolov8n_package.zip")
drone.cv_models.set_enabled(model.directory, True)
```

Without the SDK installed, the drone's HTTP endpoint accepts the package zip as a
multipart upload (field name `file`):

```shell
curl -F "file=@yolov8n_package.zip" http://192.168.1.101/api/cv-models/upload
```

or use the Blunux Web App — open `http://192.168.1.101` in a browser and upload the
zip from the Computer Vision tab.

## Managing models on the drone — `blueye models`

Installed models are managed with the `blueye models` command, or interactively by
running it without an action on a terminal:

```shell
blueye models list
blueye models upload yolov8n_package.zip
blueye models enable yolov8n-coco
blueye models set-device yolov8n-coco tensorrt-dla0
blueye models set-hz yolov8n-coco 10
blueye models warmup yolov8n-coco      # pre-build the TensorRT engine
blueye models download yolov8n-coco -o ~/packages
blueye models delete yolov8n-coco --force
```

Model names are the directory slugs shown by `blueye models list`. The `enabled` state
is the autolaunch configuration; the API does not expose a live "running" status.

| Action                         | Meaning                                                                      |
| ------------------------------ | ---------------------------------------------------------------------------- |
| `list`                         | Table of installed models: name, directory, type, format, size, enabled, device, rate. |
| `enable NAME`, `disable NAME`  | Turn autolaunch on or off.                                                   |
| `set-device NAME DEVICE`       | Execution provider: `cuda`, `tensorrt`, `tensorrt-dla0` or `tensorrt-dla1`.   |
| `set-hz NAME HZ`               | Maximum inference rate; one of `0`, `5`, `10`, `15`. `0` means unlimited, the same setting `bundle-model --runtime-hz max` writes into a package. |
| `warmup NAME`                  | Build the inference engine now so the first launch is instant. TensorRT builds take minutes; the command waits. |
| `delete NAME [--force]`        | Remove the package. Asks for confirmation on a terminal; `--force` skips the question and is required when not interactive. |
| `upload PACKAGE`               | Upload a package zip, as `bundle-model --push` does.                          |
| `download NAME [-o PATH]`      | Save a package zip from the drone to a file or directory (default: current directory). |
| `rescan`                       | Ask the drone's vision pipeline to re-read the package directory.            |

## Downloading dive logs — `blueye logs`

The drone's binary dive logs (`.bez`) can be listed and downloaded from the terminal.
The command connects to the drone as an observer — taking no control:

```shell
blueye logs list                       # table of logs on the drone
blueye logs download --latest 1        # newest log to the current directory
blueye logs download --latest 1 --mcap # ...and convert it for Foxglove
blueye logs download BYEDP000000_ea9ac92e1817a1d4_00002 -o ~/dives
blueye logs download --all --since 2026-06-01 --dives-only
blueye logs convert mydive.bez         # convert an already-downloaded log (no drone)
blueye logs                            # interactive: pick logs to download
```

| Action                         | Meaning                                                                      |
| ------------------------------ | ---------------------------------------------------------------------------- |
| `list`                         | Table of the logs on the drone: name, start time, max depth, size, dive flag. |
| `download [NAMES...]`          | Download logs by name, or the `--latest N` newest, or `--all`. Exactly one of the three. `-o`/`--output DIR` sets the destination (default: current directory); `--mcap` also converts each log. |
| `convert FILES...`             | Convert `.bez` files already on disk to `.mcap`. `-o`/`--output DIR` sets the destination (default: next to each input). Needs no drone. |

`list`, `download`, and the interactive view accept `--dives-only`, `--since
YYYY-MM-DD`, and `--until YYYY-MM-DD` to narrow the selection; the interactive view
is a single scrollable table (type to filter, space to select, sorted newest first).
`--mcap` converts each downloaded log to a Foxglove-ready `.mcap` next to the
`.bez` — `blueye logs convert` does the same for files already on disk. Both need the
`cli` extra. See
[visualizing dive logs with Foxglove](logs/foxglove-bez-to-mcap.md).
For working with logs from Python (streaming, filtering, plotting), see
[logs from the drone](logs/listing-and-downloading.md).

## Third-party tools — `blueye tools`

The `blueye` command is built to grow: besides the built-in commands, anyone can drop
single-file Python tools into a per-user directory. The CLI discovers them
automatically, lists them in `blueye --help`, and runs them as
`blueye <tool-name> ...` — no SDK changes needed.

### Writing a tool

A tool is a normal Python script carrying [PEP 723](https://peps.python.org/pep-0723/)
inline metadata, extended with a `[tool.blueye]` table. It can import `blueye.sdk`
like any other script:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas"]
#
# [tool.blueye]
# name = "export-logs"
# description = "Export the dive log index to CSV"
# min-sdk-version = "2.7.0"
# ///
import sys

import pandas as pd

from blueye.sdk import Drone


def main() -> int:
    drone = Drone(connect_as_observer=True)
    rows = [
        {"name": log.name, "start": log.start_time, "max_depth": log.max_depth_magnitude}
        for log in drone.logs
    ]
    pd.DataFrame(rows).to_csv(sys.stdout, index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

The `[tool.blueye]` keys:

| Key               | Required | Meaning                                                        |
| ----------------- | -------- | -------------------------------------------------------------- |
| `name`            | yes      | The subcommand name (`blueye export-logs`). Lowercase letters, digits, and hyphens; must start with a letter; at most 32 characters. |
| `description`     | yes      | One line shown in `blueye --help` and `blueye tools list`.     |
| `min-sdk-version` | no       | Minimum blueye.sdk version; a mismatch prints a warning but never blocks. |

Arguments after the tool name are passed to the script verbatim, and its exit code
becomes the CLI's exit code. Invocation is strictly `blueye <tool-name> args...`.

**Dependencies.** A tool always runs on the same Python interpreter as the `blueye`
command, so `blueye.sdk` and everything installed next to it are importable without
being listed. Packages the tool needs beyond that go in the PEP 723 `dependencies`
list. When [uv](https://docs.astral.sh/uv/) is installed, the CLI runs the tool as
`uv run --with-requirements <script> python <script>`: uv puts the listed packages in
a cached environment layered on top of the CLI's own, without installing anything into
it. The first run of a tool downloads its packages, so do that before heading out on the
drone's Wi-Fi; later runs come from uv's cache. A package the CLI's environment already
satisfies is never downloaded. Without uv, the listed packages must already be
installed next to the SDK (`pip install pandas` into the same environment). The tool's
`requires-python` is not enforced; the interpreter is the CLI's. uv's own
`[tool.uv.sources]` table in the script is not applied either; dependencies come from
the package index.

### Installing and managing tools

```shell
blueye tools validate my_script.py   # check the metadata before installing
blueye tools install my_script.py    # copy it into the tools directory
blueye tools install my_script.py --force   # replace an installed tool of the same name
blueye tools list                    # built-ins + installed tools
blueye tools uninstall export-logs
blueye tools dir                     # print the resolved tools directory
```

Discovery scans the tools directory on every invocation and parses **only the
metadata block — tool code is never executed during discovery** or listing.

The directory is resolved from the `BLUEYE_CLI_TOOLS_DIR` environment variable when
set, otherwise from the platform default:

| Platform | Default tools directory                              |
| -------- | ---------------------------------------------------- |
| macOS    | `~/Library/Application Support/blueye/cli-tools`     |
| Linux    | `$XDG_DATA_HOME/blueye/cli-tools` (or `~/.local/share/blueye/cli-tools`) |
| Windows  | `%APPDATA%\blueye\cli-tools`                         |

Name collisions always resolve in favor of built-in commands; `blueye tools list`
shows shadowed or invalid tools with the reason.

SDK contributors adding a **built-in** command should follow the recipe and
invariants documented in the `blueye.sdk.cli.commands` module docstring.

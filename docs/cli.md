# The blueye CLI

The SDK ships with a `blueye` command line interface for working with the drone from
the terminal. It is installed together with the SDK:

```shell
pip install blueye.sdk
```

Running `blueye --help` lists the available commands. One command needs an extra:
`blueye bundle-model` inspects ONNX files and requires the heavyweight `onnx` package,
installed with the SDK's `cli` extra:

```shell
pip install "blueye.sdk[cli]"
```

(Keep the quotes — most shells treat square brackets specially.) If the extra is
missing, `bundle-model` detects it and prints the install command for your platform
instead of failing.

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

The result is a zip with `model.onnx` and `model_meta.json` at its root.

### Scripted use

Every prompt can be answered with a flag, and `--yes` accepts all inferred defaults:

```shell
blueye bundle-model yolov8n.onnx --yes \
    --name "YOLOv8n (COCO)" \
    --tracking byte_track \
    --runtime-device tensorrt-dla0 --runtime-hz 10 --runtime-enabled \
    --output yolov8n_package.zip
```

Use `--dry-run` to print the generated `model_meta.json` without writing anything, and
`--labels labels.txt` (one class name per line) when the model does not embed its class
names.

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
still written and can be pushed later.

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
running it without arguments on a terminal:

```shell
blueye models list
blueye models enable yolov8n-coco
blueye models set-device yolov8n-coco tensorrt-dla0
blueye models warmup yolov8n-coco      # pre-build the TensorRT engine
blueye models delete yolov8n-coco
```

Model names are the directory slugs shown by `blueye models list`. Note: the
`enabled` state is the autolaunch configuration; the API does not expose a live
"running" status.

## Downloading dive logs — `blueye logs`

The drone's binary dive logs (`.bez`) can be listed and downloaded from the terminal.
The command connects to the drone as an observer — taking no control:

```shell
blueye logs list                       # table of logs on the drone
blueye logs download --latest 1        # newest log to the current directory
blueye logs download --latest 1 --mcap # ...and convert it for Foxglove
blueye logs download BYEDP000000_ea9ac92e1817a1d4_00002 -o ~/dives
blueye logs convert mydive.bez         # convert an already-downloaded log (no drone)
blueye logs                            # interactive: pick logs to download
```

`list`, `download`, and the interactive view accept `--dives-only`, `--since
YYYY-MM-DD`, and `--until YYYY-MM-DD` to narrow the selection; the interactive view
is a single scrollable table (type to filter, space to select, sorted newest first).
`--mcap` converts each downloaded log to a Foxglove-ready `.mcap` next to the
`.bez` — `blueye logs convert` does the same for files already on disk. See
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
inline metadata, extended with a `[tool.blueye]` table:

```python
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

import pandas as pd


def main() -> int:
    print(f"exporting with args: {sys.argv[1:]}")
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

**Dependencies**: when the script declares PEP 723 `dependencies` and
[uv](https://docs.astral.sh/uv/) is installed, the CLI runs it with `uv run`, giving
the script an isolated environment with those dependencies — your tool can use pandas
without pandas ever being installed next to the SDK. Without uv, the script runs with
the current interpreter and must find its dependencies there.

### Installing and managing tools

```shell
blueye tools validate my_script.py   # check the metadata before installing
blueye tools install my_script.py    # copy it into the tools directory
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

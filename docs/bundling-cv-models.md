# Bundling CV models

Blueye drones with an onboard GPU can run your own computer vision models: object
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

## Installation

The CLI needs a few extra packages, installed with the SDK's `cli` extra:

```shell
pip install "blueye.sdk[cli]"
```

or with [uv](https://docs.astral.sh/uv/):

```shell
uv pip install "blueye.sdk[cli]"
```

(Keep the quotes — most shells treat square brackets specially.) If the extra is
missing, `blueye bundle-model` will detect it and print the install command for your
platform instead of failing.

## Interactive use

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

## Scripted use

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

## Supported model types

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

## Deploying to the drone

The easiest way is to push the package directly: interactive runs offer it after the
zip is written, and scripts pass `--push` (with `--drone-ip` if the drone is not at
the default `192.168.1.101`):

```shell
blueye bundle-model yolov8n.onnx --yes --push
```

If the drone cannot be reached, the command fails with a clear message — the zip is
still written and can be pushed later.

Installed models are managed with the `blueye models` command (or interactively by
running it without arguments on a terminal):

```shell
blueye models list
blueye models enable yolov8n-coco
blueye models set-device yolov8n-coco tensorrt-dla0
blueye models warmup yolov8n-coco      # pre-build the TensorRT engine
```

The same operations are available programmatically through the SDK:

```python
import blueye.sdk

drone = blueye.sdk.Drone(auto_connect=False)  # HTTP only, takes no control
model = drone.cv_models.upload("yolov8n_package.zip")
drone.cv_models.set_enabled(model.directory, True)
```

Note: the `enabled` state is the autolaunch configuration; the API does not expose a
live "running" status.

Manual alternative: use the Blunux Web App — open `http://192.168.1.101` in a
browser and upload the zip from the Computer Vision tab.

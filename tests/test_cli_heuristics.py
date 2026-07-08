from pathlib import Path

import pytest

from blueye.sdk.cli.heuristics import (
    UnsupportedModelError,
    assess_dla_fitness,
    infer,
    parse_ultralytics_metadata,
)
from blueye.sdk.cli.introspect import FLOAT16, FLOAT32, ModelInfo, TensorSpec


def make_info(inputs, outputs, metadata=None, op_histogram=None):
    return ModelInfo(
        path=Path("model.onnx"),
        inputs=tuple(inputs),
        outputs=tuple(outputs),
        metadata=metadata or {},
        op_histogram=op_histogram or {"Conv": 10},
    )


def image_input(name="images", height=640, width=640, channels=3, dtype=FLOAT32):
    return TensorSpec(name=name, dtype=dtype, dims=(1, channels, height, width))


def output(name, *dims):
    return TensorSpec(name=name, dtype=FLOAT32, dims=tuple(dims))


class TestDetectionFormats:
    def test_yolov8_flat(self):
        config = infer(make_info([image_input()], [output("output0", 1, 84, 8400)]))
        assert config.output_format == "yolov8_flat"
        assert config.kind == "detection"
        assert config.confidence == "high"
        assert config.num_classes == 80
        assert config.input_width == 640
        assert config.input_height == 640

    def test_yolov5_flat(self):
        config = infer(make_info([image_input()], [output("output", 1, 25200, 85)]))
        assert config.output_format == "yolov5_flat"
        assert config.num_classes == 80

    def test_yolo_e2e(self):
        config = infer(make_info([image_input()], [output("output0", 1, 300, 6)]))
        assert config.output_format == "yolo_e2e"
        assert config.confidence == "high"

    def test_yolov8_seg(self):
        config = infer(
            make_info(
                [image_input()],
                [output("output0", 1, 116, 8400), output("output1", 1, 32, 160, 160)],
            )
        )
        assert config.output_format == "yolov8_seg"
        assert config.num_classes == 80

    def test_yolo_e2e_seg(self):
        config = infer(
            make_info(
                [image_input()],
                [output("output0", 1, 300, 38), output("output1", 1, 32, 160, 160)],
            )
        )
        assert config.output_format == "yolo_e2e_seg"

    def test_detr(self):
        config = infer(
            make_info(
                [image_input(height=800, width=800)],
                [output("logits", 1, 100, 92), output("boxes", 1, 100, 4)],
            )
        )
        assert config.output_format == "detr"
        assert config.num_classes == 91  # 92 logits including the no-object class.

    def test_ssd_multi(self):
        config = infer(
            make_info(
                [image_input()],
                [
                    output("boxes", 1, 100, 4),
                    output("classes", 1, 100),
                    output("scores", 1, 100),
                    output("count", 1),
                ],
            )
        )
        assert config.output_format == "ssd_multi"
        assert config.confidence == "low"

    def test_yolov2_grid(self):
        # TinyYOLOv2's real output shape: 5 anchors * (5 + 20 classes) = 125.
        config = infer(
            make_info([image_input(height=416, width=416)], [output("grid", 1, 125, 13, 13)])
        )
        assert config.output_format == "yolov2_grid"
        assert config.grid_size == 13
        assert config.confidence == "low"  # anchors are never inferable

    def test_ambiguous_is_unknown(self):
        config = infer(make_info([image_input()], [output("weird", 1, 2, 3, 4, 5)]))
        assert config.kind == "unknown"
        assert config.output_format is None


class TestSotFormats:
    def test_two_inputs_is_ostrack(self):
        config = infer(
            make_info(
                [
                    image_input("template", 128, 128),
                    image_input("search", 256, 256),
                ],
                [
                    output("score_map", 1, 1, 16, 16),
                    output("size_map", 1, 2, 16, 16),
                    output("offset_map", 1, 2, 16, 16),
                ],
            )
        )
        assert config.kind == "sot"
        assert config.output_format == "ostrack"
        assert config.template_size == 128
        assert config.search_size == 256
        assert config.labels == ["tracked"]

    def test_three_inputs_is_mixformerv2(self):
        config = infer(
            make_info(
                [
                    image_input("template", 112, 112),
                    image_input("online_template", 112, 112),
                    image_input("search", 224, 224),
                ],
                [output("boxes", 1, 4), output("scores", 1, 1)],
            )
        )
        assert config.output_format == "mixformerv2"
        assert config.template_size == 112
        assert config.search_size == 224


class TestUnsupportedModels:
    def test_classifier_2d_rejected(self):
        with pytest.raises(UnsupportedModelError, match="classifier"):
            infer(make_info([image_input(height=224, width=224)], [output("probs", 1, 1000)]))

    def test_classifier_4d_squeezed_rejected(self):
        with pytest.raises(UnsupportedModelError, match="classifier"):
            infer(make_info([image_input(height=224, width=224)], [output("probs", 1, 1000, 1, 1)]))

    def test_no_image_input_rejected(self):
        nlp_input = TensorSpec(name="input_ids", dtype=7, dims=(1, 128))
        with pytest.raises(UnsupportedModelError, match="no image-like input"):
            infer(make_info([nlp_input], [output("logits", 1, 128, 768)]))

    def test_fp16_input_rejected(self):
        with pytest.raises(UnsupportedModelError, match="float16"):
            infer(make_info([image_input(dtype=FLOAT16)], [output("output0", 1, 84, 8400)]))

    def test_too_many_image_inputs_rejected(self):
        inputs = [image_input(f"in{i}", 128, 128) for i in range(4)]
        with pytest.raises(UnsupportedModelError, match="4 image inputs"):
            infer(make_info(inputs, [output("out", 1, 4)]))


class TestMetadata:
    def test_names_dict_parsed(self):
        parsed = parse_ultralytics_metadata({"names": "{0: 'person', 1: 'bicycle'}"})
        assert parsed["labels"] == ["person", "bicycle"]

    def test_imgsz_parsed(self):
        parsed = parse_ultralytics_metadata({"imgsz": "[640, 480]"})
        assert parsed["imgsz"] == (640, 480)

    def test_garbage_metadata_ignored(self):
        parsed = parse_ultralytics_metadata({"names": "not a dict {", "imgsz": "nope"})
        assert "labels" not in parsed
        assert "imgsz" not in parsed

    def test_labels_flow_into_config(self):
        names = "{" + ", ".join(f"{i}: 'class{i}'" for i in range(80)) + "}"
        config = infer(
            make_info([image_input()], [output("output0", 1, 84, 8400)], metadata={"names": names})
        )
        assert config.labels is not None
        assert len(config.labels) == 80

    def test_label_count_mismatch_warns(self):
        config = infer(
            make_info(
                [image_input()],
                [output("output0", 1, 84, 8400)],
                metadata={"names": "{0: 'only-one'}"},
            )
        )
        assert any("warning" in note for note in config.notes)


class TestDynamicDims:
    def test_dynamic_batch_accepted(self):
        spec = TensorSpec(name="images", dtype=FLOAT32, dims=("batch", 3, 640, 640))
        config = infer(make_info([spec], [output("output0", 1, 84, 8400)]))
        assert config.output_format == "yolov8_flat"

    def test_dynamic_hw_leaves_size_unset(self):
        spec = TensorSpec(name="images", dtype=FLOAT32, dims=(1, 3, "height", "width"))
        config = infer(make_info([spec], [output("output0", 1, 84, 8400)]))
        assert config.input_width is None
        assert config.input_height is None

    def test_imgsz_metadata_fills_dynamic_size(self):
        spec = TensorSpec(name="images", dtype=FLOAT32, dims=(1, 3, "height", "width"))
        config = infer(
            make_info([spec], [output("output0", 1, 84, 8400)], metadata={"imgsz": "[640, 640]"})
        )
        assert config.input_height == 640
        assert config.input_width == 640


class TestDlaFitness:
    def test_conv_heavy_model_is_good_fit(self):
        info = make_info(
            [image_input()],
            [output("output0", 1, 84, 8400)],
            op_histogram={"Conv": 60, "Relu": 58, "MaxPool": 4, "Concat": 10, "Add": 8},
        )
        assessment = assess_dla_fitness(info)
        assert assessment.good_fit
        assert "convolution" in assessment.reason

    def test_nms_in_graph_is_poor_fit(self):
        info = make_info(
            [image_input()],
            [output("output0", 1, 300, 6)],
            op_histogram={"Conv": 60, "NonMaxSuppression": 1, "TopK": 1},
        )
        assessment = assess_dla_fitness(info)
        assert not assessment.good_fit
        assert "NonMaxSuppression" in assessment.reason

    def test_transformer_is_poor_fit(self):
        info = make_info(
            [image_input()],
            [output("logits", 1, 100, 92), output("boxes", 1, 100, 4)],
            op_histogram={"MatMul": 120, "Softmax": 24, "Conv": 4},
        )
        assessment = assess_dla_fitness(info)
        assert not assessment.good_fit
        assert "transformer" in assessment.reason

    def test_no_conv_is_poor_fit(self):
        info = make_info(
            [image_input()], [output("out", 1, 300, 6)], op_histogram={"Gemm": 3, "Relu": 2}
        )
        assessment = assess_dla_fitness(info)
        assert not assessment.good_fit

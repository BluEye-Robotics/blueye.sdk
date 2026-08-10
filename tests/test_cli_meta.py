from blueye.sdk.cli.commands.bundle_model.meta import (
    IMAGENET_MEAN,
    IMAGENET_STD,
    SCALE_1_OVER_255,
    MetaOptions,
    build_meta,
    default_preprocessing,
    validate_meta,
)


def detection_options(**overrides) -> MetaOptions:
    options = MetaOptions(
        name="Test model",
        output_format="yolov8_flat",
        kind="detection",
        num_classes=2,
        labels=["cat", "dog"],
        input_width=640,
        input_height=640,
    )
    for key, value in overrides.items():
        setattr(options, key, value)
    return options


class TestBuildMeta:
    def test_yolov8_flat_matches_reference_package_shape(self):
        meta = build_meta(detection_options(num_classes=80, labels=[f"c{i}" for i in range(80)]))
        assert meta["format_version"] == 1
        assert meta["model_file"] == "model.onnx"
        assert meta["preprocessing"] == {
            "color_order": "rgb",
            "normalize_scale": SCALE_1_OVER_255,
        }
        assert meta["detection"] == {
            "output_format": "yolov8_flat",
            "num_classes": 80,
            "input_width": 640,
            "input_height": 640,
            "confidence_threshold": 0.3,
            "nms_threshold": 0.45,
        }
        assert "tracking" not in meta
        assert "runtime" not in meta
        assert len(meta["labels"]) == 80

    def test_yolov2_grid_includes_anchors_and_grid(self):
        meta = build_meta(
            detection_options(
                output_format="yolov2_grid",
                anchors=[[1.08, 1.19], [3.42, 4.41]],
                grid_size=13,
            )
        )
        assert meta["detection"]["anchors"] == [[1.08, 1.19], [3.42, 4.41]]
        assert meta["detection"]["grid_size"] == 13

    def test_byte_track_block_gets_spec_defaults(self):
        meta = build_meta(detection_options(tracking_algorithm="byte_track"))
        assert meta["tracking"] == {
            "algorithm": "byte_track",
            "max_age": 50,
            "min_hits": 1,
            "iou_threshold": 0.2,
            "high_threshold": 0.5,
            "low_threshold": 0.1,
        }

    def test_runtime_block(self):
        meta = build_meta(
            detection_options(runtime_device="tensorrt-dla0", runtime_hz=10.0, runtime_enabled=True)
        )
        assert meta["runtime"] == {"enabled": True, "device": "tensorrt-dla0", "hz": 10.0}

    def test_runtime_hz_omitted_for_unlimited(self):
        meta = build_meta(detection_options(runtime_device="tensorrt", runtime_hz=None))
        assert "hz" not in meta["runtime"]

    def test_sot_gets_per_format_defaults(self):
        options = MetaOptions(
            name="OSTrack",
            output_format="ostrack",
            kind="sot",
            template_size=128,
            search_size=256,
        )
        meta = build_meta(options)
        assert meta["sot"]["output_format"] == "ostrack"
        assert meta["sot"]["hann_window"] is True
        assert meta["sot"]["search_crop_factor"] == 4.0
        assert meta["labels"] == ["tracked"]
        assert "detection" not in meta

        options.output_format = "mixformerv2"
        meta = build_meta(options)
        assert meta["sot"]["hann_window"] is False
        assert meta["sot"]["search_crop_factor"] == 4.5
        assert meta["sot"]["template_update_interval"] == 15

    def test_one_indexed_classes_only_when_set(self):
        assert "one_indexed_classes" not in build_meta(detection_options())["detection"]
        meta = build_meta(detection_options(output_format="ssd_multi", one_indexed_classes=True))
        assert meta["detection"]["one_indexed_classes"] is True

    def test_informational_fields_emitted_after_name(self):
        meta = build_meta(
            detection_options(
                version="1.2.0",
                description="Test detector",
                author="Blueye Robotics",
                license="MIT",
            )
        )
        assert meta["version"] == "1.2.0"
        assert meta["description"] == "Test detector"
        assert meta["author"] == "Blueye Robotics"
        assert meta["license"] == "MIT"
        keys = list(meta)
        assert keys.index("name") < keys.index("version")
        assert keys.index("license") < keys.index("preprocessing")

    def test_informational_fields_omitted_when_empty(self):
        meta = build_meta(detection_options())
        for key in ("version", "description", "author", "license"):
            assert key not in meta


class TestDefaultPreprocessing:
    def test_raw_pixel_formats(self):
        assert default_preprocessing("yolov2_grid") == (1.0, [], [])
        assert default_preprocessing("ssd_multi") == (1.0, [], [])

    def test_imagenet_formats(self):
        for output_format in ("detr", "ostrack", "mixformerv2"):
            scale, mean, std = default_preprocessing(output_format)
            assert scale == SCALE_1_OVER_255
            assert mean == IMAGENET_MEAN
            assert std == IMAGENET_STD

    def test_default_scale_only(self):
        assert default_preprocessing("yolov8_flat") == (SCALE_1_OVER_255, [], [])


class TestValidateMeta:
    def test_valid_detection_meta_passes(self):
        assert validate_meta(build_meta(detection_options())) == []

    def test_valid_sot_meta_passes(self):
        options = MetaOptions(
            name="t", output_format="ostrack", kind="sot", template_size=128, search_size=256
        )
        assert validate_meta(build_meta(options)) == []

    def test_bad_format_version(self):
        meta = build_meta(detection_options())
        meta["format_version"] = 2
        assert any("format_version" in error for error in validate_meta(meta))

    def test_empty_model_file(self):
        meta = build_meta(detection_options())
        meta["model_file"] = ""
        assert any("model_file" in error for error in validate_meta(meta))

    def test_neither_detection_nor_sot(self):
        meta = build_meta(detection_options())
        del meta["detection"]
        assert any("detection" in error and "sot" in error for error in validate_meta(meta))

    def test_label_count_mismatch(self):
        meta = build_meta(detection_options())
        meta["labels"] = ["only-one"]
        assert any("labels" in error for error in validate_meta(meta))

    def test_yolov2_grid_requires_anchors(self):
        meta = build_meta(detection_options(output_format="yolov2_grid", grid_size=13))
        assert any("anchors" in error for error in validate_meta(meta))

    def test_input_size_required_formats(self):
        options = detection_options(input_width=None, input_height=None)
        meta = build_meta(options)
        assert any("input_width" in error for error in validate_meta(meta))

    def test_sot_sizes_must_be_positive(self):
        options = MetaOptions(
            name="t", output_format="ostrack", kind="sot", template_size=0, search_size=256
        )
        meta = build_meta(options)
        assert any("template_size" in error for error in validate_meta(meta))

    def test_valid_informational_fields_pass(self):
        meta = build_meta(
            detection_options(version="1.0.0", description="d", author="a", license="MIT")
        )
        assert validate_meta(meta) == []

    def test_non_string_informational_field_rejected(self):
        meta = build_meta(detection_options())
        meta["license"] = 42
        assert "license must be a string" in validate_meta(meta)


class TestDetectionLabelsNotDefaulted:
    def test_detection_without_labels_fails_validation(self):
        # A detection model must never silently receive the SOT ["tracked"] default:
        # for a 1-class model that would VALIDATE with a nonsense label.
        options = detection_options(num_classes=1, labels=[])
        meta = build_meta(options)
        assert meta["labels"] == []
        assert any("labels" in error for error in validate_meta(meta))

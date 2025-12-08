#!/usr/bin/env python3
import time
import json
import requests
from mcap.writer import Writer
from mcap.records import Channel

BASE_URL="http://192.168.1.99"
URL_spectrum = BASE_URL + "/api/spectrum"
URL_graph = BASE_URL + "/api/graph"
FREQUENCY = 10.0  # Hz
PERIOD = 1.0 / FREQUENCY
# Create a dynamic name based on timestamp with format spectrum_YYYYMMDD_HHMMSS.mcap
OUTPUT_FILE = time.strftime("%Y_%m_%d_%H%M%S_DVL_Diagnostics.mcap")

def fetch_and_process_spectrum(writer, channel_id_spectrum, t, temp_max, temp_min):
    """Fetch and process WaterLinked spectrum data."""
    r = requests.get(URL_spectrum, timeout=2.0)
    msg = r.json()
    msg["timestamp"] = t

    msg["data"] = [
        {
            "t1": v[0],
            "t2": v[1],
            "t3": v[2],
            "t4": v[3],
            "t_avg": sum(v) / 4.0,
        }
        for v in msg["data"]
    ]

    for v, v_max in zip(msg["data"], temp_max):
        v_max[0] = max(v["t1"], v_max[0] or v["t1"])
        v_max[1] = max(v["t2"], v_max[1] or v["t2"])
        v_max[2] = max(v["t3"], v_max[2] or v["t3"])
        v_max[3] = max(v["t4"], v_max[3] or v["t4"])

    for v, v_min in zip(msg["data"], temp_min):
        v_min[0] = min(v["t1"], v_min[0] or v["t1"])
        v_min[1] = min(v["t2"], v_min[1] or v["t2"])
        v_min[2] = min(v["t3"], v_min[2] or v["t3"])
        v_min[3] = min(v["t4"], v_min[3] or v["t4"])

    msg["max"] = [
        {"t1": v[0], "t2": v[1], "t3": v[2], "t4": v[3], "t_avg": sum(v) / 4.0} for v in temp_max
    ]
    msg["min"] = [
        {"t1": v[0], "t2": v[1], "t3": v[2], "t4": v[3], "t_avg": sum(v) / 4.0} for v in temp_min
    ]

    msg["x_axis"] = [
        msg["x_offset"] + i * msg["x_scale"] for i in range(len(msg["data"]))
    ]

    writer.add_message(
        channel_id=channel_id_spectrum,
        log_time=int(t * 1e9),
        publish_time=int(t * 1e9),
        data=json.dumps(msg).encode("utf-8"),
    )

def fetch_and_process_graph(writer, channel_id_graph, t):
    """Fetch and process WaterLinked graph data."""
    r = requests.get(URL_graph, timeout=2.0)
    msg_graph = r.json()
    msg_graph["timestamp"] = t
    msg_graph["data"] = [
        {
            "t1": v[0],
            "t2": v[1],
            "t3": v[2],
            "t4": v[3],
            "t_avg": sum(v) / 4.0,
        }
        for v in msg_graph["data"]
    ]

    msg_graph["x_axis"] = [
        i * msg_graph["x_scale"] for i in range(len(msg_graph["data"]))
    ]

    writer.add_message(
        channel_id=channel_id_graph,
        log_time=int(t * 1e9),
        publish_time=int(t * 1e9),
        data=json.dumps(msg_graph).encode("utf-8"),
    )

def main():
    with open(OUTPUT_FILE, "wb") as f:
        writer = Writer(f)
        writer.start()

        # ------------------------------
        # 1. Register schema (NEW API)
        # ------------------------------
        schema_spectrum_json = {
            "type": "object",
            "properties": {
                "timestamp": {"type": "number"},
                "x_offset": {"type": "number"},
                "x_scale": {"type": "number"},
                "y_scale": {"type": "number"},
                "x_axis": {"type": "array", "items": {"type": "number"}},
                "max": {
                  "type": "array",
                  "items": {
                        "type": "object",
                        "properties": {
                          "t1": {"type": "number"},
                          "t2": {"type": "number"},
                          "t3": {"type": "number"},
                          "t4": {"type": "number"},
                          "t_avg": {"type": "number"},
                        }
                  }
                },
                "min": {
                "type": "array",
                "items": {
                      "type": "object",
                      "properties": {
                        "t1": {"type": "number"},
                        "t2": {"type": "number"},
                        "t3": {"type": "number"},
                        "t4": {"type": "number"},
                        "t_avg": {"type": "number"},
                      }
                    }
                },
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                          "t1": {"type": "number"},
                          "t2": {"type": "number"},
                          "t3": {"type": "number"},
                          "t4": {"type": "number"},
                          "t_avg": {"type": "number"},
                        }
                    }
                }
            }
        }

        schema_graph_json = {
            "type": "object",
            "properties": {
                "timestamp": {"type": "number"},
                "x_scale": {"type": "number"},
                "y_scale": {"type": "number"},
                "x_axis": {"type": "array", "items": {"type": "number"}},
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                          "t1": {"type": "number"},
                          "t2": {"type": "number"},
                          "t3": {"type": "number"},
                          "t4": {"type": "number"},
                          "t_avg": {"type": "number"},
                        }
                    }
                }
            }
        }

        schema_id_spectrum = writer.register_schema(
            name="waterlinked/Spectrum",
            encoding="jsonschema",
            data=json.dumps(schema_spectrum_json).encode("utf-8"),
        )

        schema_id_graph = writer.register_schema(
            name="waterlinked/Graph",
            encoding="jsonschema",
            data=json.dumps(schema_graph_json).encode("utf-8"),
        )

        # ------------------------------
        # 2. Register channel (metadata now required)
        # ------------------------------
        channel_id_spectrum = writer.register_channel(
            topic="/waterlinked/spectrum",
            message_encoding="json",
            schema_id=schema_id_spectrum,
            metadata={},
        )

        channel_id_graph = writer.register_channel(
            topic="/waterlinked/graph",
            message_encoding="json",
            schema_id=schema_id_graph,
            metadata={},
        )

        print("Logging WaterLinked spectrum @ 10 Hz → spectrum.mcap")
        print("Press Ctrl-C to stop.\n")

        # ------------------------------
        # 3. Write messages at 10 Hz
        # ------------------------------

        temp_max = [[None for _ in range(4)] for _ in range(128)]
        temp_min = [[None for _ in range(4)] for _ in range(128)]

        try:
          while True:
            t = time.time()

            fetch_and_process_spectrum(writer, channel_id_spectrum, t, temp_max, temp_min)
            fetch_and_process_graph(writer, channel_id_graph, t)

            # Maintain rate
            delay = PERIOD - (time.time() - t)
            if delay > 0:
                time.sleep(delay)

        finally:
            writer.finish()
            print("\nStopped in finally.")



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")

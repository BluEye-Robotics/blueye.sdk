#!/usr/bin/env python3
import threading
import time

from blueye.sdk import Drone

last_message = {}
message_size = {}
message_number = {}
message_number_unique = {}
first_time = None
last_time = None
stats_lock = threading.Lock()


def parse_message(payload_msg_name, data):
    with stats_lock:
        update_stats(payload_msg_name, data)


def update_stats(payload_msg_name, data):
    global first_time, last_time

    if payload_msg_name not in last_message:
        message_size[payload_msg_name] = 0
        message_number[payload_msg_name] = 0
        message_number_unique[payload_msg_name] = 1
        last_message[payload_msg_name] = data

    message_number[payload_msg_name] += 1
    message_size[payload_msg_name] += len(data)
    if data != last_message[payload_msg_name]:
        message_number_unique[payload_msg_name] += 1

    if first_time is None:
        first_time = time.monotonic()
    last_time = time.monotonic()
    last_message[payload_msg_name] = data


def print_stats():
    # Snapshot while holding the lock; telemetry callbacks update these dictionaries.
    with stats_lock:
        if first_time is None or last_time is None or last_time <= first_time:
            return
        time_diff = last_time - first_time
        sizes = message_size.copy()
        numbers = message_number.copy()
        unique = message_number_unique.copy()
    total_size = sum(sizes.values())
    bytes_per_second = total_size / time_diff

    for name, count in sorted(numbers.items(), key=lambda item: -item[1]):
        freq = count / time_diff
        print(f"{name:28} unique/all:{unique[name]:8} / {count:8}    {freq:.2f} Hz")
    print("====")
    for name, size in sorted(sizes.items(), key=lambda item: -item[1]):
        percentage = size / total_size * 100 if total_size else 0
        print(f"{name:28} : {size:8}  {percentage:.0f}%")
    print("====")
    print(f"Time logged: {time_diff:.0f} s")
    print(f"bytes per s: {bytes_per_second:.0f}")


def main():
    with Drone(connect_as_observer=True) as drone:
        print("Listening to protobuf messages")
        drone.telemetry.add_msg_callback([], parse_message, raw=True)
        while True:
            time.sleep(1)
            print_stats()


if __name__ == "__main__":
    main()

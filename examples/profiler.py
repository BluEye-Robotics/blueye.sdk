#!/usr/bin/env python3
import time

from blueye.sdk import Drone

last_message = {}
message_size = {}
message_number = {}
message_number_unique = {}
first_time = None
last_time = None


def parse_message(payload_msg_name, data):
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
        first_time = time.time()
    last_time = time.time()
    last_message[payload_msg_name] = data


myDrone = Drone()

print("Listening to protobuf messages")

loop_time = time.time()
myDrone.add_telemetry_msg_callback([], parse_message, raw=True)
while True:
    if time.time() - loop_time > 1:
        loop_time = time.time()

        time_diff = last_time - first_time
        total_size = sum(message_size.values())
        bytes_per_second = total_size / time_diff

        mn = sorted(message_number.items(), key=lambda item: -item[1])
        for k, v in mn:
            freq = v / time_diff
            print(f"{k:28} unique/all:{message_number_unique[k]:8} / {v:8}    {freq:.2f} Hz")
        print("====")
        ms = sorted(message_size.items(), key=lambda item: -item[1])
        for k, v in ms:
            percentage = v / total_size * 100
            print(f"{k:28} : {v:8}  {percentage:.0f}%")
        print("====")
        print(f"Time logged: {time_diff:.0f} s")
        print(f"bytes per s: {bytes_per_second:.0f}")

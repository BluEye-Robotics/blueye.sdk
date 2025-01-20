import serial
import time
import blueye.protocol as bp
from blueye.sdk import Drone


# Configure the COM port
COM_PORT = "COM2"  # Change this to your virtual COM port
BAUD_RATE = 9600  # Set the baud rate (ensure it matches your virtual COM port configuration)
heading = 0.0


def calculate_checksum(nmea_sentence):
    """
    Calculate the NMEA checksum for a sentence (excluding $ and *hh).
    Returns the checksum as a two-character hexadecimal string.
    """
    checksum = 0
    for char in nmea_sentence:
        checksum ^= ord(char)  # XOR each character
    return f"{checksum:02X}"


def callback_attitude(msg_type: str, msg: bp.AttitudeTel):
    """
    Callback function to handle attitude telemetry messages.
    Updates the global heading variable with the drone's yaw.
    """
    global heading
    print(f"Got a {msg_type} message with heading: {msg.attitude.yaw:.3f}")
    heading = msg.attitude.yaw


def main():
    """
    Main function to set up the drone telemetry, process attitude data,
    and publish it as an NMEA sentence to a virtual COM port.
    """
    my_drone = Drone()

    # Add a callback for the AttitudeTel message
    my_drone.telemetry.add_msg_callback([bp.AttitudeTel], callback_attitude)

    # Adjust the publishing frequency to 10 Hz
    my_drone.telemetry.set_msg_publish_frequency(bp.AttitudeTel, 10)

    try:
        # Open the serial port
        with serial.Serial(COM_PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connected to {COM_PORT} at {BAUD_RATE} baud.")

            while True:
                # Format the heading into an NMEA sentence
                heading_nmea = f"--HDT,{heading:.1f},T"
                checksum = calculate_checksum(heading_nmea)
                nmea_sentence = f"${heading_nmea}*{checksum}\r\n"

                # Send the NMEA sentence to the COM port
                ser.write(nmea_sentence.encode("utf-8"))
                print(f"Sent: {nmea_sentence.strip()}")

                # Wait before sending the next value
                time.sleep(0.1)  # Send data every second

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()

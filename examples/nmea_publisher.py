import socket
import time
import blueye.protocol as bp
from blueye.sdk import Drone


def nmea_sentence(lat: float, lon: float, valid: bool) -> str:
    """Generate an NMEA 0183 sentence for the given latitude and longitude."""
    lat_deg = int(lat)
    lat_min = (lat - lat_deg) * 60
    lon_deg = int(lon)
    lon_min = (lon - lon_deg) * 60

    lat_hemisphere = "N" if lat >= 0 else "S"
    lon_hemisphere = "E" if lon >= 0 else "W"
    is_valid = "A" if valid else "V"
    return f"GPGLL,{lat_deg:02d}{lat_min:07.4f},{lat_hemisphere},{lon_deg:03d}{lon_min:07.4f},{lon_hemisphere},{is_valid}"


def callback_position_estimate(
    msg_type: str, msg: bp.PositionEstimateTel, udp_socket: socket.socket
):
    """Callback for the PositionEstimateTel message."""
    position_estimate = msg.position_estimate
    lat = position_estimate.global_position.latitude
    lon = position_estimate.global_position.longitude
    is_valid = position_estimate.is_valid
    nmea_msg = nmea_sentence(lat, lon, is_valid)
    udp_socket.sendto(nmea_msg.encode("utf-8"), (UDP_IP, UDP_PORT))
    print(f"Sent NMEA message: {nmea_msg}")


if __name__ == "__main__":
    # UDP configuration
    # This IP will broadcast to all devices in the 192.168.1 subnet
    UDP_IP = "192.168.1.255"
    UDP_PORT = 10110
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting

    # Instantiate a drone object
    my_drone = Drone(connect_as_observer=True)

    # Add a callback for the PositionEstimateTel message
    callback_id = my_drone.telemetry.add_msg_callback(
        [bp.PositionEstimateTel], callback_position_estimate, udp_socket=udp_socket
    )

    # Keep the script running to receive and send messages
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # Cleanup
        my_drone.disconnect()
        udp_socket.close()

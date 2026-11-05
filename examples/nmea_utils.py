"""NMEA sentence formatting shared by the examples in this directory."""

import datetime
import math


def nmea_sentence(body: str) -> str:
    """Add the XOR checksum and CRLF to a sentence body without delimiters."""
    checksum = 0
    for byte in body.encode("ascii"):
        checksum ^= byte
    return f"${body}*{checksum:02X}\r\n"


def _coordinate(value: float, degree_digits: int) -> str:
    # Round before splitting so 59.99996 minutes carries into the next degree.
    units = round(abs(value) * 60 * 10000)
    degrees, minute_units = divmod(units, 60 * 10000)
    minutes, fraction = divmod(minute_units, 10000)
    return f"{degrees:0{degree_digits}d}{minutes:02d}.{fraction:04d}"


def nmea_gll(lat: float, lon: float, valid: bool) -> str:
    """Format decimal-degree coordinates as GPGLL with the current UTC time.

    Raises:
        ValueError: If a coordinate is non-finite or outside its geographic range.
    """
    if not math.isfinite(lat) or not -90 <= lat <= 90:
        raise ValueError("Latitude must be finite and between -90 and 90 degrees")
    if not math.isfinite(lon) or not -180 <= lon <= 180:
        raise ValueError("Longitude must be finite and between -180 and 180 degrees")
    now = datetime.datetime.now(datetime.timezone.utc)
    utc_time = now.strftime("%H%M%S") + f".{now.microsecond // 10000:02d}"
    return nmea_sentence(
        f"GPGLL,{_coordinate(lat, 2)},{'N' if lat >= 0 else 'S'},"
        f"{_coordinate(lon, 3)},{'E' if lon >= 0 else 'W'},"
        f"{utc_time},{'A' if valid else 'V'}"
    )


def nmea_hdt(heading: float) -> str | None:
    """Format heading in degrees as HDT, or skip a non-finite heading."""
    if not math.isfinite(heading):
        return None
    # Wrap again after rounding: 359.99 must not be sent as 360.0.
    heading = round(heading % 360, 1) % 360
    return nmea_sentence(f"IIHDT,{heading:.1f},T")

from influxdb_client import Point


def gpu_point(host: str, util_pct: float, mem_mb: int) -> Point:
    """Build a single GPU metric point (used by server-usage-monitor pattern)."""
    return Point("gpu").tag("host", host).field("util_pct", util_pct).field("mem_mb", mem_mb)


def to_line_protocol(host: str, util_pct: float, mem_mb: int) -> str:
    """Render the same point as raw line protocol (used by CircuitPython/ESP32)."""
    return f"gpu,host={host} util_pct={util_pct},mem_mb={mem_mb}i"

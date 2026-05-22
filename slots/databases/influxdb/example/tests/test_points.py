from influxdb_example import gpu_point, to_line_protocol


def test_gpu_point_line_protocol() -> None:
    line = gpu_point("dgx-01", 87.0, 23000).to_line_protocol()
    assert line.startswith("gpu,host=dgx-01 ")
    assert "util_pct=87" in line
    assert "mem_mb=23000" in line


def test_raw_line_protocol_matches() -> None:
    assert to_line_protocol("dgx-01", 87.0, 23000) == "gpu,host=dgx-01 util_pct=87.0,mem_mb=23000i"

# influxdb cheatsheet

## Write

```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

client = InfluxDBClient(
    url="http://localhost:8086",
    org="my-org",
    token="my-token",
)
write_api = client.write_api(write_options=SYNCHRONOUS)

p = (
    Point("gpu")
    .tag("host", "dgx-01")
    .field("util_pct", 87.0)
    .field("mem_mb", 23000)
)
write_api.write(bucket="metrics", record=p)
```

## Batched write (high-volume sensors)

```python
from influxdb_client.client.write_api import WriteOptions

write_api = client.write_api(
    write_options=WriteOptions(batch_size=500, flush_interval=10_000)
)
for sample in stream():
    write_api.write(bucket="metrics", record=sample_to_point(sample))
write_api.close()
```

## Query (Flux)

```python
flux = """
from(bucket:"metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "gpu" and r.host == "dgx-01")
  |> mean()
"""
tables = client.query_api().query(flux)
for table in tables:
    for r in table.records:
        print(r.get_time(), r.get_field(), r.get_value())
```

## Line protocol (raw HTTP, what ESP32/CircuitPython uses)

```
gpu,host=dgx-01 util_pct=87.0,mem_mb=23000 1716345600
```

POST to `/api/v2/write?org=...&bucket=metrics&precision=s` with `Authorization: Token <token>`.

## Local dev

```sh
docker run -d --name influx -p 8086:8086 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=devdev123 \
  -e DOCKER_INFLUXDB_INIT_ORG=my-org \
  -e DOCKER_INFLUXDB_INIT_BUCKET=metrics \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-token \
  influxdb:2.7
```

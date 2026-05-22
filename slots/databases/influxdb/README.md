# influxdb

**Slot**: Time-series database — metrics, sensors, telemetry.

## Why influxdb

Used in `server-usage-monitor` (GPU/CPU/disk telemetry) and `dazzo-monitor` (BLE pet tracker). InfluxDB v2's line protocol is trivial to push from any device — including CircuitPython MCUs over WiFi.

## Conventions

- v2 API (`influxdb-client` Python SDK), not legacy v1. Tokens, orgs, buckets.
- Env vars: `INFLUX_URL`, `INFLUX_ORG`, `INFLUX_TOKEN`, `INFLUX_BUCKET`. Surface via [pydantic-settings](../../python-web/pydantic-settings/).
- Use a `WriteApi` in **batching** mode for any device pushing more than a few points/min.
- One measurement per logical signal. Tags are indexed (low cardinality); fields are not (numbers).
- For dashboards, prefer Grafana over Influx's built-in UI (matches the GPU-Dashboard precedent).

## Alternatives considered

- **prometheus** — pull-based, perfect for service metrics; bad for embedded devices behind NAT.
- **timescaledb** — Postgres extension; great if you also need relational. More ops overhead.
- **questdb** — fast, smaller community.

## Gotchas

- High-cardinality tags (UUIDs, free text) explode index size — *never* tag with user input.
- v2 tokens are scoped per-org-per-bucket; "all access" tokens belong in dev only.
- Line protocol: timestamps in nanoseconds; `precision="s"` saves you from string-formatting.

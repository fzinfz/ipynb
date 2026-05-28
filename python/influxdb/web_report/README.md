# InfluxDB Web Report

A lightweight Flask-based web UI for running InfluxDB Flux queries and visualizing results.

## Features

- Supports multiple InfluxDB servers
- Two report types:
  - `table_*.flux` — table only
  - `chart_*.flux` — table + line chart
- Tag-based filtering
- Configurable time range per report

## Project Structure

```
.
├── app.py                  # Flask application
├── conf/
│   ├── servers.toml        # InfluxDB server credentials
│   ├── chart_*.flux        # Queries that render table + chart
│   └── table_*.flux        # Queries that render table only
├── templates/
│   └── index.html          # Frontend UI
├── docker_run.sh           # Docker run helper
└── README.md               # This file
```

## Configuration

### `conf/servers.toml`

```toml
[server_id]
influxdb_url = "http://localhost:8086"
influxdb_token = "YOUR_TOKEN"
influxdb_org = "your-org"
influxdb_bucket = "your-bucket"
```

### `conf/chart_*.flux` / `conf/table_*.flux`

Write standard Flux queries. Use `v.timeRangeStart` and `v.timeRangeStop` for time range variables.

Example:

```flux
from(bucket: "home")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "degrees")
  |> filter(fn: (r) => r["_field"] == "current")
  |> last()
```

## Run

### Native

```bash
uv run python app.py
```

### Docker

```bash
./docker_run.sh
```

Then open http://localhost:5001

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/servers` | List configured servers (without token) |
| `GET /api/reports` | List available reports with type |
| `GET /api/query/<report_id>?server_id=<id>&start=<range>` | Run a Flux query and return CSV |

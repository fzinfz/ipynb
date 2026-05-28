import glob
import os
import tomllib
from flask import Flask, render_template, jsonify, request
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONF_DIR = os.path.join(BASE_DIR, "conf")

app = Flask(__name__)


def load_toml(filename):
    path = os.path.join(CONF_DIR, filename)
    with open(path, "rb") as f:
        return tomllib.load(f)


def get_servers():
    data = load_toml("servers.toml")
    servers = []
    for sid, cfg in data.items():
        if isinstance(cfg, dict):
            token = cfg.get("influxdb_token", "")
            if not token:
                token = os.environ.get("INFLUXDB_TOKEN", "")
            servers.append({
                "id": str(sid),
                "url": cfg.get("influxdb_url", ""),
                "token": token,
                "org": cfg.get("influxdb_org", ""),
                "bucket": cfg.get("influxdb_bucket", ""),
            })
    return servers


def get_reports():
    reports = []
    for pattern in ("chart_*.flux.conf", "table_*.flux.conf"):
        for path in sorted(glob.glob(os.path.join(CONF_DIR, pattern))):
            name = os.path.basename(path)
            rid = name[:-10]  # strip .flux
            rtype = "table" if name.startswith("table_") else "chart"
            with open(path, "r", encoding="utf-8") as f:
                query = f.read()
            reports.append({"id": rid, "query": query, "type": rtype})
    return reports


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/servers")
def api_servers():
    servers = get_servers()
    return jsonify([{k: v for k, v in s.items() if k != "token"} for s in servers])


@app.route("/api/reports")
def api_reports():
    reports = get_reports()
    return jsonify([{"id": r["id"], "type": r["type"]} for r in reports])


@app.route("/api/query/<report_id>")
def api_query(report_id):
    server_id = request.args.get("server_id")
    if not server_id:
        return jsonify({"error": "missing server_id"}), 400

    servers = {s["id"]: s for s in get_servers()}
    reports = {r["id"]: r for r in get_reports()}

    server = servers.get(server_id)
    report = reports.get(report_id)

    if not server:
        return jsonify({"error": "server not found"}), 404
    if not report:
        return jsonify({"error": "report not found"}), 404

    query = report["query"]
    # Replace Grafana-style variables with defaults if not provided
    time_range_start = request.args.get("start", "-1h")
    time_range_stop = request.args.get("stop", "now()")
    query = query.replace("v.timeRangeStart", time_range_start)
    query = query.replace("v.timeRangeStop", time_range_stop)

    url = f"{server['url'].rstrip('/')}/api/v2/query"
    headers = {
        "Authorization": f"Token {server['token']}",
        "Content-Type": "application/vnd.flux",
        "Accept": "application/csv",
    }
    params = {"org": server["org"]}

    try:
        resp = requests.post(url, params=params, headers=headers, data=query, timeout=30)
        resp.raise_for_status()
        return resp.text, 200, {"Content-Type": "text/plain"}
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

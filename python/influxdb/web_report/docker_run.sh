#!/bin/bash
set -e

IMAGE_NAME="fzinfz/python:py12-flask"
CONTAINER_NAME="influxdb-web-report"
HOST_PORT="${HOST_PORT:-5001}"

INFLUXDB_TOKEN=$(grep -oP "(?<=influxdb_token=)(.*)" /data/conf/init.sh | tail -1)
echo INFLUXDB_TOKEN=\"$INFLUXDB_TOKEN\"

echo "Stopping existing container if any..."
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

echo "Starting container on port $HOST_PORT..."
docker run -d --restart unless-stopped \
  -e http_proxy="" -e https_proxy="" -e ftp_proxy="" -e no_proxy="" \
  -e INFLUXDB_TOKEN="$INFLUXDB_TOKEN" \
  --name "$CONTAINER_NAME" \
  -p "$HOST_PORT:5001" \
  -v "$(pwd):/app/:ro" \
  "$IMAGE_NAME"

echo "Running at http://localhost:$HOST_PORT"

docker logs -f "$CONTAINER_NAME"

#!/usr/bin/env bash

set -e

SERVER_IP="your.server.ip"
DOMAIN="yourdomain.com"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[1/5] Building frontend"
cd "${PROJECT_ROOT}/frontend"
npm run build

echo "[2/5] Uploading frontend dist to server"
cd "${PROJECT_ROOT}"
rsync -avz frontend/dist/ "root@${SERVER_IP}:/var/www/learning-os/frontend/dist/"

echo "[3/5] Updating backend and restarting API service"
ssh "root@${SERVER_IP}" "cd /opt/learning-os/backend && git pull && pip install -r requirements.txt && systemctl restart learningos-api"

echo "[4/5] Reloading nginx"
ssh "root@${SERVER_IP}" "nginx -t && systemctl reload nginx"

echo "[5/5] Deploy done: https://${DOMAIN}"
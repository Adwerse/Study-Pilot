#!/usr/bin/env bash

set -e

DOMAIN="yourdomain.com"
EMAIL="admin@yourdomain.com"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[1/6] Installing nginx, certbot and certbot nginx plugin"
apt update
apt install -y nginx certbot python3-certbot-nginx

echo "[2/6] Requesting Let's Encrypt certificate for ${DOMAIN} and api.${DOMAIN}"
certbot --nginx -d "$DOMAIN" -d "api.$DOMAIN" --non-interactive --agree-tos -m "$EMAIL"

echo "[3/6] Creating frontend dist directory"
mkdir -p /var/www/learning-os/frontend/dist

echo "[4/6] Installing nginx configuration"
cp "${PROJECT_ROOT}/nginx/nginx.conf" /etc/nginx/nginx.conf

echo "[5/6] Validating and reloading nginx"
nginx -t
systemctl reload nginx

echo "[6/6] Configuring automatic certificate renewal"
if ! grep -q "certbot renew --quiet" /etc/cron.d/certbot 2>/dev/null; then
    echo "0 12 * * * root certbot renew --quiet" >> /etc/cron.d/certbot
fi

echo "Server setup completed"
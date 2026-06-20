#!/usr/bin/env bash
# Initial setup for a fresh Ubuntu 22.04/24.04 DigitalOcean Droplet.
# Run as root:  bash deploy/setup-droplet.sh
set -euo pipefail

echo "==> Installing Docker..."
apt-get update
apt-get install -y ca-certificates curl git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${VERSION_CODENAME}") stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "==> Enabling Docker on boot..."
systemctl enable docker
systemctl start docker

echo "==> Opening firewall (SSH + HTTP + HTTPS)..."
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo ""
echo "Done. Next steps:"
echo "  1. Clone your repo:  git clone <your-repo-url> /opt/guardianeye && cd /opt/guardianeye"
echo "  2. Create env file:  cp deploy/.env.production.example .env && nano .env"
echo "  3. Start app:        docker compose up -d --build"
echo "  4. Optional HTTPS:     see deploy/DEPLOY.md (Certbot section)"

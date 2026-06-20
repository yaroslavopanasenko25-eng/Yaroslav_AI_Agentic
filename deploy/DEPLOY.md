# Deploying to DigitalOcean

Two supported paths:

| Method | Best for | Difficulty |
|--------|----------|------------|
| **Droplet + Docker Compose** | Full control, one VM, lowest cost | Easy (recommended) |
| **App Platform** | Managed deploys from GitHub | Medium |

---

## Prerequisites

1. A [DigitalOcean](https://www.digitalocean.com/) account
2. API keys ready (see `deploy/.env.production.example`):
   - `XAI_API_KEY` — Grok AI
   - `ALERTS_API_KEY` — alerts.in.ua (when approved)
   - `SUPABASE_URL` + `SUPABASE_KEY` — optional but recommended for history
3. Domain name (optional, for HTTPS)

---

## Option A — Droplet + Docker Compose (recommended)

### 1. Create a Droplet

- **Image:** Ubuntu 24.04 LTS  
- **Size:** Basic → $6/mo (1 GB RAM) minimum; **$12/mo (2 GB)** recommended  
- **Region:** Frankfurt (`fra1`) or closest to Ukraine  
- Add your SSH key  

### 2. Initial server setup

```bash
ssh root@YOUR_DROPLET_IP
bash deploy/setup-droplet.sh
```

### 3. Deploy the app

```bash
git clone https://github.com/YOUR_USER/YOUR_REPO.git /opt/guardianeye
cd /opt/guardianeye

cp deploy/.env.production.example .env
nano .env   # fill in all secrets and ALLOWED_ORIGINS
```

Set `ALLOWED_ORIGINS` to your public URL, e.g.:

```
ALLOWED_ORIGINS=https://alarms.example.com,http://YOUR_DROPLET_IP
```

Build and start:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
```

Open **http://YOUR_DROPLET_IP** — the app should load.

### 4. HTTPS with Let's Encrypt (optional)

Point your domain A record to the Droplet IP, then:

```bash
apt install -y certbot
docker compose down

# Temporarily stop web on port 80, or use nginx plugin on host
certbot certonly --standalone -d alarms.example.com

# Add a reverse-proxy container or mount certs — simplest approach:
# Put Caddy or host nginx in front; see DigitalOcean docs for certbot + docker.
```

Quick Caddy option (replace `alarms.example.com`):

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install -y caddy

cat > /etc/caddy/Caddyfile <<'EOF'
alarms.example.com {
    reverse_proxy localhost:80
}
EOF

systemctl reload caddy
```

Update `ALLOWED_ORIGINS` in `.env` to include `https://alarms.example.com`, then:

```bash
docker compose up -d
```

### 5. Updates

```bash
cd /opt/guardianeye
git pull
docker compose up -d --build
```

---

## Option B — App Platform

1. Push this repo to GitHub  
2. Edit `.do/app.yaml` — set your `github.repo`  
3. Create app:

```bash
doctl auth init
doctl apps create --spec .do/app.yaml
```

4. In the DO dashboard, add **encrypted** environment variables:
   - `SUPABASE_URL`, `SUPABASE_KEY`
   - `XAI_API_KEY`
   - `ALERTS_API_KEY`
5. Set `ALLOWED_ORIGINS` to your App Platform URL (e.g. `https://guardianeye-xxxxx.ondigitalocean.app`)

The `web` service nginx proxies `/api/*` to the internal `backend` service.

---

## Architecture (production)

```
Internet
   │
   ▼
┌─────────────┐     /api/*     ┌──────────────────┐
│  nginx:80   │ ─────────────► │  FastAPI :8080   │
│  (React SPA)│                │  gunicorn+uvicorn│
└─────────────┘                └──────────────────┘
       │                                │
       │ static files                   ├── alerts.in.ua
       │ (shelters.json)                ├── Grok (xAI)
       ▼                                └── Supabase
  index.html + assets
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ALLOWED_ORIGINS` | Yes (prod) | Comma-separated URLs for CORS |
| `XAI_API_KEY` | Yes | Grok API key |
| `XAI_MODEL` | No | Default `grok-3-mini` |
| `ALERTS_API_KEY` | When available | Live air-raid map |
| `SUPABASE_URL` | Recommended | Alarm history storage |
| `SUPABASE_KEY` | Recommended | Service-role key |
| `DEBUG` | No | Keep `false` in production |
| `SHELTERS_JSON_PATH` | Auto in Docker | `/app/data/shelters.json` |

---

## Health checks

- Backend: `GET /health` → `{"status":"healthy"}`  
- API status: `GET /api/v1/health` → shows which integrations are configured  

---

## Troubleshooting

**Black screen after deploy**  
→ Check `docker compose logs web backend`. Backend must be healthy before nginx starts.

**502 on /api/**  
→ Backend not running or wrong proxy. Run `curl http://localhost:8080/health` inside the backend container.

**CORS errors**  
→ Add your exact domain (with `https://`) to `ALLOWED_ORIGINS` in `.env` and restart backend.

**Grok agent not responding**  
→ Verify `XAI_API_KEY` is set and `curl -X POST http://localhost:8080/api/v1/ai/chat -H 'Content-Type: application/json' -d '{"message":"test"}'`.

---

## Local production test

Test the same Docker stack locally before deploying:

```bash
cp deploy/.env.production.example .env
# edit .env — set ALLOWED_ORIGINS=http://localhost

docker compose up --build
# open http://localhost
```

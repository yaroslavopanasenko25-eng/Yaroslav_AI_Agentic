# GuardianEye: Ukraine Air Raid Defense Analytics

GuardianEye is a production-oriented full-stack analytics platform designed to transform raw Ukrainian air raid alert events into actionable defense intelligence.

It combines:

- **Defense data engineering** for ingesting and structuring alert/interception streams
- **Time series analytics** for trend and seasonality discovery
- **AI-assisted forecasting** for next-day regional risk probabilities

The platform mission is to improve operational awareness by analyzing alert timestamps, durations, threat types, and interception outcomes.

---

## Quick Start (Python — основний спосіб запуску)

Згідно з вимогами проєкту, **весь застосунок працює через Python (FastAPI)**:

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8080
```

Відкрийте в браузері: **http://127.0.0.1:8080**

| URL | Сторінка |
|-----|----------|
| `/` | Карта тривог (Dashboard) |
| `/analysis` | Аналіз, графіки, RAG-диспетчер |
| `/safety` | Безпека та карта укриттів |
| `/api/v1/...` | REST API |

**Стек:** Python 3.11+ · FastAPI · Jinja2 · pandas · Grok API · alerts.in.ua  

Папка `alarm-app/frontend/` (React) — застарілий UI; для здачі використовуйте Python-версію вище.

---

GuardianEye enables analysts and decision-support teams to:

1. Monitor historical and live air raid alert behavior by region
2. Quantify exposure through duration and frequency metrics
3. Correlate alerts with interception performance indicators
4. Produce predictive risk outlooks for upcoming 24-hour windows

Typical workflow:

1. Ingest alerts from external providers (e.g., `alerts-in-ua`)
2. Normalize and enrich records (durations, risk levels)
3. Persist structured data in Supabase/PostgreSQL
4. Compute analytical features via FastAPI service modules
5. Forecast daily threat probabilities with Grok-powered reasoning
6. Visualize trends in a dark-themed Next.js dashboard

---

## System Architecture (3-Tier)

GuardianEye follows a clear 3-tier architecture:

### 1) Presentation Tier — Next.js Frontend

- **Stack**: Next.js 13+ App Router, React, Tailwind CSS
- **Responsibilities**:
  - Defense dashboard rendering
  - Time series and risk visualizations
  - Operator settings (theme/language)
  - API consumption from backend services

### 2) Application Tier — FastAPI Backend

- **Stack**: FastAPI, pandas, statsmodels, NumPy, Pydantic
- **Responsibilities**:
  - REST API endpoints for health and analytics
  - Data ingestion orchestration and transformation
  - Statistical analysis of alert/interception patterns
  - AI prompt generation and forecast requests to Grok API

### 3) Data Tier — Supabase (PostgreSQL)

- **Stack**: Supabase hosted PostgreSQL + Python client
- **Responsibilities**:
  - Durable storage of alerts/interception entities
  - Relational joins between threat events and outcomes
  - Query-ready historical snapshots for model context

---

## Database Schema Guide

GuardianEye stores data using two primary tables.

### `alerts`

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` / `text` | Primary identifier for an alert record |
| `start_time` | `timestamp` | Alert activation time |
| `end_time` | `timestamp` | Alert end time (nullable for active alerts) |
| `duration` | `integer` | Duration in minutes, computed dynamically |
| `region` | `text` | Ukrainian region tied to the alert |
| `threat_type` | `text` | Threat class (missile, drone, mixed, unknown) |
| `risk_level` | `text` | Derived risk band (low/medium/high/critical) |

### `interceptions`

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` / `text` | Primary identifier for interception record |
| `alert_id` | `uuid` / `text` | Foreign key to `alerts.id` |
| `missiles_launched` | `integer` | Number of incoming missiles |
| `missiles_shot_down` | `integer` | Number of successful missile interceptions |
| `drone_stats` | `jsonb` | Structured drone engagement summary |

Recommended index strategy:

- `alerts(start_time)` for time-window queries
- `alerts(region, start_time)` for regional trend analysis
- `interceptions(alert_id)` for join performance

---

## AI Forecasting Core (Grok Integration)

GuardianEye includes a forecasting service template that:

1. Pulls historical rows from Supabase
2. Converts records into compact time series vectors and aggregated context
3. Builds a structured prompt for the Grok API
4. Requests next-day risk probabilities per region and threat profile
5. Returns machine-readable forecast output for dashboard overlays

Expected model outputs include:

- Probability distribution of risk levels by region
- Forecast confidence and uncertainty notes
- Textual rationale tied to recent alert/interception dynamics

> The repository scaffold ships with a secure, environment-driven Grok client template; production deployments should enforce strict request timeout, retry policy, and response schema validation.

---

## Repository Structure

```text
.
├── README.md
├── backend
│   ├── ai_service.py
│   ├── analytics.py
│   ├── data_loader.py
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
└── frontend
    ├── app
    │   ├── layout.tsx
    │   └── page.tsx
    ├── components
    │   ├── LiveMap.tsx
    │   ├── Settings.tsx
    │   └── TimeSeriesChart.tsx
    └── package.json
```

---

## Installation & Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- npm 10+
- Supabase project credentials
- Grok API credentials

### 1) Clone and enter repository

```bash
git clone https://github.com/yaroslavopanasenko25-eng/Yaroslav_AI_Agentic.git
cd Yaroslav_AI_Agentic
```

### 2) Backend setup (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows PowerShell
pip install --upgrade pip
pip install -r requirements.txt
```

Run backend:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Health checks:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/api/v1/health`

### 3) Frontend setup (Next.js)

```bash
cd ../frontend
npm install
npm run dev
```

Open:

- `http://localhost:3000`

Frontend dependencies include both **Recharts** (implemented in current scaffold) and **Plotly** packages (pre-added for advanced geospatial/analytical visualizations in upcoming dashboard iterations).

### 4) Environment variables (`.env`)

Create `/backend/.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-key
GROK_API_KEY=your-grok-api-key
GROK_API_URL=https://api.x.ai/v1/chat/completions
ALERTS_API_URL=https://api.alerts.in.ua/v1/alerts/active.json
```

Optional frontend env (`/frontend/.env.local`):

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 5) Data ingestion placeholder execution

```bash
cd ../backend
python data_loader.py
```

The loader script currently provides a production-ready scaffold with robust validation and upsert placeholders for adaptation to your live schema and API contracts.

---

## Security and Operations Notes

- Never commit secret keys to source control
- Use short-lived service keys where possible
- Restrict CORS origins in production
- Add authentication/authorization for analytics endpoints before deployment
- Implement rate limiting and request logging for all public APIs

---

## Roadmap Ideas

- Real-time websocket stream for live alert overlays
- Feature store for model-ready lag/rolling metrics
- Region-level anomaly detection pipeline
- Automated model evaluation and drift monitoring
- SOC-style alerting integrations

---

## License

Add a project license aligned with your deployment policy before production release.

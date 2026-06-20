# Ukraine Alarm Shield 🛡️

A full-stack web application for monitoring Ukrainian air alarm status, analyzing historical alarm data, and providing safety information.

## Features

| Tab | Description |
|-----|-------------|
| **Dashboard** | Live Ukraine alarm map with region status (active / warning / clear / occupied) |
| **Analysis** | 14-day alarm history with bar & line charts, intercept rates, and a detailed data table |
| **Safety** | Safety tips for before/during/after alarms + interactive shelter map |
| **Settings** | Dark/Light theme, Ukrainian/English language, Dyslexia mode (OpenDyslexic font) |
| **AI Agent** | Floating chat window (bottom-right) with safety advice |

## Design

- iOS 26 "Liquid Glass" aesthetic — frosted glass panels, dark ambient background
- Sidebar: Dashboard, Analysis, Safety (top-left) · Settings (bottom-left)
- AI Agent FAB: bottom-right corner

## Quick Start

### Option A — Windows batch file
```
alarm-app\start.bat
```

### Option B — Manual

**Backend** (Express.js, port 3001):
```bash
cd alarm-app/backend
npm install
npm start
```

**Frontend** (Vite + React, port 5173):
```bash
cd alarm-app/frontend
npm install
npm run dev
```

Then open **http://localhost:5173**

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Map (alarm)**: react-simple-maps + deldersveld/topojson Ukraine regions
- **Map (shelters)**: react-leaflet + CartoDB dark tiles
- **Charts**: Recharts
- **i18n**: react-i18next (UK / EN)
- **Backend**: Express.js with mock data

## Data

Currently uses **mock data**. To connect a real API, update:
- `backend/index.js` routes to fetch from `https://api.ukrainealarm.com`
- Add your API key to the backend environment

# Campus Parking MVP

Small-scale MVP for a campus parking SaaS: Node.js (TypeScript) API, TimescaleDB/Postgres, Redis, and stubs for admin and driver clients.

## Quick Start

1) Requirements: Docker, Docker Compose, Node 18+.

2) Start databases and API (first run builds the API image):

```bash
docker compose up -d --build
```

3) View API at http://localhost:4000/health

4) Local dev (hot reload):

```bash
cd backend
npm install
npx prisma generate
npm run dev
```

Services:
- Postgres/TimescaleDB: localhost:5432 (db/db creds from .env)
- Redis: localhost:6379
- API: http://localhost:4000

# parkeye
ParkEye Software

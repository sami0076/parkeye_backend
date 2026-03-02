# Parkeye Backend

MVP backend for the Parkeye GMU campus parking app — FastAPI + Supabase (PostgreSQL).

## Local setup

```bash
git clone <repo>
cd parkeye_backend
cp .env.example .env   # fill in Supabase keys
docker-compose up      # FastAPI + Postgres
python mock/seed.py    # load mock data (run once)
```

- **API**: http://localhost:8000  
- **Docs**: http://localhost:8000/docs  

## Demo flow (end-to-end)

Use this checklist to verify the full user flow against the API:

| Step | Action | Endpoint / Action |
|------|--------|-------------------|
| **Home / Map** | Load map and live occupancy | `GET /lots` — all lots with current occupancy and color |
| | | `ws://host/ws/occupancy` — connect; receive `[{ lot_id, occupancy_pct, color }, ...]` every 30 s |
| **Lot detail** | User taps a lot | `GET /lots/{id}` — single lot + upcoming events |
| | | `GET /lots/{id}/history` — hourly occupancy for graph |
| | | `GET /lots/{id}/floors` — per-floor breakdown (decks only) |
| **Prediction** | Show 15/30 min look-ahead | `GET /predictions/{lot_id}` |
| **Feedback** | User submits rating | `POST /feedback` — body: `{ lot_id, accuracy_rating, experience_rating, note? }` (auth optional) |
| **Events** | Context / list | `GET /events` — upcoming campus events (next 7 days) |

Replace `host` with your server (e.g. `localhost:8000` for local dev).

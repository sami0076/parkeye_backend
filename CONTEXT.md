# Parkeye Backend — Context for Cursor
# Save this file as CONTEXT.md in the root of the parkeye-backend repository.
# Cursor will use this as a reference for all AI-assisted coding in this project.

================================================================================
WHAT THIS PROJECT IS
================================================================================

Parkeye is a campus parking app for George Mason University (GMU). This repo
is the backend MVP — a single FastAPI service connected to Supabase (PostgreSQL).

Its job is to serve mock parking data to the iOS app so every frontend screen
works end-to-end for a live demo. There is no real-time GPS ingestion, no ML
model training, and no complex infrastructure. Just a clean REST API and a
WebSocket feed powered by pre-seeded mock data.

OUT OF SCOPE FOR THIS MVP:
- Live GPS / telemetry ingestion from real users
- Real ML model training (predictions use simple table lookups, not a model)
- Weather or other external API integrations
- APNs push notifications (admin changes surface via WebSocket only)
- Redis caching layer
- Analytics dashboards


================================================================================
TECH STACK
================================================================================

Language:    Python 3.12
Framework:   FastAPI (auto-generates docs, Pydantic validation built in)
Database:    Supabase (hosted PostgreSQL) — free tier, easy to inspect seeded data
Auth:        Supabase Auth (JWT) — handles GMU OAuth and Google OAuth
             Backend only verifies the JWT, no custom auth logic
WebSocket:   FastAPI native WebSocket — streams mock occupancy every 30 seconds
Mock Data:   JSON/CSV files + seed.py — populates DB on startup
Hosting:     Render.com (free tier, zero-config Docker deploy)
Local Dev:   docker-compose (FastAPI + Postgres in one command)


================================================================================
PROJECT FILE STRUCTURE
================================================================================

parkeye-backend/
├── app/
│   ├── main.py                  # FastAPI app init, router registration, CORS
│   ├── config.py                # Settings loaded from .env via Pydantic BaseSettings
│   ├── database.py              # Supabase client + async SQLAlchemy session factory
│   ├── auth.py                  # JWT decode helper, get_current_user dependency
│
│   ├── models/                  # SQLAlchemy ORM table definitions (one file per table)
│   │   ├── lot.py               # Lot: id, name, capacity, permit_types, lat, lon, status, etc.
│   │   ├── occupancy.py         # OccupancySnapshot: lot_id, hour_of_day, day_of_week, pct, color
│   │   ├── event.py             # CampusEvent: title, start, end, affected_lots
│   │   └── feedback.py          # Feedback: lot_id, accuracy_rating, experience_rating, note
│
│   ├── schemas/                 # Pydantic request/response shapes (agreed on Day 1)
│   │   ├── lot.py               # LotResponse, LotListResponse
│   │   ├── occupancy.py         # OccupancyResponse, PredictionResponse
│   │   ├── feedback.py          # FeedbackCreate
│   │   └── recommendations.py   # RecommendationResponse
│
│   ├── routers/                 # One file per feature area — each registers its own routes
│   │   ├── lots.py              # GET /lots, GET /lots/{id}, GET /lots/{id}/history
│   │   ├── predictions.py       # GET /predictions/{lot_id}
│   │   ├── recommendations.py   # GET /recommendations
│   │   ├── events.py            # GET /events
│   │   ├── feedback.py          # POST /feedback
│   │   ├── admin.py             # PATCH /admin/lots/{id}/status (requires admin JWT claim)
│   │   └── websocket.py         # ws://.../ws/occupancy — 30-second broadcast loop
│
│   └── services/                # Business logic layer (thin for MVP, no external calls)
│       ├── occupancy.py         # get_current_occupancy(lot_id) — DB snapshot lookup
│       ├── prediction.py        # get_prediction(lot_id) — rule-based look-ahead (no ML)
│       └── recommendation.py    # get_recommendations(...) — rank lots by predicted pct + distance
│
├── mock/                        # ALL mock data lives here — this powers the entire demo
│   ├── lots.json                # 10 GMU lots: real coordinates, capacity, permit types
│   ├── occupancy_history.csv    # Synthetic hourly occupancy (24h x 7 days x 10 lots)
│   ├── events.json              # ~20 campus events with affected lot IDs
│   └── seed.py                  # Run once: loads all mock files into Supabase (idempotent)
│
├── tests/
│   └── test_api.py              # Smoke tests covering every endpoint
│
├── .env                         # Secrets — NEVER commit to GitHub
├── Dockerfile
├── docker-compose.yml           # Local: FastAPI + Postgres
├── requirements.txt
└── README.md


================================================================================
DATABASE SCHEMA (4 TABLES)
================================================================================

--- lots ---
id              UUID (PK)         Auto-generated
name            TEXT              e.g. "Lot K", "Parking Deck 1"
capacity        INT               Total spaces in this lot
permit_types    TEXT[]            e.g. ["general", "west_campus"]
lat             FLOAT             Centroid latitude (real GMU coordinates)
lon             FLOAT             Centroid longitude
is_deck         BOOL              True if multi-floor parking deck
floors          INT               Floor count (decks only, null otherwise)
status          TEXT              "open" | "limited" | "closed"
status_until    TIMESTAMPTZ       Expiry of admin override (null = no expiry)
status_reason   TEXT              Admin note shown to users in the app

--- occupancy_snapshots ---
Pre-populated from mock/occupancy_history.csv on seed.
The WebSocket loop and prediction service read rows matching the current
hour_of_day + day_of_week to simulate live data with no real feeds.

id              BIGINT (PK)       Auto-increment
lot_id          UUID (FK)         References lots.id
hour_of_day     INT               0 to 23
day_of_week     INT               0 = Monday, 6 = Sunday
occupancy_pct   FLOAT             0.0 to 1.0
color           TEXT              "green" | "yellow" | "red"

--- campus_events ---
id              UUID (PK)
title           TEXT              e.g. "Basketball vs. VCU"
start_time      TIMESTAMPTZ
end_time        TIMESTAMPTZ
impact_level    TEXT              "low" | "medium" | "high"
affected_lots   UUID[]            Array of lot IDs expected to be impacted

--- feedback ---
id              UUID (PK)
user_id         UUID              From Supabase Auth JWT (nullable for guests)
lot_id          UUID (FK)
accuracy_rating INT               1 to 5 stars
experience_rating INT             1 to 5 stars
note            TEXT              Optional free text from user
created_at      TIMESTAMPTZ       Auto-set on insert


================================================================================
API ENDPOINTS
================================================================================

--- LOTS ---
GET  /lots                    All lots with current occupancy_pct, color badge, admin status
GET  /lots/{id}               Single lot: occupancy, permit types, status, upcoming events
GET  /lots/{id}/history       Hourly occupancy for past 7 days (powers the detail screen graph)
GET  /lots/{id}/floors        Per-floor occupancy breakdown (parking decks only)

--- PREDICTIONS (Rule-Based Look-Ahead — No ML) ---
GET  /predictions/{lot_id}    Returns:
                              {
                                t15: { pct, color },
                                t30: { pct, color },
                                note: "Estimated from historical patterns"
                              }
How it works: fetches occupancy_snapshots rows for hour+1 and hour+2
on the same day_of_week. No model file, no inference — just a table lookup.
Confidence is always labeled "Estimated from historical patterns" for honesty.

--- RECOMMENDATIONS ---
GET  /recommendations         Query params: permit_type, dest_lat, dest_lon,
                              arrival_time (ISO 8601), duration_min

Logic:
  1. Filter lots by permit_types containing the requested permit_type
  2. Fetch predicted occupancy at arrival_hour from occupancy_snapshots
  3. Apply +20% occupancy bump for lots affected by events in the arrival window
  4. Compute haversine distance from each lot to destination coordinates
  5. Sort by occupancy ascending → return top 5
  Each result includes: predicted_pct, color, walk_minutes, confidence label
  No ML — pure logic on the snapshot table.

--- EVENTS ---
GET  /events                  Upcoming campus events for the next 7 days

--- FEEDBACK ---
POST /feedback                Body: { lot_id, accuracy_rating, experience_rating, note? }

--- ADMIN ---
PATCH /admin/lots/{id}/status Body: { status, status_until?, status_reason? }
                              Requires admin JWT claim (role == "admin")
                              Admin users are set manually in Supabase dashboard before demo

--- WEBSOCKET ---
ws://.../ws/occupancy         Every 30 seconds, broadcasts JSON array:
                              [{ lot_id, occupancy_pct, color }, ...]
                              Reads occupancy_snapshots for current hour/day.
                              Admin status overrides are reflected automatically.
                              iOS map colors update on each received message.


================================================================================
MOCK DATA LAYER
================================================================================

This is the heart of the MVP. All API responses are backed by three seeded files.
Switching to live data later only requires changing what writes to
occupancy_snapshots — no API or schema changes needed.

--- mock/lots.json ---
10 GMU parking lots and decks. Each entry:
  id, name, capacity, permit_types (array), lat, lon, is_deck, floors
Coordinates are real GMU lot centroids sourced from Google Maps.

--- mock/occupancy_history.csv ---
Synthetic hourly occupancy per lot covering 24 hours x 7 days.
Columns: lot_id, hour_of_day, day_of_week, occupancy_pct

Generation formula (in seed.py):
  base = sin_curve(hour, peak=10, trough=3)   # peaks 10 AM, troughs 3 AM
  weekend_factor = 0.4 if day_of_week >= 5 else 1.0
  noise = random.gauss(0, 0.05)
  occupancy_pct = clamp(base * weekend_factor + noise, 0.0, 1.0)
  color = "green" if pct < 0.6 else "yellow" if pct < 0.85 else "red"

This one file powers: current occupancy display, history graphs, and predictions.

--- mock/events.json ---
~20 campus events (basketball games, graduation, finals weeks, etc.)
with start/end times and affected lot IDs.
Events within 2 hours of a requested arrival time bump predicted occupancy
for affected lots by +20% in the recommendations logic.

--- mock/seed.py ---
Run once on setup. Reads all three files and inserts into Supabase.
Idempotent — skips rows that already exist (checks by lot name).
Safe to re-run without creating duplicates.

  python mock/seed.py


================================================================================
SERVICES LAYER
================================================================================

Three small files. No ML, no external calls — logic only on top of the DB.

--- services/occupancy.py: get_current_occupancy(lot_id) ---
Queries occupancy_snapshots for the row matching:
  lot_id + current hour_of_day + current day_of_week
If an admin override is active (status = "closed"), returns 1.0 / red
regardless of the snapshot value.

--- services/prediction.py: get_prediction(lot_id) ---
Fetches occupancy_snapshots rows for hours t+1 and t+2
for the same lot and day_of_week.
Returns { t15: { pct, color }, t30: { pct, color }, note: "Estimated..." }
No model file. No inference. Pure table look-ahead.

--- services/recommendation.py: get_recommendations(...) ---
Inputs: permit_type, dest_lat, dest_lon, arrival_time, duration_min
Steps:
  1. Filter lots by permit_types
  2. Fetch predicted occupancy at arrival_hour
  3. Apply +20% event bump for affected lots
  4. Compute haversine distance to destination → walk_minutes
  5. Sort by pct ascending → return top 5


================================================================================
AUTH
================================================================================

Supabase Auth handles GMU OAuth and Google OAuth entirely.
The iOS app receives a JWT from Supabase directly after login.
Every API call sends this JWT as: Authorization: Bearer <token>

Backend decodes the JWT using the Supabase JWT secret and extracts user_id and role.
No custom auth logic is needed.

  # app/auth.py — one dependency used by all protected routes
  async def get_current_user(token = Depends(oauth2_scheme)):
      payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET)
      return User(id=payload["sub"], role=payload.get("role", "user"))

Admin endpoints check: role == "admin"
Admin users are set manually in the Supabase dashboard before the demo.


================================================================================
DATA FLOW
================================================================================

--- How the iOS Map Gets Its Data ---
1. iOS app connects to ws://.../ws/occupancy on launch
2. Backend every 30 seconds:
   a. SELECT * FROM occupancy_snapshots WHERE hour_of_day = current_hour
      AND day_of_week = current_day
   b. Apply admin overrides (status = "closed" → color = "red")
   c. Broadcast JSON array to all connected iOS clients
3. iOS map colors update on each received message

--- How Recommendations Work ---
GET /recommendations?permit_type=general&dest_lat=38.83&arrival_time=2026-03-01T10:00
  1. Filter lots WHERE permit_types contains "general"
  2. For each lot: fetch occupancy_snapshots WHERE hour = 10, day = Saturday
  3. Check campus_events overlapping arrival window:
     affected lots get occupancy_pct += 0.20
  4. Compute haversine(lot.lat, lot.lon, dest_lat, dest_lon) → walk_minutes
  5. Sort by occupancy_pct ASC → return top 5

--- How Admin Status Overrides Work ---
Admin: PATCH /admin/lots/{id}/status { status: "closed", status_reason: "Construction until 5pm" }
  → Updates lots.status in DB
  → Next WebSocket broadcast (within 30s) picks up the change
  → iOS map refreshes automatically (no push notification needed for demo)


================================================================================
ENVIRONMENT VARIABLES (.env)
================================================================================

SUPABASE_URL          Your Supabase project URL
SUPABASE_KEY          Supabase service role key (NEVER expose to iOS app)
SUPABASE_JWT_SECRET   From Supabase dashboard: Settings > API > JWT Secret
DATABASE_URL          postgres://... async connection string for SQLAlchemy
ALLOWED_ORIGINS       CORS origins: iOS app scheme + localhost for local dev
ENV                   "development" | "production"

IMPORTANT: Never commit .env to GitHub. Use .env.example with placeholder values.


================================================================================
LOCAL DEVELOPMENT (ONE COMMAND)
================================================================================

  git clone https://github.com/parkeye/parkeye-backend
  cd parkeye-backend
  cp .env.example .env        # fill in your Supabase keys
  docker-compose up           # starts FastAPI + Postgres locally
  python mock/seed.py         # load mock data (run once)

  API live at:   http://localhost:8000
  Auto-docs at:  http://localhost:8000/docs


================================================================================
PYTHON DEPENDENCIES (requirements.txt)
================================================================================

fastapi          Web framework
uvicorn          ASGI server
supabase         Supabase Python client (used in seed.py)
sqlalchemy       ORM
asyncpg          Async PostgreSQL driver for SQLAlchemy
pydantic         Request/response validation (built into FastAPI)
python-jose      JWT decode for auth middleware
httpx            Async HTTP client (used in tests)
pytest           Testing


================================================================================
DIVISION OF LABOR
================================================================================

SHABEER — API & Database
  - Supabase project setup: create the 4 tables, set RLS policies
  - models/ and database.py
  - routers/lots.py, routers/admin.py, routers/feedback.py, routers/events.py
  - routers/websocket.py — 30-second broadcast loop
  - auth.py JWT middleware
  - docker-compose.yml for local dev
  - Deployment to Render.com

SAMI — Mock Data & Intelligence
  - Generate mock/occupancy_history.csv using the formula above
  - Compile mock/lots.json (real GMU coordinates from Google Maps)
  - Compile mock/events.json (~20 campus events)
  - Write mock/seed.py
  - services/occupancy.py, services/prediction.py, services/recommendation.py
  - routers/predictions.py, routers/recommendations.py
  - tests/test_api.py — smoke tests for every endpoint

SHARED (Day 1 Priority)
  - schemas/ — agree on ALL Pydantic response shapes before either person writes a router
  - README with local setup instructions
  - Integration testing with iOS team in Weeks 2–3


================================================================================
4-WEEK BUILD SCHEDULE
================================================================================

WEEK 1
  Shabeer: Supabase tables + RLS. /lots GET returning seeded data. docker-compose running.
  Sami:    Generate all mock files. Write and run seed.py against Shabeer's DB.
  Together: Agree on all Pydantic schemas on Day 1. iOS can hit /lots by end of week.

WEEK 2
  Shabeer: /lots/{id}, /lots/{id}/history, /lots/{id}/floors. Auth middleware. Admin PATCH.
  Sami:    services/occupancy.py + prediction.py. Wire up /predictions endpoint.
  Together: iOS map screen pulling real (mock) data. Verify JSON shapes match frontend.

WEEK 3
  Shabeer: WebSocket hub — 30-second occupancy broadcast. /feedback POST. /events GET.
  Sami:    services/recommendation.py. /recommendations endpoint. Tune event bump logic.
  Together: Full user flow demo-able end to end:
            Home → Map → Lot Detail → Prediction → Feedback

WEEK 4
  Shabeer: Deploy to Render.com with HTTPS. Final bug fixes and README polish.
  Sami:    Smoke tests for all endpoints. Seed data tuned for demo time window.
  Together: Full dry-run of demo script against production URL.
            iOS app points to prod. No localhost during demo.


================================================================================
KEY RISKS & MITIGATIONS
================================================================================

RISK: Mock occupancy looks unconvincing during demo
FIX:  Tune seed data so the demo hour (e.g. 10 AM Tuesday) shows a realistic
      mix of green/yellow/red across lots — not all one color.

RISK: WebSocket adds Week 1 complexity
FIX:  Start with a polling fallback: iOS calls GET /lots every 30 seconds.
      Add WebSocket in Week 3 once the rest is stable.

RISK: Supabase RLS accidentally blocks API calls
FIX:  Use service role key server-side (bypasses RLS entirely).
      RLS only matters for direct browser/client queries, not our API.

RISK: iOS and backend disagree on JSON shapes
FIX:  Lock Pydantic schemas on Day 1 and share as a spec.
      iOS mocks against the spec immediately so both teams work in parallel.

RISK: Render deployment breaks the day before the demo
FIX:  Deploy to Render at end of Week 3.
      Demo against production from Week 4 onward — never localhost during demo.


================================================================================
NOTES FOR CURSOR / AI CODING ASSISTANT
================================================================================

- Keep the architecture flat. Do not add new abstraction layers without discussion.
- The services/ layer should stay thin. No direct DB calls from routers — always
  go through a service function.
- All secrets come from .env via config.py (Pydantic BaseSettings). Never hardcode.
- Use async/await throughout. All DB access uses async SQLAlchemy + asyncpg.
- Pydantic schemas in schemas/ are the contract with the iOS team. Do not change
  field names or types without coordinating with the frontend.
- The occupancy_snapshots table is the single source of truth for all occupancy
  data — current display, history graphs, predictions, and recommendations all
  read from it. Keep this in mind when debugging or modifying data flow.
- The WebSocket in routers/websocket.py should re-query the DB on each 30-second
  tick so admin overrides are reflected automatically without any extra logic.
- seed.py must remain idempotent. Always check for existence before inserting.
- When in doubt, keep it simple. This is a demo MVP, not a production system.
# EngageIU : Campus Event Attendance Leaderboard

Built for the **Luddy Hacks 24-Hour Hackathon** : Dynamic Leaderboard/Ranking System case (Graduate Team).

Students earn points by entering event check-in codes after attending IU events. A weekly leaderboard ranks participants by total points, with live updates via Server-Sent Events. Admins manage everything through a protected dashboard.

---

## Architecture

```
Browser (HTML / CSS / Vanilla JS)
        │
        │  HTTP REST  +  SSE (live updates)
        ▼
┌───────────────────────────────────────┐
│  FastAPI  (Python 3.11)               │
│  ├─ POST  /add          ← required    │
│  ├─ DELETE /remove      ← required    │
│  ├─ GET  /leaderboard   ← required    │
│  │       ?format=html   ← HTML table  │
│  │       /stream        ← SSE / live  │
│  │       /export        ← CSV export  │
│  ├─ GET  /info          ← required    │
│  ├─ GET  /performance   ← required    │
│  ├─ GET  /history       ← grad req    │
│  ├─ GET/POST /events    ← admin       │
│  ├─ POST /checkin       ← public      │
│  └─ POST /auth/login    ← JWT         │
│                                       │
│  Performance middleware (auto-log)    │
│  StaticFiles → frontend/              │
└──────────────┬────────────────────────┘
               │  SQLAlchemy 2.0
               ▼
        PostgreSQL 16
        ├─ students
        ├─ events
        ├─ attendance
        └─ endpoint_performance
```

---

## Quick Start

### Docker (recommended)

```bash
git clone <repo-url>
cd engageiu
docker-compose up --build
```

- App: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Admin panel: http://localhost:8000/admin

### Without Docker

```bash
# Requires PostgreSQL running locally
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Set the database URL via environment variable if your credentials differ:
```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/engageiu
```

**Default admin credentials:**
- Username: `admin`
- Password: `engageiu2025`

Override via env: `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SECRET_KEY`

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | — | Admin login, returns JWT bearer token |
| **POST** | **`/add`** | Admin | Add a check-in entry to the leaderboard |
| **DELETE** | **`/remove`** | Admin | Remove a check-in entry |
| **GET** | **`/leaderboard`** | Public | Top 10 weekly rankings (JSON or `?format=html`) |
| GET | `/leaderboard/stream` | Public | Live updates via Server-Sent Events |
| GET | `/leaderboard/export` | Public | Full leaderboard download as CSV |
| **GET** | **`/info`** | Public | Full score statistics (mean, median, std dev, percentile ranks, distribution) |
| **GET** | **`/performance`** | Admin | Average response time per endpoint |
| **GET** | **`/history`** | Admin | Timestamped check-in log with date/user filtering |
| GET | `/events` | Public/Admin | List events (admin sees check-in codes) |
| POST | `/events` | Admin | Create event with auto-generated check-in code |
| PATCH | `/events/{id}` | Admin | Update event details or regenerate code |
| DELETE | `/events/{id}` | Admin | Delete event |
| POST | `/checkin` | Public | Student self check-in with event code |
| GET | `/students/search` | Public | Search students by name or username |

**Explore interactively:** [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)

---

## Key Features

**Live Leaderboard**
- Leaderboard updates in real time via SSE (`/leaderboard/stream`) — no page refresh needed
- LIVE badge on the homepage pulses green when connected, turns gray on disconnect with auto-reconnect

**Achievement Badges**
- Each leaderboard row shows earned badges: 👑 Top, 📈 Rising (most improved from last week), ⚡ Dedicated (3+ events this week), ⭐ Consistent (active last week too)

**Rank Trend Arrows**
- Up/down arrows next to each rank number show week-over-week rank change
- NEW label for first-time entrants

**Multiple Leaderboard Formats**
- JSON API (default)
- HTML table: `/leaderboard?format=html`
- CSV download: `/leaderboard/export`

**Extended Statistics (`/info`)**
- Mean, median, Q1, Q3, min, max
- Standard deviation, variance, IQR, range
- Percentile ranks (P25, P50, P75, P90 via ceiling-index formula)
- Score distribution (histogram buckets)
- Category breakdown, top campus, most active day, most attended event

**Admin Dashboard**
- Protected by JWT authentication
- Tabs: Leaderboard, Statistics, Performance, History, Events
- QR code generation for each event's check-in code (scan to check in)
- Full CRUD for events

---

## Student Check-In Flow

1. Student attends a real IU event
2. Admin shares the event's check-in code (from admin panel, also available as QR code)
3. Student visits EngageIU → clicks **Check In Now**
4. Enters: Full Name, IU Username, Campus, Event Code
5. System validates code, records attendance, returns rank and points earned
6. Leaderboard updates live (SSE pushes within 2 seconds)

---

## Graduate Requirements

| Requirement | Status | Details |
|-------------|--------|---------|
| `/history` with filtering | Done | Filters: `name`, `iu_username`, `category`, `start_date`, `end_date`; paginated |
| Docker containerization | Done | `Dockerfile` + `docker-compose.yml` with PostgreSQL 16 health check |
| `/info` extended stats | Done | std_deviation, variance, IQR, percentile_ranks (P25–P90), score_distribution, category_breakdown |
| OpenAPI YAML | Done | `openapi.yaml` in project root — covers all required endpoints |

---

## Technical Notes

- **Statistics**: All computed in pure Python (`backend/utils/stats.py`) — no numpy or scipy
- **Frontend**: Plain HTML, CSS, vanilla JavaScript — no frameworks
- **Database aggregation**: Leaderboard `GROUP BY + SUM` runs entirely in PostgreSQL, no Python-side aggregation
- **Check-in codes**: Generated with Python's `secrets` module (cryptographically secure), 8-char alphanumeric
- **Timestamps**: Stored and returned as ISO 8601 UTC; frontend converts to local time display
- **Input validation**: Pydantic field validators enforce non-blank names, valid campus values, lowercase usernames
- **Performance tracking**: Middleware auto-logs every request (path, method, response_time_ms) to the database

---

## Project Structure

```
engageiu/
├── backend/
│   ├── main.py              # FastAPI app, CORS, performance middleware
│   ├── models.py            # SQLAlchemy models (Student, Event, Attendance, ...)
│   ├── database.py          # Engine, session, init_db
│   ├── seed.py              # Demo data seeded on first run
│   ├── requirements.txt
│   ├── routers/
│   │   ├── auth.py          # JWT login
│   │   ├── leaderboard.py   # /add /remove /leaderboard /info /performance /history
│   │   └── events.py        # /events /checkin /students
│   └── utils/
│       └── stats.py         # Pure-Python statistics
├── frontend/
│   ├── index.html           # Leaderboard (public)
│   ├── events.html          # Event listing (public)
│   ├── analytics.html       # Statistics visualization (public)
│   ├── admin.html           # Admin dashboard (protected)
│   └── assets/
│       ├── style.css
│       └── app.js
├── openapi.yaml             # OpenAPI 3.0.3 spec
├── Dockerfile
├── docker-compose.yml
└── README.md
```

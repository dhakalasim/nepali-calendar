# Nepali Calendar

A Bikram Sambat (BS) + Gregorian (AD) calendar where you add important dates and
get **email reminders** before they arrive. Nepali festivals and public holidays
come pre-loaded.

- **Backend** – Python / FastAPI, SQLAlchemy, APScheduler
- **Database** – PostgreSQL
- **Frontend** – React (Vite)
- **Date conversion** – [`nepali-datetime`](https://pypi.org/project/nepali-datetime/)

![stack](https://img.shields.io/badge/FastAPI-009688) ![stack](https://img.shields.io/badge/PostgreSQL-4169E1) ![stack](https://img.shields.io/badge/React-61DAFB)

---

## Quick start (Docker)

```bash
git clone <this-repo> nepali-calendar && cd nepali-calendar
cp .env.example .env          # optional – only needed for real emails
docker compose up --build
```

| Service        | URL                          |
| -------------- | ---------------------------- |
| Frontend       | http://localhost:5273        |
| API            | http://localhost:8200/api    |
| API docs       | http://localhost:8200/docs   |
| Postgres       | localhost:5532 (`nepcal`/`nepcal`) |

Holidays are seeded automatically on first boot.

> Non-standard host ports (5273 / 8200 / 5532) are the defaults on purpose, so
> the stack doesn't collide with other local dev servers on 5173 / 8000 / 5432.
> Change them any time:
> ```bash
> FRONTEND_PORT=5173 BACKEND_PORT=8000 DB_PORT=5432 docker compose up
> ```

> `.env` is optional. Without SMTP settings the app still runs and reminder
> emails are **printed to the backend console** so you can see exactly what
> would be sent.

---

## Quick start (without Docker)

> Uses the standard ports 5432 / 8000 / 5173 – make sure nothing else is on them
> (or adjust the commands).

**1. Postgres** – have a database reachable, e.g.

```bash
docker run -d --name nepcal-db -p 5432:5432 \
  -e POSTGRES_USER=nepcal -e POSTGRES_PASSWORD=nepcal -e POSTGRES_DB=nepcal \
  postgres:16-alpine
```

**2. Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://nepcal:nepcal@localhost:5432/nepcal"
python -m app.seed                       # create tables + load holidays
uvicorn app.main:app --reload            # http://localhost:8000
```

**3. Frontend**

```bash
cd frontend
npm install
npm run dev                              # http://localhost:5173
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

---

## Enabling email reminders

Edit `.env` (see `.env.example`). For Gmail, create an
[App Password](https://myaccount.google.com/apppasswords):

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFY_TO=you@gmail.com
NOTIFY_HOUR=7
```

Restart the backend. A background job runs every day at `NOTIFY_HOUR`
(Asia/Kathmandu) and emails **one digest** listing every event that has entered
its reminder window (`notify_days_before`). Each reminder is sent once —
`notification_log` prevents duplicates.

Trigger it by hand any time:

```bash
curl -X POST http://localhost:8200/api/notifications/run
# pretend it is a different day:
curl -X POST "http://localhost:8200/api/notifications/run?as_of=2025-09-30"
```

Or click **🔔 Reminders** in the UI for a dry-run preview.

---

## How dates work

- Every event stores a canonical **AD date**; the matching **BS year/month/day**
  is kept alongside it for display and recurrence.
- **Repeat options**
  - `One time only` – fixed date.
  - `Every year (same English date)` – birthdays, anniversaries (AD-fixed).
  - `Every year (same Nepali date)` – e.g. Nepali New Year, always Baishakh 1.
- The month grid is a **BS month**; each day also shows its AD day, with
  weekends (Saturday) and holidays highlighted.

### Seeded holidays

`backend/data/holidays.json` holds two groups:

| Group          | Recurrence  | Reliability                                    |
| -------------- | ----------- | ---------------------------------------------- |
| `recurring_bs` | `yearly_bs` | Fixed BS date – accurate every year            |
| `dated`        | `none`      | Lunar festivals for 2025–2027 – **verify** against an official patro |

Everything seeded is marked `source = "seed"` and can be edited or deleted in
the app.

---

## API

| Method | Path                                | Purpose                              |
| ------ | ----------------------------------- | ----------------------------------- |
| GET    | `/api/today`                        | Today in BS + AD                    |
| GET    | `/api/convert?ad_date=YYYY-MM-DD`   | Convert AD ↔ BS                     |
| GET    | `/api/calendar?year=&month=`        | A BS month grid with events         |
| GET    | `/api/events`                       | List events                         |
| POST   | `/api/events`                       | Create (`ad_date` or `bs`)          |
| PUT    | `/api/events/{id}`                  | Update                              |
| DELETE | `/api/events/{id}`                  | Delete                             |
| GET    | `/api/events/upcoming?days=`        | Upcoming occurrences (expanded)     |
| GET    | `/api/notifications/status`         | SMTP / scheduler state              |
| GET    | `/api/notifications/preview`        | What the next run would send        |
| POST   | `/api/notifications/run`            | Send the digest now                 |
| GET    | `/api/notifications/log`            | Sent-reminder history               |

Full interactive docs at `/docs`.

---

## Tests

```bash
cd backend && pytest
```

Covers BS↔AD conversion round-trips, month lengths, and recurrence expansion.

---

## Project layout

```
backend/
  app/
    main.py            FastAPI app + lifespan (scheduler)
    config.py          env-driven settings
    database.py        engine / session / init_db
    models.py          Event, NotificationLog
    schemas.py         Pydantic models
    nepali_date.py     BS <-> AD helpers
    recurrence.py      expand events into occurrences
    crud.py            event DB operations
    seed.py            load data/holidays.json
    routers/           calendar, dates, events, notifications
    notifications/     email, templates, service, scheduler
  data/holidays.json
  tests/
frontend/
  src/
    App.jsx
    api.js
    constants.js
    components/        Header, CalendarGrid, DayCell, Sidebar, EventModal
docker-compose.yml
```

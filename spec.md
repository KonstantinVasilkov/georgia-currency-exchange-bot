**Telegram Currency Exchange Bot - Developer Specification**

---

### 1. Overview

This project involves building a Telegram bot that provides real-time currency exchange services with location-based features, conversion tools, and rate comparisons. The system will prioritize correctness, privacy, and simplicity in both UX and architecture.

---

### 2. Core Features

#### 2.1 Exchange Rates
- Pull best exchange rates and provider-specific rates via the MyFin API.
- Sync data hourly via cron job.
- Store only the **most recent** rates per office and currency.
- Discard any rates older than **3 hours**.
- Show both **buy** and **sell** rates, and always display **NBG rates** at the top as a reference.

#### 2.2 Location-Based Services
- Users share their location through Telegram.
- The bot replies with an **inline keyboard** prompting:
  - Nearest exchange office
  - Best rate for a specific currency
  - Nearest office of a specific organization
- Offices shown must have fresh rates (<= 3 hours old).
- Directions returned as **Google Maps links** (default mode).
- Organization lookup supports **fuzzy matching**.

#### 2.3 Conversion Tool
- Stateless conversion (user provides source, target, and amount).
- Supports any-to-any conversion (e.g., USD -> EUR) via GEL.
- Limited to **two decimal places**.
- Returns an error message if any required rate is missing or outdated.

#### 2.4 User Interaction
- Stateless interaction: No user data stored.
- All messages guided by **inline keyboards and prompts**.
- Unknown messages return a fallback: "Please use the buttons below."

---

### 3. Error Handling & Monitoring

- Use **Python logging** with proper levels.
- Integrate with **Sentry** for critical failures.
- Background task failures (e.g., geocoding or sync) are logged and reported.
- If the bot starts with **no fresh rates (<3h)**, it sends a warning to users and reports to Sentry.

---

### 4. Technology Stack

- **Language**: Python 3.12
- **Project Manager**: `uv` (for envs and dependencies)
- **Bot Framework**: `aiogram` 3.x with router-based architecture
- **Async HTTP Client**: `aiohttp`
- **Database**: SQLite with SQLModel + SQLAlchemy + Alembic
- **Scheduling**: Cron inside a Docker container
- **Containerization**: Docker & Docker Compose
- **Deployment**: AWS EC2
- **Configuration**: `.env` file + `pydantic.BaseSettings`

---

### 5. Monorepo Structure

```
repo/
├── config/             # .env loader and settings management
├── db/
│   ├── models/         # SQLModel models (Office, Organization, Rate)
│   ├── repositories/   # Repository classes for DB operations
│   └── session.py      # DB engine and session handling
├── services/           # Business logic classes
│   ├── CurrencyService
│   ├── GeolocationService
│   ├── ConversionService
│   └── SyncService
├── bot/
│   ├── routers/        # aiogram routers (conversion, location, rates, fallback)
│   └── keyboards/      # Inline keyboard builders
├── main.py             # Entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

### 6. Data Management

- **Rates**:
  - Fetched hourly
  - Updated only if timestamps are newer
  - Stored with `time` and `timeFrom` fields
  - Discarded if older than 3 hours

- **Offices**:
  - Persisted with Google geocoded coordinates
  - Coordinates stored only once unless address changes
  - Offices not in API response marked `is_active: false`

- **Organizations**:
  - Tracked separately
  - Also soft-deactivated if removed from API response

- **Geocoding**:
  - If fails, log error to Sentry
  - Office saved with null coords and excluded from geo queries

---

### 7. Bot Behavior Summary

- Stateless design: no storage of user IDs or locations
- Currency selection required for every query
- Rates and office results filtered by 3-hour freshness
- Always returns a single best result per user query

---

### 8. Testing Plan

- Framework: `pytest` only
- Test type: **Integration tests only**
- Focus areas:
  - Currency sync flow and DB updates
  - Conversion accuracy and GEL routing logic
  - Location matching and geocoding fallback
  - Telegram interaction logic via aiogram test client

```
tests/
├── conftest.py
├── test_sync.py
├── test_conversion.py
├── test_geo.py
└── test_bot.py
```

---

### 9. Deployment Notes

- Bot and scheduler run in **separate containers** via Docker Compose
- SQLite DB is **persisted via host-mounted volume**
- No external API is exposed
- Sentry DSN, API tokens, and city name provided via `.env`
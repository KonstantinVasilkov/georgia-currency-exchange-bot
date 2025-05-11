# Georgia Currency Exchange Bot

A Telegram bot providing real-time currency exchange rates, location-based office search, and conversion tools for Georgia. The system is designed for correctness, privacy, and simplicity, with a modular, testable architecture.

---

## Features

- **Exchange Rates:**
  - Fetches best and provider-specific rates via the MyFin API
  - Always displays National Bank of Georgia (NBG) rates as reference
  - Syncs data hourly and stores only the most recent rates per office/currency
  - Discards rates older than 3 hours
- **Location-Based Services:**
  - Users can share their location to find the nearest exchange office or best rates
  - Inline keyboards guide all user interactions
  - Google Maps and Apple Maps links for office directions
- **Conversion Tool:**
  - Stateless currency conversion (any-to-any via GEL)
  - Two decimal places, error on missing/outdated rates
- **Stateless, Privacy-First:**
  - No user data is stored
  - All interactions are guided by inline keyboards and prompts
- **Robust Error Handling:**
  - Python logging throughout
  - Sentry integration for critical failures
  - Warnings if no fresh rates are available
- **Testing:**
  - Comprehensive unit and integration tests using pytest
  - Mocks and fixtures for all external dependencies

---

## Project Structure

```
repo/
├── src/
│   ├── bot/                # Telegram bot routers and keyboards
│   ├── config/             # Settings, logging, and .env management
│   ├── db/                 # Models, session, and migrations
│   ├── external_connectors/# MyFin API connector and schemas
│   ├── repositories/       # Repository pattern for data access
│   ├── schemas/            # Pydantic models for validation
│   ├── scheduler/          # APScheduler-based background tasks
│   ├── services/           # Business logic (currency, sync, etc.)
│   ├── utils/              # Utilities (HTTP, datetime, etc.)
│   ├── start_bot.py        # Bot entrypoint
│   └── start_sync.py       # Sync/scheduler entrypoint
├── tests/                  # Unit and integration tests (pytest only)
├── .env.dev                # Example environment variables
├── pyproject.toml          # Dependencies and tool config
├── alembic.ini             # DB migrations
├── Makefile                # Common dev commands
└── README.md
```

---

## Architecture & Design Principles

- **Modular, Layered Design:**
  - Source code is organized by responsibility (bot, services, repositories, etc.)
  - Business logic is in the service layer; controllers/routers are thin
  - Data access via repository pattern, injected into services
  - Pydantic models for all data validation
- **Dependency Injection:**
  - All services and repositories are passed explicitly as arguments
- **Configuration Management:**
  - All secrets and config via environment variables (`.env` files)
  - Managed with Pydantic `BaseSettings` in `src/config/settings.py`
- **Error Handling & Logging:**
  - Structured logging throughout
  - Sentry integration for production error reporting
- **Testing:**
  - All tests use `pytest` (no unittest)
  - Mocks for external APIs and DB
  - Coverage for business logic, bot flows, and sync
- **Code Style:**
  - Follows PEP8/PEP257, enforced by Ruff
  - Type hints everywhere, explicit argument passing
  - Descriptive variable/function names

---

## Setup & Installation

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd georgia-currency-exchange-bot
   ```
2. **Install [uv](https://github.com/astral-sh/uv) and create a virtual environment:**
   ```sh
   uv venv .venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   - Copy `.env.dev` to `.env` and fill in your secrets (Telegram token, Sentry DSN, etc.)
4. **Run database migrations:**
   ```sh
   alembic upgrade head
   ```

---

## Running the Bot and Sync Service

- **Start the Telegram bot:**
  ```sh
  python src/start_bot.py
  ```
- **Start the sync/scheduler service:**
  ```sh
  python src/start_sync.py
  ```
- **Both can be run in separate containers (see Dockerfile/docker-compose.yml if present)**

---

## Testing

- **Run all tests:**
  ```sh
  pytest
  ```
- **Run with coverage:**
  ```sh
  pytest --cov=src
  ```
- **Type checking:**
  ```sh
  mypy src/
  ```
- **Linting:**
  ```sh
  ruff check src/
  ```

---

## Contribution & Code Style

- Use explicit argument passing and type hints everywhere
- Organize code by responsibility (services, repositories, routers, etc.)
- All new code must include docstrings and follow PEP257
- All tests must use pytest (no unittest)
- Run `mypy` and `ruff` before submitting PRs
- Add or update tests for all new features

---

## Configuration Reference

- All configuration is managed via environment variables (see `.env.dev` for example):
  - `TELEGRAM_BOT_TOKEN`: Telegram bot token
  - `DATABASE_URL`: SQLite DB URL
  - `SENTRY_DSN`: Sentry DSN for error reporting
  - `MYFIN_API_BASE_URL`: MyFin API endpoint
  - `ENVIRONMENT`, `DEBUG`, etc.

---

## License

This project is licensed under the MIT License.
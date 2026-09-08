# Georgia Currency Exchange Bot

[![CI](https://github.com/KonstantinVasilkov/georgia-currency-exchange-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/KonstantinVasilkov/georgia-currency-exchange-bot/actions/workflows/ci.yml)

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
├── docs/                   # Spec, refactoring and coverage plans
├── .github/workflows/      # CI: ruff, mypy, pytest
├── .env.example            # Example environment variables (copy to .env.dev)
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
   git clone https://github.com/KonstantinVasilkov/georgia-currency-exchange-bot.git
   cd georgia-currency-exchange-bot
   ```
2. **Install [uv](https://github.com/astral-sh/uv) and sync the environment** (creates `.venv` and installs all dependencies, including dev tools):
   ```sh
   uv sync
   ```
3. **Configure environment variables:**
   - Copy `.env.example` to `.env.dev` and fill in your Telegram bot token (and Sentry DSN if you use it). Settings are loaded from `.env.dev` at runtime and from `.env.test` under pytest.
4. **Run database migrations:**
   ```sh
   uv run alembic upgrade head
   ```

---

## Running the Bot and Sync Service

- **Start the Telegram bot:**
  ```sh
  make start_bot        # uv run python -m src.start_bot
  ```
- **Start the sync/scheduler service:**
  ```sh
  make start_sync       # uv run python -m src.start_sync
  ```
- Both processes are independent and can run in separate containers.

---

## Testing

- **Run all tests:**
  ```sh
  make test             # uv run pytest -v
  ```
- **Run with coverage:**
  ```sh
  make test_with_coverage
  ```
- **Type checking and linting:**
  ```sh
  make lint             # ruff check --fix + mypy
  make format           # ruff format
  ```
- The same checks run in GitHub Actions on every push and pull request (`.github/workflows/ci.yml`).

---

## Project Documentation

Design notes live in [`docs/`](docs/): the original [developer specification](docs/spec.md), the [refactoring plan](docs/refactoring_plan.md) and [checklist](docs/refactoring_todo.md), and the [test coverage plan](docs/coverage_plan.md).

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

- All configuration is managed via environment variables (see `.env.example`):
  - `TELEGRAM_BOT_TOKEN`: Telegram bot token
  - `DATABASE_URL`: SQLite DB URL
  - `SENTRY_DSN`: Sentry DSN for error reporting
  - `MYFIN_API_BASE_URL`: MyFin API endpoint
  - `ENVIRONMENT`, `DEBUG`, etc.

---

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
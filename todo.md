# Todo Checklist

Below is a comprehensive checklist for building the Telegram Currency Exchange Bot. Use it as a guide to track progress across all steps. Each item can be checked off once completed.

---

## **1. Project Initialization**

- [ ] **1.1 Create Monorepo Structure**  
  - [ ] Create the `repo/` directory.  
  - [ ] Inside `repo/`, create subdirectories:  
    - `bot/`  
    - `services/`  
    - `db/models/`  
    - `db/repositories/`  
    - `db/migrations/`  
    - `config/`  
    - `tests/`  
  - [ ] Add an empty `main.py` at `repo/` root.  
  - [ ] Create a `.gitignore` that ignores Python caches and env files.  
  - [ ] Verify the structure matches the requirement.

- [ ] **1.2 Create Minimal `README.md`**  
  - [ ] Summarize the Telegram Currency Exchange Bot.  
  - [ ] Mention core features (real-time rates, location-based services, conversion).  
  - [ ] Add a "Getting Started" section (placeholder).  
  - [ ] Add a "License" section (MIT or other).

- [ ] **1.3 Set Up Environment & Basic Dependencies**  
  - [ ] Create and activate a Python virtual environment (via `uv` or `venv`).  
  - [ ] Add dependencies to `requirements.txt` or similar:
    - `aiogram==3.*`
    - `SQLModel==0.*`
    - `pydantic==2.*`
    - `aiohttp`
    - `rapidfuzz`
    - `alembic`
    - `pytest`
  - [ ] Install dependencies with `pip install -r requirements.txt` (or `uv sync`).

- [ ] **1.4 Minimal `main.py`**  
  - [ ] In `main.py`, add a simple `if __name__ == "__main__": print("Hello, Telegram Bot!")`.
  - [ ] Run `python main.py` to confirm output.

---

## **2. Database Setup**

- [ ] **2.1 DB Engine & Session**  
  - [ ] Create `db/session.py` with `get_engine()` using `create_engine`.  
  - [ ] Define a sessionmaker (e.g., `SessionLocal`).  
  - [ ] Use environment variables or default for `DB_URL`.  
  - [ ] Confirm the file loads without errors.

- [ ] **2.2 SQLModel Models**  
  - [ ] Create `db/models/office.py` with `Office(SQLModel, table=True)`.  
  - [ ] Create `db/models/organization.py` with `Organization(SQLModel, table=True)`.  
  - [ ] Create `db/models/rate.py` with `Rate(SQLModel, table=True)`.  
  - [ ] Add primary keys and foreign keys (e.g., `Rate.office_id -> Office.id`).  
  - [ ] Ensure fields align with the specification (timestamps, is_active, etc.).

- [ ] **2.3 Alembic Initialization**  
  - [ ] Run `alembic init db/migrations`.  
  - [ ] Modify `alembic.ini` and `env.py` to reference the engine from `db/session.py`.  
  - [ ] Ensure Alembic can detect model changes.

- [ ] **2.4 Initial Migration**  
  - [ ] Autogenerate a migration: `alembic revision --autogenerate -m "Initial tables"`.  
  - [ ] Inspect the migration script to confirm correct table creation.  
  - [ ] Run `alembic upgrade head` to apply.

- [ ] **2.5 Verify DB Creation**  
  - [ ] Write a small Python snippet to confirm tables exist (e.g., `session.exec(select(Office)).all()`).  
  - [ ] Check for errors or warnings.

---

## **3. Data Sync (MyFin API)**

- [ ] **3.1 Basic `SyncService`**  
  - [ ] Create `services/SyncService.py`.  
  - [ ] Define `async def sync_exchange_data()`, currently just prints a message.  
  - [ ] Confirm file imports cleanly.

- [ ] **3.2 Fetch Data with `aiohttp`**  
  - [ ] Open `aiohttp.ClientSession` in `sync_exchange_data()`.  
  - [ ] Make GET request to a mock MyFin URL (placeholder).  
  - [ ] Parse JSON and store in a variable (no DB logic yet).

- [ ] **3.3 Parse & Upsert to DB**  
  - [ ] After JSON fetch, create/update `Office`, `Organization`, and `Rate` records.  
  - [ ] Use DB session from `db/session.py`.  
  - [ ] Handle partial data or duplicates gracefully.

- [ ] **3.4 Mark Stale Entities**  
  - [ ] After processing new data, query DB for all offices/organizations.  
  - [ ] Set `is_active=False` if they weren’t in the latest fetch.

- [ ] **3.5 Cleanup Old Rates**  
  - [ ] Delete `Rate` records older than 3 hours (`timestamp < now - 3h`).  
  - [ ] Confirm deletion or toggling logic meets spec.

---

## **4. Geolocation & Fuzzy Matching**

- [ ] **4.1 `GeolocationService`**  
  - [ ] Create `services/GeolocationService.py`.  
  - [ ] Implement `async def geocode_address(address: str) -> tuple[float, float]`.  
  - [ ] For now, mock or placeholder the Google Geocoding API.  
  - [ ] If fail, log to Sentry (placeholder) and return `(None, None)`.

- [ ] **4.2 Integrate Geocoding in Sync**  
  - [ ] In `SyncService.py`, call `geocode_address()` for new/updated offices.  
  - [ ] Store `lat/lng` in `Office`.

- [ ] **4.3 Fuzzy Matching**  
  - [ ] Create a function `search_organization(query: str) -> Organization`.  
  - [ ] Use `rapidfuzz` or similar.  
  - [ ] Return best match if above threshold.

---

## **5. Bot Foundations**

- [ ] **5.1 Initialize Aiogram**  
  - [ ] In `main.py`, import `Bot`, `Dispatcher` from `aiogram`.  
  - [ ] Create a `Bot` instance with placeholder token.  
  - [ ] Create a `Dispatcher`, run polling.

- [ ] **5.2 `/start` Command**  
  - [ ] Create `bot/routers/start.py`.  
  - [ ] Add `/start` handler returning "Welcome to the Currency Exchange Bot!".  
  - [ ] Register router in `main.py`.

- [ ] **5.3 Local Test**  
  - [ ] Run `python main.py`.  
  - [ ] Test `/start` in Telegram.  
  - [ ] Confirm response.

- [ ] **5.4 Unknown Commands Handler**  
  - [ ] Add a message handler for unrecognized text.  
  - [ ] Reply with "Please use the buttons below."

---

## **6. Conversion Logic**

- [ ] **6.1 `ConversionService`**  
  - [ ] Create `services/ConversionService.py` with `convert(amount, from_curr, to_curr) -> float`.  
  - [ ] Query DB for relevant rates.  
  - [ ] Convert via GEL.

- [ ] **6.2 Rounding & Missing Data**  
  - [ ] If rate is missing/outdated (>3h), raise an exception.  
  - [ ] Otherwise, return `round(value, 2)`.

---

## **7. Inline Keyboards & Bot Features**

- [ ] **7.1 Create Inline Keyboards**  
  - [ ] In `bot/keyboards/inline.py`, define `get_main_keyboard()` with buttons:
    - "Nearest Office"
    - "Best Rate for a Currency"
    - "Nearest Office for an Organization"

- [ ] **7.2 Routers for Conversion, Location, Rates**  
  - [ ] `bot/routers/conversion_router.py` (handles currency queries).  
  - [ ] `bot/routers/location_router.py` (handles location-based logic).  
  - [ ] `bot/routers/rates_router.py` (handles best-rate queries).

- [ ] **7.3 Integrate Routers & Keyboards**  
  - [ ] Register new routers in `main.py`.  
  - [ ] Adjust `/start` command to display the inline keyboard.

- [ ] **7.4 Interactive Testing**  
  - [ ] Run the bot.  
  - [ ] Tap each inline button, confirm correct response.  
  - [ ] Check location, rates, and conversions in practice.

---

## **8. Error Handling & Monitoring**

- [ ] **8.1 Logging Config**  
  - [ ] In `config/logging_config.py`, set up a standard `dictConfig`.  
  - [ ] Separate levels for DEBUG, INFO, WARNING, ERROR.

- [ ] **8.2 Sentry Integration**  
  - [ ] In `config/settings.py`, load `SENTRY_DSN` from `.env`.  
  - [ ] If present, `sentry_sdk.init(dsn=SENTRY_DSN)`.

- [ ] **8.3 Exception Logging**  
  - [ ] Wrap `sync_exchange_data()` in try/except, log exceptions to Sentry.  
  - [ ] Add a top-level error handler in the bot to log to Sentry.

- [ ] **8.4 Handle No Fresh Rates**  
  - [ ] In conversion/rates routers, if no rates <3h, warn user & log to Sentry.

---

## **9. Testing**

- [ ] **9.1 `test_sync.py`**  
  - [ ] Mock MyFin response.  
  - [ ] Call `sync_exchange_data()`.  
  - [ ] Assert DB updates (offices, rates).

- [ ] **9.2 `test_conversion.py`**  
  - [ ] Insert sample `Rate` records.  
  - [ ] Test `convert(100, "USD", "EUR")`.  
  - [ ] Check correctness with rounding.

- [ ] **9.3 Bot Flow Testing (Optional)**  
  - [ ] Use `aiogram` test client or manual testing.  
  - [ ] Confirm main flows function as expected.

---

## **10. Docker & Deployment**

- [ ] **10.1 `Dockerfile`**  
  - [ ] Use `python:3.12-slim` base.  
  - [ ] Copy code, install dependencies, run `main.py`.

- [ ] **10.2 `docker-compose.yml`**  
  - [ ] Define `bot` service.  
  - [ ] Define `sync` service (cron or scheduled script).  
  - [ ] Link volumes for DB persistence.

- [ ] **10.3 Volume Persistence**  
  - [ ] Verify SQLite file is mounted in a shared volume.  
  - [ ] Confirm data is retained across restarts.

- [ ] **10.4 Update `README.md` for Env Vars**  
  - [ ] Document `BOT_TOKEN`, `SENTRY_DSN`, `MYFIN_API_KEY`, etc.  
  - [ ] Add any geocoding keys or city config.

- [ ] **10.5 Deploy to AWS EC2**  
  - [ ] Set up EC2 instance (Ubuntu or Amazon Linux).  
  - [ ] Clone repo, set `.env`, run `docker-compose up -d`.  
  - [ ] Confirm bot is reachable and fully functional.

---

**Use this checklist** as a guide to ensure every step is completed before moving on. Each item corresponds to one of the iterative tasks discussed in the project plan, helping you track progress from initial setup to full deployment.

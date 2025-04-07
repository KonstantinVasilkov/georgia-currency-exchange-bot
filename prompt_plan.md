## **Round 1: High-Level Blueprint**

1. **Initialize Project**
   - Create folder structure.
   - Define environment and tool requirements (Python 3.12, `uv`, `aiogram`, etc.).
   - Establish a basic `README.md`.

2. **Set Up Database**
   - Choose SQLite for local development.
   - Create a minimal table structure for offices, organizations, and rates.
   - Configure Alembic migrations.

3. **Implement Data Sync**
   - Create a SyncService to fetch data from MyFin API.
   - Set up logic to parse, store, and refresh exchange rates.
   - Implement a cleanup for old data (>3 hours).

4. **Geolocation & Fuzzy Matching**
   - Integrate a geocoding library or Google Geocoding (if possible, else mock).
   - Store office coordinates, with fallback if geocoding fails.
   - Implement fuzzy matching for organization lookups.

5. **Bot Foundations**
   - Implement a basic `aiogram` bot using routers.
   - Add a simple inline keyboard for testing.
   - Return placeholder text.

6. **Conversion Logic**
   - Implement a ConversionService that relies on up-to-date rates.
   - Validate logic for any-currency-to-any-currency via GEL as an intermediary.
   - Round results to two decimals.

7. **Inline Keyboards & Telegram UX**
   - Build inline keyboards: 
     - “Nearest office” 
     - “Best rate for X currency”
     - “Nearest office for Organization X”
   - Integrate actual data from DB.

8. **Error Handling & Monitoring**
   - Configure logging with Python’s logging framework.
   - Integrate Sentry for critical error reporting.
   - Handle missing data gracefully.

9. **Testing**
   - Write integration tests with `pytest`.
   - Test SyncService, ConversionService, and basic bot flow.

10. **Docker & Deployment**
   - Build Docker images for the bot and the cron/sync container.
   - Finalize `.env` secrets with Sentry DSN, MyFin API key, etc.
   - Deploy to AWS EC2 with a mounted volume for the SQLite DB.

---

## **Round 2: Break Down the Steps Further**

1. **Project Initialization**
   1.1 Create the monorepo folder structure.  
   1.2 Add `requirements.txt` and set up `uv`/virtual env.  
   1.3 Create initial `README.md`.

2. **Database Setup**
   2.1 Initialize `db/session.py` with `SQLModel` engine setup.  
   2.2 Create `db/models` for `Office`, `Organization`, and `Rate`.  
   2.3 Write migration scripts with Alembic.  
   2.4 Configure a test script to ensure DB creation/migration works.

3. **Data Sync (MyFin API)**
   3.1 Implement `services/SyncService` with an async method to fetch MyFin data.  
   3.2 Parse JSON, map to DB models.  
   3.3 Upsert new or updated rates.  
   3.4 Mark stale offices/organizations as inactive.  
   3.5 Cleanup old rates (timestamp > 3 hours).

4. **Geolocation & Fuzzy Matching**
   4.1 Implement `services/GeolocationService` with geocoding calls.  
   4.2 Save lat/long in `Office`. Handle fallback on error.  
   4.3 Integrate a fuzzy search library (e.g., `rapidfuzz`) for organization name matching.  
   4.4 Add a test script to confirm geolocation/fuzzy works with example data.

5. **Bot Foundations**
   5.1 Set up `main.py` with an `aiogram` Bot and Dispatcher instance.  
   5.2 Add a simple router to respond to `/start`.  
   5.3 Ensure the bot can run and respond to a test message.

6. **Conversion Logic**
   6.1 Implement `services/ConversionService` that references `Rate` objects.  
   6.2 Include a function `convert(amount, from_currency, to_currency)`.  
   6.3 Round to two decimals, fallback if data is missing/outdated.

7. **Inline Keyboards & Bot Features**
   7.1 Create `bot/keyboards/inline.py` with helper functions for building menus.  
   7.2 Write separate routers for conversion, location, best-rate queries.  
   7.3 Integrate with DB for real results.

8. **Error Handling & Monitoring**
   8.1 Add logging configuration with `logging.config.dictConfig` or a standard config.  
   8.2 Integrate Sentry with DSN from `.env`.  
   8.3 Add graceful fallback for missing data (older than 3h).

9. **Testing**
   9.1 Write integration tests for SyncService DB updates.  
   9.2 Test ConversionService with mocked rates.  
   9.3 Test Telegram bot flows (where possible).

10. **Docker & Deployment**
   10.1 Write a `Dockerfile` for the bot container.  
   10.2 Write a second `Dockerfile` or single multi-stage for the cron job.  
   10.3 Provide `docker-compose.yml` to run both.  
   10.4 Document environment variables in `README.md`.  
   10.5 Deploy to AWS EC2, ensuring volumes are mounted to persist SQLite.

---

## **Round 3: Final, Detailed Steps**

Each step is now broken down enough to be approached safely while making tangible progress. Below is an even more granular plan:

1. **Project Initialization**  
   - **Step 1.1**: Create the folder structure (`repo/` with `bot/`, `services/`, `db/`, `config/`, etc.).  
   - **Step 1.2**: Add a minimal `README.md` with project overview.  
   - **Step 1.3**: Create and activate a virtual environment (via `uv` or `venv`), install basics (`aiogram`, `pydantic`, `SQLModel`, etc.).  
   - **Step 1.4**: Create an empty `main.py` that prints `"Hello, Telegram Bot!"`.

2. **Database Setup**  
   - **Step 2.1**: Add `db/session.py` to set up the engine with `SQLModel`.  
   - **Step 2.2**: Create `db/models/office.py`, `db/models/organization.py`, and `db/models/rate.py` with `SQLModel` classes.  
   - **Step 2.3**: Initialize Alembic (`alembic init`) and configure migrations in `db/migrations/`.  
   - **Step 2.4**: Write an initial migration script (auto-generated or manual).  
   - **Step 2.5**: Run `alembic upgrade head` to confirm DB creation.

3. **Data Sync (MyFin API)**  
   - **Step 3.1**: Create `services/SyncService.py` with an async function `sync_exchange_data()`.  
   - **Step 3.2**: Use `aiohttp` to fetch MyFin rates.  
   - **Step 3.3**: Parse the JSON response, upsert offices, organizations, and rates.  
   - **Step 3.4**: Mark stale offices/organizations as inactive if not in latest API data.  
   - **Step 3.5**: Implement a cleanup to remove or mark rates older than 3 hours.

4. **Geolocation & Fuzzy Matching**  
   - **Step 4.1**: Create `services/GeolocationService.py` with a function `geocode_address(address)` returning `(lat, lng)`.  
   - **Step 4.2**: Integrate or mock a geocoding API call. If fail, log to Sentry (placeholder).  
   - **Step 4.3**: In `SyncService`, call the geocoding service for new/updated offices to store coordinates.  
   - **Step 4.4**: Implement fuzzy matching with `rapidfuzz` in a helper function `search_organization(query)`.

5. **Bot Foundations**  
   - **Step 5.1**: Update `main.py` to instantiate the bot with `aiogram`.  
   - **Step 5.2**: Create a router in `bot/routers/start.py` that handles `/start`.  
   - **Step 5.3**: Register the router in `main.py`, run the bot, test the `/start` command.  
   - **Step 5.4**: Add a minimal error handler for unknown commands.

6. **Conversion Logic**  
   - **Step 6.1**: Create `services/ConversionService.py` with `convert(amount, from_curr, to_curr) -> float`.  
   - **Step 6.2**: The function queries the DB for the relevant rates, using GEL as the pivot.  
   - **Step 6.3**: Round to two decimals, handle missing/outdated data with an exception.

7. **Inline Keyboards & Bot Features**  
   - **Step 7.1**: Add `bot/keyboards/inline.py` with functions that build inline keyboards for:  
     1. Nearest office  
     2. Best rate for X currency  
     3. Nearest office for Organization X  
   - **Step 7.2**: Create separate routers in `bot/routers/`, e.g. `conversion_router.py`, `location_router.py`, `rates_router.py`.  
   - **Step 7.3**: In each router, handle user input (buttons or text) and call the relevant service.  
   - **Step 7.4**: Combine them into `main.py` with router registration. Test interactive flows.

8. **Error Handling & Monitoring**  
   - **Step 8.1**: Add a Python logging config in `config/logging_config.py`.  
   - **Step 8.2**: Integrate Sentry using a DSN from `.env`.  
   - **Step 8.3**: Ensure the bot logs critical errors and that sync tasks also log to Sentry on failure.  
   - **Step 8.4**: If no fresh rates (<3h), show a user-facing warning and log to Sentry.

9. **Testing**  
   - **Step 9.1**: Add `tests/` folder.  
   - **Step 9.2**: Write test scripts for SyncService (check DB updates, stale data).  
   - **Step 9.3**: Test ConversionService logic with sample rate data.  
   - **Step 9.4**: (Optional) Use `aiogram` test client or manual tests for basic bot commands.

10. **Docker & Deployment**  
   - **Step 10.1**: Write `Dockerfile` for the bot.  
   - **Step 10.2**: Write `docker-compose.yml` with separate services for bot and cron job (for `SyncService`).  
   - **Step 10.3**: Confirm volumes are mounted for persistent SQLite.  
   - **Step 10.4**: Document environment variables in `README.md`.  
   - **Step 10.5**: Deploy to AWS EC2, test end-to-end.

---

# **Code Generation Prompts**

Below are carefully scoped prompts for each step. The idea is that you can feed each prompt **in sequence** to a code-generation LLM. Each prompt references the previous steps’ code. Make sure to follow the order and integrate the newly generated code into your local repository before moving on.

---

## **Prompt for Step 1.1**

```text
**Objective**: Create the initial monorepo folder structure.

**Instructions**:
1. Create a `repo/` directory (adjust naming as needed).
2. Inside `repo/`, create the following subdirectories:
   - `bot/`
   - `services/`
   - `db/models/`
   - `db/repositories/`
   - `db/migrations/` (empty for now)
   - `config/`
   - `tests/`
3. Add an empty `main.py` at the root of `repo/`.
4. Add a placeholder `.gitignore` ignoring typical Python, cache, and env files.
5. Provide a textual output describing the final structure.

**Output Format**: 
- Show the structure in a code block (like a tree listing).
- Provide any clarifying comments inline as needed.
```

---

## **Prompt for Step 1.2**

```text
**Objective**: Create a minimal README.md file.

**Instructions**:
1. In the `repo/` root, create a `README.md` file.
2. Include a short paragraph summarizing the Telegram Currency Exchange Bot and mention the core features:
   - Real-time currency exchange rates
   - Location-based services
   - Conversion tool
3. Include a “Getting Started” section explaining how to set up the environment (placeholder for now).
4. End with a “License” section (MIT or your preferred license).
5. Show the final contents of `README.md`.

**Output Format**:
- Provide the final text of `README.md` in a single fenced code block.
```

---

## **Prompt for Step 1.3**

```text
**Objective**: Set up a Python virtual environment and basic dependencies.

**Instructions**:
1. Assume we use `uv` or standard `venv`. Describe the command to create the virtual environment (e.g., `python3 -m venv venv`).
2. List the initial dependencies: `aiogram==3.*`, `SQLModel==0.*`, `pydantic==2.*`, `aiohttp`, `rapidfuzz`, `alembic`, and `pytest`.
3. Provide a sample `requirements.txt` (or `pyproject.toml` if you prefer) with these dependencies pinned.
4. Show how to activate the environment and install requirements.

**Output Format**:
- Provide the `requirements.txt` in a code block.
- Provide terminal commands in a separate code block.
```

---

## **Prompt for Step 1.4**

```text
**Objective**: Create an empty `main.py` that prints a simple message when run.

**Instructions**:
1. Open `main.py`.
2. Write a minimal `if __name__ == "__main__":` block that prints `"Hello, Telegram Bot!"`.
3. Provide the final `main.py`.

**Output Format**:
- Show the entire `main.py` in a fenced code block.
```

---

## **Prompt for Step 2.1**

```text
**Objective**: Initialize the DB engine and session management with SQLModel.

**Instructions**:
1. In `db/session.py`, create a function `get_engine()` that returns a SQLAlchemy engine (using `create_engine`).
2. Also add a sessionmaker or context-manager-based session (e.g., `SessionLocal`).
3. Reference an environment variable or a default for the DB URL (e.g., `sqlite:///./test.db`).
4. Provide the complete file content.

**Output Format**:
- Show the final `db/session.py` in a code block.
```

---

## **Prompt for Step 2.2**

```text
**Objective**: Create the SQLModel models for Office, Organization, and Rate.

**Instructions**:
1. Create `db/models/office.py` with a class `Office(SQLModel, table=True)`.
   - Fields: `id`, `name`, `address`, `lat`, `lng`, `is_active`, etc.
2. Create `db/models/organization.py` with a class `Organization(SQLModel, table=True)`.
   - Fields: `id`, `name`, `is_active`, etc.
3. Create `db/models/rate.py` with a class `Rate(SQLModel, table=True)`.
   - Fields: `id`, `office_id`, `currency`, `buy_rate`, `sell_rate`, `timestamp`.
4. Provide PK/ForeignKey references (e.g., `Rate.office_id -> Office.id`).
5. Show all 3 files fully, each in its own code block.

**Output Format**:
- Three code blocks: one for each model file.
```

---

## **Prompt for Step 2.3**

```text
**Objective**: Initialize Alembic for migrations.

**Instructions**:
1. Show how to run `alembic init db/migrations`.
2. Modify the generated `alembic.ini` and `env.py` to reference the `db/session.py` engine and `db.models` metadata.
3. Make sure the models import is recognized so Alembic can auto-detect changes.
4. Provide the relevant sections of `alembic.ini` and `env.py` that you changed.
```

---

## **Prompt for Step 2.4**

```text
**Objective**: Generate and apply the initial Alembic migration.

**Instructions**:
1. Use `alembic revision --autogenerate -m "Initial tables"`.
2. Show the generated migration script, focusing on the `upgrade` and `downgrade` methods.
3. Apply it with `alembic upgrade head`.
4. Confirm that your local SQLite DB has the new tables.

**Output Format**:
- Provide the final migration script content in a fenced code block.
- Provide any console output or relevant logs in another code block.
```

---

## **Prompt for Step 2.5**

```text
**Objective**: Verify DB creation.

**Instructions**:
1. Demonstrate a small Python snippet that imports the models and checks that the tables exist.
2. For example, open a session and run a quick query: `session.exec(select(Office)).all()`.
3. Provide the snippet and a short expected output.

**Output Format**:
- Provide the Python script snippet in a fenced code block.
- Provide the expected output in a second code block (or text explanation).
```

---

## **Prompt for Step 3.1**

```text
**Objective**: Start implementing `services/SyncService.py` with an async function to fetch MyFin data.

**Instructions**:
1. Create `services/SyncService.py`.
2. Define an async function `sync_exchange_data()` that will eventually use `aiohttp` to hit MyFin’s endpoint (mock the URL for now).
3. For now, just print `"Fetching MyFin data..."`.
4. Provide the entire file in a code block.

**Output Format**:
- One code block showing `services/SyncService.py`.
```

---

## **Prompt for Step 3.2**

```text
**Objective**: Use `aiohttp` to fetch MyFin rates in `sync_exchange_data()`.

**Instructions**:
1. In `SyncService.py`, import `aiohttp`.
2. Inside `sync_exchange_data()`, open an `aiohttp.ClientSession`, make a GET request to your MyFin mock URL, and parse JSON.
3. For demonstration, pretend the JSON has a structure with offices and rates. Store it in a local variable (no DB logic yet).
4. Provide the updated file.

**Output Format**:
- One code block for the updated `services/SyncService.py`.
- You can show a sample JSON structure in a comment.
```

---

## **Prompt for Step 3.3**

```text
**Objective**: Parse the JSON response, upsert offices/organizations, and rates.

**Instructions**:
1. In `sync_exchange_data()`, parse the mocked JSON.
2. For each office, create or update `Office` and `Organization`.
3. For each currency entry, create/update `Rate`.
4. Use the session from `db/session.py` for DB operations.
5. Provide the updated code. If you need to handle partial data or duplicates, show that logic as well.

**Output Format**:
- One code block with the new logic in `SyncService.py`.
- Include explanatory comments.
```

---

## **Prompt for Step 3.4**

```text
**Objective**: Mark stale offices/organizations as inactive if not in the latest API data.

**Instructions**:
1. After processing new data, query for all offices/organizations in DB.
2. If an entity was not seen in the new data, set `is_active = False`.
3. Provide code that does this in `sync_exchange_data()`.

**Output Format**:
- Single code block showing the relevant snippet.
```

---

## **Prompt for Step 3.5**

```text
**Objective**: Implement cleanup logic for rates older than 3 hours.

**Instructions**:
1. After inserting new rates, query for any `Rate` with a `timestamp` older than `now - 3 hours`.
2. Decide whether to delete them or mark them as inactive (the spec says “discard,” so we can delete).
3. Provide the code snippet in `sync_exchange_data()`.

**Output Format**:
- Code block with the relevant snippet in `SyncService.py`.
```

---

## **Prompt for Step 4.1**

```text
**Objective**: Create `services/GeolocationService.py` with a function to geocode addresses.

**Instructions**:
1. Implement `async def geocode_address(address: str) -> tuple[float, float]`.
2. You can mock the API call or show a placeholder for actual Google Geocoding usage.
3. If the geocoding fails, log to Sentry (or a placeholder function) and return `(None, None)`.

**Output Format**:
- Full code of `GeolocationService.py` in a code block.
```

---

## **Prompt for Step 4.2**

```text
**Objective**: Integrate the geocoding call during the Sync process.

**Instructions**:
1. In `SyncService.py`, when inserting/updating an `Office`, call `geocode_address(office.address)` if lat/lng is not set.
2. Store the lat/lng in the `Office`.
3. Show the updated portion of `sync_exchange_data()`.

**Output Format**:
- Code block with the relevant snippet, highlighting changes.
```

---

## **Prompt for Step 4.3**

```text
**Objective**: Implement fuzzy matching with `rapidfuzz` for organization searches.

**Instructions**:
1. In `services/GeolocationService.py` or a new file `services/FuzzyService.py`, create a function `search_organization(query: str) -> Organization`.
2. Use `rapidfuzz.fuzz.partial_ratio` or `rapidfuzz.process.extract` to find the best match among all `Organization` names in DB.
3. Return the top match if above a certain threshold.

**Output Format**:
- Code block with the new function.
- If you prefer a separate `FuzzyService.py`, show the entire file content.
```

---

## **Prompt for Step 5.1**

```text
**Objective**: Update `main.py` to instantiate an `aiogram` bot and run it.

**Instructions**:
1. Install `aiogram==3.*` if not done.
2. Import `Bot`, `Dispatcher` from `aiogram`.
3. Create a `Bot` instance with a placeholder token (e.g., `"123:ABC"`).
4. Create a `Dispatcher`.
5. Show how to run the bot with `dp.run_polling(bot)` or the recommended pattern for aiogram 3.
6. Provide the entire `main.py`.

**Output Format**:
- Single code block with `main.py`.
```

---

## **Prompt for Step 5.2**

```text
**Objective**: Create `bot/routers/start.py` to handle `/start` command.

**Instructions**:
1. In `start.py`, import `Router` from `aiogram`.
2. Create a new router instance. Add a handler for the `/start` command.
3. Return a welcome message, e.g., `"Welcome to the Currency Exchange Bot!"`.
4. Show how to register this router in `main.py`.

**Output Format**:
- Code block for `start.py`.
- A short snippet of how you updated `main.py` to include the new router.
```

---

## **Prompt for Step 5.3**

```text
**Objective**: Test the bot by running it locally.

**Instructions**:
1. Provide the command to run `main.py` (e.g., `python main.py`).
2. Show a sample Telegram screenshot or text explanation that `/start` works.
3. No code needed—just demonstration and explanation.

**Output Format**:
- Text or simulated console logs verifying the bot is up and responding.
```

---

## **Prompt for Step 5.4**

```text
**Objective**: Add a minimal error handler for unknown commands.

**Instructions**:
1. In `start.py` or a new router, add a message handler for `ContentTypes.TEXT`.
2. If the text is not recognized, reply `"Please use the buttons below."`.
3. Provide the code.

**Output Format**:
- Code block with the new handler.
```

---

## **Prompt for Step 6.1**

```text
**Objective**: Create a `services/ConversionService.py` with a `convert()` function.

**Instructions**:
1. `def convert(amount: float, from_curr: str, to_curr: str) -> float:`
2. It queries the DB for the `buy_rate` or `sell_rate` (choose buy/sell logic or unify).
3. Converts `from_curr -> GEL -> to_curr`.
4. Returns the result as a float.

**Output Format**:
- Show the entire file with the conversion logic.
```

---

## **Prompt for Step 6.2**

```text
**Objective**: Round result to 2 decimals and handle missing/outdated data.

**Instructions**:
1. If `Rate` for `from_curr` or `to_curr` is missing or older than 3 hours, raise an exception (e.g., `ValueError`).
2. Otherwise, do the math and `round(value, 2)`.
3. Provide the updated code.

**Output Format**:
- Show the updated function in one code block.
```

---

## **Prompt for Step 7.1**

```text
**Objective**: Build inline keyboards in `bot/keyboards/inline.py`.

**Instructions**:
1. Create a function `get_main_keyboard()` returning an inline keyboard with buttons:
   - "Nearest Office"
   - "Best Rate for a Currency"
   - "Nearest Office for an Organization"
2. Provide code building an `InlineKeyboardMarkup` or `InlineKeyboardBuilder`.
3. Show the final `inline.py` code.

**Output Format**:
- Single code block with the file’s content.
```

---

## **Prompt for Step 7.2**

```text
**Objective**: Create routers for conversion, location, and rates queries.

**Instructions**:
1. In `bot/routers/conversion_router.py`, add handlers that respond to the "Best Rate for a Currency" button or a `/convert` command.
2. In `bot/routers/location_router.py`, handle location sharing logic or user-sent location (if you choose).
3. In `bot/routers/rates_router.py`, handle queries about specific rates or nearest offices.
4. Provide each router's code in separate code blocks.

**Output Format**:
- Three code blocks: `conversion_router.py`, `location_router.py`, `rates_router.py`.
```

---

## **Prompt for Step 7.3**

```text
**Objective**: Integrate these routers and the inline keyboards into the bot.

**Instructions**:
1. In `main.py`, import and register the new routers.
2. Adjust the `/start` command to display the inline keyboard from `inline.py`.
3. Show the final updated `main.py`.

**Output Format**:
- Provide `main.py` in one code block, highlighting new changes.
```

---

## **Prompt for Step 7.4**

```text
**Objective**: Test interactive flows in Telegram.

**Instructions**:
1. Run the bot.
2. Show how you tested the inline keyboard, location queries, conversion queries.
3. No code needed, just text or console log output demonstrating success.

**Output Format**:
- Text explanation or console logs.
```

---

## **Prompt for Step 8.1**

```text
**Objective**: Add a logging config in `config/logging_config.py`.

**Instructions**:
1. Use `dictConfig` or a simple logging config.
2. Configure different levels (INFO, ERROR).
3. Provide the entire file content.

**Output Format**:
- Single code block with `logging_config.py`.
```

---

## **Prompt for Step 8.2**

```text
**Objective**: Integrate Sentry using DSN from `.env`.

**Instructions**:
1. In `config/settings.py`, load environment variables (e.g., using `pydantic.BaseSettings`).
2. If `SENTRY_DSN` is present, call `sentry_sdk.init(dsn=SENTRY_DSN)`.
3. Provide the entire file or relevant snippet.

**Output Format**:
- Code block with relevant snippet in `settings.py` or wherever you initialize Sentry.
```

---

## **Prompt for Step 8.3**

```text
**Objective**: Ensure the bot logs critical errors and that sync tasks log to Sentry on failure.

**Instructions**:
1. Show how you wrap `sync_exchange_data()` with a try/except, logging exceptions.
2. Similarly, show a top-level error handler for the bot.
3. Provide code snippets.

**Output Format**:
- Code block with updated error handling in `SyncService.py`.
- Code block with updated error handling in `main.py` or the relevant router.
```

---

## **Prompt for Step 8.4**

```text
**Objective**: If no fresh rates (<3h), show a user-facing warning and log to Sentry.

**Instructions**:
1. In the conversion or rates routers, before returning results, check if any rate is fresh.
2. If none, send a message: `"Warning: We have no fresh rates, data may be outdated."` and log to Sentry.
3. Provide the relevant snippet.

**Output Format**:
- Code snippet in the respective router(s).
```

---

## **Prompt for Step 9.1**

```text
**Objective**: Add integration tests for SyncService DB updates.

**Instructions**:
1. In `tests/test_sync.py`, write a test with a mocked MyFin response.
2. Run `sync_exchange_data()`.
3. Check DB for newly inserted offices, rates, etc.
4. Provide the entire test file.

**Output Format**:
- Single code block with `test_sync.py`.
```

---

## **Prompt for Step 9.2**

```text
**Objective**: Test ConversionService with sample rate data.

**Instructions**:
1. In `tests/test_conversion.py`, insert test data for `Rate` (USD->GEL, EUR->GEL).
2. Call `convert(amount=100, from_curr="USD", to_curr="EUR")`.
3. Assert correctness within rounding rules.
4. Provide the test file.

**Output Format**:
- Code block with `test_conversion.py`.
```

---

## **Prompt for Step 9.3**

```text
**Objective**: (Optional) Test Telegram bot flows.

**Instructions**:
1. Demonstrate how to test with `aiogram` test client or manual tests.
2. Provide a code snippet if using test client.
3. Provide textual explanation if tested manually.

**Output Format**:
- Code block or textual explanation of the test approach.
```

---

## **Prompt for Step 10.1**

```text
**Objective**: Write a `Dockerfile` for the bot.

**Instructions**:
1. Use an official Python base image (e.g., `python:3.12-slim`).
2. Copy the code, install dependencies, set `CMD` to run `main.py`.
3. Provide the entire `Dockerfile`.

**Output Format**:
- Single code block with the `Dockerfile`.
```

---

## **Prompt for Step 10.2**

```text
**Objective**: Write a `docker-compose.yml` for running the bot and a separate container for the cron job.

**Instructions**:
1. One service named `bot`.
2. One service named `sync`.
3. The `sync` might run `cron` or a periodic script calling `sync_exchange_data()`.
4. Show how you handle volumes for SQLite persistence.

**Output Format**:
- Single code block with the `docker-compose.yml`.
```

---

## **Prompt for Step 10.3**

```text
**Objective**: Confirm the volume is mounted properly.

**Instructions**:
1. Provide the lines in `docker-compose.yml` or the Dockerfile for mounting a volume.
2. Summarize how you verified that `database.db` persists across container restarts.

**Output Format**:
- Code block or textual explanation referencing the relevant part of `docker-compose.yml`.
```

---

## **Prompt for Step 10.4**

```text
**Objective**: Document environment variables in `README.md`.

**Instructions**:
1. In the "Getting Started" or new "Configuration" section, list required environment variables:
   - `BOT_TOKEN`, `SENTRY_DSN`, `MYFIN_API_KEY`, etc.
2. Update the `README.md` to reflect any new variables for geocoding or deployment.
3. Show the updated README section.

**Output Format**:
- A snippet of the new `README.md` text.
```

---

## **Prompt for Step 10.5**

```text
**Objective**: Deploy to AWS EC2 and run end-to-end tests.

**Instructions**:
1. Provide the general steps for setting up an EC2 instance (Ubuntu or Amazon Linux).
2. Pull the code, set up `.env`, run `docker-compose up -d`.
3. Show how you tested the bot via Telegram, ensuring everything works.
4. Summarize any final notes or known issues.

**Output Format**:
- Text explanation. No code block needed unless you want to show a sample command.
```
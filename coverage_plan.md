# Coverage Review & Plan

## Summary

This document outlines the current test coverage status of the project, identifies gaps, and proposes a plan for reviewing and improving coverage. The focus is on ensuring that all business logic, services, and critical utilities are covered, while avoiding unnecessary coverage of pure entrypoints or generated code.

**Latest update:**
- All bot callback tests now pass and main conversational flows are robustly covered with async tests.
- `src/bot/keyboards/inline.py` is now at 100% coverage.
- `src/bot/routers/currency.py` coverage increased to 46% (from 22%), with all main user flows and callback logic covered. Remaining gaps are in more complex flows, error branches, and message-based handlers.

---

## Coverage Status by File

| File/Module                                      | Coverage | Notes/Uncovered Lines/Functions                | Action Needed? |
|--------------------------------------------------|----------|------------------------------------------------|---------------|
| src/bot/keyboards/inline.py                      | 100%     | Fully covered                                  | NO            |
| src/bot/routers/currency.py                      | 46%      | Main conversational flows covered; complex flows, error branches, and message-based handlers remain | PARTIAL       |
| src/bot/routers/start.py                         | 100%     | -                                              | NO            |
| src/db/models/*                                  | 75-100%  | Some model fields/constructors not hit         | PARTIAL       |
| src/db/session.py                                | 88%      | 24-26 (session closing/cleanup)                | PARTIAL       |
| src/external_connectors/myfin/api_connector.py   | 62%      | 87-89, 109-128 (API error/edge cases)          | YES           |
| src/external_connectors/myfin/schemas.py         | 100%     | -                                              | NO            |
| src/repositories/base_repository.py              | 72%      | 31, 41-43, 49, 66-71, 74-79 (error/edge cases) | YES           |
| src/repositories/office_repository.py            | 98%      | 56 (edge case)                                 | PARTIAL       |
| src/repositories/organization_repository.py      | 84%      | 39, 64-73 (edge cases)                         | PARTIAL       |
| src/repositories/rate_repository.py              | 94%      | 39-46 (edge cases)                             | PARTIAL       |
| src/repositories/schedule_repository.py          | 41%      | 20-22, 25-28, 31-36 (most logic not covered)   | YES           |
| src/scheduler/scheduler.py                       | 100%     | -                                              | NO            |
| src/services/currency_service.py                 | 90%      | 66-73, 91, 146-147, 164, 186, 212, 215         | PARTIAL       |
| src/services/sync_service.py                     | 77%      | 63-65, 89-90, 118, 132-134, ... (many lines)   | YES           |
| src/start_bot.py                                 | 91%      | 96-98, 105-106 (shutdown/edge)                 | PARTIAL       |
| src/start_sync.py                                | 0%       | All (entrypoint, migrations, scheduler)        | REVIEW        |
| src/utils/base_requester.py                      | 72%      | 40, 116, 124-129, 156-160, ... (request logic) | YES           |
| src/utils/datetime_utils.py                      | 54%      | 26-29, 31, 35 (utility edge cases)             | PARTIAL       |
| src/utils/http_client.py                         | 86%      | 64-68, 92, 100 (error/edge cases)              | PARTIAL       |
| src/utils/schedule_parser.py                     | 43%      | 71-72, 93-95, 106-137 (parsing logic)          | YES           |

---

## File-by-File Review Order

1. **Core Business Logic & Services**
   - src/services/currency_service.py
   - src/services/sync_service.py
   - src/external_connectors/myfin/api_connector.py
2. **Repositories (Data Access)**
   - src/repositories/base_repository.py
   - src/repositories/office_repository.py
   - src/repositories/organization_repository.py
   - src/repositories/rate_repository.py
   - src/repositories/schedule_repository.py
3. **Controllers/Routers**
   - src/bot/routers/currency.py
   - src/bot/keyboards/inline.py
4. **Utilities**
   - src/utils/base_requester.py
   - src/utils/schedule_parser.py
   - src/utils/datetime_utils.py
   - src/utils/http_client.py
5. **Entrypoints/Scripts**
   - src/start_sync.py (review if worth covering; likely exclude)
   - src/start_bot.py (only cover logic, not CLI/entrypoint)

---

## Exclusion Recommendations
- **src/start_sync.py**: Pure entrypoint, migrations, and scheduler startup. Recommend excluding from coverage unless business logic is present.
- **__init__.py** files: Exclude unless they contain logic.
- **Generated code**: Exclude if any.

---

## Next Steps
1. **Review uncovered lines in each file (see table above).**
2. **Add or improve tests for business logic, error handling, and edge cases.**
3. **For `src/bot/routers/currency.py`, focus on complex flows, error branches, and message-based handlers for further improvements.**
4. **Exclude pure entrypoints and generated code from coverage reporting.**
5. **Re-run coverage and update this plan as progress is made.**

---

## Notes
- Focus on business logic, service layer, and repository pattern coverage.
- Avoid unnecessary coverage of CLI wrappers, entrypoints, or generated code.
- Use pytest and pytest-asyncio for all new tests.
- Ensure all new tests have type hints and follow project conventions. 
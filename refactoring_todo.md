# Refactoring TODOs: Bot Functionality

This checklist tracks actionable refactoring tasks based on the refactoring plan. Check off items as you complete them. For details, see `refactoring_plan.md`.

---

## Routers & Handlers
- [x] Split `src/bot/routers/currency.py` into:
  - [x] `rates.py` (rate queries)
  - [x] `conversion.py` (currency conversion)
  - [x] `location.py` (office search)
  - [x] `org.py` (organization selection)
- [x] Refactor all handlers to be thin (no business logic inside) for rates and conversion

## State Management
- [ ] Remove global `user_search_state` dict
- [ ] Use aiogram FSM/context for any required per-user state
- [ ] If stateless, encode all state in callback data or message text

## Service Layer
- [ ] Move rate table formatting to a service method
- [ ] Move office search and distance calculation to a service
- [ ] Move conversion logic to a service
- [ ] Ensure all business logic is outside handlers

## Dependency Injection
- [ ] Create a factory or provider for repositories/services
- [ ] Pass dependencies explicitly to handlers (no instantiation inside handlers)

## UI Formatting
- [x] Move all map link utilities to `src/bot/utils/map_links.py`
- [ ] Move all keyboard construction to `src/bot/keyboards/`
- [ ] Move all message formatting (tables, lists, etc.) to utilities or services

## Error Handling & Logging
- [ ] Implement error handling decorator or middleware for all handlers
- [ ] Ensure all exceptions are logged with context
- [ ] Return user-friendly error messages for all failures

## Testing
- [x] Update tests for modular routers and new handler locations
- [x] Ensure all tests pass after refactor
- [ ] Add/expand unit tests for new/updated service methods
- [ ] Keep handler tests focused on routing/integration

## Type Hints & Validation
- [ ] Add/expand type hints for all handler and service signatures
- [ ] Use Pydantic models for all complex handler inputs

## Repository Pattern
- [ ] Refactor any direct DB access in handlers to use repositories

## Documentation
- [ ] Add/expand docstrings for all handlers, services, and utilities
- [ ] Add comments for complex logic/business rules

---

*Update this file as you make progress or add new refactoring tasks.* 
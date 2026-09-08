# Refactoring Plan: Bot Functionality

This document outlines a comprehensive refactoring plan for the Telegram bot functionality in the Georgia Currency Exchange Bot project. The goal is to improve modularity, maintainability, and testability, while aligning with best practices and project conventions.

---

## Summary Table

| Area                | Current Issue                        | Refactoring Action                                 |
|---------------------|--------------------------------------|----------------------------------------------------|
| Router size         | Large, monolithic files              | Split by domain, keep handlers thin                |
| State management    | Global dict, not robust              | Use FSM/context or stateless callback data         |
| Business logic      | In handlers                          | Move to services                                   |
| Dependency wiring   | Instantiated in handlers             | Centralize, use DI/factories                       |
| UI formatting       | Mixed with logic                     | Centralize in keyboards/utilities                  |
| Error handling      | Inconsistent                         | Standardize with decorators/middleware             |
| Testing             | Some tight coupling                  | Test services, keep handler tests focused          |
| Type hints/validation | Not always explicit                | Use Pydantic models, add type hints everywhere     |
| Repository usage    | Occasional direct DB access          | Always use repositories                            |
| Documentation       | Incomplete docstrings                | Add/expand docstrings and comments                 |

---

## 1. Router and Handler Organization

- **Split large router files (e.g., `currency.py`) into smaller, domain-focused modules:**
  - `rates.py` (rate queries)
  - `conversion.py` (currency conversion)
  - `location.py` (office search)
  - `org.py` (organization selection)
- **Keep handlers thin:**
  - Move all business logic, data formatting, and filtering to service classes.
  - Handlers should only parse input, call services, and format responses.

## 2. State Management

- **Replace global `user_search_state` with aiogram FSM/context:**
  - Use aiogram's FSM or context storage for per-user state.
  - If statelessness is required, encode all state in callback data or message text.
  - Remove all global state.

## 3. Service Layer Usage

- **Move business logic out of handlers:**
  - Create/expand service classes for:
    - Rate formatting and filtering
    - Office search and distance calculation
    - Conversion logic
  - Handlers should only orchestrate calls to these services.

## 4. Dependency Injection

- **Centralize dependency wiring:**
  - Use a factory or dependency provider to construct services and repositories.
  - Pass dependencies explicitly to handlers (using aiogram's DI or via router setup).
  - Avoid instantiating repositories/services inside handlers.

## 5. Keyboard and Message Formatting

- **Centralize all keyboard and message formatting:**
  - Keep all keyboard builders in `src/bot/keyboards/`.
  - Move all message formatting (e.g., rate tables, office lists) to utility functions or service methods.
  - This will simplify UI/UX updates and localization.

## 6. Error Handling and Logging

- **Standardize error handling:**
  - Use a decorator or middleware for logging and error reporting in all handlers.
  - Ensure all exceptions are logged with context (user, command, etc.).
  - Return user-friendly error messages for all failure cases.

## 7. Testing Improvements

- **Test at the service layer:**
  - After moving business logic to services, write focused unit tests for those services.
  - Keep handler tests focused on routing and integration.

## 8. Type Hints and Pydantic Models

- **Use Pydantic models for all input validation:**
  - Define request/response models for complex handler inputs.
  - Use type hints for all handler signatures and service methods.

## 9. Repository Pattern Consistency

- **Ensure all DB access is via repositories:**
  - Refactor any direct DB access or ad-hoc queries in handlers to use repository classes.
  - This will make it easier to swap DB backends or mock for tests.

## 10. Documentation and Comments

- **Add/expand docstrings and comments:**
  - Ensure every handler, service, and utility function has a clear docstring (PEP257).
  - Add comments for complex logic or business rules.

---

## Example Refactoring Steps

1. **Split `currency.py` into multiple router files by domain.**
2. **Move all business logic (e.g., rate table formatting, office filtering) into new/existing service classes.**
3. **Refactor handlers to only call services and format responses.**
4. **Replace global state with FSM/context or stateless callback data.**
5. **Centralize dependency creation and pass dependencies explicitly.**
6. **Move all keyboard/message formatting to dedicated modules.**
7. **Add error handling decorators/middleware for all handlers.**
8. **Expand unit tests for new service methods.**
9. **Add/expand docstrings and comments throughout the codebase.**

---

## Rationale

- **Maintainability:** Smaller, focused modules and clear separation of concerns make the codebase easier to navigate and update.
- **Testability:** Moving logic to services and using dependency injection enables more granular and reliable tests.
- **Scalability:** Modular design and clear boundaries allow for easier feature expansion and onboarding of new contributors.
- **Robustness:** Standardized error handling and input validation reduce bugs and improve user experience.

---

*For any questions or to prioritize specific refactoring steps, please consult this plan or open an issue in the repository.* 
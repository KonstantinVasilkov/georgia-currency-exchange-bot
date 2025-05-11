# Office Search Feature Implementation Plan

This document outlines the implementation plan for the "Find Nearest Office" and related features in the currency exchange bot. Use this as a reference and checklist during development. Mark each item as complete when done.

---

## 1. Update Main Menu

- [x] Add a new button: "Find Nearest Office"
- [x] On tap, show three options:
  - [ ] Find nearest office (requires location)
  - [ ] Find nearest office with best rates (requires location, after currency pair selection)
  - [ ] Show all offices of a chosen organization (does not require location)
- [x] Add explanation: Clearly state that the first two options require location sharing.
- [x] Add/extend tests for main menu and office search menu keyboards.

---

## 2. Routing and User Flow

### 2.1. "Find Nearest Office" and "Find Nearest Office with Best Rates"

- [ ] Prompt user to share location.
- [ ] If user declines, show two buttons:
  - [ ] "Share location" (retry)
  - [ ] "List organizations" (fallback, leads to map with pins for all offices)

### 2.2. "Find Nearest Office with Best Rates"

- [ ] Before location prompt: Ask user to select the currency pair (reuse existing best rates logic).
- [ ] After currency pair selection: Prompt for location, then proceed as in 2.1.

### 2.3. "Show All Offices of a Chosen Organization"

- [ ] Show a list of organizations (filtered by type: `Bank` or `MicrofinanceOrganization`).
- [ ] On selection, show all offices for that organization.

---

## 3. Business Logic & Filtering

- [ ] All office searches, best rates, and organization lists must only include organizations where `type` is `"Bank"` or `"MicrofinanceOrganization"`.
- [ ] Fallback map and lists must also apply this filter.

---

## 4. Location Handling

- [ ] When user shares location:
  - [ ] Calculate the distance from user to each office (using latitude/longitude).
  - [ ] For "nearest office," select the closest office.
  - [ ] For "nearest office with best rates," filter offices by best rate for the selected currency pair, then select the closest among them.

- [ ] When user does not share location:
  - [ ] Show two buttons: "Share location" and "List organizations."
  - [ ] If "List organizations" is chosen, show a list of organizations (filtered as above), then show all offices for the selected organization.

---

## 5. Map Link Generation

- [ ] For fallback (no location):
  - [ ] Generate a Google Maps link and an Apple Maps link with pins for all offices of the selected organization (or all offices, if needed).
  - [ ] Present both links to the user with clear labels.

- [ ] For location-based search:
  - [ ] For the nearest office, provide a button to open directions in Google Maps and a button for Apple Maps, pre-filled with the office address/coordinates.

---

## 6. Service Layer

- [ ] Extend or add service methods:
  - [ ] To filter organizations by type.
  - [ ] To find nearest office given user coordinates.
  - [ ] To find nearest office with best rates for a currency pair.
  - [ ] To generate map links for a set of offices.

---

## 7. Data Validation & Models

- [ ] Use Pydantic models for all user input (location, currency pair, etc.).
- [ ] Ensure all new endpoints and services are type-annotated and validated.

---

## 8. Error Handling & UX

- [ ] Handle missing data gracefully (e.g., no offices found, no rates available).
- [ ] Log all errors with context.
- [ ] Provide user-friendly messages for all fallback and error scenarios.

---

## 9. Testing

- [ ] Add/extend pytest tests for:
  - [ ] Service logic (distance calculation, filtering, best rates)
  - [ ] Routing and user flows (location/no location, currency pair selection)
  - [ ] Map link generation

---

## 10. Documentation

- [ ] Update docstrings for all new/modified functions and classes (PEP257).
- [ ] Update README to describe the new features and user flows.

---

## 11. Code Style & CI

- [ ] Run Ruff and mypy to ensure code style and type correctness.
- [ ] Update CI/CD pipeline if needed to include new tests.

---

### Optional (Future-proofing)

- [ ] Consider abstracting city support for future multi-city expansion.
- [ ] Consider using a config or DB-driven list of supported organization types. 
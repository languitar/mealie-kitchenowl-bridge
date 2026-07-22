# Agent Guide — Mealie ↔ KitchenOwl Bridge

## What this project is

A Flask + HTMX bridge that, when triggered from a Mealie recipe action, lets the
user review a recipe's ingredients and push them onto a KitchenOwl shopping list.

This repository currently contains only the **skeleton**: an app factory, a working
`/healthz` endpoint, and placeholder modules for the real capabilities. The webhook
trigger, the ingredient review UI, and the KitchenOwl push are deliberately
unimplemented — they get built one feature request at a time.

## The BDD workflow

Every new feature request is turned into an acceptance test *before* it's implemented:

1. **Write a `.feature` file** in `tests/bdd/features/<capability>.feature` describing
   the behavior in Gherkin (`Given`/`When`/`Then`). One feature file per capability —
   don't pile unrelated behavior into an existing file.
2. **Add step definitions** in `tests/bdd/steps/`. Put the scenario's steps in a
   `test_<capability>.py` module that does:
   ```python
   from pytest_bdd import scenarios
   from .common import *  # noqa: F401,F403

   scenarios("../features/<capability>.feature")
   ```
   Check `tests/bdd/steps/common.py` first for reusable `Given`/`When`/`Then` steps
   (e.g. `"the bridge is running"`). Only add a new step there once a *second*
   scenario needs it verbatim — keep single-use steps local to their own module.
3. **Implement the application code** under `src/bridge/` until the scenario passes.
   Wire real logic into the existing placeholder blueprints/clients rather than
   creating new top-level modules where an obvious one already exists:
   - `src/bridge/routes/webhook.py` — the Mealie recipe-action trigger
   - `src/bridge/routes/review.py` — the HTMX ingredient review/edit screen
   - `src/bridge/clients/mealie.py`, `src/bridge/clients/kitchenowl.py` — API clients
4. **Add `pytest` coverage for anything awkward to express acceptance-style**:
   ingredient parsing/normalization, quantity/unit conversion, API client error
   handling, edge cases. These go in `tests/unit/` (pure logic, no I/O) or
   `tests/integration/` (a client wrapper against a stubbed HTTP server/`requests_mock`,
   without going through Flask).

Acceptance scenarios always go through Flask's test client
(`app.test_client()`, via the `client`/`running_app` fixtures) with the real
Mealie/KitchenOwl HTTP calls stubbed via `requests_mock`. Never hit live services in
tests.

## Deferred decisions

These were explicitly deferred when the skeleton was created — don't assume they're
settled, and revisit them as their own feature requests when they become relevant:

- **Mealie trigger shape**: it's not yet confirmed whether Mealie's recipe action
  opens a URL in the browser (GET, with template variables like the recipe slug) or
  posts a server-to-server webhook. Verify against a real Mealie instance/its docs
  when implementing the first triggering feature, and adjust `routes/webhook.py`
  accordingly.
- **Auth**: none. A single shared Mealie API token and a single shared KitchenOwl API
  token are configured via environment variables (see `.env.example`). No login
  screen, no per-user credentials. Multi-user auth (e.g. an identity provider such as
  Keycloak in front of the bridge's own UI) is a possible future feature, not assumed
  by anything currently built.
- **Persistence**: none. No database. If a feature needs to hold state across
  requests (e.g. a pending ingredient review), keep it in-process/in-memory until a
  feature request specifically calls for durability, then add persistence at that
  point.

## Conventions

- `src/` layout, package name `bridge`, installed editable (`pip install -e .[dev]`).
- Flask blueprints per concern, registered in `src/bridge/app.py`.
- HTMX is vendored at `src/bridge/static/htmx.min.js` — no CDN dependency.
- Lint with `ruff check .`.
- Run tests with `pytest` (runs both BDD and plain unit/integration tests).

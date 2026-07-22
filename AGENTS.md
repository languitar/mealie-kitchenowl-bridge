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

0–1. **Check for an existing match/conflict, then draft or extend the `.feature`
   file.** Use the `add-feature` skill (`.agent/skills/add-feature/`, symlinked at
   `.claude/skills/`) for this — it owns the classification criteria (belongs to an
   existing capability / contradicts an existing scenario / genuinely new) and the
   Gherkin drafting conventions, so they're not repeated here. It stops after
   drafting and sanity-checking the scenario; it does not write step definitions or
   application code.
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

Acceptance scenarios default to Flask's test client (`app.test_client()`, via the
`client`/`running_app` fixtures) with the real Mealie/KitchenOwl HTTP calls stubbed
via `requests_mock`. Never hit live services in tests.

### Browser-driven scenarios

Some behavior — real DOM rendering, HTMX partial swaps, client-side JS — can't be
verified through the Flask test client and needs an actual browser. For that, tag the
`Scenario` with `@browser` (pytest-bdd maps Gherkin tags to pytest markers
automatically) and write its steps against the `page` fixture (from
`pytest-playwright`) and the `live_server` fixture (serves the real `app` on a real
port — see `tests/bdd/conftest.py`; this overrides `pytest-flask`'s own `live_server`,
which is broken under Python 3.14's `forkserver` multiprocessing default). See
`tests/bdd/features/home_page.feature` / `tests/bdd/steps/test_home_page.py` for the
pattern.

Default to the fast Flask-test-client tier — reach for `@browser` only when the
behavior genuinely requires a real browser. Browser scenarios are excluded from the
default `uv run pytest` (see `addopts` in `pyproject.toml`) since they need Chromium
installed; run them explicitly:

```bash
uv run playwright install chromium  # one-time setup
uv run pytest -m browser
```

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

- `src/` layout, package name `bridge`, dependencies managed with
  [uv](https://docs.astral.sh/uv/) (`uv sync` installs both runtime deps and the
  `dev` dependency group; `uv.lock` pins everything — regenerate it with `uv lock`
  after changing dependencies, and commit the updated lockfile).
- Flask blueprints per concern, registered in `src/bridge/app.py`.
- HTMX is vendored at `src/bridge/static/htmx.min.js` — no CDN dependency.
- Lint with `uv run ruff check .`.
- Run tests with `uv run pytest` (runs both BDD and plain unit/integration tests).

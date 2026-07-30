# Agent Guide — Mealie ↔ KitchenOwl Bridge

## What this project is

A Flask bridge that, when triggered from a Mealie recipe action, lets the
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
   Acceptance scenarios run against Flask's test client (`client`/`running_app`
   fixtures). If a scenario touches KitchenOwl, point its module's `config` fixture
   at the `kitchenowl_config` fixture (`tests/bdd/conftest.py`; see
   `tests/bdd/steps/test_recipe_to_shopping_list.py` for the pattern) rather than
   touching the shared one in `tests/conftest.py`, so scenarios that don't need
   KitchenOwl (e.g. `health_check`, `home_page`) stay fast. Tag browser-only
   scenarios `@browser` and write their steps against the `page`/`live_server`
   fixtures — see `tests/bdd/features/home_page.feature` /
   `tests/bdd/steps/test_home_page.py` for the pattern. See README.md's Testing
   section for how Mealie/KitchenOwl are faked and how to run each tier.
3. **Implement the application code** under `src/bridge/` until the scenario passes.
   Wire real logic into the existing placeholder blueprints/clients rather than
   creating new top-level modules where an obvious one already exists:
   - `src/bridge/routes/webhook.py` — the Mealie recipe-action trigger
   - `src/bridge/routes/review.py` — the ingredient review/edit screen
   - `src/bridge/clients/mealie.py`, `src/bridge/clients/kitchenowl.py` — API clients
4. **Add `pytest` coverage for anything awkward to express acceptance-style**:
   ingredient parsing/normalization, quantity/unit conversion, API client error
   handling, edge cases. These go in `tests/unit/` (pure logic, no I/O) or
   `tests/integration/` (a client wrapper against a stubbed HTTP server/`requests_mock`,
   without going through Flask) — `requests_mock` is the right tool even for
   KitchenOwl-client error paths here, since simulating e.g. a 500 response is
   impractical against the real instance used at the BDD tier.

## Deferred decisions

These were explicitly deferred when the skeleton was created — don't assume they're
settled, and revisit them as their own feature requests when they become relevant.
See README.md for the current concrete configuration and behavior; this section
records *why* each thing is the way it is and *when* it's worth reconsidering:

- **Mealie trigger shape**: resolved for the recipe-to-shopping-list feature —
  Mealie POSTs the full recipe JSON directly to `/recipes/action`, so the bridge
  never calls back into Mealie's own API, and `clients/mealie.py` stays an unused
  placeholder. Revisit if a future feature needs data Mealie doesn't include in
  that payload (at which point a real Mealie API client/token would be needed).
- **Auth**: the webhook trigger is authenticated (see README's Configuration
  section), but per-user login (an identity provider in front of the bridge's own
  UI, plus per-user KitchenOwl access) was investigated and deliberately dropped:
  KitchenOwl's OIDC login flow can't be driven server-side by a third party (its
  redirect URI is hardcoded to KitchenOwl's own frontend, so an external caller
  can't capture the resulting code), and KitchenOwl has no admin API to resolve
  which household an arbitrary authenticated user belongs to. Revisit as its own
  feature request if that trade-off stops being acceptable.
- **Persistence**: none (see README). If a feature needs to hold state across
  requests (e.g. a pending ingredient review), keep it in-process/in-memory until a
  feature request specifically calls for durability, then add persistence at that
  point.

## Conventions

See README.md's "Architecture & conventions" section (package layout, blueprint
structure, UI design direction) and "Commits" section (Conventional
Commits format used in this repo).

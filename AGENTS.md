# Agent Guide — Mealie ↔ KitchenOwl Bridge

## What this project is

A Flask bridge that, when triggered from a Mealie recipe action, lets the
user review a recipe's ingredients and push them onto a KitchenOwl shopping list.

This repository currently contains only the **skeleton**: an app factory, a working
`/healthz` endpoint, and placeholder modules for the real capabilities. The
recipe-action trigger, the ingredient review UI, and the KitchenOwl push are
deliberately unimplemented — they get built one feature request at a time.

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
   (e.g. `"the bridge is running"`, `"the bridge is running as a logged-in user"`).
   Only add a new step there once a *second* scenario needs it verbatim — keep
   single-use steps local to their own module. Every scenario drives a real
   Chromium browser via Playwright's `page`/`live_server`/`context` fixtures
   (`tests/bdd/conftest.py`) against a real Flask server — there's no separate
   non-browser tier. If a scenario touches KitchenOwl, point its module's `config`
   fixture at the `kitchenowl_config` fixture rather than touching the shared one
   in `tests/conftest.py`, so scenarios that don't need KitchenOwl (e.g.
   `health_check`) stay fast.

   Interact with the page through Playwright locators, in order of preference:
   role/label/text (`get_by_role`, `get_by_label`, `get_by_text`), falling back to
   `data-testid` only for elements with no meaningful accessible role (e.g. a
   JS-managed hidden `<select>` — see `select_ingredients.html`). Avoid scraping
   rendered HTML with regexes or reaching for a CSS/XPath selector when a
   role/label-based one would work. If a template doesn't expose an accessible way
   to target something a scenario needs, add one (an `aria-label`, an associated
   `<label>`, or `role="group"` to scope a repeated block) rather than writing a
   brittle selector against it. See `tests/bdd/steps/test_recipe_to_shopping_list.py`
   for the pattern. See README.md's Testing section for how Mealie/KitchenOwl are
   faked.
3. **Implement the application code** under `src/bridge/` until the scenario passes.
   Wire real logic into the existing placeholder blueprints/clients rather than
   creating new top-level modules where an obvious one already exists:
   - `src/bridge/routes/trigger.py` — the Mealie recipe-action trigger
   - `src/bridge/routes/review.py` — the ingredient review/edit screen
   - `src/bridge/routes/auth.py`, `src/bridge/auth.py` — OIDC login and the
     app-wide login gate
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
  Mealie's "Post"-type recipe action can't redirect the user's browser (it's
  executed entirely server-side by Mealie's own backend, invisible to the
  browser), so the bridge is triggered via a "Link"-type action instead. Link
  actions only carry whatever's templated into their configured URL (here, the
  recipe's slug via `${slug}`), so `clients/mealie.py`'s `MealieClient.get_recipe`
  fetches the full recipe from Mealie's own API (`GET /api/recipes/{slug}`,
  Bearer token) rather than reading it from a request body.
- **Auth**: the bridge's own UI is gated app-wide by mandatory OIDC login (see
  README's Configuration section and `src/bridge/auth.py`) - the trigger token
  that used to guard only `/recipes/action` has been retired in favor of this.
  This is a *different, narrower* thing than the per-user KitchenOwl access idea
  that was investigated and deliberately dropped: driving KitchenOwl's own OIDC
  login server-side (to resolve per-user KitchenOwl household access) still isn't
  possible - KitchenOwl's OIDC redirect URI is hardcoded to its own frontend, so
  an external caller can't capture the resulting code, and KitchenOwl has no admin
  API to resolve which household an arbitrary authenticated user belongs to. The
  bridge's OIDC login is independent of that: it's its own relying party gating
  only its own session, while KitchenOwl access remains one shared
  `KITCHENOWL_API_TOKEN`/`KITCHENOWL_HOUSEHOLD_ID` regardless of who's logged in.
  Per-user KitchenOwl access is still deferred - revisit as its own feature
  request if that trade-off stops being acceptable.
- **Persistence**: none (see README). If a feature needs to hold state across
  requests (e.g. a pending ingredient review), keep it in-process/in-memory until a
  feature request specifically calls for durability, then add persistence at that
  point.

## Conventions

See README.md's "Architecture & conventions" section (package layout, blueprint
structure, UI design direction) and "Commits" section (Conventional
Commits format used in this repo).

### Rewriting history on feature branches

Unlike the general default of only ever creating new commits, in this repo it's
fine to amend or force-push commits on a **feature branch** (not `main`) - e.g. to
fix up a commit that hasn't been reviewed yet, or to fold a small follow-up fix
into the commit it belongs with. This still needs the same judgment as any other
git action - the change may be visible to others via an open PR - but no separate
confirmation is needed each time for a feature branch already worked on in the
current conversation. `main` itself is never rewritten.

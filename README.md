# Mealie ↔ KitchenOwl Bridge

> **Disclaimer**: this project is mostly vibe-coded - it's a testbed for exploring
> agentic coding practices (BDD-driven feature workflows, AI-agent-assisted
> development) as much as it is a real tool. Expect the usual consequences: review
> anything here carefully, especially around security and data-handling, before
> trusting it with real accounts or real data.

Bridges a Mealie recipe action to a KitchenOwl shopping list: trigger from a recipe
in Mealie, review the ingredients in a small HTMX UI, and push them onto a
KitchenOwl shopping list.

This repo is currently a **skeleton**. See [AGENTS.md](AGENTS.md) for the BDD-driven
workflow used to build out real features, and for what's deliberately not built yet.

Dependencies are managed with [uv](https://docs.astral.sh/uv/), pinned via `uv.lock`.

## Setup

```bash
uv sync
cp .env.example .env  # then fill in real Mealie/KitchenOwl URLs and tokens
uv run playwright install chromium  # only needed for browser-based tests
```

## Configuration

All configuration is via environment variables (see `.env.example`):

- `KITCHENOWL_URL` / `KITCHENOWL_API_TOKEN` / `KITCHENOWL_HOUSEHOLD_ID` - a single
  shared KitchenOwl household and API token. There's no multi-household or
  per-user KitchenOwl access - everyone who uses the bridge sees and pushes to the
  same household.
- `WEBHOOK_TOKEN` - required; the app refuses to start without it. A shared secret
  that must be sent as a `token` query parameter on Mealie's webhook call (Mealie's
  "Post"-type recipe action only supports a configurable target URL, not custom
  headers). Configure Mealie's recipe action URL as:
  ```
  https://bridge.example.com/recipes/action?token=<WEBHOOK_TOKEN>
  ```

There's no login of any kind on the ingredient review/confirm screens - anyone who
can reach the bridge can use them once past the webhook token. Only the webhook
trigger itself is authenticated. If that matters for your deployment, put your own
access control (e.g. a reverse proxy) in front of the bridge. There's also no
database - nothing persists across requests or restarts.

## Running

```bash
uv run flask --app bridge.app:create_app run
```

`GET /healthz` should respond with `{"status": "ok"}`.

## Testing

```bash
uv run pytest              # unit, integration, and Flask-test-client BDD scenarios
uv run pytest -m browser   # browser-driven BDD scenarios (needs `playwright install chromium`)
uv run ruff check .
```

Unit and integration tests are plain pytest with no external services. Acceptance
(BDD) scenarios run through a real Flask test client; how the two external services
are faked differs:

- **Mealie** is stubbed with `requests_mock` - tests never call a live Mealie.
- **KitchenOwl** scenarios run against a **real KitchenOwl instance in a
  container** instead of a mock, so tests can't drift from what KitchenOwl actually
  does. This is why the default suite needs a working local Docker (or Podman, see
  below) daemon - the KitchenOwl image is pulled and started automatically, no
  manual `docker compose up` needed for tests.

Some behavior (real DOM rendering, HTMX partial swaps, client-side JS) can only be
verified through an actual browser rather than the Flask test client. Those
scenarios are tagged `@browser` and excluded from the default `uv run pytest` run
since they need Chromium installed; run them explicitly with
`uv run pytest -m browser` after `uv run playwright install chromium`.

### Using Podman instead of Docker

`testcontainers` (via the `docker` Python SDK) also works against a rootless Podman
socket - point `DOCKER_HOST` at it and disable `ryuk` (testcontainers' cleanup
sidecar, which commonly hits privilege issues under rootless Podman):

```bash
systemctl --user start podman.socket  # if not already running
DOCKER_HOST=unix:///run/user/$(id -u)/podman/podman.sock \
  TESTCONTAINERS_RYUK_DISABLED=true \
  uv run pytest
```

Export both variables in your shell profile if you want this to be the default
rather than passing them per invocation.

## Docker

```bash
docker compose up --build
```

## Architecture & conventions

- `src/` layout, package name `bridge`. `uv.lock` pins all dependencies -
  regenerate it with `uv lock` after changing dependencies, and commit the updated
  lockfile.
- Flask blueprints per concern, registered in `src/bridge/app.py`.
- HTMX is vendored at `src/bridge/static/htmx.min.js` - no CDN dependency.
- UI design follows KitchenOwl's own UI (layout, styling, interaction patterns)
  rather than Mealie's or an independent style, since the bridge's screens are the
  step just before pushing onto a KitchenOwl list and should feel like part of that
  experience.

See [AGENTS.md](AGENTS.md) for how new features get built (the BDD-driven
workflow) and for the reasoning behind decisions deliberately deferred so far.

## Commits

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):
`<type>: <short, imperative summary>`, e.g. `feat: add fuzzy item matching` or
`fix: handle missing recipe ingredients`. No scopes are used in this repo. Common
types:

- `feat` - new user-facing behavior
- `fix` - a bug fix
- `docs` - documentation only (README, AGENTS.md, comments)
- `test` - test-only changes (no application code)
- `refactor` - code change that doesn't alter behavior
- `build` - build system, dependencies, tooling
- `chore` - everything else (repo housekeeping, CI config, etc.)

Add a body when the *why* isn't obvious from the summary or diff alone - see the
existing `git log` for examples. Keep the summary line short; put details in the
body.

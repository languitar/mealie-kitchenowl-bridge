# Mealie ↔ KitchenOwl Bridge

> **Disclaimer**: this project is mostly vibe-coded - it's a testbed for exploring
> agentic coding practices (BDD-driven feature workflows, AI-agent-assisted
> development) as much as it is a real tool. Expect the usual consequences: review
> anything here carefully, especially around security and data-handling, before
> trusting it with real accounts or real data.

Bridges a Mealie recipe action to a KitchenOwl shopping list: trigger from a recipe
in Mealie, review the ingredients in a small web UI, and push them onto a
KitchenOwl shopping list.

This repo is currently a **skeleton**. See [AGENTS.md](AGENTS.md) for the BDD-driven
workflow used to build out real features, and for what's deliberately not built yet.

Dependencies are managed with [uv](https://docs.astral.sh/uv/), pinned via `uv.lock`.

## Setup

```bash
uv sync
cp .env.example .env  # then fill in real Mealie/KitchenOwl URLs and tokens
uv run playwright install chromium  # needed to run the acceptance (BDD) test suite
```

## Configuration

All configuration is via environment variables (see `.env.example`):

- `KITCHENOWL_URL` / `KITCHENOWL_API_TOKEN` / `KITCHENOWL_HOUSEHOLD_ID` - a single
  shared KitchenOwl household and API token. There's no multi-household or
  per-user KitchenOwl access - everyone who uses the bridge sees and pushes to the
  same household.
- `OIDC_ISSUER` / `OIDC_CLIENT_ID` / `OIDC_CLIENT_SECRET` - required; the app
  refuses to start without them. Every page of the bridge requires signing in
  via this OIDC provider first (see below); `OIDC_ISSUER` is the bare issuer
  URL, and the bridge discovers everything else from
  `{OIDC_ISSUER}/.well-known/openid-configuration`. Register the bridge as a
  confidential client with your provider, with
  `https://bridge.example.com/auth/callback` as an allowed redirect URI.
- `SECRET_KEY` - required; the app refuses to start without it. Signs the login
  session cookie. Keep it stable across restarts (rotating it logs everyone
  out) and generate it with real randomness, e.g.
  `python -c "import secrets; print(secrets.token_hex(32))"`.
- `MEALIE_URL` / `MEALIE_API_TOKEN` - required; the app refuses to start without
  them. Used to fetch the triggering recipe's ingredients server-side by slug
  (`MEALIE_API_TOKEN` is a long-lived API token, generated in Mealie's user
  profile). Mealie's "Post"-type recipe action can't redirect your browser to
  the bridge - it's executed entirely server-side by Mealie's own backend, so
  any response the bridge returns is invisible to you. Only a "Link"-type
  action causes a real browser navigation, but it can't carry the recipe's
  data - just whatever's templated into its configured URL - so the bridge
  fetches the triggering recipe from Mealie's own API by slug instead.
  Configure Mealie's recipe action as type **Link**, with URL:
  ```
  https://bridge.example.com/recipes/action?slug=${slug}
  ```
  Mealie substitutes `${slug}` with the current recipe's slug before opening the
  URL in a new tab.

Every route requires an authenticated OIDC session - including that Link action
above and the ingredient review/confirm screens - except `GET /healthz`. OIDC
login only gates the bridge's own UI: KitchenOwl access is still one shared
household/API token (`KITCHENOWL_*` above) regardless of who's logged in - there's
no per-user KitchenOwl access (see AGENTS.md's deferred multi-user decision).
The app is expected to run behind a TLS-terminating reverse proxy that forwards
`X-Forwarded-Proto`/`X-Forwarded-Host`, so the OIDC redirect URI it generates
matches its real public URL. There's also no database - nothing persists across
requests or restarts.

## Running

```bash
uv run flask --app bridge.app:create_app run
```

`GET /healthz` should respond with `{"status": "ok"}`.

## Testing

```bash
uv run pytest
uv run ruff check .
```

Unit and integration tests are plain pytest with no external services. Acceptance
(BDD) scenarios drive a real Chromium browser via Playwright against a real Flask
server - so `uv run playwright install chromium` (see Setup above) is required for
the full suite, not just a subset - accepting the slower runtime in exchange for
exercising real DOM rendering and client-side JS (e.g. htmx) rather than bypassing
them. How the two external services are faked differs:

- **Mealie** is stubbed with `requests_mock` for most scenarios - tests never call
  a live Mealie there.
- The **OIDC provider** is a real identity provider in a container
  (`mock-oauth2-server`, `tests/bdd/oidc_container.py`), like KitchenOwl below, so
  the app's actual Authlib login code runs end to end against a real discovery
  document, token endpoint, and JWKS - with its interactive login page disabled, so
  a browser navigating through it completes the whole authorization-code flow in a
  single hop, with nothing to click.
- **KitchenOwl** scenarios run against a **real KitchenOwl instance in a
  container** instead of a mock, so tests can't drift from what KitchenOwl actually
  does. This is why the suite needs a working local Docker (or Podman, see below)
  daemon - the KitchenOwl image is pulled and started automatically, no manual
  `docker compose up` needed for tests.

One scenario also runs against a **real Mealie instance in a container** (like
KitchenOwl's), driving an actual browser click through Mealie's own UI - this is
the only way to catch bugs in how Mealie's frontend actually triggers the bridge
(see AGENTS.md), which a direct HTTP call to `/recipes/action` can't.

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

Released versions are also published as prebuilt images to
`ghcr.io/languitar/mealie-kitchenowl-bridge`, tagged with the released
version (e.g. `v1.2.3`) and `latest`. Every commit on `main` that passes CI is
additionally published under `dev`, its short commit hash, and the build date
(e.g. `2026-07-29`), for testing unreleased changes.

## Architecture & conventions

- `src/` layout, package name `bridge`. `uv.lock` pins all dependencies -
  regenerate it with `uv lock` after changing dependencies, and commit the updated
  lockfile.
- Flask blueprints per concern, registered in `src/bridge/app.py`.
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

Pull requests are checked against this format with
[commitlint](https://commitlint.js.org/) (`commitlint.config.js`) in CI.

## Releases

Merges to `main` are released automatically with
[semantic-release](https://semantic-release.gitbook.io/) (`.releaserc.json`),
based on the conventional-commit types since the last release: `fix` bumps a
patch version, `feat` bumps a minor version, and a `BREAKING CHANGE:` footer
bumps a major version. A release updates `pyproject.toml` and `uv.lock` and
publishes a GitHub release with generated notes - all pushed back to `main` by
the workflow, so no manual version bumping or tagging is needed.

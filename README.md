# Mealie ↔ KitchenOwl Bridge

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

The default suite needs a working local Docker daemon: scenarios that exercise
KitchenOwl run against a real instance in a container (started automatically) rather
than a mock, so tests can't drift from KitchenOwl's actual API behavior - see
AGENTS.md.

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

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
uv run pytest              # fast suite: unit, integration, and Flask-test-client BDD scenarios
uv run pytest -m browser   # browser-driven BDD scenarios (needs `playwright install chromium`)
uv run ruff check .
```

## Docker

```bash
docker compose up --build
```

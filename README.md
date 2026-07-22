# Mealie ↔ KitchenOwl Bridge

Bridges a Mealie recipe action to a KitchenOwl shopping list: trigger from a recipe
in Mealie, review the ingredients in a small HTMX UI, and push them onto a
KitchenOwl shopping list.

This repo is currently a **skeleton**. See [AGENTS.md](AGENTS.md) for the BDD-driven
workflow used to build out real features, and for what's deliberately not built yet.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # then fill in real Mealie/KitchenOwl URLs and tokens
```

## Running

```bash
flask --app bridge.app:create_app run
```

`GET /healthz` should respond with `{"status": "ok"}`.

## Testing

```bash
pytest
ruff check .
```

## Docker

```bash
docker compose up --build
```

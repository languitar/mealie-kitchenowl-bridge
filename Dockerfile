FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

COPY src ./src
RUN uv sync --locked --no-dev

ENV FLASK_APP=bridge.app:create_app
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]

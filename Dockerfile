FROM ghcr.io/astral-sh/uv:0.9.11 AS uv
FROM python:3.12-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /srv/relaydesk
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY app ./app
RUN useradd --create-home --uid 10001 relaydesk && mkdir /data && chown relaydesk:relaydesk /data
USER relaydesk
EXPOSE 8000
CMD ["/srv/relaydesk/.venv/bin/uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

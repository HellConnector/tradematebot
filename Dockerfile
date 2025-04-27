ARG PYTHON_VERSION=3.13.3-alpine
ARG UV_VERSION=0.6.17

FROM ghcr.io/astral-sh/uv:${UV_VERSION} as uv
FROM python:${PYTHON_VERSION} as builder
COPY --from=uv /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --compile-bytecode --frozen --no-install-project --no-dev

FROM python:${PYTHON_VERSION} as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
ENV PYTHONBUFFERED 1
ENV PYTHONOPTIMIZE 1
ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PATH "${PATH}:/usr/local/bin"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY bot ./app/bot
COPY price_worker ./app/price_worker
COPY search_items_worker ./app/search_items_worker
COPY mini_app_api ./app/mini_app_api

ENTRYPOINT ["python", "-m", "bot.main" ]

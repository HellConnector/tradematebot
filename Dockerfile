ARG PYTHON_VERSION=3.11-slim-buster

FROM python:${PYTHON_VERSION} as builder
ARG POETRY_VERSION=1.8.2

RUN pip install --upgrade pip
RUN pip install poetry==${POETRY_VERSION}

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --without dev --no-root --no-directory && rm -rf ${POETRY_CACHE_DIR}

FROM python:${PYTHON_VERSION} as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY bot ./app/bot
COPY cs2-items-parser ./app/cs2-items-parser
COPY price-worker ./app/price-worker
COPY mini_app ./app/mini_app

ENV PYTHONBUFFERED 1
ENV PYTHONOPTIMIZE 1
ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PATH "${PATH}:/usr/local/bin"

ENTRYPOINT ["python", "-m", "bot.main" ]

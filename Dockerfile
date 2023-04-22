ARG PYTHON_VERSION=3.11-slim-buster

FROM python:${PYTHON_VERSION}
WORKDIR /bot

ENV PYTHONBUFFERED 1
ENV PYTHONOPTIMIZE 1

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY bot .
ENV PYTHONPATH "${PYTHONPATH}:/"

CMD ["python", "runner.py"]

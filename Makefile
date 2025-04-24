all: build_image

include .env

PYTHON_VERSION = 3.11-slim-buster
POETRY_VERSION = 1.8.5
IMAGE_NAME = hellconnector/tradematebot
IMAGE_TAG = $(PYTHON_VERSION)
PLATFORM = linux/amd64

.PHONY: build_image
build_image:
	docker build --platform=$(PLATFORM) \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg POETRY_VERSION=$(POETRY_VERSION) \
		--no-cache --pull --tag $(IMAGE_NAME):$(IMAGE_TAG) ./; \

.PHONY: upload_image
upload_image:
	docker push $(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: run_bot
run_bot:
	poetry run bot

.PHONY: run_price_worker
run_price_worker:
	poetry run price-worker

.PHONY: run_items2db_worker
run_items2db_worker:
	poetry run items2db-worker

.PHONY: run_mini_app_api
run_mini_app_api:
	poetry run mini-app-api

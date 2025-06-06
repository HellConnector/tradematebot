all: build_image

include .env

PYTHON_VERSION = 3.13.3-alpine
UV_VERSION = 0.6.17
IMAGE_NAME = hellconnector/tradematebot
IMAGE_TAG = $(PYTHON_VERSION)
PLATFORM = linux/amd64

.PHONY: build_image
build_image:
	docker build --platform=$(PLATFORM) \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg UV_VERSION=$(UV_VERSION) \
		--no-cache --pull --tag $(IMAGE_NAME):$(IMAGE_TAG) ./; \

.PHONY: upload_image
upload_image:
	docker push $(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: run_bot
run_bot:
	uv run bot

.PHONY: run_price_worker
run_price_worker:
	uv run price-worker

.PHONY: run_search_items_rowker
run_search_items_worker:
	uv run search-items-worker

.PHONY: run_mini_app_api
run_mini_app_api:
	uv run mini-app-api

.PHONY: clean
clean:
	rm -rfv dist .venv

.PHONY: prepare_dev
prepare_dev: clean
	uv sync --all-extras --compile-bytecode --all-groups --frozen

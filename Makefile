all: build_image

include .env
export

PYTHON_VERSION = 3.11-slim-buster
IMAGE_NAME = hellconnector/tradematebot
IMAGE_TAG = $(PYTHON_VERSION)

.PHONY: build_image
build_image:
	poetry export --without-hashes --format=requirements.txt > requirements.txt; \
	docker build --build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--no-cache --pull --tag $(IMAGE_NAME):$(IMAGE_TAG) ./; \
	rm -rfv requirements.txt;

.PHONY: upload_image
upload_image:
	docker push $(IMAGE_NAME):$(IMAGE_TAG)

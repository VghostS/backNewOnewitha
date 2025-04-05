IMAGE_NAME = unigram-payment_node-server-api:${VERSION}
CONTAINER_NAME = unigram-payment_node-server-api_container

PORT = 1000
VERSION = 1.0.3

build:
	docker build -t $(IMAGE_NAME) .

run: build
	docker run -d -p $(PORT):$(PORT) --name $(CONTAINER_NAME) $(IMAGE_NAME)

stop:
	docker stop $(CONTAINER_NAME) || true

restart: clean run

clean: stop
	docker rm $(CONTAINER_NAME) || true
	docker rmi $(IMAGE_NAME)

logs:
	docker logs -f $(CONTAINER_NAME)

help:
	@echo "Usage:"
	@echo " make build - Build the Docker image"
	@echo " make run - Start the Docker container"
	@echo " make stop - Stopping the Docker container."
	@echo " make restart - Restart the Docker container"
	@echo " make logs - View the Docker container logs"
	@echo " make clean - Deleting the Docker image"

all: docker

.PHONY: docker
docker:
	docker build -t hardplacepro:`git describe --tags --dirty` -t hardplacepro:latest .

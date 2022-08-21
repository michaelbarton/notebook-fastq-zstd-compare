# export COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1

benchmark SRC_FILE N_TIMES: image
	docker-compose run --rm runner \
	python3 /root/bin/benchmark.py \
		--input-file=/mnt/{{SRC_FILE}} \
		--output-csv-file=/mnt/out/benchmarks.csv \
		--iterations={{N_TIMES}} \
		--verbose

shell: image
	docker-compose run --rm runner /bin/bash

image:
	docker-compose build runner


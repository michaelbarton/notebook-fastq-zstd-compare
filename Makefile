export COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1

ITERATIONS = 10

all: image test out/benchmark.SRR7589561.small.csv

out/notebook.md: src/notebook.Rmd
	docker-compose run --rm notebook_builder \
		Rscript -e "rmarkdown::render('/mnt/$<', 'md_document', output_file = '/mnt/$@')"

out/benchmark.%.csv: data/%.fastq
	docker-compose run --rm runner \
	python3 /root/bin/benchmark.py \
		--input-file=/mnt/$< \
		--output-csv-file=/mnt/$@ \
		--iterations=${ITERATIONS} \
		--verbose


test: image
	docker-compose run --rm runner pytest .

shell: image
	docker-compose run --rm runner /bin/bash

image:
	docker-compose build runner


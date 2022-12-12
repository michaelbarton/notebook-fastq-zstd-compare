export COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1

ITERATIONS = 10
S3_BUCKET = s3://bioinformatics-zen/202212120000-use-zstd-for-raw-fastq/

all: out/benchmark.SRR7589561.csv out/notebook.md .token/sync

.token/sync: out/notebook.md
	mkdir -p .token
	aws s3 sync \
		--acl=public-read \
		--cache-control='max-age=604800, public' \
		out/notebook_files/figure-markdown_strict/ \
		${S3_BUCKET}
	touch $@

out/notebook.md: src/notebook.Rmd
	docker-compose run --rm notebook_builder \
		Rscript --vanilla -e "rmarkdown::render('/mnt/$<', 'md_document', output_file = '/mnt/$@')"

out/benchmark.%.csv: data/%.fastq
	docker-compose run --rm runner \
	python3 /root/bin/benchmark.py \
		--input-file=/mnt/$< \
		--output-csv-file=/mnt/$@ \
		--iterations=${ITERATIONS} \
		--verbose

test: image
	docker-compose run --rm runner pytest .

shell_py: image
	docker-compose run --rm runner /bin/bash

shell_r: image
	docker-compose run --entrypoint=/bin/bash --rm notebook_builder


image:
	docker-compose build runner
	docker-compose build notebook_builder

clean:
	rm -fr out .token

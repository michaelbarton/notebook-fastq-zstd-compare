export COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1

ITERATIONS = 10
SLUG = use-zstd-for-raw-fastq

SRC_IMG_DIR = out/notebook_files/figure-markdown_strict/
DST_IMG_URLS = https://s3.amazonaws.com/bioinformatics-zen/202212120000-${SLUG}/

S3_BUCKET = s3://bioinformatics-zen/202212120000-${SLUG}/
DST_FILE = /Users/michaelbarton/cache/bioinformatics-zen/post/${SLUG}.md

# all: out/benchmark.SRR7589561.csv ${DST_FILE}

# Strictly need the benchmark data for this but don't want to regenerate everytime
${DST_FILE}: out/notebook.njk.md src/front_matter.md .token/sync
	cp src/front_matter.md $@
	cat $< >> $@


.token/sync: out/notebook.md
	mkdir -p .token
	aws s3 sync \
		--acl=public-read \
		--cache-control='max-age=604800, public' \
		out/notebook_files/figure-markdown_strict/ \
		${S3_BUCKET}
	touch $@

out/notebook.njk.md: ~/cache/bioinformatics-zen/bin/convert_markdown_images_to_captions.py out/notebook.md
	 $^ \
		 $@ \
		--src-image-dir=/mnt/${SRC_IMG_DIR} \
		--dst-image-url=${DST_IMG_URLS} \
		--lede


out/notebook.md: src/notebook.Rmd
	docker-compose run --rm notebook_builder \
		Rscript --vanilla -e "rmarkdown::render('/mnt/$<', 'md_document', output_file = '/mnt/$@')"
	# Copy image card over
	cp src/image_card.jpg out/notebook_files/figure-markdown_strict/

out/notebook.html: src/notebook.Rmd
	docker-compose run --rm notebook_builder \
		Rscript --vanilla -e "rmarkdown::render('/mnt/$<', 'html_document', output_file = '/mnt/$@')"

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
	rm -fr out .token ${DST_FILE}

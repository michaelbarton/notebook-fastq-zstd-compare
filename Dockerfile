FROM buildpack-deps:bullseye AS cloudflare-builder
RUN git clone --depth 1 https://github.com/cloudflare/zlib cloudflare-zlib
WORKDIR cloudflare-zlib
RUN ./configure
RUN make


FROM buildpack-deps:bullseye AS libdeflate-builder
RUN apt-get update
RUN apt-get install --yes cmake
RUN git clone --depth 1 https://github.com/ebiggers/libdeflate.git
WORKDIR libdeflate
RUN cmake -B build && cmake --build build


FROM buildpack-deps:bullseye AS deflate-ng-builder
RUN apt-get update
RUN apt-get install --yes cmake
RUN git clone --depth 1 https://github.com/zlib-ng/zlib-ng.git
WORKDIR zlib-ng
RUN cmake .
RUN cmake --build . --config Release


FROM python:3
RUN apt-get update
RUN apt-get install --yes zstd pigz zopfli
RUN pip3 install click pytest
COPY --from=deflate-ng-builder zlib-ng/minigzip /usr/local/bin/minigzip-ng
COPY --from=cloudflare-builder cloudflare-zlib/minigzip /usr/local/bin/minigzip-cloudflare
COPY --from=libdeflate-builder libdeflate/build/programs/libdeflate-gzip /usr/local/bin/libdeflate-gunzip


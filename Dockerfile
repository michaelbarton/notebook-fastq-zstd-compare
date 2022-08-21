FROM python:3 AS minigzip-builder
RUN apt-get install --yes git
RUN git clone https://github.com/cloudflare/zlib cloudflare-zlib
WORKDIR cloudflare-zlib
RUN ./configure
RUN make

FROM python:3
RUN apt-get update
RUN apt-get install --yes zstd pigz git
COPY --from=minigzip-builder cloudflare-zlib/minigzip /usr/local/bin

RUN pip3 install click pytest
COPY bin/benchmark.py /root/bin/benchmark.py


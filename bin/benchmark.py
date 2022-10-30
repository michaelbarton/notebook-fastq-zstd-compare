import csv
import dataclasses
import logging
from pathlib import Path

import click

from lib import benchmark

from lib.compression_tool import (
    GZIP,
    GZIP_NG,
    GZIP_CLOUDFLARE,
    GZIP_LIB_DEFLATE,
    Z_STANDARD, GZIP_ZOPFLI,
)


@click.command("Benchmark file compression")
@click.option(
    "--input-file",
    "-i",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    required=True,
    help="Input file to benchmark.",
)
@click.option(
    "--output-csv-file",
    "-o",
    type=click.Path(exists=False),
    required=True,
    help="Output CSV file write results.",
)
@click.option("--iterations", "-n", type=int, required=True, help="Number of iterations to run.")
@click.option(
    "--verbose/--no-verbose", "-v", type=bool, help="How verbose to log output.", default=False
)
def main(input_file: str, output_csv_file: str, iterations: int, verbose: bool = False) -> None:
    if verbose:
        benchmark.LOGGER.setLevel(logging.DEBUG)

    zstd_compression_levels = list(range(2, 20))
    gzip_compression_levels = list(range(2, 10))
    with open(output_csv_file, "w") as fh_out:
        csv_out = csv.DictWriter(
            fh_out,
            fieldnames=[
                "method",
                "compress_time",
                "decompress_time",
                "compression_level",
                "compression_ratio",
            ],
        )
        csv_out.writeheader()
        for tool in [
            Z_STANDARD,
            GZIP_ZOPFLI,
            GZIP,
            GZIP_NG,
            GZIP_CLOUDFLARE,
            GZIP_LIB_DEFLATE,
        ]:
            benchmark_rows = benchmark.benchmark(
                tool=tool,
                src_file=Path(input_file),
                n_times=iterations,
                compression_levels=tool.allowed_levels,
            )
            for row in benchmark_rows:
                csv_out.writerow(dataclasses.asdict(row))


if __name__ == "__main__":
    main()

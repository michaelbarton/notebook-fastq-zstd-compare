import abc
import csv
import dataclasses
import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Any, Type, Callable

import pytest
import click

LOGGER = logging.getLogger("compression_benchmark")
logging.basicConfig()


@dataclasses.dataclass(frozen=True)
class BenchmarkRow:
    method: str
    compress_time: float
    decompress_time: float
    compression_level: int
    compression_ratio: float


class AbstractBenchmark(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def suffix(cls) -> str:
        ...

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        ...

    def exec(self, args: List[Any]):
        """Execute a third party tool."""
        cmd_str = " ".join([str(x) for x in args])
        proc: subprocess.CompletedProcess[bytes] = subprocess.run(
            cmd_str, shell=True, capture_output=True, check=False
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"Error running command: `{cmd_str}`\n\n'{proc.stderr.decode().strip()}'"
            )

    def run_time_s(self, func: Callable, *args: Any) -> float:
        """Call a function and return the time it took to execute in seconds."""
        start = time.time()
        func(*args)
        return time.time() - start

    @abc.abstractmethod
    def _compress(self, src_file: Path, dst_file: Path, compression_level: int) -> Path:
        ...

    @abc.abstractmethod
    def _decompress(self, src_file: Path) -> None:
        ...

    def benchmark(
        self, src_file: Path, n_times: int, compression_levels: List[int]
    ) -> List[BenchmarkRow]:
        """Benchmark a compression algorithm."""
        original_file_size = src_file.stat().st_size

        benchmark_rows: List[BenchmarkRow] = []

        for compression_level in compression_levels:
            for idx in range(n_times):
                dst_file = (
                    Path(tempfile.mkdtemp())
                    / f"{src_file.name}.{compression_level}.{self.suffix()}"
                )
                compression_time = self.run_time_s(
                    self._compress, src_file, dst_file, compression_level
                )
                file_size = dst_file.stat().st_size
                decompression_time = self.run_time_s(self._decompress, dst_file)
                compression_ratio = file_size / original_file_size
                benchmark_rows.append(
                    BenchmarkRow(
                        self.name(),
                        compression_time,
                        decompression_time,
                        compression_level,
                        compression_ratio,
                    )
                )

                for tmp_file in dst_file.parent.glob("*"):
                    tmp_file.unlink()

                LOGGER.debug(
                    "Benchmarked i=%s name=%s level=%s time=%.2f ratio=%.2f",
                    idx,
                    self.name(),
                    compression_level,
                    compression_time + decompression_time,
                    compression_ratio,
                )
            LOGGER.info("Finished benchmarking name=%s level=%s", self.name(), compression_level)

        return benchmark_rows


class GzipBenchmark(AbstractBenchmark):
    def suffix(cls) -> str:
        return "gz"

    def name(cls) -> str:
        return "gzip"

    def _compress(self, src_file: Path, dst_file: Path, compression_level: int) -> None:
        """Execute gzip on the given file."""
        self.exec(["gzip", f"-{compression_level}", src_file, "--to-stdout", ">", dst_file])

    def _decompress(self, src_file: Path) -> None:
        """Decompress given gzip file."""
        self.exec(["gzip", "-d", src_file])


class CloudFlareGzipBenchmark(AbstractBenchmark):
    def suffix(cls) -> str:
        return "gz"

    def name(cls) -> str:
        return "cloudflare_gzip"

    def _compress(self, src_file: Path, dst_file: Path, compression_level: int) -> None:
        """Execute gzip on the given file."""
        self.exec(["minigzip", f"-{compression_level}", "-c", src_file, ">", dst_file])

    def _decompress(self, src_file: Path) -> None:
        """Decompress given gzip file."""
        self.exec(["minigzip", "-d", src_file])


class ZstandardBenchmark(AbstractBenchmark):
    def suffix(cls) -> str:
        return "zst"

    def name(cls) -> str:
        return "zstd"

    def _compress(self, src_file: Path, dst_file: Path, compression_level: int) -> None:
        """Execute gzip on the given file."""
        self.exec(
            ["zstd", f"-{compression_level}", "-c", src_file, "--single-thread", ">", dst_file]
        )

    def _decompress(self, src_file: Path) -> None:
        """Decompress given gzip file."""
        self.exec(["zstd", "-d", src_file])


@pytest.mark.parametrize("benchmark", [CloudFlareGzipBenchmark, GzipBenchmark, ZstandardBenchmark])
def test_benchmarks(benchmark: Type[AbstractBenchmark]):
    """Test all benchmarks."""
    test_file = Path(tempfile.mkdtemp()) / "test.txt"
    test_file.write_text("Quick brown fox jumps over the lazy dog\n")
    results = benchmark().benchmark(test_file, 1, [1])
    assert results
    assert results[0].method == benchmark().name()


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
        LOGGER.setLevel(logging.DEBUG)

    zstd_compression_levels = list(range(2, 19))
    gzip_compression_levels = list(range(2, 9))
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
        for benchmark in [GzipBenchmark, CloudFlareGzipBenchmark, ZstandardBenchmark]:
            compression_levels = (
                zstd_compression_levels
                if benchmark is ZstandardBenchmark
                else gzip_compression_levels
            )
            benchmark_rows = benchmark().benchmark(
                src_file=Path(input_file), n_times=iterations, compression_levels=compression_levels
            )
            for row in benchmark_rows:
                csv_out.writerow(dataclasses.asdict(row))


if __name__ == "__main__":
    main()

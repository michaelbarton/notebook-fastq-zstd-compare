import dataclasses
import itertools
import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Any, Callable

from lib import compression_tool

LOGGER = logging.getLogger("compression_benchmark")
logging.basicConfig()


@dataclasses.dataclass(frozen=True)
class BenchmarkRow:
    method: str
    compress_time: float
    decompress_time: float
    compression_level: int
    compression_ratio: float


def exec(args: List[Any]):
    """Execute a third party tool."""
    cmd_str = " ".join([str(x) for x in args])
    proc: subprocess.CompletedProcess[bytes] = subprocess.run(
        cmd_str, shell=True, capture_output=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Error running command: `{cmd_str}`\n\n'{proc.stderr.decode().strip()}'"
        )


def run_time_s(func: Callable, *args: Any) -> float:
    """Call a function and return the time it took to execute in seconds."""
    start = time.time()
    func(*args)
    return time.time() - start


def _exec_single_iteration(
    tool: compression_tool.CompressionTool,
    src_file: Path,
    compression_level: int,
    idx: int,
) -> BenchmarkRow:
    original_file_size = src_file.stat().st_size
    dst_file = Path(tempfile.mkdtemp()) / f"{src_file.name}.{compression_level}.{tool.file_suffix}"
    compression_time = run_time_s(exec, tool.compress_cmd(compression_level, src_file, dst_file))
    file_size = dst_file.stat().st_size
    decompression_time = run_time_s(exec, tool.decompress_cmd(dst_file))
    compression_ratio = file_size / original_file_size
    for tmp_file in dst_file.parent.glob("*"):
        tmp_file.unlink()

    LOGGER.debug(
        "Benchmarked i=%s name=%s level=%s time=%.2f ratio=%.2f",
        idx,
        tool.name,
        compression_level,
        compression_time + decompression_time,
        compression_ratio,
    )
    return BenchmarkRow(
        tool.name,
        compression_time,
        decompression_time,
        compression_level,
        compression_ratio,
    )


def benchmark(
    tool: compression_tool.CompressionTool,
    src_file: Path,
    n_times: int,
    compression_levels: List[int],
) -> List[BenchmarkRow]:
    """Benchmark a compression algorithm."""
    args = ((tool, src_file, *x) for x in itertools.product(compression_levels, range(n_times)))
    results = [_exec_single_iteration(*arg) for arg in args]
    LOGGER.info("Benchmarking %s finished", tool.name)
    return results

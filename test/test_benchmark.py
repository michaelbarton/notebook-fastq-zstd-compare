import tempfile
from pathlib import Path

import pytest

from lib import benchmark

from lib.compression_tool import (
    GZIP,
    GZIP_NG,
    GZIP_CLOUDFLARE,
    GZIP_LIB_DEFLATE,
    GZIP_ZOPFLI,
    Z_STANDARD,
    CompressionTool,
)


@pytest.mark.parametrize(
    "tool", [GZIP, GZIP_NG, GZIP_CLOUDFLARE, GZIP_LIB_DEFLATE, GZIP_ZOPFLI, Z_STANDARD]
)
def test_benchmarks(tool: CompressionTool):
    """Test all benchmarks."""
    test_file = Path(tempfile.mkdtemp()) / "test.txt"
    test_file.write_text("Quick brown fox jumps over the lazy dog\n")
    results = benchmark.benchmark(tool, test_file, 1, [1])
    assert results
    assert results[0].method == tool.name

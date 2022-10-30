import dataclasses
from pathlib import Path
from typing import Callable, List

CompressCommand = Callable[[Path, Path, int], List[str]]
DecompressCommand = Callable[[Path], List[str]]


@dataclasses.dataclass(frozen=True)
class CompressionTool:
    name: str
    file_suffix: str
    compress_cmd: CompressCommand
    decompress_cmd: DecompressCommand
    allowed_levels: List[int]


GZIP = CompressionTool(
    name="gzip",
    file_suffix="gz",
    compress_cmd=lambda level, src, dst: [
        "gzip",
        f"-{level}",
        src,
        "--to-stdout",
        ">",
        dst,
    ],
    decompress_cmd=lambda src: ["gzip", "-d", src],
    allowed_levels=[1,2,3,4,5,6,7,8,9]
)

GZIP_LIB_DEFLATE = CompressionTool(
    name="gzip_libdeflate",
    file_suffix="gz",
    compress_cmd=lambda level, src, dst: [
        "libdeflate-gzip",
        f"-{level}",
        src,
        "-c",
        ">",
        dst,
    ],
    decompress_cmd=lambda src: ["libdeflate-gunzip", "-d", src],
    allowed_levels=[1, 2, 3, 4, 5, 6, 7, 8, 9]
)

GZIP_CLOUDFLARE = CompressionTool(
    name="gzip_cloudflare",
    file_suffix="gz",
    compress_cmd=lambda level, src, dst: ["minigzip-cloudflare", f"-{level}", "-c", src, ">", dst],
    decompress_cmd=lambda src: ["minigzip-cloudflare", "-d", src],
    allowed_levels=[1, 2, 3, 4, 5, 6, 7, 8, 9]
)

GZIP_NG = CompressionTool(
    name="gzip_ng",
    file_suffix="gz",
    compress_cmd=lambda level, src, dst: ["minigzip-ng", f"-{level}", "-c", src, ">", dst],
    decompress_cmd=lambda src: ["minigzip-ng", "-d", src],
    allowed_levels=[1, 2, 3, 4, 5, 6, 7, 8, 9]
)

GZIP_ZOPFLI = CompressionTool(
    name="zopfli",
    file_suffix="gz",
    compress_cmd=lambda level, src, dst: ["zopfli", "-c", src, ">", dst],
    decompress_cmd=lambda src: ["gzip", "-d", src],
    allowed_levels=[11]
)

Z_STANDARD = CompressionTool(
    name="zstd",
    file_suffix="zst",
    compress_cmd=lambda level, src, dst: [
        "zstd",
        f"-{level}",
        "-c",
        src,
        "--single-thread",
        ">",
        dst,
    ],
    decompress_cmd=lambda src: ["zstd", "-d", src],
    allowed_levels=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19]
)

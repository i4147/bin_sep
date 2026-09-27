import sys
from collections.abc import Iterable, Sequence
from multiprocessing import Pool
from pathlib import Path
from typing import Final, List, Optional, Tuple
from loguru import logger

POOL_SIZE = 8
LARGE_FILE_THRESHOLD = 10_000
MIN_CHUNK_SIZE = 1_000
CODE_EXT = frozenset(
    {
        ".py",
        ".js",
        ".ts",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".java",
        ".go",
        ".rs",
        ".rb",
        ".sh",
        ".lua",
    }
)
FileLines = tuple[Path, list[str]]
DiffChunkArgs = tuple[list[str], "frozenset[str]", str]


def count_lines(path):
    return path.read_bytes().count(b"\n") + 1


def strip_indentation(lines):
    return [line.strip(" \t") for line in lines]


def read_file_task(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines(keepends=False)
    if path.suffix.lower() in CODE_EXT:
        lines = strip_indentation(lines)
    return path, lines


def filter_diff_chunk(args):
    chunk, exclude_set, mode = args
    if mode == "only_in_first":
        return [p for p in chunk if p not in exclude_set]
    return [p for p in chunk if p in exclude_set]


def _chunked(lines, size):
    return [lines[i : i + size] for i in range(0, len(lines), size)]


def report_diff_lines(path1, path2):
    lines1_count = count_lines(path1)
    lines2_count = count_lines(path2)
    with Pool(processes=POOL_SIZE) as pool:
        file_map = {}
        for path, lines in pool.imap_unordered(read_file_task, [path1, path2]):
            file_map[path] = lines
    lines1 = file_map[path1]
    lines2 = file_map[path2]
    set1 = set(lines1)
    set2 = set(lines2)
    if lines1_count > LARGE_FILE_THRESHOLD and lines2_count > LARGE_FILE_THRESHOLD:
        chunk_size = max(MIN_CHUNK_SIZE, len(lines1) // POOL_SIZE)
        chunks = _chunked(lines1, chunk_size)
        frozen2 = frozenset(set2)
        args_list = [(chunk, frozen2, "only_in_first") for chunk in chunks]
        only_in_first = []
        with Pool(processes=POOL_SIZE) as pool:
            for partial in pool.imap_unordered(filter_diff_chunk, args_list):
                only_in_first.extend(partial)
    else:
        only_in_first = [p for p in lines1 if p not in set2]
    only_in_second = [p for p in lines2 if p not in set1]
    common_count = len(set1 & set2)
    if only_in_first:
        logger.info("only in {}:", path1.name)
        for line in only_in_first:
            logger.opt(colors=True).info("<green>  - {}</green>", line)
    if only_in_second:
        logger.info("only in {}:", path2.name)
        for line in only_in_second:
            logger.opt(colors=True).info("<yellow>  - {}</yellow>", line)
    logger.opt(colors=True).info(
        "<blue>common lines: {}\nonly in {}: {}\nonly in {}: {}</blue>",
        common_count,
        path1.name,
        len(only_in_first),
        path2.name,
        len(only_in_second),
    )


def main(argv=None):
    args = list(argv) if argv is not None else sys.argv[1:]
    if len(args) != 2:
        logger.error("Usage: python difflines.py <file1> <file2>")
        return 1
    f1 = Path(args[0])
    f2 = Path(args[1])
    report_diff_lines(f1, f2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

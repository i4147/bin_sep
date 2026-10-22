import argparse
from collections.abc import Generator
from multiprocessing import Pool
from multiprocessing.pool import AsyncResult
from pathlib import Path
from typing import Final
import chardet
from dh import get_nobinary, is_binary
from loguru import logger

MAX_WORKERS = 8
SAMPLE_SIZE = 100_000
ConvertResult = tuple[Path, bool, str]


def detect_encoding(file_path):
    try:
        with file_path.open("rb") as f:
            raw_data = f.read(SAMPLE_SIZE)
        result = chardet.detect(raw_data)
        encoding = result.get("encoding")
        if isinstance(encoding, str) and encoding:
            return encoding
        return "utf-8"
    except Exception:
        return "utf-8"


def convert_file(file_path):
    try:
        if is_binary(file_path):
            return file_path, False, "Skipped (binary/unsupported)"
        encoding = detect_encoding(file_path)
        if encoding.lower() == "utf-8":
            return file_path, True, "Already UTF8"
        with file_path.open("r", encoding=encoding, errors="replace") as f:
            content = f.read()
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content)
        return file_path, True, f"Converted from {encoding}"
    except Exception as exc:
        return file_path, False, f"Error: {exc!s}"


def collect_files(paths):
    for path_str in paths:
        path = Path(path_str).resolve()
        if path.is_file():
            yield path
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file():
                    yield child
        else:
            logger.warning(f"⚠ {path} not found")


def main():
    parser = argparse.ArgumentParser(
        description="Convert non-UTF8 files to UTF8 encoding (in-place)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python script.py                    # Process current directory\n"
            "  python script.py ./src ./docs       # Process specific directories\n"
            "  python script.py file.txt dir/      # Process file and directory"
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to process (default: current directory)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed output for each file",
    )
    args = parser.parse_args()
    input_paths = list(args.paths) if args.paths else ["."]
    cwd = Path.cwd()
    if args.paths:
        files = list(collect_files(input_paths))
    else:
        files = list(get_nobinary(cwd))
    if not files:
        print("No files to process.")
        return 0
    print(f"Processing {len(files)} file(s) with {MAX_WORKERS} worker(s)...\n")
    converted = 0
    skipped = 0
    errors = 0
    with Pool(processes=MAX_WORKERS) as pool:
        async_results = [pool.apply_async(convert_file, (f,)) for f in files]
        for async_res in async_results:
            file_path, success, message = async_res.get()
            if args.verbose:
                status = "✓" if success else "✗"
                try:
                    rel = file_path.relative_to(cwd)
                except ValueError:
                    rel = file_path
                print(f"{status} {rel} - {message}")
            if success:
                if "Already UTF8" in message or "Skipped" in message:
                    skipped += 1
                else:
                    converted += 1
            else:
                errors += 1
    print("=" * 40)
    print("Summary:")
    print(f"  Converted: {converted}")
    print(f"  Skipped:   {skipped}")
    print(f"  Errors:    {errors}")
    print("=" * 40)
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

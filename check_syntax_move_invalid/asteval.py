import argparse
import ast
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Final
from dh import get_pyfiles
from loguru import logger

POOL_SIZE = 8
"""Fixed number of worker processes used for concurrent file processing."""
ERROR_DIR_NAME = "error"
"""Name of the subdirectory where invalid Python files are copied."""


def process_file(args):
    path, counter, total, dry_run = args
    path = Path(path)
    prefix = "[DRY RUN] " if dry_run else ""
    print(f"{prefix}[{counter}/{total}] {path.name}")
    try:
        content = path.read_text(encoding="utf-8")
        ast.parse(content)
        if dry_run:
            print(f"  ✅ {path.name} - Valid Python syntax")
        return
    except (SyntaxError, ValueError, UnicodeDecodeError, OSError) as e:
        error_dir = path.parent / ERROR_DIR_NAME
        new_path = error_dir / path.name
        if dry_run:
            print(f"  🔍 Would move to: {new_path} | Error: {e}")
            return
        error_dir.mkdir(exist_ok=True)
        if new_path.exists():
            base = path.stem
            ext = path.suffix
            idx = 1
            while new_path.exists():
                new_path = error_dir / f"{base}_{idx}{ext}"
                idx += 1
        try:
            raw = path.read_bytes()
            new_path.write_bytes(raw)
            logger.warning(f"  ⚠️  copied to: {new_path} | Error: {e}")
        except OSError as move_error:
            logger.error(f"  ❌ Failed to move {path}: {move_error}")


def get_files_to_process(paths):
    files = []
    if paths:
        for path_str in paths:
            p = Path(path_str)
            if p.is_file() and p.suffix == ".py":
                files.append(p)
            elif p.is_dir():
                files.extend(get_pyfiles(p))
            else:
                logger.warning(f"⚠️  Skipping: {path_str} (not a .py file or directory)")
    else:
        files = get_pyfiles(Path.cwd())
    seen = set()
    unique_files = []
    for f in files:
        resolved = f.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_files.append(f)
    return unique_files


def process_files(files, dry_run=False):
    total = len(files)
    if total == 0:
        return
    args_list = [(path, idx, total, dry_run) for idx, path in enumerate(files, 1)]
    with Pool(processes=POOL_SIZE) as pool:
        async_results = [pool.apply_async(process_file, (arg,)) for arg in args_list]
        for result in async_results:
            try:
                result.get()
            except Exception as e:
                logger.error(f"  ❌ Unexpected error in worker: {e}")


def build_parser():
    parser = argparse.ArgumentParser(
        description=("Check Python files for syntax errors and move invalid ones to 'error' directories"),
        epilog="Example: python script.py --dry-run /path/to/project",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to process (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be done without actually moving files",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        files = get_files_to_process(args.paths)
    except Exception as e:
        logger.error(f"❌ Error collecting files: {e}")
        return 1
    if not files:
        print("ℹ️  No Python files found to process.")
        return 0
    print(f"📁 Found {len(files)} Python file(s) to process")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be moved")
        print("-" * 40)
    try:
        process_files(files, dry_run=bool(args.dry_run))
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Error processing files: {e}")
        return 1
    if args.dry_run:
        print("-" * 40)
        print("🔍 DRY RUN COMPLETE - No files were moved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import sys
from collections.abc import Iterable
from multiprocessing import Pool
from pathlib import Path
from typing import Final
from dh import is_binary
from loguru import logger

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".so",
    ".dll",
    ".dylib",
    ".class",
    ".exe",
    ".bin",
    ".dat",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".ico",
    ".svg",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".wav",
    ".flac",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".eot",
    ".min.js",
    ".min.css",
}
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".tox",
    ".eggs",
    ".idea",
    ".vscode",
    "vendor",
    "bower_components",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
POOL_SIZE = 8
ProcessResult = tuple[Path, int, str | None, bool]


def remove_comments_from_content(content):
    lines = content.split("\n")
    modified_lines = []
    removed_count = 0
    in_multiline_string = False
    string_delimiter = None
    for line in lines:
        if in_multiline_string:
            modified_lines.append(line)
            if string_delimiter is not None and string_delimiter in line:
                in_multiline_string = False
                string_delimiter = None
            continue
        if '"""' in line or "'''" in line:
            for delim in ('"""', "'''"):
                if delim in line:
                    if line.count(delim) % 2 == 1:
                        in_multiline_string = not in_multiline_string
                        string_delimiter = delim if in_multiline_string else None
                    modified_lines.append(line)
                    break
            continue
        stripped = line.strip()
        if not stripped:
            modified_lines.append(line)
            continue
        if stripped.startswith("#"):
            removed_count += 1
            modified_lines.append("")
            continue
        quote_char = None
        comment_pos = -1
        for i, char in enumerate(line):
            if char in ('"', "'"):
                if quote_char is None:
                    quote_char = char
                elif quote_char == char:
                    quote_char = None
            elif char == "#" and quote_char is None:
                comment_pos = i
                break
        if comment_pos != -1:
            before_comment = line[:comment_pos].strip()
            removed_count += 1
            if before_comment:
                modified_lines.append(line[:comment_pos].rstrip())
            else:
                modified_lines.append("")
        else:
            modified_lines.append(line)
    return "\n".join(modified_lines), removed_count


def is_ignored_extension(path):
    suffix = path.suffix.lower()
    if suffix in EXCLUDE_EXTENSIONS:
        return True
    suffixes = path.suffixes
    if len(suffixes) > 1:
        double_suffix = "".join(suffixes[-2:]).lower()
        if double_suffix in EXCLUDE_EXTENSIONS:
            return True
    return False


def is_hidden(path):
    return any(part.startswith(".") for part in path.parts)


def process_file(path):
    try:
        if is_binary(str(path)):
            return path, 0, None, True
        original_content = path.read_text(encoding="utf-8")
        modified_content, removed_count = remove_comments_from_content(original_content)
        if removed_count > 0:
            path.write_text(modified_content, encoding="utf-8")
        return path, removed_count, None, False
    except UnicodeDecodeError:
        return path, 0, "Unable to read as text file (encoding issue)", True
    except Exception as exc:
        return path, 0, str(exc), False


def find_target_files(
    root_dir,
    include_hidden=False,
    exclude_dirs=None,
    ignore_extensions=True,
):
    if exclude_dirs is None:
        exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
    target_files = []
    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(excluded in path.parts for excluded in exclude_dirs):
            continue
        if not include_hidden and is_hidden(path):
            continue
        if ignore_extensions and is_ignored_extension(path):
            continue
        try:
            if path.stat().st_size > MAX_FILE_SIZE_BYTES:
                continue
        except OSError:
            continue
        target_files.append(path)
    return target_files


def _build_parser():
    parser = argparse.ArgumentParser(description="Remove comments from non-binary files using # comment syntax")
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to process (default: current directory)",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories (starting with .)",
    )
    parser.add_argument(
        "--no-ignore-extensions",
        action="store_true",
        help="Process files with typically ignored extensions",
    )
    parser.add_argument(
        "--exclude-dirs",
        nargs="+",
        help="Additional directories to exclude",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed processing information",
    )
    return parser


def _iter_results(
    results,
    total,
    root_dir,
    verbose,
):
    total_removed = 0
    files_changed = 0
    files_with_errors = 0
    binary_files = 0
    completed = 0
    for path, removed, error, was_binary in results:
        completed += 1
        try:
            rel = path.relative_to(root_dir)
        except ValueError:
            rel = path
        if was_binary:
            binary_files += 1
            if verbose:
                logger.debug("[{}/{}] Skipped binary: {}", completed, total, rel)
        elif error:
            logger.error("[{}/{}] Error: {}: {}", completed, total, rel, error)
            files_with_errors += 1
        elif removed > 0:
            print(
                "[{}/{}] Removed {} comment(s): {}",
                completed,
                total,
                removed,
                rel,
            )
            total_removed += removed
            files_changed += 1
        else:
            if verbose:
                logger.debug("[{}/{}] No changes: {}", completed, total, rel)
    return total_removed, files_changed, files_with_errors, binary_files, completed


def main():
    parser = _build_parser()
    args = parser.parse_args()
    root_dir = Path(args.directory).resolve()
    if not root_dir.exists():
        logger.error("Directory '{}' does not exist", root_dir)
        return 1
    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
    if args.exclude_dirs:
        exclude_dirs.update(args.exclude_dirs)
    print("Scanning directory: {}", root_dir)
    print("Finding non-binary files...")
    target_files = find_target_files(
        root_dir,
        include_hidden=bool(args.include_hidden),
        exclude_dirs=exclude_dirs,
        ignore_extensions=not bool(args.no_ignore_extensions),
    )
    if not target_files:
        print("No files found to process.")
        return 0
    print("Found {} file(s) to check", len(target_files))
    if args.dry_run:
        print("[Dry Run] Would check these files:")
        for f in sorted(target_files)[:20]:
            print("  {}", f.relative_to(root_dir))
        if len(target_files) > 20:
            print("  ... and {} more files", len(target_files) - 20)
        return 0
    total_removed = 0
    files_changed = 0
    files_with_errors = 0
    binary_files = 0
    print("Processing files in parallel with {} workers...", POOL_SIZE)
    results = []
    try:
        with Pool(processes=POOL_SIZE) as pool:
            async_results = [pool.apply_async(process_file, (path,)) for path in target_files]
            for async_result in async_results:
                try:
                    results.append(async_result.get())
                except Exception as exc:
                    logger.exception("Unexpected error in worker: {}", exc)
                    files_with_errors += 1
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    (
        total_removed,
        files_changed,
        files_with_errors_extra,
        binary_files,
        _completed,
    ) = _iter_results(results, len(target_files), root_dir, bool(args.verbose))
    files_with_errors += files_with_errors_extra
    print("{}", "=" * 40)
    print("Summary:")
    print("  Files scanned: {}", len(target_files))
    print("  Binary files skipped: {}", binary_files)
    print("  Files changed: {}", files_changed)
    print("  Total comments removed: {}", total_removed)
    if files_with_errors > 0:
        print("  Files with errors: {}", files_with_errors)
    print("{}", "=" * 40)
    return 0


if __name__ == "__main__":
    sys.exit(main())

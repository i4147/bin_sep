#!/usr/bin/env python3
"""LineEditOpsUnified for line_edit_ops.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (12):
  add2lines <- add2lines.py (16L): top-level script
  appender <- appender.py (9L): top-level script [no __main__ guard (top-level script or library fragment; exec runs top-level code)]
  bnn <- bnn.py (210L): is_text_file() + 4 more
  f45 <- f45.py (82L): wrap_text_content() + 1 more
  gll <- gll.py (48L): main() + 0 more
  joinlines <- joinlines.py (16L): main() + 0 more
  mvl <- mvl.py (31L): move_lines() + 0 more
  nnb <- nnb.py (16L): main() + 0 more
  sortbylen <- sortbylen.py (23L): sort_by_length() + 0 more [requires missing module 'dh' (ImportError at runtime)]
  striper <- striper.py (21L): remove_spaces_from_file() + 0 more
  tnn <- tnn.py (37L): process_file() + 1 more [requires missing module 'dh' (ImportError at runtime)]
  xlr <- xlr.py (15L): process_file() + 0 more

Usage:
  python main.py --list
  python main.py --info <tool>
  python main.py <tool> [args ...]
  python main.py <tool> --help  (passthrough when supported)

Notes:
- Each subcommand execs the embedded original source with isolated globals,
  sys.argv patched to [source_file] + args, and __name__ == "__main__".
- Missing third-party deps (e.g. 'dh') or SyntaxErrors fail plainly at runtime;
  nothing is simulated or faked.
- Multi-tool folder: first arg must be a tool name; use --list to see names.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

_ADD2LINES_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) != 3:\n'
    '        print(f"Usage: {sys.argv[0]} <filename> <prefix_string>", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    fn = Path(sys.argv[1])\n'
    '    str_to_add = sys.argv[2]\n'
    '    if not fn.is_file():\n'
    '        print(f"Error: {fn} does not exist or is not a file", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    lines = fn.read_text().splitlines(keepends=True)\n'
    '    newlines = [f"{str_to_add} {line}" if line.strip() else line for line in lines]\n'
    '    fn.write_text("".join(newlines))\n'
    '    print(f"{fn} updated")\n'
)

_APPENDER_SOURCE: str = (
    'from pathlib import Path\n'
    '\n'
    'text = "\\n#migrate from logging with print and standard logging module to loguru\\n"\n'
    'for py_file in Path.cwd().glob("*.py"):\n'
    '    try:\n'
    '        py_file.write_text(py_file.read_text(encoding="utf-8") + text, encoding="utf-8")\n'
    '        print(f"✓ Updated: {py_file.name}")\n'
    '    except Exception as e:\n'
    '        print(f"✗ Error: {py_file.name} - {e}")\n'
)

_BNN_SOURCE: str = (
    'import argparse\n'
    'import logging\n'
    'import shutil\n'
    'import tempfile\n'
    'from collections.abc import Generator\n'
    'from dataclasses import dataclass\n'
    'from pathlib import Path\n'
    'from joblib import Parallel, delayed\n'
    '\n'
    'logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")\n'
    'logger = logging.getLogger(__name__)\n'
    '\n'
    '\n'
    '@dataclass\n'
    'class FileStats:\n'
    '    replacements = 0\n'
    '    original_size = 0\n'
    '    new_size = 0\n'
    '    error_msg = None\n'
    '\n'
    '    def __str__(self):\n'
    '        relpath = self.path.relative_to(Path.cwd())\n'
    '        if not self.success:\n'
    '            return f"✗ {relpath}: {self.error_msg}"\n'
    '        size_delta = self.new_size - self.original_size\n'
    '        size_change = f"({size_delta:+d} bytes)" if size_delta != 0 else "(no size change)"\n'
    '        return f"✓ {relpath}: {self.replacements} replacements {size_change}"\n'
    '\n'
    '\n'
    'def is_text_file(path, max_sample=8192):\n'
    '    try:\n'
    '        with open(path, "rb") as f:\n'
    '            chunk = f.read(max_sample)\n'
    '            return b"\\x00" not in chunk\n'
    '    except OSError:\n'
    '        return False\n'
    '\n'
    '\n'
    'def should_process_file(path, text_only=True):\n'
    '    if path.is_dir() or path.is_symlink():\n'
    '        return False\n'
    '    return not (text_only and not is_text_file(path))\n'
    '\n'
    '\n'
    'def collect_files(inputs):\n'
    '    for input_path in inputs:\n'
    '        path = Path(input_path).resolve()\n'
    '        if path.is_file():\n'
    '            if should_process_file(path):\n'
    '                yield path\n'
    '        elif path.is_dir():\n'
    '            for path in path.rglob("*"):\n'
    '                if should_process_file(path):\n'
    '                    yield path\n'
    '        else:\n'
    '            logger.warning(f"Path not found: {path}")\n'
    '\n'
    '\n'
    'def process_file_chunked(\n'
    '    path,\n'
    '    chunk_size=1024 * 1024,\n'
    '):\n'
    '    stats = FileStats(path=path, success=True)\n'
    '    try:\n'
    '        stats.original_size = path.stat().st_size\n'
    '        with tempfile.NamedTemporaryFile(\n'
    '            mode="w",\n'
    '            delete=False,\n'
    '            encoding="utf-8",\n'
    '            newline="",\n'
    '        ) as temp_file:\n'
    '            temp_path = Path(temp_file.name)\n'
    '            try:\n'
    '                total_replacements = 0\n'
    '                with open(path, "r", encoding="utf-8", errors="replace") as f:\n'
    '                    buffer = ""\n'
    '                    while True:\n'
    '                        chunk = f.read(chunk_size)\n'
    '                        if not chunk:\n'
    '                            if buffer:\n'
    '                                new_buffer, count = (\n'
    '                                    buffer.replace("\\\\n", "\\n"),\n'
    '                                    buffer.count("\\\\n"),\n'
    '                                )\n'
    '                                temp_file.write(new_buffer)\n'
    '                                total_replacements += count\n'
    '                            break\n'
    '                        buffer += chunk\n'
    '                        last_safe_pos = len(buffer)\n'
    '                        if buffer.endswith("\\\\"):\n'
    '                            last_safe_pos -= 1\n'
    '                        processable = buffer[:last_safe_pos]\n'
    '                        buffer = buffer[last_safe_pos:]\n'
    '                        new_content, count = (\n'
    '                            processable.replace("\\\\n", "\\n"),\n'
    '                            processable.count("\\\\n"),\n'
    '                        )\n'
    '                        temp_file.write(new_content)\n'
    '                        total_replacements += count\n'
    '                stats.replacements = total_replacements\n'
    '            except Exception as e:\n'
    '                temp_path.unlink()\n'
    '                raise\n'
    '            temp_path.chmod(path.stat().st_mode)\n'
    '        stats.new_size = temp_path.stat().st_size\n'
    '        shutil.move(str(temp_path), str(path))\n'
    '    except UnicodeDecodeError as e:\n'
    '        stats.success = False\n'
    '        stats.error_msg = f"Encoding error: {e}"\n'
    '        if temp_path.exists():\n'
    '            temp_path.unlink()\n'
    '    except PermissionError as e:\n'
    '        stats.success = False\n'
    '        stats.error_msg = f"Permission denied: {e}"\n'
    '        if temp_path.exists():\n'
    '            temp_path.unlink()\n'
    '    except Exception as e:\n'
    '        stats.success = False\n'
    '        stats.error_msg = f"Error: {type(e).__name__}: {e}"\n'
    '        if temp_path.exists():\n'
    '            temp_path.unlink()\n'
    '    return stats\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Replace literal \\\\n with actual newlines in files",\n'
    '        formatter_class=argparse.RawDescriptionHelpFormatter,\n'
    '        epilog="""\n'
    'Examples:\n'
    '  %(prog)s\n'
    '  %(prog)s file.txt\n'
    '  %(prog)s dir1 dir2 file.txt\n'
    '  %(prog)s --workers 8 --chunk-size 2M dir/\n'
    '        """,\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "inputs",\n'
    '        nargs="*",\n'
    '        help="Files or directories to process (default: current directory)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-w",\n'
    '        "--workers",\n'
    '        type=int,\n'
    '        default=4,\n'
    '        help="Number of parallel workers (default: 4)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-c",\n'
    '        "--chunk-size",\n'
    '        default="1M",\n'
    '        help="Chunk size for streaming (default: 1M, e.g., 512K, 2M)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--include-binary",\n'
    '        action="store_true",\n'
    '        help="Process binary files (not recommended)",\n'
    '    )\n'
    '    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed logging")\n'
    '    args = parser.parse_args()\n'
    '    if args.verbose:\n'
    '        logger.setLevel(logging.DEBUG)\n'
    '    chunk_size_str = args.chunk_size.upper()\n'
    '    multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3}\n'
    '    try:\n'
    '        if chunk_size_str[-1] in multipliers:\n'
    '            chunk_size = int(chunk_size_str[:-1]) * multipliers[chunk_size_str[-1]]\n'
    '        else:\n'
    '            chunk_size = int(chunk_size_str)\n'
    '    except ValueError:\n'
    '        logger.error(f"Invalid chunk size: {args.chunk_size}")\n'
    '        return 1\n'
    '    if not args.inputs:\n'
    '        inputs = [Path.cwd()]\n'
    '        print("No inputs provided, processing current directory recursively")\n'
    '    else:\n'
    '        inputs = args.inputs\n'
    '    files = list(collect_files(inputs))\n'
    '    if not files:\n'
    '        logger.warning("No files found to process")\n'
    '        return 0\n'
    '    print(f"Found {len(files)} files to process")\n'
    '    print(f"Starting parallel processing with {args.workers} workers")\n'
    '    results = Parallel(n_jobs=args.workers, verbose=0)(\n'
    '        delayed(process_file_chunked)(path, chunk_size) for path in files\n'
    '    )\n'
    '    print("\\n" + "=" * 40)\n'
    '    print("PROCESSING RESULTS")\n'
    '    print("=" * 40)\n'
    '    successful = 0\n'
    '    total_replacements = 0\n'
    '    total_size_change = 0\n'
    '    for stats in results:\n'
    '        print(stats)\n'
    '        if stats.success:\n'
    '            successful += 1\n'
    '            total_replacements += stats.replacements\n'
    '            total_size_change += stats.new_size - stats.original_size\n'
    '    failed = len(results) - successful\n'
    '    print("=" * 40)\n'
    '    print(f"Summary: {successful} succeeded, {failed} failed out of {len(results)} files")\n'
    '    print(f"Total replacements: {total_replacements}")\n'
    '    print(f"Total size change: {total_size_change:+d} bytes")\n'
    '    print("=" * 40 + "\\n")\n'
    '    return 0 if failed == 0 else 1\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_F45_SOURCE: str = (
    'import argparse\n'
    'import shutil\n'
    'import sys\n'
    'import textwrap\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def wrap_text_content(content, width):\n'
    '    paragraphs = content.split("\\n\\n")\n'
    '    wrapped_paragraphs = []\n'
    '    for paragraph in paragraphs:\n'
    '        lines = paragraph.splitlines()\n'
    '        if not lines:\n'
    '            wrapped_paragraphs.append("")\n'
    '            continue\n'
    '        wrapped_lines = []\n'
    '        for line in lines:\n'
    '            if not line.strip():\n'
    '                wrapped_lines.append("")\n'
    '                continue\n'
    '            wrapped = textwrap.fill(\n'
    '                line,\n'
    '                width=width,\n'
    '                break_long_words=False,\n'
    '                break_on_hyphens=False,\n'
    '                replace_whitespace=False,\n'
    '                drop_whitespace=True,\n'
    '            )\n'
    '            wrapped_lines.append(wrapped)\n'
    '        wrapped_paragraphs.append("\\n".join(wrapped_lines))\n'
    '    return "\\n\\n".join(wrapped_paragraphs)\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(description="Wrap text file content to match terminal width.")\n'
    '    parser.add_argument("file", type=Path, help="Path to the target file")\n'
    '    parser.add_argument(\n'
    '        "-i",\n'
    '        "--inplace",\n'
    '        action="store_true",\n'
    '        help="Modify the original file in-place",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-w",\n'
    '        "--width",\n'
    '        type=int,\n'
    '        default=None,\n'
    '        help="Override target wrapping width (defaults to current terminal width)",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    file_path = args.file\n'
    '    if not file_path.exists():\n'
    '        print(f"Error: File \'{file_path}\' not found.", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    if file_path.is_dir():\n'
    '        print(f"Error: \'{file_path}\' is a directory.", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    if args.width:\n'
    '        width = max(args.width, 20)\n'
    '    else:\n'
    '        columns = shutil.get_terminal_size().columns\n'
    '        width = max(columns, 20)\n'
    '    try:\n'
    '        content = file_path.read_text(encoding="utf-8")\n'
    '    except Exception as e:\n'
    '        print(f"Error reading file: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    wrapped_content = wrap_text_content(content, width)\n'
    '    if args.inplace:\n'
    '        output_path = file_path\n'
    '    else:\n'
    '        output_path = file_path.with_name(f"{file_path.stem}_wrapped{file_path.suffix}")\n'
    '    try:\n'
    '        output_path.write_text(wrapped_content + "\\n", encoding="utf-8")\n'
    '        print(f"Successfully wrote wrapped text ({width} cols) to \'{output_path}\'.")\n'
    '    except Exception as e:\n'
    '        print(f"Error writing file: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    main()\n'
)

_GLL_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 3:\n'
    '        print(\n'
    '            f"""get from line X to Y of a file:\n'
    'Usage: {sys.argv[0]} <filename> <start_line> [end_line]""",\n'
    '            file=sys.stderr,\n'
    '        )\n'
    '        return 1\n'
    '    filename = sys.argv[1]\n'
    '    try:\n'
    '        start = int(sys.argv[2])\n'
    '        end = int(sys.argv[3]) if len(sys.argv) >= 4 else -1\n'
    '    except ValueError:\n'
    '        print("Error: start_line and end_line must be integers.", file=sys.stderr)\n'
    '        return 1\n'
    '    if start < 1 or (end != -1 and end < start):\n'
    '        print("Invalid range: start must be >=1 and end >= start.", file=sys.stderr)\n'
    '        return 1\n'
    '    path = Path(filename)\n'
    '    if not path.is_file():\n'
    '        print("Error: Cannot open input file.", file=sys.stderr)\n'
    '        return 1\n'
    '    ext = path.suffix\n'
    '    outname = f"{start}{ext}" if end == -1 else f"{start}_{end}{ext}"\n'
    '    try:\n'
    '        with (\n'
    '            path.open("r", encoding="utf-8", errors="replace") as infile,\n'
    '            Path(outname).open("w", encoding="utf-8") as outfile,\n'
    '        ):\n'
    '            for lineno, line in enumerate(infile, start=1):\n'
    '                if lineno < start:\n'
    '                    continue\n'
    '                if end != -1 and lineno > end:\n'
    '                    break\n'
    '                outfile.write(line)\n'
    '    except OSError:\n'
    '        print("Error: Cannot create output file.", file=sys.stderr)\n'
    '        return 1\n'
    '    print(f"Saved to {outname}")\n'
    '    return 0\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_JOINLINES_SOURCE: str = (
    'from pathlib import Path\n'
    'from sys import argv\n'
    '\n'
    '\n'
    'def main():\n'
    '    nl = ""\n'
    '    with Path(argv[1]).open(encoding="utf-8") as f:\n'
    '        lines = f.readlines()\n'
    '        for line in lines:\n'
    '            if line.strip():\n'
    '                nl += line.strip("\\n")\n'
    '    Path(argv[1]).write_text(nl + "\\n", encoding="utf-8")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_MVL_SOURCE: str = (
    'import sys\n'
    '\n'
    '\n'
    'def move_lines(src_file, start_line, end_line, dest_file):\n'
    '    try:\n'
    '        with open(src_file, encoding="utf-8") as f:\n'
    '            lines = f.readlines()\n'
    '        start_idx = max(0, start_line - 1)\n'
    '        end_idx = min(len(lines), end_line)\n'
    '        lines_to_move = lines[start_idx:end_idx]\n'
    '        with open(dest_file, "a", encoding="utf-8") as f:\n'
    '            f.writelines(lines_to_move)\n'
    '        del lines[start_idx:end_idx]\n'
    '        with open(src_file, "w", encoding="utf-8") as f:\n'
    '            f.writelines(lines)\n'
    '        print(f"Successfully moved lines {start_line}-{end_line} from {src_file} to {dest_file}.")\n'
    '    except FileNotFoundError:\n'
    '        print(f"Error: The file {src_file} was not found.")\n'
    '    except Exception as e:\n'
    '        print(f"An error occurred: {e}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) != 5:\n'
    '        print("Usage: python move_lines.py <src_file> <start_line> <end_line> <dest_file>")\n'
    '    else:\n'
    '        src = sys.argv[1]\n'
    '        start = int(sys.argv[2])\n'
    '        end = int(sys.argv[3])\n'
    '        dest = sys.argv[4]\n'
    '        move_lines(src, start, end, dest)\n'
)

_NNB_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) != 2:\n'
    '        print(f"Usage: {sys.argv[0]} <filename>")\n'
    '        sys.exit(1)\n'
    '    fname = sys.argv[1]\n'
    '    content = Path(fname).read_text(encoding="utf-8")\n'
    '    content = content.replace("\\n", "\\\\n")\n'
    '    Path(fname).write_text(content, encoding="utf-8")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_SORTBYLEN_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from dh import read_lines\n'
    '\n'
    '\n'
    'def sort_by_length(lines, reverse=False):\n'
    '    return sorted(lines, key=len, reverse=reverse)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    args = sys.argv[1:]\n'
    '    reverse = False\n'
    '    if "-r" in args:\n'
    '        reverse = True\n'
    '        args.remove("-r")\n'
    '    if not args:\n'
    '        print("Usage: python script.py [-r] <path>")\n'
    '        sys.exit(1)\n'
    '    path = Path(args[0].strip())\n'
    '    lines = read_lines(path, ke=True)\n'
    '    sorted_lines = sort_by_length(lines, reverse=reverse)\n'
    '    path.write_text("".join(sorted_lines), encoding="utf8")\n'
    '    print(f"{path.name} updated (reverse={reverse})")\n'
)

_STRIPER_SOURCE: str = (
    'from pathlib import Path\n'
    'from sys import argv\n'
    '\n'
    '\n'
    'def remove_spaces_from_file(fname):\n'
    '    try:\n'
    '        with Path(fname).open(encoding="utf-8") as file:\n'
    '            lines = file.readlines()\n'
    '            cleaned_lines = [line.lstrip().strip().rstrip() for line in lines]\n'
    '        with Path(fname).open("w", encoding="utf-8") as file:\n'
    '            for k in cleaned_lines:\n'
    '                file.writelines(k + "\\n")\n'
    '        print(f"{fname} cleaned.")\n'
    '    except FileNotFoundError:\n'
    '        print(f"Error: File \'{fname}\' not found.")\n'
    '    except Exception as e:\n'
    '        print(f"An error occurred: {e}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    remove_spaces_from_file(argv[1])\n'
)

_TNN_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from dh import cprint, get_nobinary, mpf3\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    content = path.read_text(encoding="utf-8")\n'
    '    new_content = content.replace("\\t", "    ")\n'
    '    if new_content == content:\n'
    '        cprint(f"{path.name} (no change)", "grey")\n'
    '        return\n'
    '    path.write_text(new_content, encoding="utf-8")\n'
    '    cprint(f"{path.name} (updated)", "cyan")\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path.cwd()\n'
    '    args = sys.argv[1:]\n'
    '    files = []\n'
    '    if args:\n'
    '        for arg in args:\n'
    '            p = Path(arg)\n'
    '            if p.is_file():\n'
    '                files.append(p)\n'
    '            elif p.is_dir():\n'
    '                files.extend(get_nobinary(p))\n'
    '    else:\n'
    '        files = get_nobinary(cwd)\n'
    '    if len(files) == 1:\n'
    '        process_file(files[0])\n'
    '        sys.exit(1)\n'
    '    mpf3(process_file, files)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_XLR_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    con = path.read_text()\n'
    '    nl = [(line + "\\n\\n\\n\\n") for line in con.splitlines()]\n'
    '    newconn = "\\n".join(nl)\n'
    '    path.write_text(newconn)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    fn = Path(sys.argv[1])\n'
    '    process_file(fn)\n'
)

class BaseTool:
    """Base class for embedded original-script tools."""

    name: str = "base"
    source_file: str = ""
    description: str = ""
    functions: list[str] = []
    notes: str = ""
    source: str = ""

    @classmethod
    def run(cls: type[BaseTool], argv: Sequence[str]) -> int:
        """Execute embedded original source with patched sys.argv."""
        old_argv: list[str] = sys.argv
        sys.argv = [cls.source_file] + list(argv)
        gbls: dict[str, object] = {"__name__": "__main__", "__file__": cls.source_file}
        try:
            code: object = compile(cls.source, cls.source_file, "exec")
            exec(code, gbls)  # noqa: S102 - intentional exec of embedded original
            return 0
        except SystemExit as e:
            c: object = e.code
            if c is None:
                return 0
            if isinstance(c, int):
                return c
            print(str(c), file=sys.stderr)
            return 1
        except SyntaxError as e:
            print(f"[{cls.name}] SyntaxError in {cls.source_file}: {e}", file=sys.stderr)
            return 2
        except ImportError as e:
            print(f"[{cls.name}] ImportError in {cls.source_file}: {e}", file=sys.stderr)
            return 3
        except Exception as e:
            print(f"[{cls.name}] error in {cls.source_file}: {e}", file=sys.stderr)
            return 1
        finally:
            sys.argv = old_argv

    @classmethod
    def info_text(cls: type[BaseTool]) -> str:
        """Return human-readable info for --info."""
        funcs: str = ", ".join(cls.functions) if cls.functions else "(none)"
        base: str = f"tool: {cls.name}\nfile: {cls.source_file}\ndesc: {cls.description}\nfuncs: {funcs}"
        if cls.notes:
            base += f"\nnotes: {cls.notes}"
        base += "\nrun: python main.py " + cls.name + " [args ...]"
        return base


class Add2linesTool(BaseTool):
    """Wrapper for original add2lines.py: top-level script."""
    name: str = 'add2lines'
    source_file: str = 'add2lines.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _ADD2LINES_SOURCE

class AppenderTool(BaseTool):
    """Wrapper for original appender.py: top-level script NOTE: no __main__ guard (top-level script or library fragment; exec runs top-level code)."""
    name: str = 'appender'
    source_file: str = 'appender.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = 'no __main__ guard (top-level script or library fragment; exec runs top-level code)'
    source: str = _APPENDER_SOURCE

class BnnTool(BaseTool):
    """Wrapper for original bnn.py: is_text_file() + 4 more."""
    name: str = 'bnn'
    source_file: str = 'bnn.py'
    description: str = 'is_text_file() + 4 more'
    functions: list[str] = ['is_text_file', 'should_process_file', 'collect_files', 'process_file_chunked', 'main']
    notes: str = ''
    source: str = _BNN_SOURCE

class F45Tool(BaseTool):
    """Wrapper for original f45.py: wrap_text_content() + 1 more."""
    name: str = 'f45'
    source_file: str = 'f45.py'
    description: str = 'wrap_text_content() + 1 more'
    functions: list[str] = ['wrap_text_content', 'main']
    notes: str = ''
    source: str = _F45_SOURCE

class GllTool(BaseTool):
    """Wrapper for original gll.py: main() + 0 more."""
    name: str = 'gll'
    source_file: str = 'gll.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _GLL_SOURCE

class JoinlinesTool(BaseTool):
    """Wrapper for original joinlines.py: main() + 0 more."""
    name: str = 'joinlines'
    source_file: str = 'joinlines.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _JOINLINES_SOURCE

class MvlTool(BaseTool):
    """Wrapper for original mvl.py: move_lines() + 0 more."""
    name: str = 'mvl'
    source_file: str = 'mvl.py'
    description: str = 'move_lines() + 0 more'
    functions: list[str] = ['move_lines']
    notes: str = ''
    source: str = _MVL_SOURCE

class NnbTool(BaseTool):
    """Wrapper for original nnb.py: main() + 0 more."""
    name: str = 'nnb'
    source_file: str = 'nnb.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _NNB_SOURCE

class SortbylenTool(BaseTool):
    """Wrapper for original sortbylen.py: sort_by_length() + 0 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'sortbylen'
    source_file: str = 'sortbylen.py'
    description: str = 'sort_by_length() + 0 more'
    functions: list[str] = ['sort_by_length']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _SORTBYLEN_SOURCE

class StriperTool(BaseTool):
    """Wrapper for original striper.py: remove_spaces_from_file() + 0 more."""
    name: str = 'striper'
    source_file: str = 'striper.py'
    description: str = 'remove_spaces_from_file() + 0 more'
    functions: list[str] = ['remove_spaces_from_file']
    notes: str = ''
    source: str = _STRIPER_SOURCE

class TnnTool(BaseTool):
    """Wrapper for original tnn.py: process_file() + 1 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'tnn'
    source_file: str = 'tnn.py'
    description: str = 'process_file() + 1 more'
    functions: list[str] = ['process_file', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _TNN_SOURCE

class XlrTool(BaseTool):
    """Wrapper for original xlr.py: process_file() + 0 more."""
    name: str = 'xlr'
    source_file: str = 'xlr.py'
    description: str = 'process_file() + 0 more'
    functions: list[str] = ['process_file']
    notes: str = ''
    source: str = _XLR_SOURCE

class LineEditOpsUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'add2lines': Add2linesTool,
        'appender': AppenderTool,
        'bnn': BnnTool,
        'f45': F45Tool,
        'gll': GllTool,
        'joinlines': JoinlinesTool,
        'mvl': MvlTool,
        'nnb': NnbTool,
        'sortbylen': SortbylenTool,
        'striper': StriperTool,
        'tnn': TnnTool,
        'xlr': XlrTool,
    }

    @classmethod
    def list_tools(cls: type[LineEditOpsUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[LineEditOpsUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[LineEditOpsUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for line_edit_ops (12 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[LineEditOpsUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[LineEditOpsUnified], argv: Sequence[str] | None = None) -> int:
        """Entry point: dispatch to subcommand or handle --list/--info."""
        args: list[str] = list(sys.argv[1:] if argv is None else argv)
        # Fast path: first arg is a known tool -> direct dispatch (preserves --help passthrough).
        if args and args[0] in cls.TOOLS:
            tname: str = args[0]
            targs: list[str] = args[1:]
            tool: type[BaseTool] = cls.TOOLS[tname]
            return tool.run(targs)
        # Single-tool convenience: `main.py [args...]` runs the only tool.
        if len(cls.TOOLS) == 1 and args and args[0] not in ("--list", "--info", "--help", "-h"):
            only: type[BaseTool] = next(iter(cls.TOOLS.values()))
            # Allow both `main.py <tool> ...` and `main.py ...` (already handled <tool> above).
            if args[0] == only.name:
                return only.run(args[1:])
            # If it looks like a unified flag combo we already excluded, else treat all as tool args.
            # Guard: if user passed an unknown tool-like bare word, still pass to tool (faithful passthrough).
            return only.run(args)
        parser: argparse.ArgumentParser = cls.build_parser()
        ns: argparse.Namespace = parser.parse_args(args)
        flag_list: bool = bool(getattr(ns, "list", False))
        flag_info: str | None = getattr(ns, "info", None)
        tool_arg: str | None = getattr(ns, "tool", None)
        if flag_list:
            cls.print_list()
            return 0
        if flag_info is not None:
            tgt: type[BaseTool] | None = cls.get_tool(flag_info)
            if tgt is None:
                print(f"unknown tool: {flag_info}", file=sys.stderr)
                print("available:", ", ".join(cls.list_tools()), file=sys.stderr)
                return 2
            print(tgt.info_text())
            return 0
        if tool_arg is not None:
            tgt2: type[BaseTool] | None = cls.get_tool(tool_arg)
            if tgt2 is None:
                print(f"unknown tool: {tool_arg}", file=sys.stderr)
                print("available:", ", ".join(cls.list_tools()), file=sys.stderr)
                return 2
            rest: list[str] = list(getattr(ns, "passthrough", []) or [])
            return tgt2.run(rest)
        parser.print_help()
        print("\navailable tools:")
        cls.print_list()
        return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Module entry point."""
    return LineEditOpsUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

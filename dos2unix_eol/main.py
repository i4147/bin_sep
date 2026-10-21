#!/usr/bin/env python3
"""Dos2unixEolUnified for dos2unix_eol.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (2):
  dostounix <- dostounix.py (108L): _iter_files() + 4 more [requires missing module 'dh' (ImportError at runtime)]
  pydos2unix <- pydos2unix.py (137L): should_skip_dir() + 4 more [requires missing module 'dh' (ImportError at runtime)]

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

_DOSTOUNIX_SOURCE: str = (
    'import sys\n'
    'from multiprocessing import Pool\n'
    'from pathlib import Path\n'
    'from dh import is_binary, should_skip\n'
    '\n'
    'WORKERS = 8\n'
    'CHUNK_SIZE = 64\n'
    '\n'
    '\n'
    'def _iter_files(paths):\n'
    '    for raw in paths:\n'
    '        p = Path(raw).expanduser().resolve()\n'
    '        if p.is_dir():\n'
    '            yield from (f for f in p.rglob("*") if f.is_file() and not is_binary(f) and not should_skip(f))\n'
    '        elif p.is_file() and not is_binary(p) and not should_skip(p):\n'
    '            yield p\n'
    '\n'
    '\n'
    'def _collect_files(args):\n'
    '    if not args:\n'
    '        return list(_iter_files([Path.cwd()]))\n'
    '    return list(_iter_files(args))\n'
    '\n'
    '\n'
    'def _convert_file(path_str):\n'
    '    path = Path(path_str)\n'
    '    try:\n'
    '        data = path.read_bytes()\n'
    '        if b"\\r\\n" not in data:\n'
    '            return (path, False, "")\n'
    '        new_data = data.replace(b"\\r\\n", b"\\n")\n'
    '        tmp = path.with_name(path.name + ".dos2unix.tmp")\n'
    '        tmp.write_bytes(new_data)\n'
    '        tmp.replace(path)\n'
    '        return (path, True, "")\n'
    '    except (OSError, PermissionError) as e:\n'
    '        return (path, False, f"{e}")\n'
    '\n'
    '\n'
    'def _run_parallel(files):\n'
    '    changed = 0\n'
    '    errors = []\n'
    '    with Pool(processes=WORKERS) as pool:\n'
    '        futures = [pool.apply_async(_convert_file, (str(f),)) for f in files]\n'
    '        for fut in futures:\n'
    '            try:\n'
    '                _, was_changed, err = fut.get()\n'
    '                if was_changed:\n'
    '                    changed += 1\n'
    '                if err:\n'
    '                    errors.append(err)\n'
    '            except Exception as e:\n'
    '                errors.append(f"Unexpected error: {e}")\n'
    '    return (changed, len(files) - changed - len(errors), errors)\n'
    '\n'
    '\n'
    'def main(argv=None):\n'
    '    import argparse\n'
    '\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Convert DOS/Windows (CRLF) files to Unix (LF) format in-place.",\n'
    '        epilog="If no paths are given, processes all files in the current directory recursively.",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "paths",\n'
    '        nargs="*",\n'
    '        metavar="FILE_OR_DIR",\n'
    '        help="Files or directories to process (recursive for directories).",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-q",\n'
    '        "--quiet",\n'
    '        action="store_true",\n'
    '        help="Suppress per-file output; only show summary.",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-n",\n'
    '        "--dry-run",\n'
    '        action="store_true",\n'
    '        help="Show what would be done without modifying files.",\n'
    '    )\n'
    '    args = parser.parse_args(argv)\n'
    '    files = _collect_files(args.paths)\n'
    '    if not files:\n'
    '        print("No files to process.", file=sys.stderr)\n'
    '        return 0\n'
    '    if args.dry_run:\n'
    '        for f in files:\n'
    '            print(f"Would convert: {f}")\n'
    '        print(f"\\n{len(files)} file(s) would be processed.")\n'
    '        return 0\n'
    '    changed, unchanged, errors = _run_parallel(files)\n'
    '    if not args.quiet:\n'
    '        for f in files:\n'
    '            pass\n'
    '    print(f"Converted: {changed} file(s)")\n'
    '    print(f"Unchanged: {unchanged} file(s)")\n'
    '    if errors:\n'
    '        print(f"Errors: {len(errors)}", file=sys.stderr)\n'
    '        for e in errors[:10]:\n'
    '            print(f"  {e}", file=sys.stderr)\n'
    '        if len(errors) > 10:\n'
    '            print(f"  ... and {len(errors) - 10} more", file=sys.stderr)\n'
    '    return 1 if errors else 0\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    sys.exit(main())\n'
)

_PYDOS2UNIX_SOURCE: str = (
    'import argparse\n'
    'from multiprocessing import Pool\n'
    'from pathlib import Path\n'
    'from dh import is_binary\n'
    'from dos2unix import dos2unix\n'
    'from loguru import logger\n'
    '\n'
    'MAX_WORKERS = 8\n'
    'CHUNK_SIZE = 32768\n'
    'SKIP_DIRS = {\n'
    '    ".git",\n'
    '    "__pycache__",\n'
    '    ".pytest_cache",\n'
    '    ".mypy_cache",\n'
    '    ".coverage",\n'
    '    ".egg-info",\n'
    '    ".idea",\n'
    '}\n'
    '\n'
    '\n'
    'def should_skip_dir(directory):\n'
    '    return directory.name in SKIP_DIRS\n'
    '\n'
    '\n'
    'def convert_file(path):\n'
    '    path = Path(path)\n'
    '    try:\n'
    '        if not path.is_file():\n'
    '            return (str(path), False, "Not a file")\n'
    '        if is_binary(path):\n'
    '            return (str(path), False, "Binary file (skipped)")\n'
    '        try:\n'
    '            data = f.read_bytes()\n'
    '            new_data = dos2unix(data)\n'
    '            if new_data != data:\n'
    '                path.write_bytes(new_data)\n'
    '                return (str(path), True, "Converted")\n'
    '            else:\n'
    '                return (str(path), True, "Already Unix format")\n'
    '        except OSError as e:\n'
    '            return (str(path), False, f"Read/Write error: {e}")\n'
    '    except Exception as e:\n'
    '        return (str(path), False, f"Error: {e}")\n'
    '\n'
    '\n'
    'def find_text_files(paths):\n'
    '    files = []\n'
    '    for path in paths:\n'
    '        if path.is_file():\n'
    '            if not is_binary(path):\n'
    '                files.append(path)\n'
    '        elif path.is_dir():\n'
    '            for text_file in path.rglob("*"):\n'
    '                if any(should_skip_dir(parent) for parent in text_file.parents):\n'
    '                    continue\n'
    '                if text_file.is_file() and not is_binary(text_file):\n'
    '                    files.append(text_file)\n'
    '    return files\n'
    '\n'
    '\n'
    'def get_input_paths(input_args):\n'
    '    if not input_args:\n'
    '        return [Path.cwd()]\n'
    '    paths = []\n'
    '    for arg in input_args:\n'
    '        path = Path(arg).resolve()\n'
    '        if path.exists():\n'
    '            paths.append(path)\n'
    '        else:\n'
    '            logger.warning(f"Path does not exist: {arg}")\n'
    '    return paths\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Convert DOS/Windows line endings (CRLF) to Unix (LF)",\n'
    '        formatter_class=argparse.RawDescriptionHelpFormatter,\n'
    '        epilog="\\nExamples:\\n  %(prog)s file.txt\\n  %(prog)s file1.txt file2.txt file3.txt\\n  %(prog)s /path/to/folder\\n  %(prog)s /path/to/folder file.txt\\n  %(prog)s                    # Process current directory recursively\\n\\nSkip Directories: .git, __pycache__, .venv, venv, node_modules, .env, \\n                  .pytest_cache, .tox, .mypy_cache, .coverage, dist, build\\n        ",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "paths",\n'
    '        nargs="*",\n'
    '        help="Files or folders to process (default: current directory)",\n'
    '    )\n'
    '    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output messages")\n'
    '    parser.add_argument(\n'
    '        "-v",\n'
    '        "--verbose",\n'
    '        action="store_true",\n'
    '        help="Show detailed output for each file",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    input_paths = get_input_paths(args.paths if args.paths else None)\n'
    '    if not input_paths:\n'
    '        logger.error("No valid paths provided")\n'
    '        return 1\n'
    '    files_to_process = find_text_files(input_paths)\n'
    '    if not files_to_process:\n'
    '        if not args.quiet:\n'
    '            print("No text files found to process")\n'
    '        return 0\n'
    '    if not args.quiet and (not args.verbose):\n'
    '        print(f"Processing {len(files_to_process)} file(s) with {args.jobs} worker(s)...")\n'
    '    converted_count = 0\n'
    '    skipped_count = 0\n'
    '    error_count = 0\n'
    '    try:\n'
    '        with Pool(processes=MAX_WORKERS) as pool:\n'
    '            results = pool.map(convert_file, files_to_process)\n'
    '        for path, success, message in results:\n'
    '            if args.verbose:\n'
    '                status = "✓" if success else "✗"\n'
    '                print(f"{status} {path}: {message}")\n'
    '            if success:\n'
    '                if "Converted" in message:\n'
    '                    converted_count += 1\n'
    '                else:\n'
    '                    skipped_count += 1\n'
    '            else:\n'
    '                error_count += 1\n'
    '        if not args.quiet:\n'
    '            print()\n'
    '            print(f"Converted: {converted_count} file(s)")\n'
    '            print(f"Already Unix format: {skipped_count} file(s)")\n'
    '            if error_count > 0:\n'
    '                logger.warning(f"Errors: {error_count} file(s)")\n'
    '        return 0 if error_count == 0 else 1\n'
    '    except KeyboardInterrupt:\n'
    '        logger.error("\\nInterrupted by user")\n'
    '        return 130\n'
    '    except Exception as e:\n'
    '        logger.error(f"Fatal error: {e}")\n'
    '        return 1\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
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


class DostounixTool(BaseTool):
    """Wrapper for original dostounix.py: _iter_files() + 4 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'dostounix'
    source_file: str = 'dostounix.py'
    description: str = '_iter_files() + 4 more'
    functions: list[str] = ['_iter_files', '_collect_files', '_convert_file', '_run_parallel', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _DOSTOUNIX_SOURCE

class Pydos2unixTool(BaseTool):
    """Wrapper for original pydos2unix.py: should_skip_dir() + 4 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'pydos2unix'
    source_file: str = 'pydos2unix.py'
    description: str = 'should_skip_dir() + 4 more'
    functions: list[str] = ['should_skip_dir', 'convert_file', 'find_text_files', 'get_input_paths', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _PYDOS2UNIX_SOURCE

class Dos2unixEolUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'dostounix': DostounixTool,
        'pydos2unix': Pydos2unixTool,
    }

    @classmethod
    def list_tools(cls: type[Dos2unixEolUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[Dos2unixEolUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[Dos2unixEolUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for dos2unix_eol (2 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[Dos2unixEolUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[Dos2unixEolUnified], argv: Sequence[str] | None = None) -> int:
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
    return Dos2unixEolUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

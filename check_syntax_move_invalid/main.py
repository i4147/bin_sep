#!/usr/bin/env python3
"""CheckSyntaxMoveInvalidUnified for check_syntax_move_invalid.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (4):
  asteval <- asteval.py (134L): process_file() + 4 more [requires missing module 'dh' (ImportError at runtime)]
  black_check_mp <- black_check_mp.py (71L): ensure_dirs() + 4 more
  luaeval <- luaeval.py (56L): make_parser() + 3 more
  okerror <- okerror.py (49L): ensure_dirs() + 3 more

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

_ASTEVAL_SOURCE: str = (
    'import argparse\n'
    'import ast\n'
    'from multiprocessing import Pool\n'
    'from pathlib import Path\n'
    'from typing import Any, Final\n'
    'from dh import get_pyfiles\n'
    'from loguru import logger\n'
    '\n'
    'POOL_SIZE = 8\n'
    '"""Fixed number of worker processes used for concurrent file processing."""\n'
    'ERROR_DIR_NAME = "error"\n'
    '"""Name of the subdirectory where invalid Python files are copied."""\n'
    '\n'
    '\n'
    'def process_file(args):\n'
    '    path, counter, total, dry_run = args\n'
    '    path = Path(path)\n'
    '    prefix = "[DRY RUN] " if dry_run else ""\n'
    '    print(f"{prefix}[{counter}/{total}] {path.name}")\n'
    '    try:\n'
    '        content = path.read_text(encoding="utf-8")\n'
    '        ast.parse(content)\n'
    '        if dry_run:\n'
    '            print(f"  ✅ {path.name} - Valid Python syntax")\n'
    '        return\n'
    '    except (SyntaxError, ValueError, UnicodeDecodeError, OSError) as e:\n'
    '        error_dir = path.parent / ERROR_DIR_NAME\n'
    '        new_path = error_dir / path.name\n'
    '        if dry_run:\n'
    '            print(f"  🔍 Would move to: {new_path} | Error: {e}")\n'
    '            return\n'
    '        error_dir.mkdir(exist_ok=True)\n'
    '        if new_path.exists():\n'
    '            base = path.stem\n'
    '            ext = path.suffix\n'
    '            idx = 1\n'
    '            while new_path.exists():\n'
    '                new_path = error_dir / f"{base}_{idx}{ext}"\n'
    '                idx += 1\n'
    '        try:\n'
    '            raw = path.read_bytes()\n'
    '            new_path.write_bytes(raw)\n'
    '            logger.warning(f"  ⚠️  copied to: {new_path} | Error: {e}")\n'
    '        except OSError as move_error:\n'
    '            logger.error(f"  ❌ Failed to move {path}: {move_error}")\n'
    '\n'
    '\n'
    'def get_files_to_process(paths):\n'
    '    files = []\n'
    '    if paths:\n'
    '        for path_str in paths:\n'
    '            p = Path(path_str)\n'
    '            if p.is_file() and p.suffix == ".py":\n'
    '                files.append(p)\n'
    '            elif p.is_dir():\n'
    '                files.extend(get_pyfiles(p))\n'
    '            else:\n'
    '                logger.warning(f"⚠️  Skipping: {path_str} (not a .py file or directory)")\n'
    '    else:\n'
    '        files = get_pyfiles(Path.cwd())\n'
    '    seen = set()\n'
    '    unique_files = []\n'
    '    for f in files:\n'
    '        resolved = f.resolve()\n'
    '        if resolved not in seen:\n'
    '            seen.add(resolved)\n'
    '            unique_files.append(f)\n'
    '    return unique_files\n'
    '\n'
    '\n'
    'def process_files(files, dry_run=False):\n'
    '    total = len(files)\n'
    '    if total == 0:\n'
    '        return\n'
    '    args_list = [(path, idx, total, dry_run) for idx, path in enumerate(files, 1)]\n'
    '    with Pool(processes=POOL_SIZE) as pool:\n'
    '        async_results = [pool.apply_async(process_file, (arg,)) for arg in args_list]\n'
    '        for result in async_results:\n'
    '            try:\n'
    '                result.get()\n'
    '            except Exception as e:\n'
    '                logger.error(f"  ❌ Unexpected error in worker: {e}")\n'
    '\n'
    '\n'
    'def build_parser():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description=("Check Python files for syntax errors and move invalid ones to \'error\' directories"),\n'
    '        epilog="Example: python script.py --dry-run /path/to/project",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "paths",\n'
    '        nargs="*",\n'
    '        help="Files or directories to process (default: current directory)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--dry-run",\n'
    '        "-n",\n'
    '        action="store_true",\n'
    '        help="Show what would be done without actually moving files",\n'
    '    )\n'
    '    return parser\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = build_parser()\n'
    '    args = parser.parse_args()\n'
    '    try:\n'
    '        files = get_files_to_process(args.paths)\n'
    '    except Exception as e:\n'
    '        logger.error(f"❌ Error collecting files: {e}")\n'
    '        return 1\n'
    '    if not files:\n'
    '        print("ℹ️  No Python files found to process.")\n'
    '        return 0\n'
    '    print(f"📁 Found {len(files)} Python file(s) to process")\n'
    '    if args.dry_run:\n'
    '        print("🔍 DRY RUN MODE - No files will be moved")\n'
    '        print("-" * 40)\n'
    '    try:\n'
    '        process_files(files, dry_run=bool(args.dry_run))\n'
    '    except KeyboardInterrupt:\n'
    '        logger.warning("\\n⚠️  Interrupted by user")\n'
    '        return 1\n'
    '    except Exception as e:\n'
    '        logger.error(f"❌ Error processing files: {e}")\n'
    '        return 1\n'
    '    if args.dry_run:\n'
    '        print("-" * 40)\n'
    '        print("🔍 DRY RUN COMPLETE - No files were moved")\n'
    '    return 0\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_BLACK_CHECK_MP_SOURCE: str = (
    'import ast\n'
    'import shutil\n'
    'from concurrent.futures import ProcessPoolExecutor, as_completed\n'
    'from pathlib import Path\n'
    '\n'
    'ERROR_DIR = Path("error")\n'
    'OK_DIR = Path("ok")\n'
    '\n'
    '\n'
    'def ensure_dirs():\n'
    '    ERROR_DIR.mkdir(exist_ok=True)\n'
    '    OK_DIR.mkdir(exist_ok=True)\n'
    '\n'
    '\n'
    'def unique_destination(dest):\n'
    '    if not dest.exists():\n'
    '        return dest\n'
    '    stem = dest.stem\n'
    '    suffix = dest.suffix\n'
    '    parent = dest.parent\n'
    '    counter = 1\n'
    '    while True:\n'
    '        new_dest = parent / f"{stem}_{counter}{suffix}"\n'
    '        if not new_dest.exists():\n'
    '            return new_dest\n'
    '        counter += 1\n'
    '\n'
    '\n'
    'def black_check(path):\n'
    '    print(f"[OK] {path}")\n'
    '    try:\n'
    '        ast.parse(path.read_text(encoding="utf-8"))\n'
    '        return path, True\n'
    '    except:\n'
    '        return path, False\n'
    '\n'
    '\n'
    'def collect_python_files():\n'
    '    current_script = Path(__file__).resolve()\n'
    '    files = []\n'
    '    for file in Path().rglob("*.py"):\n'
    '        resolved = file.resolve()\n'
    '        if resolved == current_script:\n'
    '            continue\n'
    '        if ERROR_DIR in resolved.parents or OK_DIR in resolved.parents:\n'
    '            continue\n'
    '        files.append(file)\n'
    '    return files\n'
    '\n'
    '\n'
    'def main():\n'
    '    ensure_dirs()\n'
    '    files = collect_python_files()\n'
    '    if not files:\n'
    '        print("No python files found.")\n'
    '        return\n'
    '    print(f"Found {len(files)} python files.")\n'
    '    results = []\n'
    '    with ProcessPoolExecutor(max_workers=8) as executor:\n'
    '        futures = [executor.submit(black_check, f) for f in files]\n'
    '        results.extend(future.result() for future in as_completed(futures))\n'
    '    for path, passed in results:\n'
    '        target_dir = OK_DIR if passed else ERROR_DIR\n'
    '        dest = unique_destination(target_dir / path.name)\n'
    '        shutil.move(str(path), str(dest))\n'
    '        status = "OK" if passed else "ERROR"\n'
    '        print(f"{status:6} → {path} → {dest}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_LUAEVAL_SOURCE: str = (
    'from pathlib import Path\n'
    'import tree_sitter_lua\n'
    'from tree_sitter import Language, Parser\n'
    '\n'
    '\n'
    'def make_parser():\n'
    '    language = Language(tree_sitter_lua.language())\n'
    '    return Parser(language)\n'
    '\n'
    '\n'
    'def has_syntax_error(parser, source):\n'
    '    tree = parser.parse(source)\n'
    '    stack = [tree.root_node]\n'
    '    while stack:\n'
    '        node = stack.pop()\n'
    '        if node.is_error or node.is_missing:\n'
    '            return True\n'
    '        stack.extend(node.children)\n'
    '    return False\n'
    '\n'
    '\n'
    'def move_to_error_dir(path):\n'
    '    error_dir = path.parent / "error"\n'
    '    error_dir.mkdir(exist_ok=True)\n'
    '    target = error_dir / path.name\n'
    '    if target.exists():\n'
    '        i = 1\n'
    '        while True:\n'
    '            candidate = error_dir / f"{path.stem}_{i}{path.suffix}"\n'
    '            if not candidate.exists():\n'
    '                target = candidate\n'
    '                break\n'
    '            i += 1\n'
    '    path.rename(target)\n'
    '    print(f"Moved: {path} -> {target}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = make_parser()\n'
    '    cwd = Path.cwd()\n'
    '    for lua_file in cwd.rglob("*.lua"):\n'
    '        if "error" in lua_file.parts:\n'
    '            continue\n'
    '        try:\n'
    '            source = lua_file.read_bytes()\n'
    '        except OSError as e:\n'
    '            print(f"Could not read {lua_file}: {e}")\n'
    '            continue\n'
    '        if has_syntax_error(parser, source):\n'
    '            move_to_error_dir(lua_file)\n'
    '        else:\n'
    '            print(f"OK: {lua_file}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    main()\n'
)

_OKERROR_SOURCE: str = (
    'import shutil\n'
    'import subprocess\n'
    'from pathlib import Path\n'
    '\n'
    'ERROR_DIR = Path("error")\n'
    'OK_DIR = Path("ok")\n'
    '\n'
    '\n'
    'def ensure_dirs():\n'
    '    ERROR_DIR.mkdir(exist_ok=True)\n'
    '    OK_DIR.mkdir(exist_ok=True)\n'
    '\n'
    '\n'
    'def unique_destination(dest):\n'
    '    if not dest.exists():\n'
    '        return dest\n'
    '    stem = dest.stem\n'
    '    suffix = dest.suffix\n'
    '    parent = dest.parent\n'
    '    counter = 1\n'
    '    while True:\n'
    '        new_dest = parent / f"{stem}_{counter}{suffix}"\n'
    '        if not new_dest.exists():\n'
    '            return new_dest\n'
    '        counter += 1\n'
    '\n'
    '\n'
    'def black_check(path):\n'
    '    result = subprocess.run(["black", "--check", str(path)], capture_output=True)\n'
    '    return result.returncode == 0\n'
    '\n'
    '\n'
    'def main():\n'
    '    ensure_dirs()\n'
    '    for py_file in Path().glob("*.py"):\n'
    '        if py_file.name == Path(__file__).name:\n'
    '            continue\n'
    '        print(f"Checking {py_file}...")\n'
    '        if black_check(py_file):\n'
    '            dest = unique_destination(OK_DIR / py_file.name)\n'
    '            print(f"  ✓ OK → {dest}")\n'
    '        else:\n'
    '            dest = unique_destination(ERROR_DIR / py_file.name)\n'
    '            print(f"  ✗ ERROR → {dest}")\n'
    '        shutil.move(str(py_file), str(dest))\n'
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


class AstevalTool(BaseTool):
    """Wrapper for original asteval.py: process_file() + 4 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'asteval'
    source_file: str = 'asteval.py'
    description: str = 'process_file() + 4 more'
    functions: list[str] = ['process_file', 'get_files_to_process', 'process_files', 'build_parser', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _ASTEVAL_SOURCE

class BlackCheckMpTool(BaseTool):
    """Wrapper for original black_check_mp.py: ensure_dirs() + 4 more."""
    name: str = 'black_check_mp'
    source_file: str = 'black_check_mp.py'
    description: str = 'ensure_dirs() + 4 more'
    functions: list[str] = ['ensure_dirs', 'unique_destination', 'black_check', 'collect_python_files', 'main']
    notes: str = ''
    source: str = _BLACK_CHECK_MP_SOURCE

class LuaevalTool(BaseTool):
    """Wrapper for original luaeval.py: make_parser() + 3 more."""
    name: str = 'luaeval'
    source_file: str = 'luaeval.py'
    description: str = 'make_parser() + 3 more'
    functions: list[str] = ['make_parser', 'has_syntax_error', 'move_to_error_dir', 'main']
    notes: str = ''
    source: str = _LUAEVAL_SOURCE

class OkerrorTool(BaseTool):
    """Wrapper for original okerror.py: ensure_dirs() + 3 more."""
    name: str = 'okerror'
    source_file: str = 'okerror.py'
    description: str = 'ensure_dirs() + 3 more'
    functions: list[str] = ['ensure_dirs', 'unique_destination', 'black_check', 'main']
    notes: str = ''
    source: str = _OKERROR_SOURCE

class CheckSyntaxMoveInvalidUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'asteval': AstevalTool,
        'black_check_mp': BlackCheckMpTool,
        'luaeval': LuaevalTool,
        'okerror': OkerrorTool,
    }

    @classmethod
    def list_tools(cls: type[CheckSyntaxMoveInvalidUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[CheckSyntaxMoveInvalidUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[CheckSyntaxMoveInvalidUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for check_syntax_move_invalid (4 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[CheckSyntaxMoveInvalidUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[CheckSyntaxMoveInvalidUnified], argv: Sequence[str] | None = None) -> int:
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
    return CheckSyntaxMoveInvalidUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

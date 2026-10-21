#!/usr/bin/env python3
"""AddMainGuardUnified for add_main_guard.

Assumption: single original script preserved; `main.py [args...]` passes through to it.

Original scripts (1):
  main_guard_merger <- main_guard_merger.py (361L): Unified main guard tool: detect and optionally add `if __name__ == "__main__":` guards.

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
- Single-tool folder: `python main.py [args...]` runs the only tool directly.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

_MAIN_GUARD_MERGER_SOURCE: str = (
    '#!/usr/bin/env python3\n'
    '"""\n'
    'Unified main guard tool: detect and optionally add `if __name__ == "__main__":` guards.\n'
    '\n'
    'Usage:\n'
    '  python main_guard_merger.py check [PATH] [OPTIONS]\n'
    '  python main_guard_merger.py fix [PATH] [OPTIONS]\n'
    '\n'
    'Examples:\n'
    '  python main_guard_merger.py check                    # Find missing guards in current dir\n'
    '  python main_guard_merger.py check src/               # Check src/ directory\n'
    '  python main_guard_merger.py fix -m ast               # Add guards using AST method\n'
    '  python main_guard_merger.py fix --dry-run            # Preview changes without modifying\n'
    '  python main_guard_merger.py fix --method regex       # Use regex method for adding\n'
    '\n'
    'Original script mapping:\n'
    '  addmain.py  -> python main_guard_merger.py fix --method ast\n'
    '  addmainguard.py  -> python main_guard_merger.py fix --method regex --parallel 8\n'
    '"""\n'
    '\n'
    'import argparse\n'
    'import ast\n'
    'import json\n'
    'import multiprocessing as mp\n'
    'import re\n'
    'import sys\n'
    'import subprocess\n'
    'from dataclasses import dataclass, field\n'
    'from pathlib import Path\n'
    'from typing import Optional, Literal, Sequence\n'
    '\n'
    '\n'
    'DEFAULT_EXCLUDES = (\n'
    '    ".git",\n'
    '    "__pycache__",\n'
    '    "venv",\n'
    '    ".venv",\n'
    '    "env",\n'
    '    "dist",\n'
    '    "build",\n'
    '    ".pytest_cache",\n'
    '    ".mypy_cache",\n'
    ')\n'
    'MAIN_GUARD_PATTERN = re.compile(r"if\\s+__name__\\s*==\\s*[\\"\\\']__main__[\\"\\\']\\s*:")\n'
    'MAIN_FUNC_TEMPLATE_REGEX = (\n'
    '    "\\n\\ndef main() -> None:\\n"\n'
    '    \'    """Entry point for the script."""\\n\'\n'
    '    "    # TODO: Add your main logic here\\n"\n'
    '    \'    print("Hello from main!")\\n\'\n'
    ')\n'
    'MAIN_GUARD_TEMPLATE_REGEX = \'\\nif __name__ == "__main__":\\n    raise SystemExit(main())\\n\'\n'
    '\n'
    '\n'
    '@dataclass\n'
    'class FileResult:\n'
    '    path: Path\n'
    '    status: Literal["skipped", "missing", "would_add", "added", "error", "fixed"]\n'
    '    message: str = ""\n'
    '    duration: float = 0.0\n'
    '\n'
    '\n'
    'def has_main_guard_regex(content: str) -> bool:\n'
    '    return bool(MAIN_GUARD_PATTERN.search(content))\n'
    '\n'
    '\n'
    'def has_main_guard_ast(tree: ast.Module) -> bool:\n'
    '    for node in tree.body if isinstance(tree, ast.Module) else []:\n'
    '        if isinstance(node, ast.If):\n'
    '            test = node.test\n'
    '            if not isinstance(test, ast.Compare):\n'
    '                continue\n'
    '            if not (len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)):\n'
    '                continue\n'
    '            left = test.left\n'
    '            if not (isinstance(left, ast.Name) and left.id == "__name__"):\n'
    '                continue\n'
    '            if len(test.comparators) != 1:\n'
    '                continue\n'
    '            comp = test.comparators[0]\n'
    '            if isinstance(comp, ast.Constant) and comp.value == "__main__":\n'
    '                return True\n'
    '    return False\n'
    '\n'
    '\n'
    'def is_docstring_expr(node: ast.expr) -> bool:\n'
    '    if not isinstance(node, ast.Expr):\n'
    '        return False\n'
    '    return bool(isinstance(node.value, ast.Constant) and isinstance(node.value.value, str))\n'
    '\n'
    '\n'
    'def should_wrap_node_ast(node: ast.stmt) -> bool:\n'
    '    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):\n'
    '        return False\n'
    '    if isinstance(node, (ast.Import, ast.ImportFrom)):\n'
    '        return False\n'
    '    if is_docstring_expr(node):\n'
    '        return False\n'
    '    if isinstance(node, ast.If):\n'
    '        test = node.test\n'
    '        if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):\n'
    '            left = test.left\n'
    '            if isinstance(left, ast.Name) and left.id == "__name__" and len(test.comparators) == 1:\n'
    '                comp = test.comparators[0]\n'
    '                if isinstance(comp, ast.Constant) and comp.value == "__main__":\n'
    '                    return False\n'
    '    return True\n'
    '\n'
    '\n'
    'def indent_block(block: str, spaces: int = 4) -> str:\n'
    '    prefix = " " * spaces\n'
    '    lines = block.splitlines(True)\n'
    '    out = []\n'
    '    for ln in lines:\n'
    '        if ln.strip() == "":\n'
    '            out.append(ln)\n'
    '        else:\n'
    '            out.append(prefix + ln)\n'
    '    return "".join(out)\n'
    '\n'
    '\n'
    'def fix_file_ast(path: Path) -> FileResult:\n'
    '    src = path.read_text(encoding="utf-8")\n'
    '    try:\n'
    '        tree = ast.parse(src, filename=str(path))\n'
    '    except SyntaxError as e:\n'
    '        return FileResult(path, "error", f"Parse error: {e}")\n'
    '\n'
    '    if has_main_guard_ast(tree):\n'
    '        return FileResult(path, "skipped", "Already has main guard")\n'
    '\n'
    '    nodes = list(tree.body)\n'
    '    wrap_nodes = [n for n in nodes if should_wrap_node_ast(n)]\n'
    '    if not wrap_nodes:\n'
    '        return FileResult(path, "skipped", "Nothing to wrap")\n'
    '\n'
    '    lines = src.splitlines(True)\n'
    '\n'
    '    def segment(start: int, end: int) -> str:\n'
    '        return "".join(lines[start - 1 : end])\n'
    '\n'
    '    main_parts = []\n'
    '    keep_segments = []\n'
    '    for n in nodes:\n'
    '        start = getattr(n, "lineno", None)\n'
    '        end = getattr(n, "end_lineno", None)\n'
    '        if not isinstance(start, int) or not isinstance(end, int):\n'
    '            return FileResult(path, "error", "Missing lineno/end_lineno (AST limitation)")\n'
    '        if should_wrap_node_ast(n):\n'
    '            main_parts.append(segment(start, end).rstrip() + "\\n")\n'
    '        else:\n'
    '            keep_segments.append((start, end))\n'
    '\n'
    '    keep_segments.sort()\n'
    '    new_parts = []\n'
    '    cursor = 1\n'
    '    for start, end in keep_segments:\n'
    '        if start > cursor:\n'
    '            new_parts.append("".join(lines[cursor - 1 : start - 1]))\n'
    '        new_parts.append("".join(lines[start - 1 : end]))\n'
    '        cursor = end + 1\n'
    '    if cursor <= len(lines):\n'
    '        new_parts.append("".join(lines[cursor - 1 :]))\n'
    '\n'
    '    main_body = "".join(main_parts).rstrip("\\n")\n'
    '    main_fn = "\\n\\ndef main():\\n"\n'
    '    if main_body.strip() == "":\n'
    '        main_fn += "    pass\\n"\n'
    '    else:\n'
    '        main_fn += indent_block(main_body + "\\n", 4).rstrip("\\n") + "\\n"\n'
    '    main_fn += \'\\n\\nif __name__ == "__main__":\\n\'\n'
    '    main_fn += "    raise SystemExit(main())\\n"\n'
    '\n'
    '    new_src = "".join(new_parts).rstrip() + main_fn\n'
    '    path.write_text(new_src, encoding="utf-8")\n'
    '    return FileResult(path, "fixed", "Wrapped code in main() and added guard")\n'
    '\n'
    '\n'
    'def fix_file_regex(path: Path, dry_run: bool = False) -> FileResult:\n'
    '    try:\n'
    '        content = path.read_text(encoding="utf-8")\n'
    '    except OSError as exc:\n'
    '        return FileResult(path, "error", f"Failed to read: {exc}")\n'
    '\n'
    '    if has_main_guard_regex(content):\n'
    '        return FileResult(path, "skipped", "Already has guard")\n'
    '\n'
    '    new_content = content.rstrip() + MAIN_GUARD_TEMPLATE_REGEX\n'
    '    if dry_run:\n'
    '        return FileResult(path, "would_add", "Would add guard (dry-run)")\n'
    '\n'
    '    try:\n'
    '        path.write_text(new_content, encoding="utf-8")\n'
    '    except OSError as exc:\n'
    '        return FileResult(path, "error", f"Failed to write: {exc}")\n'
    '\n'
    '    return FileResult(path, "added", "Added guard successfully")\n'
    '\n'
    '\n'
    'def find_python_files(directory: Path, exclude_patterns: Sequence[str]) -> list[Path]:\n'
    '    if not directory.exists():\n'
    '        return []\n'
    '    excluded = frozenset(exclude_patterns)\n'
    '    results = []\n'
    '    for path in directory.rglob("*.py"):\n'
    '        if excluded.intersection(path.parts):\n'
    '            continue\n'
    '        results.append(path)\n'
    '    return sorted(results)\n'
    '\n'
    '\n'
    'def iter_py_files(inputs: Sequence[str]) -> list[Path]:\n'
    '    if not inputs:\n'
    '        roots = [Path(".")]\n'
    '    else:\n'
    '        roots = [Path(p) for p in inputs]\n'
    '    out = []\n'
    '    for r in roots:\n'
    '        if r.is_dir():\n'
    '            out.extend(sorted(x for x in r.rglob("*.py") if x.is_file()))\n'
    '        else:\n'
    '            if r.suffix == ".py" and r.is_file():\n'
    '                out.append(r)\n'
    '    return sorted(set(out))\n'
    '\n'
    '\n'
    'def check_files(files: list[Path]) -> dict[str, list]:\n'
    '    results = {"missing": [], "skipped": [], "errors": []}\n'
    '    for f in files:\n'
    '        src = f.read_text(encoding="utf-8")\n'
    '        try:\n'
    '            tree = ast.parse(src, filename=str(f))\n'
    '        except SyntaxError:\n'
    '            results["errors"].append((f, "Parse error"))\n'
    '            continue\n'
    '        if has_main_guard_ast(tree):\n'
    '            results["skipped"].append(f)\n'
    '        else:\n'
    '            results["missing"].append(f)\n'
    '    return results\n'
    '\n'
    '\n'
    'def fix_files_sequential(files: list[Path], method: Literal["ast", "regex"], dry_run: bool = False) -> dict:\n'
    '    results = {"fixed": [], "added": [], "would_add": [], "skipped": [], "errors": []}\n'
    '    fix_func = fix_file_ast if method == "ast" else fix_file_regex\n'
    '\n'
    '    for f in files:\n'
    '        result = fix_func(f, dry_run) if method == "regex" else fix_func(f)\n'
    '        if result.status == "fixed":\n'
    '            results["fixed"].append(f)\n'
    '        elif result.status == "added":\n'
    '            results["added"].append(f)\n'
    '        elif result.status == "would_add":\n'
    '            results["would_add"].append(f)\n'
    '        elif result.status == "skipped":\n'
    '            results["skipped"].append(f)\n'
    '        elif result.status == "error":\n'
    '            results["errors"].append((f, result.message))\n'
    '        print(f"{f}: {result.status} - {result.message}")\n'
    '\n'
    '    return results\n'
    '\n'
    '\n'
    'def fix_files_parallel(\n'
    '    files: list[Path], method: Literal["ast", "regex"], num_workers: int, dry_run: bool = False\n'
    ') -> dict:\n'
    '    results = {"fixed": [], "added": [], "would_add": [], "skipped": [], "errors": []}\n'
    '    fix_func = fix_file_ast if method == "ast" else fix_file_regex\n'
    '\n'
    '    with mp.Pool(processes=num_workers) as pool:\n'
    '        if method == "regex":\n'
    '            async_results = [pool.apply_async(fix_func, (f, dry_run)) for f in files]\n'
    '        else:\n'
    '            async_results = [pool.apply_async(fix_func, (f,)) for f in files]\n'
    '\n'
    '        for idx, ar in enumerate(async_results, 1):\n'
    '            result = ar.get()\n'
    '            if result.status == "fixed":\n'
    '                results["fixed"].append(result.path)\n'
    '            elif result.status == "added":\n'
    '                results["added"].append(result.path)\n'
    '            elif result.status == "would_add":\n'
    '                results["would_add"].append(result.path)\n'
    '            elif result.status == "skipped":\n'
    '                results["skipped"].append(result.path)\n'
    '            elif result.status == "error":\n'
    '                results["errors"].append((result.path, result.message))\n'
    '            print(f"[{idx}/{len(files)}] {result.path}: {result.status}")\n'
    '\n'
    '    return results\n'
    '\n'
    '\n'
    'def main(argv: Optional[Sequence[str]] = None) -> int:\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Detect and add main guard to Python files",\n'
    '        formatter_class=argparse.RawDescriptionHelpFormatter,\n'
    '    )\n'
    '    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")\n'
    '\n'
    '    check_parser = subparsers.add_parser("check", help="Detect missing guards")\n'
    '    check_parser.add_argument("paths", nargs="*", help="Files or directories to scan (default: current dir)")\n'
    '    check_parser.add_argument("--exclude", nargs="+", default=[], help="Directories to exclude")\n'
    '\n'
    '    fix_parser = subparsers.add_parser("fix", help="Add guards to files")\n'
    '    fix_parser.add_argument("paths", nargs="*", help="Files or directories to scan (default: current dir)")\n'
    '    fix_parser.add_argument("--method", choices=["ast", "regex"], default="ast", help="Fix method")\n'
    '    fix_parser.add_argument("--exclude", nargs="+", default=[], help="Directories to exclude")\n'
    '    fix_parser.add_argument("--dry-run", action="store_true", help="Preview changes")\n'
    '    fix_parser.add_argument("--parallel", type=int, default=0, help="Number of workers (0=sequential)")\n'
    '\n'
    '    args = parser.parse_args(argv)\n'
    '\n'
    '    if not args.mode:\n'
    '        parser.print_help()\n'
    '        return 0\n'
    '\n'
    '    if args.mode == "check":\n'
    '        files = iter_py_files(args.paths) if args.paths else iter_py_files([])\n'
    '        results = check_files(files)\n'
    '        missing = len(results["missing"])\n'
    '        skipped = len(results["skipped"])\n'
    '        errors = len(results["errors"])\n'
    '        print(f"\\n📋 Summary: {missing} missing, {skipped} with guard, {errors} errors")\n'
    '        if missing > 0:\n'
    '            print(f"Files missing main guard:")\n'
    '            for f in sorted(results["missing"]):\n'
    '                print(f"  {f}")\n'
    '        return 0 if missing == 0 else 1\n'
    '\n'
    '    elif args.mode == "fix":\n'
    '        exclude_patterns = DEFAULT_EXCLUDES + tuple(args.exclude)\n'
    '        directory = Path(args.paths[0]) if args.paths else Path(".")\n'
    '        files = find_python_files(directory, exclude_patterns)\n'
    '\n'
    '        if not files:\n'
    '            print(f"No Python files found in {directory}")\n'
    '            return 0\n'
    '\n'
    '        print(f"Found {len(files)} Python files")\n'
    '        if args.parallel > 0:\n'
    '            results = fix_files_parallel(files, args.method, args.parallel, args.dry_run)\n'
    '        else:\n'
    '            results = fix_files_sequential(files, args.method, args.dry_run)\n'
    '\n'
    '        print(f"\\n📊 Results:")\n'
    '        print(f"  Fixed: {len(results[\'fixed\'])}")\n'
    '        print(f"  Added: {len(results[\'added\'])}")\n'
    '        print(f"  Would add (dry-run): {len(results[\'would_add\'])}")\n'
    '        print(f"  Skipped: {len(results[\'skipped\'])}")\n'
    '        print(f"  Errors: {len(results[\'errors\'])}")\n'
    '\n'
    '        if results["errors"]:\n'
    '            print("\\n❌ Errors:")\n'
    '            for path, msg in results["errors"]:\n'
    '                print(f"  {path}: {msg}")\n'
    '            return 2\n'
    '\n'
    '        return 0\n'
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


class MainGuardMergerTool(BaseTool):
    """Wrapper for original main_guard_merger.py: Unified main guard tool: detect and optionally add `if __name__ == "__main__":` guards.."""
    name: str = 'main_guard_merger'
    source_file: str = 'main_guard_merger.py'
    description: str = 'Unified main guard tool: detect and optionally add `if __name__ == "__main__":` guards.'
    functions: list[str] = ['has_main_guard_regex', 'has_main_guard_ast', 'is_docstring_expr', 'should_wrap_node_ast', 'indent_block', 'fix_file_ast', 'fix_file_regex', 'find_python_files', 'iter_py_files', 'check_files', 'fix_files_sequential', 'fix_files_parallel', 'main']
    notes: str = ''
    source: str = _MAIN_GUARD_MERGER_SOURCE

class AddMainGuardUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'main_guard_merger': MainGuardMergerTool,
    }

    @classmethod
    def list_tools(cls: type[AddMainGuardUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[AddMainGuardUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[AddMainGuardUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for add_main_guard (1 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[AddMainGuardUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[AddMainGuardUnified], argv: Sequence[str] | None = None) -> int:
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
    return AddMainGuardUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

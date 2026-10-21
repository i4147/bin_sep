#!/usr/bin/env python3
"""NormalizePrintMiscUnified for normalize_print_misc.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (3):
  ensurebracket <- ensurebracket.py (46L): process_file() + 1 more [requires missing module 'dh' (ImportError at runtime)]
  fix_is_not <- fix_is_not.py (101L): process_file() + 1 more
  normalize_print_sep <- normalize_print_sep.py (111L): normalize_separators() + 4 more

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

_ENSUREBRACKET_SOURCE: str = (
    'import sys\n'
    'from collections import deque\n'
    'from multiprocessing import get_context\n'
    'from pathlib import Path\n'
    'from dh import get_files\n'
    '\n'
    'MAX_QUEUE = 16\n'
    '\n'
    '\n'
    'def process_file(fn):\n'
    '    Path(path)\n'
    '    text = ""\n'
    '    text = Path(fn).read_text(encoding="utf-8")\n'
    '    stack = []\n'
    '    mapping = {")": "(", "]": "[", "}": "{"}\n'
    '    for char in text:\n'
    '        if char in mapping:\n'
    '            top_element = stack.pop() if stack else "#"\n'
    '            if mapping[char] != top_element:\n'
    '                return False\n'
    '        elif char in {"(", "[", "{"}:\n'
    '            stack.append(char)\n'
    '    if not stack:\n'
    '        print(fn.name)\n'
    '    return not stack\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path.cwd()\n'
    '    args = sys.argv[1:]\n'
    '    files = [Path(f) for f in args] if args else get_files(cwd, ext=[".py"])\n'
    '    if len(files) == 1:\n'
    '        process_file(files[0])\n'
    '        sys.exit(0)\n'
    '    with get_context("spawn").Pool(8) as pool:\n'
    '        pending = deque()\n'
    '        for f in files:\n'
    '            pending.append(pool.apply_async(process_file, (f,)))\n'
    '            if len(pending) > MAX_QUEUE:\n'
    '                pending.popleft().get()\n'
    '        while pending:\n'
    '            pending.popleft().get()\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_FIX_IS_NOT_SOURCE: str = (
    'import argparse\n'
    'import concurrent.futures\n'
    'import os\n'
    'import tokenize\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def process_file(path, auto_fix=False):\n'
    '    result = {\n'
    '        "path": path,\n'
    '        "found_count": 0,\n'
    '        "fixed": False,\n'
    '        "lines": [],\n'
    '        "error": None,\n'
    '    }\n'
    '    try:\n'
    '        with path.open("rb") as f:\n'
    '            tokens = list(tokenize.tokenize(f.readline))\n'
    '    except Exception as e:\n'
    '        result["error"] = f"Failed to read/tokenize: {e}"\n'
    '        return result\n'
    '    modified_tokens = []\n'
    '    i = 0\n'
    '    n = len(tokens)\n'
    '    is_modified = False\n'
    '    while i < n:\n'
    '        tok = tokens[i]\n'
    '        if (\n'
    '            i + 1 < n\n'
    '            and tok.type == tokenize.NAME\n'
    '            and tok.string == "is"\n'
    '            and tokens[i + 1].type == tokenize.NAME\n'
    '            and tokens[i + 1].string == "not"\n'
    '        ):\n'
    '            result["found_count"] += 1\n'
    '            result["lines"].append(tok.start[0])\n'
    '            if auto_fix:\n'
    '                new_tok = tok._replace(type=tokenize.OP, string="!=")\n'
    '                modified_tokens.append(new_tok)\n'
    '                i += 2\n'
    '                is_modified = True\n'
    '                continue\n'
    '        modified_tokens.append(tok)\n'
    '        i += 1\n'
    '    if is_modified and auto_fix:\n'
    '        try:\n'
    '            fixed_bytes = tokenize.untokenize(modified_tokens)\n'
    '            path.write_bytes(fixed_bytes)\n'
    '            result["fixed"] = True\n'
    '        except Exception as e:\n'
    '            result["error"] = f"Failed to write auto-fix: {e}"\n'
    '    return result\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Recursively find and optionally replace \'is not\' with \'!=\' in Python files."\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-a",\n'
    '        "--auto-fix",\n'
    '        action="store_true",\n'
    '        help="Automatically replace \'is not\' with \'!=\' across files.",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    current_dir = Path(".")\n'
    '    py_files = list(current_dir.rglob("*.py"))\n'
    '    script_path = Path(__file__).resolve()\n'
    '    py_files = [f for f in py_files if f.resolve() != script_path]\n'
    '    if not py_files:\n'
    '        print("🔍 No Python files found to scan.")\n'
    '        return\n'
    '    cpu_cores = os.cpu_count() or 1\n'
    '    print(f"🔍 Found {len(py_files)} Python files.")\n'
    '    print(f"⚡ Processing concurrently across {cpu_cores} parallel workers...")\n'
    '    if args.auto_fix:\n'
    '        print("🛠️  Auto-fix mode active (-a). \'is not\' operators will be converted to \'!=\'.")\n'
    '    print("-" * 40)\n'
    '    total_files_with_issues = 0\n'
    '    total_replacements = 0\n'
    '    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_cores) as executor:\n'
    '        futures = {executor.submit(process_file, f, args.auto_fix): f for f in py_files}\n'
    '        for future in concurrent.futures.as_completed(futures):\n'
    '            res = future.result()\n'
    '            if res["error"]:\n'
    '                print(f"❌ [ERROR] {res[\'path\']}: {res[\'error\']}")\n'
    '                continue\n'
    '            if res["found_count"] > 0:\n'
    '                total_files_with_issues += 1\n'
    '                total_replacements += res["found_count"]\n'
    '                status = "[🔧 FIXED]" if res["fixed"] else "[⚠️  FOUND]"\n'
    '                lines_str = ", ".join(map(str, res["lines"]))\n'
    '                print(f"{status} {res[\'path\']} -> Found {res[\'found_count\']} time(s) on line(s): {lines_str}")\n'
    '    print("-" * 40)\n'
    '    print("📊 Summary:")\n'
    '    print(f"   Files containing \'is not\': {total_files_with_issues}")\n'
    '    print(f"   Total instances found:     {total_replacements}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_NORMALIZE_PRINT_SEP_SOURCE: str = (
    'import argparse\n'
    'import re\n'
    'import sys\n'
    'from multiprocessing import Pool\n'
    'from pathlib import Path\n'
    'from typing import NamedTuple\n'
    '\n'
    '\n'
    'class ProcessResult(NamedTuple):\n'
    '    error = None\n'
    '\n'
    '\n'
    'def normalize_separators(content):\n'
    '    pattern = r"(cprint|print)\\s*\\(\\s*[\'\\"](.)[\'\\"](\\s*\\*\\s*)(\\d+)([^)]*)\\)"\n'
    '    replacement = "print(\'-\'*42)"\n'
    '    new_content, count = re.subn(pattern, replacement, content)\n'
    '    return new_content, count\n'
    '\n'
    '\n'
    'def process_file(args):\n'
    '    path, autofix = args\n'
    '    try:\n'
    '        content = path.read_text(encoding="utf-8")\n'
    '        new_content, replacements = normalize_separators(content)\n'
    '        if replacements > 0 and autofix:\n'
    '            path.write_text(new_content, encoding="utf-8")\n'
    '        return ProcessResult(file=path, replacements=replacements, status="success")\n'
    '    except Exception as e:\n'
    '        return ProcessResult(file=path, replacements=0, status="error", error=str(e))\n'
    '\n'
    '\n'
    'def find_python_files(paths):\n'
    '    if not paths:\n'
    '        paths = ["."]\n'
    '    all_files = set()\n'
    '    for path_str in paths:\n'
    '        path = Path(path_str)\n'
    '        if path.is_file() and path.suffix == ".py":\n'
    '            all_files.add(path.resolve())\n'
    '        elif path.is_dir():\n'
    '            all_files.update(path.resolve().rglob("*.py"))\n'
    '    return sorted(all_files)\n'
    '\n'
    '\n'
    'def report_stats(results, autofix):\n'
    '    total_files = len(results)\n'
    '    total_replacements = sum(r.replacements for r in results)\n'
    '    success_count = sum(1 for r in results if r.status == "success")\n'
    '    modified_count = sum(1 for r in results if r.replacements > 0)\n'
    '    cwd = Path.cwd()\n'
    '    rel_results = [\n'
    '        (\n'
    '            r.file.relative_to(cwd) if cwd in r.file.parents or r.file == cwd else r.file,\n'
    '            r,\n'
    '        )\n'
    '        for r in results\n'
    '    ]\n'
    '    mode = "AUTOFIX" if autofix else "DRY-RUN"\n'
    '    print(f"\\n[{mode}] {\'File\':<55} {\'Replacements\':<15} {\'Status\':<15}")\n'
    '    print("-" * 40)\n'
    '    for rel_path, result in rel_results:\n'
    '        status_str = "✓ Success" if result.status == "success" else "✗ Error"\n'
    '        if result.error:\n'
    '            status_str += f": {result.error[:20]}"\n'
    '        print(f"{rel_path!s:<55} {result.replacements:<15} {status_str:<15}")\n'
    '    print("-" * 40)\n'
    '    print(f"Total files:        {total_files}")\n'
    '    print(f"Files would change: {modified_count}")\n'
    '    print(f"Total replacements: {total_replacements}")\n'
    '    print(f"Successful:         {success_count}")\n'
    '    print(f"Errors:             {total_files - success_count}")\n'
    '    if not autofix and modified_count > 0:\n'
    '        print(f"\\n💡 Run with --autofix (or -a) to apply {total_replacements} change(s)")\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Normalize print separators in Python files.",\n'
    '        epilog="Examples:\\n"\n'
    '        "  %(prog)s                  # Dry-run current directory\\n"\n'
    '        "  %(prog)s -a src/          # Autofix files in src/ directory\\n"\n'
    '        "  %(prog)s --autofix file.py other.py  # Autofix specific files",\n'
    '        formatter_class=argparse.RawDescriptionHelpFormatter,\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "paths",\n'
    '        nargs="*",\n'
    '        help="Files or directories to process (default: current directory)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-a",\n'
    '        "--autofix",\n'
    '        action="store_true",\n'
    '        help="Modify files in-place (default: dry-run only)",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    python_files = find_python_files(args.paths)\n'
    '    if not python_files:\n'
    '        print("No Python files found.")\n'
    '        sys.exit(1)\n'
    '    print(f"Found {len(python_files)} Python file(s). Processing in parallel...")\n'
    '    file_args = [(f, args.autofix) for f in python_files]\n'
    '    with Pool() as pool:\n'
    '        results = pool.map(process_file, file_args)\n'
    '    report_stats(results, args.autofix)\n'
    '    errors = [r for r in results if r.status == "error"]\n'
    '    sys.exit(1 if errors else 0)\n'
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


class EnsurebracketTool(BaseTool):
    """Wrapper for original ensurebracket.py: process_file() + 1 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'ensurebracket'
    source_file: str = 'ensurebracket.py'
    description: str = 'process_file() + 1 more'
    functions: list[str] = ['process_file', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _ENSUREBRACKET_SOURCE

class FixIsNotTool(BaseTool):
    """Wrapper for original fix_is_not.py: process_file() + 1 more."""
    name: str = 'fix_is_not'
    source_file: str = 'fix_is_not.py'
    description: str = 'process_file() + 1 more'
    functions: list[str] = ['process_file', 'main']
    notes: str = ''
    source: str = _FIX_IS_NOT_SOURCE

class NormalizePrintSepTool(BaseTool):
    """Wrapper for original normalize_print_sep.py: normalize_separators() + 4 more."""
    name: str = 'normalize_print_sep'
    source_file: str = 'normalize_print_sep.py'
    description: str = 'normalize_separators() + 4 more'
    functions: list[str] = ['normalize_separators', 'process_file', 'find_python_files', 'report_stats', 'main']
    notes: str = ''
    source: str = _NORMALIZE_PRINT_SEP_SOURCE

class NormalizePrintMiscUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'ensurebracket': EnsurebracketTool,
        'fix_is_not': FixIsNotTool,
        'normalize_print_sep': NormalizePrintSepTool,
    }

    @classmethod
    def list_tools(cls: type[NormalizePrintMiscUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[NormalizePrintMiscUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[NormalizePrintMiscUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for normalize_print_misc (3 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[NormalizePrintMiscUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[NormalizePrintMiscUnified], argv: Sequence[str] | None = None) -> int:
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
    return NormalizePrintMiscUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

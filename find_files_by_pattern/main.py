#!/usr/bin/env python3
"""FindFilesByPatternUnified for find_files_by_pattern.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (6):
  bkk <- bkk.py (10L): top-level script
  extinfo <- extinfo.py (24L): main() + 0 more [requires missing module 'dh' (ImportError at runtime)]
  extz <- extz.py (34L): walk_files() + 1 more
  find_scripts <- find_scripts.py (34L): has_shebang() + 1 more [requires missing module 'dh' (ImportError at runtime)]
  list_files_starting_with <- list_files_starting_with.py (16L): main() + 0 more
  lkk <- lkk.py (29L): main() + 0 more

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

_BKK_SOURCE: str = (
    'from pathlib import Path\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    for r, _d, files in cwd.walk():\n'
    '        for file in files:\n'
    '            path = Path(r) / file\n'
    '            if path.is_file() and path.name.endswith(".bak"):\n'
    '                print(path.relative_to(cwd))\n'
    '                path.unlink()\n'
)

_EXTINFO_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from dh import fsz\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: script.py <extension>")\n'
    '        print("Example: script.py py")\n'
    '        sys.exit(1)\n'
    '    ext = sys.argv[1].lstrip(".")\n'
    '    cwd = Path.cwd()\n'
    '    files = list(cwd.rglob(f"*.{ext}"))\n'
    '    if not files:\n'
    '        print(f"No .{ext} files found in current directory")\n'
    '        sys.exit(0)\n'
    '    total_size = sum(f.stat().st_size for f in files)\n'
    '    count = len(files)\n'
    '    print(f"Total number of .{ext} files: {count}")\n'
    '    print(f"Total size of .{ext} files: {fsz(total_size)}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_EXTZ_SOURCE: str = (
    'from collections import Counter\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def walk_files(directory):\n'
    '    for entry in directory.iterdir():\n'
    '        if entry.is_symlink():\n'
    '            continue\n'
    '        if entry.name == ".git":\n'
    '            continue\n'
    '        if entry.is_file():\n'
    '            yield entry\n'
    '        elif entry.is_dir():\n'
    '            yield from walk_files(entry)\n'
    '\n'
    '\n'
    'def main():\n'
    '    current_dir = Path.cwd()\n'
    '    extension_counter = Counter()\n'
    '    for path in walk_files(current_dir):\n'
    '        ext = path.suffix if path.suffix else ".no_ext"\n'
    '        extension_counter[ext] += 1\n'
    '    if extension_counter:\n'
    '        max_ext_len = max(len(ext) for ext in extension_counter)\n'
    '        max_count_len = max(len(str(count)) for count in extension_counter.values())\n'
    '        print("extensions found:")\n'
    '        for ext, count in sorted(extension_counter.items()):\n'
    '            print(f" {ext:<{max_ext_len}}  {count:>{max_count_len}} files")\n'
    '    else:\n'
    '        print("No files found.")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    main()\n'
)

_FIND_SCRIPTS_SOURCE: str = (
    'from pathlib import Path\n'
    'from dh import get_filez, is_binary, is_python_file, should_skip\n'
    '\n'
    '\n'
    'def has_shebang(path):\n'
    '    with path.open("rb") as f:\n'
    '        first_two = f.read(2)\n'
    '        if first_two == b"#!":\n'
    '            return True\n'
    '    return False\n'
    '\n'
    '\n'
    'def find_scripts_without_extension(directory):\n'
    '    swe = []\n'
    '    for item in get_filez(directory):\n'
    '        if should_skip(item):\n'
    '            continue\n'
    '        if item.is_file() and (not item.suffix):\n'
    '            if is_binary(item):\n'
    '                continue\n'
    '            if has_shebang(item) and is_python_file(item):\n'
    '                swe.append(item)\n'
    '    return swe\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    found_scripts = find_scripts_without_extension(cwd)\n'
    '    if found_scripts:\n'
    '        print("Found Python scripts without extension (relative paths):")\n'
    '        for script_path in found_scripts:\n'
    '            print(script_path.relative_to(cwd))\n'
    '    else:\n'
    '        print("No Python scripts without extension found in the current directory or its subdirectories.")\n'
)

_LIST_FILES_STARTING_WITH_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def main():\n'
    '    prefix = sys.argv[1].strip() if len(sys.argv) > 1 else ""\n'
    '    if not prefix:\n'
    '        print("Usage: python script.py <prefix>", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    for entry in Path.cwd().iterdir():\n'
    '        if entry.name.startswith(prefix) and not entry.is_symlink():\n'
    '            print(entry.name)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_LKK_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path.cwd()\n'
    '    args = sys.argv[1:]\n'
    '    skip_symlinks = True\n'
    '    search_pattern = None\n'
    '    for arg in args:\n'
    '        if arg == "-s":\n'
    '            skip_symlinks = False\n'
    '        else:\n'
    '            search_pattern = arg.strip()\n'
    '    found = []\n'
    '    for path in cwd.glob("*"):\n'
    '        if search_pattern in path.name:\n'
    '            if skip_symlinks and path.is_symlink():\n'
    '                continue\n'
    '            found.append(path)\n'
    '    for k in sorted(found):\n'
    '        if k.is_symlink():\n'
    '            print(f"  - {k.name} -> {k.resolve()}")\n'
    '        else:\n'
    '            print(f"  - {k.name}")\n'
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


class BkkTool(BaseTool):
    """Wrapper for original bkk.py: top-level script."""
    name: str = 'bkk'
    source_file: str = 'bkk.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _BKK_SOURCE

class ExtinfoTool(BaseTool):
    """Wrapper for original extinfo.py: main() + 0 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'extinfo'
    source_file: str = 'extinfo.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _EXTINFO_SOURCE

class ExtzTool(BaseTool):
    """Wrapper for original extz.py: walk_files() + 1 more."""
    name: str = 'extz'
    source_file: str = 'extz.py'
    description: str = 'walk_files() + 1 more'
    functions: list[str] = ['walk_files', 'main']
    notes: str = ''
    source: str = _EXTZ_SOURCE

class FindScriptsTool(BaseTool):
    """Wrapper for original find_scripts.py: has_shebang() + 1 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'find_scripts'
    source_file: str = 'find_scripts.py'
    description: str = 'has_shebang() + 1 more'
    functions: list[str] = ['has_shebang', 'find_scripts_without_extension']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _FIND_SCRIPTS_SOURCE

class ListFilesStartingWithTool(BaseTool):
    """Wrapper for original list_files_starting_with.py: main() + 0 more."""
    name: str = 'list_files_starting_with'
    source_file: str = 'list_files_starting_with.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _LIST_FILES_STARTING_WITH_SOURCE

class LkkTool(BaseTool):
    """Wrapper for original lkk.py: main() + 0 more."""
    name: str = 'lkk'
    source_file: str = 'lkk.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _LKK_SOURCE

class FindFilesByPatternUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'bkk': BkkTool,
        'extinfo': ExtinfoTool,
        'extz': ExtzTool,
        'find_scripts': FindScriptsTool,
        'list_files_starting_with': ListFilesStartingWithTool,
        'lkk': LkkTool,
    }

    @classmethod
    def list_tools(cls: type[FindFilesByPatternUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[FindFilesByPatternUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[FindFilesByPatternUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for find_files_by_pattern (6 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[FindFilesByPatternUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[FindFilesByPatternUnified], argv: Sequence[str] | None = None) -> int:
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
    return FindFilesByPatternUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

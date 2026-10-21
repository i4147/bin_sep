#!/usr/bin/env python3
"""FindFilesBySizeUnified for find_files_by_size.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (7):
  find_big_files <- find_big_files.py (47L): get_filez() + 2 more [requires missing module 'dh' (ImportError at runtime)]
  outcast <- outcast.py (29L): copy_largest_file() + 1 more
  similar_size_files <- similar_size_files.py (26L): main() + 0 more [requires missing module 'dh' (ImportError at runtime)]
  sortbysize <- sortbysize.py (25L): sort_by_size() + 0 more
  ssize <- ssize.py (25L): list_and_sort_by_size() + 0 more [requires missing module 'dh' (ImportError at runtime)]
  top11 <- top11.py (35L): get_sizes() + 1 more [requires missing module 'dh' (ImportError at runtime)]
  top12 <- top12.py (26L): get_top_10_largest_files_optimized() + 0 more

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

_FIND_BIG_FILES_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from dh import fsz\n'
    '\n'
    '\n'
    'def get_filez(root_dir):\n'
    '    from os import walk as os_walk\n'
    '\n'
    '    visited_dirs = set()\n'
    '    root_dir = Path(root_dir)\n'
    '    if root_dir.is_dir():\n'
    '        for dirpath, dirnames, filenames in os_walk(root_dir, topdown=True):\n'
    '            base_path = Path(dirpath)\n'
    '            for dirname in list(dirnames):\n'
    '                full_path = base_path / dirname\n'
    '                resolved_path = full_path.resolve()\n'
    '                if should_skip(full_path) or resolved_path in visited_dirs:\n'
    '                    dirnames.remove(dirname)\n'
    '                visited_dirs.add(resolved_path)\n'
    '            for filename in filenames:\n'
    '                path = Path(dirpath) / filename\n'
    '                if not should_skip(path):\n'
    '                    yield path\n'
    '    else:\n'
    '        yield root_dir\n'
    '\n'
    '\n'
    'THRESHOLD = 1024 * 1024\n'
    'cwd = Path.cwd()\n'
    '\n'
    '\n'
    'def process_file(path, threshold=THRESHOLD):\n'
    '    sz = path.stat().st_size\n'
    '    path = Path(path)\n'
    '    if sz > threshold:\n'
    '        print(f"{path.relative_to(cwd)} : {fsz(sz)}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    threshold = int(sys.argv[1]) * 1024 * 1024 if len(sys.argv) > 1 else THRESHOLD\n'
    '    for path in get_filez(cwd):\n'
    '        if not path.is_symlink():\n'
    '            process_file(path, threshold)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_OUTCAST_SOURCE: str = (
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def copy_largest_file(source_dir, dest):\n'
    '    largest = None\n'
    '    max = -1\n'
    '    for path in source_dir.iterdir():\n'
    '        if path.is_file():\n'
    '            size = path.stat().st_size\n'
    '            if size > max:\n'
    '                max = size\n'
    '                largest = path\n'
    '    if largest:\n'
    '        dest.write_bytes(largest.read_bytes())\n'
    '        print(f"{dest.name} ({max / (1024 * 1024)} MB)")\n'
    '\n'
    '\n'
    'def get_random_filename(length=6):\n'
    '    from random import choice\n'
    '    from string import ascii_lowercase\n'
    '\n'
    '    letters = ascii_lowercase\n'
    '    return "".join(choice(letters) for _ in range(length))\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    source = Path("/sdcard/Android/data/org.telegram.messenger/cache")\n'
    '    dest = Path(f"/sdcard/Download/{get_random_filename()}.mkv")\n'
    '    copy_largest_file(source, dest)\n'
)

_SIMILAR_SIZE_FILES_SOURCE: str = (
    'from pathlib import Path\n'
    'from dh import cprint, gsz\n'
    '\n'
    '\n'
    'def main():\n'
    '    root = Path.cwd()\n'
    '    kp = {}\n'
    '    files = [p for p in root.rglob("*") if p.is_file() and p.exists() and not p.is_symlink() and ".git" not in p.parts]\n'
    '    for f in files:\n'
    '        path = Path(root / f)\n'
    '        psz = gsz(path)\n'
    '        kp.setdefault(psz, []).append(path.name)\n'
    '    orig = kp\n'
    '    kz = sorted(kp.keys())\n'
    '    pk = {}\n'
    '    for x in kz:\n'
    '        pk[x] = orig.get(x)\n'
    '    for k, v in pk.items():\n'
    '        if len(v) > 1:\n'
    '            cprint(f"{k}:", "cyan")\n'
    '            for i in v:\n'
    '                print(f"    - {i}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_SORTBYSIZE_SOURCE: str = (
    'import json\n'
    'import operator\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def sort_by_size(root_folder):\n'
    '    items = []\n'
    '    for path in root_folder.glob("*"):\n'
    '        if path.is_symlink():\n'
    '            continue\n'
    '        if path.is_dir():\n'
    '            size = sum(p.stat().st_size for p in path.rglob("*") if p.is_file() and (not p.is_symlink()))\n'
    '        if path.is_file():\n'
    '            size = path.stat().st_size\n'
    '        items.append({"name": path.name, "size": size})\n'
    '    items.sort(key=operator.itemgetter("size"), reverse=True)\n'
    '    return items\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    data = sort_by_size(cwd)\n'
    '    outfile = Path(cwd.name + ".json")\n'
    '    with outfile.open("w", encoding="utf-8") as out:\n'
    '        json.dump(data, out, indent=2)\n'
)

_SSIZE_SOURCE: str = (
    'import operator\n'
    'from pathlib import Path\n'
    'from dh import fsz, gsz\n'
    '\n'
    'total = 0\n'
    '\n'
    '\n'
    'def list_and_sort_by_size(path=Path()):\n'
    '    items = []\n'
    '    global total\n'
    '    for p in path.glob("*"):\n'
    '        if p.is_symlink():\n'
    '            continue\n'
    '        size = gsz(p)\n'
    '        total += size\n'
    '        items.append({"name": p.name, "size": size})\n'
    '    items.sort(key=operator.itemgetter("size"), reverse=False)\n'
    '    return items\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    data = list_and_sort_by_size()\n'
    '    for k in data:\n'
    '        print(f"{k[\'name\']} : \\x1b[5;96m {fsz(k[\'size\'])}\\x1b[0m")\n'
    '    print(f"\\ntotal:\\x1b[5;94m {fsz(total)}\\x1b[0m")\n'
)

_TOP11_SOURCE: str = (
    'import operator\n'
    'import sys\n'
    'from pathlib import Path\n'
    'from dh import fsz, get_files\n'
    '\n'
    'cwd = Path.cwd()\n'
    'N = int(sys.argv[1]) if len(sys.argv) > 1 else 11\n'
    '\n'
    '\n'
    'def get_sizes():\n'
    '    return [(path.relative_to(cwd), path.stat().st_size) for path in get_files(cwd)]\n'
    '\n'
    '\n'
    'def main():\n'
    '    sizez = get_sizes()\n'
    '    if not sizez:\n'
    '        print("No files found or unable to access directory.")\n'
    '        return\n'
    '    sizez.sort(key=operator.itemgetter(1), reverse=True)\n'
    '    num_files = N if N else 11\n'
    '    top_files = sizez[:num_files]\n'
    '    max_path_len = max((len(str(path)) for path, size in top_files))\n'
    '    max_path_len = min(max_path_len, 80)\n'
    '    print(f"{\'No.\':<4} {\'File Path\':<{max_path_len}} {\'Size\':>12}")\n'
    '    print("-" * (max_path_len + 20))\n'
    '    for i, (path, size) in enumerate(top_files, 1):\n'
    '        path_str = str(path)\n'
    '        if len(path_str) > max_path_len:\n'
    '            path_str = "..." + path_str[-(max_path_len - 3) :]\n'
    '        size_str = fsz(size)\n'
    '        print(f"{i:<3} {path_str[: max_path_len - 3]:<{max_path_len}} {size_str:>12}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_TOP12_SOURCE: str = (
    'import heapq\n'
    'import os\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def get_top_10_largest_files_optimized(directory="."):\n'
    '    top_10 = []\n'
    '    for root, _dirs, files in os.walk(directory):\n'
    '        for file in files:\n'
    '            path = Path(root) / file\n'
    '            if path.is_file():\n'
    '                try:\n'
    '                    size = path.stat().st_size\n'
    '                    if len(top_10) < 10:\n'
    '                        heapq.heappush(top_10, (size, path))\n'
    '                    elif size > top_10[0][0]:\n'
    '                        heapq.heapreplace(top_10, (size, path))\n'
    '                except OSError:\n'
    '                    pass\n'
    '    return sorted(top_10, reverse=True)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    top_10 = get_top_10_largest_files_optimized()\n'
    '    for size, path in top_10:\n'
    '        print(f"{size} bytes - {path}")\n'
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


class FindBigFilesTool(BaseTool):
    """Wrapper for original find_big_files.py: get_filez() + 2 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'find_big_files'
    source_file: str = 'find_big_files.py'
    description: str = 'get_filez() + 2 more'
    functions: list[str] = ['get_filez', 'process_file', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _FIND_BIG_FILES_SOURCE

class OutcastTool(BaseTool):
    """Wrapper for original outcast.py: copy_largest_file() + 1 more."""
    name: str = 'outcast'
    source_file: str = 'outcast.py'
    description: str = 'copy_largest_file() + 1 more'
    functions: list[str] = ['copy_largest_file', 'get_random_filename']
    notes: str = ''
    source: str = _OUTCAST_SOURCE

class SimilarSizeFilesTool(BaseTool):
    """Wrapper for original similar_size_files.py: main() + 0 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'similar_size_files'
    source_file: str = 'similar_size_files.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _SIMILAR_SIZE_FILES_SOURCE

class SortbysizeTool(BaseTool):
    """Wrapper for original sortbysize.py: sort_by_size() + 0 more."""
    name: str = 'sortbysize'
    source_file: str = 'sortbysize.py'
    description: str = 'sort_by_size() + 0 more'
    functions: list[str] = ['sort_by_size']
    notes: str = ''
    source: str = _SORTBYSIZE_SOURCE

class SsizeTool(BaseTool):
    """Wrapper for original ssize.py: list_and_sort_by_size() + 0 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'ssize'
    source_file: str = 'ssize.py'
    description: str = 'list_and_sort_by_size() + 0 more'
    functions: list[str] = ['list_and_sort_by_size']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _SSIZE_SOURCE

class Top11Tool(BaseTool):
    """Wrapper for original top11.py: get_sizes() + 1 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'top11'
    source_file: str = 'top11.py'
    description: str = 'get_sizes() + 1 more'
    functions: list[str] = ['get_sizes', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _TOP11_SOURCE

class Top12Tool(BaseTool):
    """Wrapper for original top12.py: get_top_10_largest_files_optimized() + 0 more."""
    name: str = 'top12'
    source_file: str = 'top12.py'
    description: str = 'get_top_10_largest_files_optimized() + 0 more'
    functions: list[str] = ['get_top_10_largest_files_optimized']
    notes: str = ''
    source: str = _TOP12_SOURCE

class FindFilesBySizeUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'find_big_files': FindBigFilesTool,
        'outcast': OutcastTool,
        'similar_size_files': SimilarSizeFilesTool,
        'sortbysize': SortbysizeTool,
        'ssize': SsizeTool,
        'top11': Top11Tool,
        'top12': Top12Tool,
    }

    @classmethod
    def list_tools(cls: type[FindFilesBySizeUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[FindFilesBySizeUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[FindFilesBySizeUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for find_files_by_size (7 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[FindFilesBySizeUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[FindFilesBySizeUnified], argv: Sequence[str] | None = None) -> int:
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
    return FindFilesBySizeUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

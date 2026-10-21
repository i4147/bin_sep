#!/usr/bin/env python3
"""DedupDirsUnified for dedup_dirs.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (2):
  dupdirs <- dupdirs.py (194L): _file_hash() + 6 more
  find_dup_folders <- find_dup_folders.py (77L): is_nested() + 2 more [requires missing module 'dh' (ImportError at runtime)]

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

_DUPDIRS_SOURCE: str = (
    'import argparse\n'
    'import os\n'
    'import sys\n'
    'from collections import defaultdict\n'
    'from multiprocessing import Pool\n'
    'from pathlib import Path\n'
    'import xxhash\n'
    '\n'
    'NUM_WORKERS = 8\n'
    'SKIP_DIR_NAMES = {".git"}\n'
    'HASH_CHUNK_SIZE = 1 << 20\n'
    'MAX_DEPTH = 64\n'
    '\n'
    '\n'
    'def _file_hash(path):\n'
    '    h = xxhash.xxh64()\n'
    '    with open(path, "rb") as f:\n'
    '        for chunk in iter(lambda: f.read(HASH_CHUNK_SIZE), b""):\n'
    '            h.update(chunk)\n'
    '    return h.hexdigest()\n'
    '\n'
    '\n'
    'def _collect_files(root):\n'
    '    result = []\n'
    '    root = root.resolve()\n'
    '    stack = [(root, 0)]\n'
    '    while stack:\n'
    '        cur, depth = stack.pop()\n'
    '        if depth > MAX_DEPTH:\n'
    '            continue\n'
    '        try:\n'
    '            entries = list(os.scandir(cur))\n'
    '        except (PermissionError, OSError):\n'
    '            continue\n'
    '        for entry in entries:\n'
    '            try:\n'
    '                if entry.is_symlink():\n'
    '                    continue\n'
    '                if entry.is_dir(follow_symlinks=False):\n'
    '                    if entry.name in SKIP_DIR_NAMES:\n'
    '                        continue\n'
    '                    stack.append((Path(entry.path), depth + 1))\n'
    '                elif entry.is_file(follow_symlinks=False):\n'
    '                    rel = Path(entry.path).relative_to(root).as_posix()\n'
    '                    result.append((rel, Path(entry.path)))\n'
    '            except OSError:\n'
    '                continue\n'
    '    return result\n'
    '\n'
    '\n'
    'def _collect_subdirs(root):\n'
    '    result = []\n'
    '    root = root.resolve()\n'
    '    stack = [(root, 0)]\n'
    '    while stack:\n'
    '        cur, depth = stack.pop()\n'
    '        if depth > MAX_DEPTH:\n'
    '            continue\n'
    '        try:\n'
    '            entries = list(os.scandir(cur))\n'
    '        except (PermissionError, OSError):\n'
    '            continue\n'
    '        for entry in entries:\n'
    '            try:\n'
    '                if entry.is_symlink():\n'
    '                    continue\n'
    '                if entry.is_dir(follow_symlinks=False):\n'
    '                    if entry.name in SKIP_DIR_NAMES:\n'
    '                        continue\n'
    '                    rel = Path(entry.path).relative_to(root).as_posix()\n'
    '                    result.append(rel)\n'
    '                    stack.append((Path(entry.path), depth + 1))\n'
    '            except OSError:\n'
    '                continue\n'
    '    return result\n'
    '\n'
    '\n'
    'def folder_signature(args):\n'
    '    path_str, mode = args\n'
    '    root = Path(path_str).resolve()\n'
    '    files = _collect_files(root)\n'
    '    if not files:\n'
    '        return None\n'
    '    direct_files = [rel for rel, _ in files if "/" not in rel]\n'
    '    if not direct_files:\n'
    '        return None\n'
    '    rel_files = sorted(rel for rel, _ in files)\n'
    '    subdirs = sorted(_collect_subdirs(root))\n'
    '    struct_h = xxhash.xxh64()\n'
    '    for d in subdirs:\n'
    '        struct_h.update(b"D")\n'
    '        struct_h.update(d.encode("utf-8"))\n'
    '        struct_h.update(b"\\x00")\n'
    '    for rp in rel_files:\n'
    '        struct_h.update(b"F")\n'
    '        struct_h.update(rp.encode("utf-8"))\n'
    '        struct_h.update(b"\\x00")\n'
    '    struct_key = struct_h.hexdigest()\n'
    '    if mode == "content":\n'
    '        content_h = xxhash.xxh64()\n'
    '        for rel, abs_path in sorted(files, key=lambda x: x[0]):\n'
    '            try:\n'
    '                fh = _file_hash(abs_path)\n'
    '            except (PermissionError, OSError):\n'
    '                fh = "unreadable"\n'
    '            content_h.update(rel.encode("utf-8"))\n'
    '            content_h.update(b"\\x00")\n'
    '            content_h.update(fh.encode("ascii"))\n'
    '            content_h.update(b"\\x01")\n'
    '        content_key = content_h.hexdigest()\n'
    '    else:\n'
    '        content_key = ""\n'
    '    return (struct_key, content_key, str(root))\n'
    '\n'
    '\n'
    'def find_all_folders(start):\n'
    '    start = start.resolve()\n'
    '    folders = []\n'
    '    stack = [(start, 0)]\n'
    '    while stack:\n'
    '        cur, depth = stack.pop()\n'
    '        if depth > MAX_DEPTH:\n'
    '            continue\n'
    '        folders.append(cur)\n'
    '        try:\n'
    '            entries = list(os.scandir(cur))\n'
    '        except (PermissionError, OSError):\n'
    '            continue\n'
    '        for entry in entries:\n'
    '            try:\n'
    '                if entry.is_symlink():\n'
    '                    continue\n'
    '                if entry.is_dir(follow_symlinks=False):\n'
    '                    if entry.name in SKIP_DIR_NAMES:\n'
    '                        continue\n'
    '                    stack.append((Path(entry.path), depth + 1))\n'
    '            except OSError:\n'
    '                continue\n'
    '    return folders\n'
    '\n'
    '\n'
    'def parse_args():\n'
    '    p = argparse.ArgumentParser(description="Find duplicate folders in the current directory tree.")\n'
    '    p.add_argument(\n'
    '        "-s",\n'
    '        "--structure",\n'
    '        action="store_true",\n'
    '        help="Report folders with the same tree structure (same filenames & subfolders) even if contents differ.",\n'
    '    )\n'
    '    return p.parse_args()\n'
    '\n'
    '\n'
    'def main():\n'
    '    args = parse_args()\n'
    '    mode = "structure" if args.structure else "content"\n'
    '    start = Path.cwd()\n'
    '    print(f"Scanning : {start}")\n'
    '    print(f"Mode     : {mode}")\n'
    '    print(f"Workers  : {NUM_WORKERS}")\n'
    '    folders = find_all_folders(start)\n'
    '    print(f"Found {len(folders)} folder(s) (pre-filter).")\n'
    '    results = []\n'
    '    with Pool(processes=NUM_WORKERS) as pool:\n'
    '        async_results = [pool.apply_async(folder_signature, ((str(f), mode),)) for f in folders]\n'
    '        for ar in async_results:\n'
    '            try:\n'
    '                res = ar.get()\n'
    '            except Exception as e:\n'
    '                print(f"[warn] worker error: {e}", file=sys.stderr)\n'
    '                continue\n'
    '            if res is not None:\n'
    '                results.append(res)\n'
    '    groups = defaultdict(list)\n'
    '    if mode == "content":\n'
    '        for struct_key, content_key, path in results:\n'
    '            groups[(struct_key, content_key)].append(path)\n'
    '    else:\n'
    '        for struct_key, _, path in results:\n'
    '            groups[struct_key].append(path)\n'
    '    duplicates = {k: v for k, v in groups.items() if len(v) > 1}\n'
    '    if not duplicates:\n'
    '        print("\\nNo duplicate folders found.")\n'
    '        return\n'
    '    label = "same structure" if mode == "structure" else "identical content"\n'
    '    print(f"\\nFound {len(duplicates)} set(s) of folders with {label}:\\n")\n'
    '    for i, (_, paths) in enumerate(sorted(duplicates.items(), key=lambda kv: kv[1][0]), start=1):\n'
    '        print(f"--- Group {i} ({len(paths)} folders) ---")\n'
    '        for p in sorted(paths):\n'
    '            print(f"  {p}")\n'
    '        print()\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    main()\n'
)

_FIND_DUP_FOLDERS_SOURCE: str = (
    'import json\n'
    'from collections import defaultdict\n'
    'from pathlib import Path\n'
    'from dh import get_dirs\n'
    'from xxhash import xxh64\n'
    '\n'
    'CHUNK_SIZE = 1024 * 1024\n'
    '\n'
    '\n'
    'def is_nested(path1, path2):\n'
    '    try:\n'
    '        path1.resolve().relative_to(path2.resolve())\n'
    '        return True\n'
    '    except ValueError:\n'
    '        pass\n'
    '    try:\n'
    '        path2.resolve().relative_to(path1.resolve())\n'
    '        return True\n'
    '    except ValueError:\n'
    '        pass\n'
    '    return False\n'
    '\n'
    '\n'
    'def hash_folder(folder_path):\n'
    '    hasher = xxh64()\n'
    '    files = []\n'
    '    for path in folder_path.rglob("*"):\n'
    '        if path.is_symlink():\n'
    '            continue\n'
    '        if path.is_file():\n'
    '            files.append(path)\n'
    '    if not files:\n'
    '        return ""\n'
    '    for file in sorted(files):\n'
    '        rel = file.relative_to(folder_path)\n'
    '        hasher.update(str(rel).encode("utf-8"))\n'
    '        try:\n'
    '            with file.open("rb") as f:\n'
    '                while chunk := f.read(CHUNK_SIZE):\n'
    '                    hasher.update(chunk)\n'
    '        except OSError:\n'
    '            continue\n'
    '    return hasher.hexdigest()\n'
    '\n'
    '\n'
    'def find_duplicate_folders(cwd):\n'
    '    folder_hashes = defaultdict(list)\n'
    '    for path in get_dirs(cwd):\n'
    '        if ".git" in path.parts:\n'
    '            continue\n'
    '        folder_hash = hash_folder(path)\n'
    '        if folder_hash:\n'
    '            folder_hashes.setdefault(folder_hash, []).append(path)\n'
    '    return {h: paths for h, paths in folder_hashes.items() if len(paths) > 1}\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    duplicates = find_duplicate_folders(cwd)\n'
    '    if duplicates:\n'
    '        print("Duplicate folder groups:")\n'
    '        for h, paths in duplicates.items():\n'
    '            print(f"\\nGroup (Hash: {h}):")\n'
    '            for path in paths:\n'
    '                print(f"  - {path}")\n'
    '        cleaned = defaultdict(list)\n'
    '        for h, paths in duplicates.items():\n'
    '            for i in range(len(paths)):\n'
    '                for j in range(i + 1, len(paths)):\n'
    '                    p1 = Path(paths[i])\n'
    '                    p2 = Path(paths[j])\n'
    '                    if not is_nested(p1, p2):\n'
    '                        cleaned[h].append(str(p1))\n'
    '        with Path("/sdcard/dupdirs.json").open("w", encoding="utf-8") as fo:\n'
    '            json.dump(cleaned, fo)\n'
    '    else:\n'
    '        print("No duplicate folders found.")\n'
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


class DupdirsTool(BaseTool):
    """Wrapper for original dupdirs.py: _file_hash() + 6 more."""
    name: str = 'dupdirs'
    source_file: str = 'dupdirs.py'
    description: str = '_file_hash() + 6 more'
    functions: list[str] = ['_file_hash', '_collect_files', '_collect_subdirs', 'folder_signature', 'find_all_folders', 'parse_args', 'main']
    notes: str = ''
    source: str = _DUPDIRS_SOURCE

class FindDupFoldersTool(BaseTool):
    """Wrapper for original find_dup_folders.py: is_nested() + 2 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'find_dup_folders'
    source_file: str = 'find_dup_folders.py'
    description: str = 'is_nested() + 2 more'
    functions: list[str] = ['is_nested', 'hash_folder', 'find_duplicate_folders']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _FIND_DUP_FOLDERS_SOURCE

class DedupDirsUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'dupdirs': DupdirsTool,
        'find_dup_folders': FindDupFoldersTool,
    }

    @classmethod
    def list_tools(cls: type[DedupDirsUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[DedupDirsUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[DedupDirsUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for dedup_dirs (2 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[DedupDirsUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[DedupDirsUnified], argv: Sequence[str] | None = None) -> int:
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
    return DedupDirsUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

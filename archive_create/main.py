#!/usr/bin/env python3
"""ArchiveCreateUnified for archive_create.

Assumption: single original script preserved; `main.py [args...]` passes through to it.

Original scripts (1):
  archive_merger <- archive_merger.py (102L): Unified archive creation and cleanup tool.

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

_ARCHIVE_MERGER_SOURCE: str = (
    '"""\n'
    'Unified archive creation and cleanup tool.\n'
    '\n'
    'tar_folder.py -> python archive_merger.py tar <folder>\n'
    'tgzr.py -> python archive_merger.py tgz <folder>\n'
    '"""\n'
    '\n'
    'import argparse\n'
    'import multiprocessing as mp\n'
    'import shutil\n'
    'import tarfile\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def compress_tar(folder: Path, output: Path | None = None, cleanup: bool = False) -> bool:\n'
    '    try:\n'
    '        if output is None:\n'
    '            output = folder.parent / f"{folder.name}.tar"\n'
    '        shutil.make_archive(str(output), "tar", folder.parent, folder.name)\n'
    '        if cleanup:\n'
    '            if folder.is_dir():\n'
    '                shutil.rmtree(folder)\n'
    '            print(f"Cleaned up: {folder}")\n'
    '        return True\n'
    '    except Exception as e:\n'
    '        print(f"Error compressing: {e}")\n'
    '        return False\n'
    '\n'
    '\n'
    'def compress_tgz_parallel(folder: Path, num_workers: int = 8, cleanup: bool = True) -> bool:\n'
    '    try:\n'
    '        folder = folder.resolve()\n'
    '        archive_name = f"{folder.name}.tar.gz"\n'
    '        archive_path = folder.parent / archive_name\n'
    '\n'
    '        print(f"Creating archive: {archive_path}")\n'
    '        with tarfile.open(archive_path, "w:gz") as tar:\n'
    '            tar.add(folder, arcname=folder.name)\n'
    '\n'
    '        if cleanup:\n'
    '            print("Removing original files...")\n'
    '            items = [item for item in folder.iterdir() if item.resolve() != archive_path]\n'
    '            _remove_items_fast(items, num_workers)\n'
    '            print("Cleanup complete.")\n'
    '        return True\n'
    '    except Exception as e:\n'
    '        print(f"Error: {e}")\n'
    '        return False\n'
    '\n'
    '\n'
    'def _remove_item(path: Path) -> None:\n'
    '    if path.is_dir() and not path.is_symlink():\n'
    '        shutil.rmtree(path)\n'
    '    else:\n'
    '        path.unlink()\n'
    '\n'
    '\n'
    'def _remove_items_fast(items: list[Path], num_workers: int) -> None:\n'
    '    if not items:\n'
    '        return\n'
    '    with mp.Pool(processes=num_workers) as pool:\n'
    '        results = [pool.apply_async(_remove_item, (item,)) for item in items]\n'
    '        for result in results:\n'
    '            result.get()\n'
    '\n'
    '\n'
    'def main() -> int:\n'
    '    parser = argparse.ArgumentParser(description="Archive creation and cleanup tool")\n'
    '    subparsers = parser.add_subparsers(dest="mode", required=True)\n'
    '\n'
    '    tar_parser = subparsers.add_parser("tar", help="Create TAR archive and optionally remove folder")\n'
    '    tar_parser.add_argument("folder", type=Path, help="Folder to archive")\n'
    '    tar_parser.add_argument("--output", type=Path, default=None, help="Output archive path")\n'
    '    tar_parser.add_argument("--cleanup", action="store_true", default=False, help="Remove folder after compression")\n'
    '\n'
    '    tgz_parser = subparsers.add_parser("tgz", help="Create TAR.GZ archive and cleanup contents")\n'
    '    tgz_parser.add_argument("folder", type=Path, help="Folder to archive")\n'
    '    tgz_parser.add_argument("--workers", type=int, default=8, help="Number of parallel workers")\n'
    '    tgz_parser.add_argument("--no-cleanup", action="store_true", help="Keep original files")\n'
    '\n'
    '    args = parser.parse_args()\n'
    '\n'
    '    folder = Path(args.folder)\n'
    '    if not folder.exists():\n'
    '        print(f"Error: Folder \'{folder}\' not found.")\n'
    '        return 1\n'
    '    if not folder.is_dir():\n'
    '        print(f"Error: \'{folder}\' is not a directory.")\n'
    '        return 1\n'
    '\n'
    '    if args.mode == "tar":\n'
    '        success = compress_tar(folder, args.output, args.cleanup)\n'
    '    elif args.mode == "tgz":\n'
    '        success = compress_tgz_parallel(folder, args.workers, not args.no_cleanup)\n'
    '    else:\n'
    '        return 1\n'
    '\n'
    '    return 0 if success else 1\n'
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


class ArchiveMergerTool(BaseTool):
    """Wrapper for original archive_merger.py: Unified archive creation and cleanup tool.."""
    name: str = 'archive_merger'
    source_file: str = 'archive_merger.py'
    description: str = 'Unified archive creation and cleanup tool.'
    functions: list[str] = ['compress_tar', 'compress_tgz_parallel', '_remove_item', '_remove_items_fast', 'main']
    notes: str = ''
    source: str = _ARCHIVE_MERGER_SOURCE

class ArchiveCreateUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'archive_merger': ArchiveMergerTool,
    }

    @classmethod
    def list_tools(cls: type[ArchiveCreateUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[ArchiveCreateUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[ArchiveCreateUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for archive_create (1 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[ArchiveCreateUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[ArchiveCreateUnified], argv: Sequence[str] | None = None) -> int:
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
    return ArchiveCreateUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

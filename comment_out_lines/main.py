#!/usr/bin/env python3
"""CommentOutLinesUnified for comment_out_lines.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (2):
  comment_out <- comment_out.py (56L): main() + 0 more
  commentout <- commentout.py (110L): process_chunk() + 3 more

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

_COMMENT_OUT_SOURCE: str = (
    'import os\n'
    'import sys\n'
    '\n'
    'EXTENSION_COMMENTS = {\n'
    '    ".py": "#",\n'
    '    ".sh": "#",\n'
    '    ".yaml": "#",\n'
    '    ".yml": "#",\n'
    '    ".rb": "#",\n'
    '    ".js": "//",\n'
    '    ".ts": "//",\n'
    '    ".cpp": "//",\n'
    '    ".c": "//",\n'
    '    ".java": "//",\n'
    '    ".go": "//",\n'
    '    ".html": "<!--",\n'
    '    ".css": "/*",\n'
    '}\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 4:\n'
    '        print("Error: Missing arguments.\\nUsage: python comment_range.py <filename> <start_line> <end_line>")\n'
    '        sys.exit(1)\n'
    '    path = sys.argv[1]\n'
    '    try:\n'
    '        start_line = int(sys.argv[2])\n'
    '        end_line = int(sys.argv[3])\n'
    '    except ValueError:\n'
    '        print("Error: Start and end lines must be valid integers.")\n'
    '        sys.exit(1)\n'
    '    if start_line < 1 or end_line < start_line:\n'
    '        print("Error: Line numbers must start from 1, and end line must be >= start line.")\n'
    '        sys.exit(1)\n'
    '    if not os.path.exists(path):\n'
    '        print(f"Error: The file \'{path}\' does not exist.")\n'
    '        sys.exit(1)\n'
    '    _, ext = os.path.splitext(path.lower())\n'
    '    comment_char = EXTENSION_COMMENTS.get(ext, "#")\n'
    '    with open(path, "r", encoding="utf-8") as f:\n'
    '        lines = f.readlines()\n'
    '    total_lines = len(lines)\n'
    '    if start_line > total_lines:\n'
    '        print(f"Error: Start line ({start_line}) exceeds file length ({total_lines} lines).")\n'
    '        sys.exit(1)\n'
    '    actual_end = min(end_line, total_lines)\n'
    '    for i in range(start_line - 1, actual_end):\n'
    '        if not lines[i].strip().startswith(comment_char):\n'
    '            lines[i] = f"{comment_char} {lines[i]}"\n'
    '    with open(path, "w", encoding="utf-8") as f:\n'
    '        f.writelines(lines)\n'
    '    print(f"Success: Commented out lines {start_line} to {actual_end} in \'{path}\' using \'{comment_char}\'.")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_COMMENTOUT_SOURCE: str = (
    'import sys\n'
    'from collections.abc import Iterable, Sequence\n'
    'from multiprocessing import Pool\n'
    'from pathlib import Path\n'
    'from tempfile import NamedTemporaryFile\n'
    'from typing import List, Optional\n'
    'from loguru import logger\n'
    '\n'
    'POOL_SIZE = 8\n'
    'CHUNK_SIZE = 10_000\n'
    'DEFAULT_COMMENT = "#"\n'
    'COMMENT_MAP = {\n'
    '    ".vim": \'"\',\n'
    '    ".lua": "--",\n'
    '    ".py": "#",\n'
    '    ".sh": "#",\n'
    '    ".toml": "#",\n'
    '    ".yml": "#",\n'
    '    ".yaml": "#",\n'
    '    ".js": "//",\n'
    '    ".ts": "//",\n'
    '    ".cpp": "//",\n'
    '    ".c": "//",\n'
    '    ".cs": "//",\n'
    '    ".java": "//",\n'
    '    ".sql": "--",\n'
    '    ".rb": "#",\n'
    '}\n'
    '\n'
    '\n'
    'def process_chunk(lines, comment_char):\n'
    '    processed = []\n'
    '    for line in lines:\n'
    '        stripped = line.lstrip()\n'
    '        if not stripped or stripped.startswith(comment_char):\n'
    '            processed.append(line)\n'
    '        else:\n'
    '            processed.append(f"{comment_char}{line}")\n'
    '    return processed\n'
    '\n'
    '\n'
    'def _parse_args(argv):\n'
    '    if not 3 <= len(argv) <= 4:\n'
    '        logger.error("Usage: python commentout.py <filename> <start_line> [end_line]")\n'
    '        raise SystemExit(1)\n'
    '    file_path = Path(argv[1])\n'
    '    if not file_path.exists():\n'
    '        logger.error("File {} not found.", file_path)\n'
    '        raise SystemExit(1)\n'
    '    try:\n'
    '        start_line = int(argv[2])\n'
    '        end_line = int(argv[3]) if len(argv) == 4 else None\n'
    '    except ValueError:\n'
    '        logger.error("Line numbers must be integers.")\n'
    '        raise SystemExit(1)\n'
    '    return file_path, start_line, end_line\n'
    '\n'
    '\n'
    'def _resolve_comment_char(file_path):\n'
    '    ext = file_path.suffix.lower()\n'
    '    comment_char = COMMENT_MAP.get(ext)\n'
    '    if comment_char is None:\n'
    '        logger.warning(\n'
    '            "Unknown extension {}. Using default \'{}\' as comment char.",\n'
    '            ext,\n'
    '            DEFAULT_COMMENT,\n'
    '        )\n'
    '        return DEFAULT_COMMENT\n'
    '    return comment_char\n'
    '\n'
    '\n'
    'def main(argv=None):\n'
    '    args = list(argv) if argv is not None else sys.argv\n'
    '    file_path, start_line, end_line = _parse_args(args)\n'
    '    comment_char = _resolve_comment_char(file_path)\n'
    '    target_end = end_line if end_line is not None else sys.maxsize\n'
    '    with (\n'
    '        file_path.open("r", encoding="utf-8", errors="ignore") as infile,\n'
    '        NamedTemporaryFile("w", delete=False, dir=file_path.parent, encoding="utf-8") as temp_file,\n'
    '    ):\n'
    '        temp_path = Path(temp_file.name)\n'
    '        current_line_idx = 1\n'
    '        with Pool(processes=POOL_SIZE) as pool:\n'
    '            while True:\n'
    '                raw = [infile.readline() for _ in range(CHUNK_SIZE)]\n'
    '                lines = [line for line in raw if line]\n'
    '                if not lines:\n'
    '                    break\n'
    '                chunk_start = current_line_idx\n'
    '                chunk_end = current_line_idx + len(lines) - 1\n'
    '                if chunk_start <= target_end and chunk_end >= start_line:\n'
    '                    prefix_count = max(0, start_line - chunk_start)\n'
    '                    suffix_start = max(0, target_end - chunk_start + 1) if end_line is not None else len(lines)\n'
    '                    prefix = lines[:prefix_count]\n'
    '                    target_block = lines[prefix_count:suffix_start]\n'
    '                    suffix = lines[suffix_start:]\n'
    '                    async_result = pool.apply_async(process_chunk, (target_block, comment_char))\n'
    '                    temp_file.writelines(prefix)\n'
    '                    temp_file.writelines(async_result.get())\n'
    '                    temp_file.writelines(suffix)\n'
    '                else:\n'
    '                    temp_file.writelines(lines)\n'
    '                current_line_idx += len(lines)\n'
    '    temp_path.replace(file_path)\n'
    '    logger.info("Successfully processed {} using \'{}\'", file_path, comment_char)\n'
    '    return 0\n'
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


class CommentOutTool(BaseTool):
    """Wrapper for original comment_out.py: main() + 0 more."""
    name: str = 'comment_out'
    source_file: str = 'comment_out.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _COMMENT_OUT_SOURCE

class CommentoutTool(BaseTool):
    """Wrapper for original commentout.py: process_chunk() + 3 more."""
    name: str = 'commentout'
    source_file: str = 'commentout.py'
    description: str = 'process_chunk() + 3 more'
    functions: list[str] = ['process_chunk', '_parse_args', '_resolve_comment_char', 'main']
    notes: str = ''
    source: str = _COMMENTOUT_SOURCE

class CommentOutLinesUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'comment_out': CommentOutTool,
        'commentout': CommentoutTool,
    }

    @classmethod
    def list_tools(cls: type[CommentOutLinesUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[CommentOutLinesUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[CommentOutLinesUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for comment_out_lines (2 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[CommentOutLinesUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[CommentOutLinesUnified], argv: Sequence[str] | None = None) -> int:
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
    return CommentOutLinesUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

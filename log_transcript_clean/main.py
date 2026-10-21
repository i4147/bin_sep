#!/usr/bin/env python3
"""LogTranscriptCleanUnified for log_transcript_clean.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (7):
  cleaner <- cleaner.py (28L): clean_terminal_transcript() + 0 more
  cleanhistory <- cleanhistory.py (11L): top-level script
  cliner <- cliner.py (96L): clean_line() + 4 more [requires missing module 'dh' (ImportError at runtime)]
  cliner2 <- cliner2.py (53L): clean_line() + 2 more
  histdup <- histdup.py (26L): main() + 0 more
  last5minutes <- last5minutes.py (14L): top-level script
  mchist <- mchist.py (21L): top-level script

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

_CLEANER_SOURCE: str = (
    'import re\n'
    'import sys\n'
    '\n'
    '\n'
    'def clean_terminal_transcript(path):\n'
    '    with open(path, encoding="utf-8", errors="replace") as f:\n'
    '        content = f.read()\n'
    '    ansi_escape = re.compile(r"\\x1b(\\[[0-9;]*[mABCDEFGHJKSTfhilmnprsu]|\\][^\\x07]*\\x07|[()][AB012])")\n'
    '    content = ansi_escape.sub("", content)\n'
    '    content = content.replace("\\r\\n", "\\n")\n'
    '    content = content.replace("\\r", "\\n")\n'
    '    while "\\x08" in content:\n'
    '        content = re.sub(r".\\x08", "", content)\n'
    '    content = content.replace("\\x00", "")\n'
    '    content = re.sub(r"[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]", "", content)\n'
    '    content = re.sub(r"\\n{3,}", "\\n\\n", content)\n'
    '    content = "\\n".join(line.rstrip() for line in content.splitlines())\n'
    '    content = content.rstrip("\\n") + "\\n"\n'
    '    with open(path, "w", encoding="utf-8") as f:\n'
    '        f.write(content)\n'
    '    print(f"Cleaned: {path}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) != 2:\n'
    '        print(f"Usage: {sys.argv[0]} <transcript_file>")\n'
    '        sys.exit(1)\n'
    '    clean_terminal_transcript(sys.argv[1])\n'
)

_CLEANHISTORY_SOURCE: str = (
    'from pathlib import Path\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    fn = Path.home() / ".bash_history"\n'
    '    nl = []\n'
    '    with fn.open(encoding="utf-8") as f:\n'
    '        nl.extend(line for line in f if \'cd "`printf\' not in line)\n'
    '    nl = list(set(nl))\n'
    '    with fn.open("w", encoding="utf-8") as fo:\n'
    '        fo.writelines(nl)\n'
    '    print("done.")\n'
)

_CLINER_SOURCE: str = (
    'import mmap\n'
    'import re\n'
    'from pathlib import Path\n'
    'from dh import mpf3\n'
    '\n'
    'LOG_EXT = ".log"\n'
    'MMAP_THRESHOLD = 1 * 1024 * 1024\n'
    'NUM_WORKERS = 4\n'
    'PATTERNS = [\n'
    '    r"\\^\\[",\n'
    '    r"\\[[\\dA-Z;]+m",\n'
    '    r"\\[\\d+[A-Z]",\n'
    '    r"\\[[\\dA-Z;]+",\n'
    '    r"\\^M",\n'
    '    r"\\(B",\n'
    '    r"\\(0",\n'
    '    r"\\x1b\\[[0-9;]*[A-Za-z]",\n'
    '    r"\\x1b\\([0-9AB]",\n'
    '    r"\\r",\n'
    '    r"\\x0f",\n'
    '    r"\\x0e",\n'
    ']\n'
    'COMPILED_PATTERNS = [re.compile(pattern) for pattern in PATTERNS]\n'
    '\n'
    '\n'
    'def clean_line(line):\n'
    '    cleaned = line\n'
    '    for pattern in COMPILED_PATTERNS:\n'
    '        cleaned = pattern.sub("", cleaned)\n'
    '    return re.sub(" {2,}", " ", cleaned)\n'
    '\n'
    '\n'
    'def clean_file_small(path):\n'
    '    try:\n'
    '        with path.open(encoding="utf-8", errors="ignore") as f:\n'
    '            lines = f.readlines()\n'
    '        cleaned_lines = [clean_line(line) for line in lines]\n'
    '        with path.open("w", encoding="utf-8") as f:\n'
    '            f.writelines(cleaned_lines)\n'
    '        return (path, True, "small file")\n'
    '    except Exception as e:\n'
    '        return (path, False, str(e))\n'
    '\n'
    '\n'
    'def clean_file_large(path):\n'
    '    try:\n'
    '        with path.open("r+b") as f:\n'
    '            get_size = f.seek(0, 2)\n'
    '            f.seek(0)\n'
    '            if get_size == 0:\n'
    '                return (path, True, "empty file")\n'
    '            with mmap.mmap(f.fileno(), 0) as mmapped_file:\n'
    '                content = mmapped_file.read().decode("utf-8", errors="ignore")\n'
    '        lines = content.splitlines(keepends=True)\n'
    '        cleaned_lines = [clean_line(line) for line in lines]\n'
    '        cleaned_content = "".join(cleaned_lines)\n'
    '        Path(path).write_text(cleaned_content, encoding="utf-8")\n'
    '        return (path, True, "large file (mmap)")\n'
    '    except Exception as e:\n'
    '        return (path, False, str(e))\n'
    '\n'
    '\n'
    'def clean_file_worker(path):\n'
    '    try:\n'
    '        get_size = path.stat().st_size\n'
    '        if get_size > MMAP_THRESHOLD:\n'
    '            return clean_file_large(path)\n'
    '        return clean_file_small(path)\n'
    '    except Exception as e:\n'
    '        return (path, False, str(e))\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path.cwd()\n'
    '    log_files = list(cwd.rglob(f"*{LOG_EXT}"))\n'
    '    if not log_files:\n'
    '        print(f"No {LOG_EXT} files found.")\n'
    '        return\n'
    '    print(f"Found {len(log_files)} log file(s).")\n'
    '    results = mpf3(clean_file_worker, log_files)\n'
    '    success_count = 0\n'
    '    error_count = 0\n'
    '    for path, success, message in results:\n'
    '        if success:\n'
    '            print(f"✓ Cleaned: {path} ({message})")\n'
    '            success_count += 1\n'
    '        else:\n'
    '            print(f"✗ Error: {path} - {message}")\n'
    '            error_count += 1\n'
    '    print(f"\\nDone. Successfully processed {success_count}/{len(log_files)} file(s).")\n'
    '    if error_count > 0:\n'
    '        print(f"Failed: {error_count} file(s).")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_CLINER2_SOURCE: str = (
    'import re\n'
    'from pathlib import Path\n'
    '\n'
    'LOG_EXT = ".log"\n'
    'PATTERNS = [\n'
    '    r"\\^\\[",\n'
    '    r"\\[[\\dA-Z;]+m",\n'
    '    r"\\[\\d+[A-Z]",\n'
    '    r"\\[[\\dA-Z;]+",\n'
    '    r"\\^M",\n'
    '    r"\\(B",\n'
    '    r"\\(0",\n'
    '    r"\\x1b\\[[0-9;]*[A-Za-z]",\n'
    '    r"\\x1b\\([0-9AB]",\n'
    '    r"\\r",\n'
    '    r"\\x0f",\n'
    '    r"\\x0e",\n'
    ']\n'
    '\n'
    '\n'
    'def clean_line(line):\n'
    '    cleaned = line\n'
    '    for pattern in PATTERNS:\n'
    '        cleaned = re.sub(pattern, "", cleaned)\n'
    '    return re.sub(r" {2,}", " ", cleaned)\n'
    '\n'
    '\n'
    'def clean_file(path):\n'
    '    try:\n'
    '        with Path(path).open(encoding="utf-8", errors="ignore") as f:\n'
    '            lines = f.readlines()\n'
    '        cleaned_lines = [clean_line(line) for line in lines]\n'
    '        with Path(path).open("w", encoding="utf-8") as f:\n'
    '            f.writelines(cleaned_lines)\n'
    '        print(f"✓ Cleaned: {path}")\n'
    '    except Exception as e:\n'
    '        print(f"✗ Error processing {path}: {e}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path.cwd()\n'
    '    log_files = list(cwd.rglob(f"*{LOG_EXT}"))\n'
    '    if not log_files:\n'
    '        print(f"No {LOG_EXT} files found.")\n'
    '        return\n'
    '    print(f"Found {len(log_files)} log file(s). Cleaning...\\n")\n'
    '    for log_file in log_files:\n'
    '        clean_file(log_file)\n'
    '    print(f"\\nDone. Processed {len(log_files)} file(s).")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_HISTDUP_SOURCE: str = (
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def main():\n'
    '    hist_file = Path.home() / ".bash_history"\n'
    '    if not hist_file.exists():\n'
    '        print("~/.bash_history does not exist.")\n'
    '        return\n'
    '    with hist_file.open("r", encoding="utf-8", errors="ignore") as f:\n'
    '        lines = f.readlines()\n'
    '    seen = set()\n'
    '    unique_lines = []\n'
    '    histlen = len(lines)\n'
    '    print(f"history length: {histlen}")\n'
    '    for line in lines:\n'
    '        stripped = line.rstrip("\\n")\n'
    '        if stripped not in seen:\n'
    '            seen.add(stripped)\n'
    '            unique_lines.append(line)\n'
    '    with hist_file.open("w", encoding="utf-8") as f:\n'
    '        f.writelines(unique_lines)\n'
    '    print(f"{histlen - len(unique_lines)} lines removed")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_LAST5MINUTES_SOURCE: str = (
    'import sys\n'
    'from moviepy import AudioFileClip\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    file = sys.argv[1]\n'
    '    output = "last_5_minutes.mp3"\n'
    '    print("Loading file and extracting last 5 minutes...")\n'
    '    audio = AudioFileClip(file)\n'
    '    duration = audio.duration\n'
    '    start_time = max(0, duration - 230)\n'
    '    clip = audio.subclipped(start_time, duration)\n'
    '    print(f"Writing {output} ({duration / 60:.1f} min total → last 5 min)...")\n'
    '    clip.write_audiofile(output, bitrate="320k", fps=44100)\n'
    '    print("Done! 🎉")\n'
)

_MCHIST_SOURCE: str = (
    'from pathlib import Path\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    input_file = Path("/data/data/com.termux/files/home/.local/share/mc/history")\n'
    '    output_file = Path("/data/data/com.termux/files/home/.bash_history")\n'
    '    cmdline_section = []\n'
    '    lines = input_file.read_text(encoding="utf8").splitlines()\n'
    '    capture = False\n'
    '    for line in lines:\n'
    '        line = line.strip()\n'
    '        if line == "[cmdline]":\n'
    '            capture = True\n'
    '            continue\n'
    '        if capture:\n'
    '            if line == "":\n'
    '                break\n'
    '            cleaned_line = line.split("=", 1)[-1].strip()\n'
    '            cmdline_section.append(cleaned_line)\n'
    '    soniq = list(set(cmdline_section))\n'
    '    with output_file.open("a", encoding="utf-8") as file:\n'
    '        file.writelines(cmd + "\\n" for cmd in soniq)\n'
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


class CleanerTool(BaseTool):
    """Wrapper for original cleaner.py: clean_terminal_transcript() + 0 more."""
    name: str = 'cleaner'
    source_file: str = 'cleaner.py'
    description: str = 'clean_terminal_transcript() + 0 more'
    functions: list[str] = ['clean_terminal_transcript']
    notes: str = ''
    source: str = _CLEANER_SOURCE

class CleanhistoryTool(BaseTool):
    """Wrapper for original cleanhistory.py: top-level script."""
    name: str = 'cleanhistory'
    source_file: str = 'cleanhistory.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _CLEANHISTORY_SOURCE

class ClinerTool(BaseTool):
    """Wrapper for original cliner.py: clean_line() + 4 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'cliner'
    source_file: str = 'cliner.py'
    description: str = 'clean_line() + 4 more'
    functions: list[str] = ['clean_line', 'clean_file_small', 'clean_file_large', 'clean_file_worker', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _CLINER_SOURCE

class Cliner2Tool(BaseTool):
    """Wrapper for original cliner2.py: clean_line() + 2 more."""
    name: str = 'cliner2'
    source_file: str = 'cliner2.py'
    description: str = 'clean_line() + 2 more'
    functions: list[str] = ['clean_line', 'clean_file', 'main']
    notes: str = ''
    source: str = _CLINER2_SOURCE

class HistdupTool(BaseTool):
    """Wrapper for original histdup.py: main() + 0 more."""
    name: str = 'histdup'
    source_file: str = 'histdup.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _HISTDUP_SOURCE

class Last5minutesTool(BaseTool):
    """Wrapper for original last5minutes.py: top-level script."""
    name: str = 'last5minutes'
    source_file: str = 'last5minutes.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _LAST5MINUTES_SOURCE

class MchistTool(BaseTool):
    """Wrapper for original mchist.py: top-level script."""
    name: str = 'mchist'
    source_file: str = 'mchist.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _MCHIST_SOURCE

class LogTranscriptCleanUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'cleaner': CleanerTool,
        'cleanhistory': CleanhistoryTool,
        'cliner': ClinerTool,
        'cliner2': Cliner2Tool,
        'histdup': HistdupTool,
        'last5minutes': Last5minutesTool,
        'mchist': MchistTool,
    }

    @classmethod
    def list_tools(cls: type[LogTranscriptCleanUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[LogTranscriptCleanUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[LogTranscriptCleanUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for log_transcript_clean (7 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[LogTranscriptCleanUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[LogTranscriptCleanUnified], argv: Sequence[str] | None = None) -> int:
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
    return LogTranscriptCleanUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

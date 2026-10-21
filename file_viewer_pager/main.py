#!/usr/bin/env python3
"""FileViewerPagerUnified for file_viewer_pager.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (6):
  faprinter <- faprinter.py (14L): ylines() + 0 more
  fv <- fv.py (11L): main() + 0 more
  pbat <- pbat.py (394L): parse_line_range() + 8 more
  pyhead <- pyhead.py (11L): top-level script
  quickview <- quickview.py (85L): list_files() + 4 more
  qv <- qv.py (42L): collect_files() + 1 more

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

_FAPRINTER_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from faprint import faprint as pp\n'
    '\n'
    '\n'
    'def ylines(path):\n'
    '    with path.open(encoding="utf-8") as f:\n'
    '        yield from f\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    fn = Path(sys.argv[1])\n'
    '    for k in ylines(fn):\n'
    '        print(pp(k))\n'
)

_FV_SOURCE: str = (
    'import pydoc\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def main():\n'
    '    pydoc.pager(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"))\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_PBAT_SOURCE: str = (
    'import argparse\n'
    'import io\n'
    'import os\n'
    'import re\n'
    'import shutil\n'
    'import subprocess\n'
    'import sys\n'
    'from dataclasses import dataclass, field\n'
    'from pathlib import Path\n'
    'from pygments import highlight as pyg_highlight\n'
    'from pygments.formatters import Terminal256Formatter, TerminalTrueColorFormatter\n'
    'from pygments.lexers import (\n'
    '    TextLexer,\n'
    '    get_all_lexers,\n'
    '    get_lexer_by_name,\n'
    '    get_lexer_for_filename,\n'
    '    guess_lexer,\n'
    ')\n'
    'from pygments.styles import get_all_styles, get_style_by_name\n'
    'from pygments.util import ClassNotFound\n'
    '\n'
    'RESET = "\\x1b[0m"\n'
    'GRID_COLOR = "\\x1b[38;5;238m"\n'
    'HEADER_COLOR = "\\x1b[38;5;81m"\n'
    'LINE_NUM_COLOR = "\\x1b[38;5;244m"\n'
    'ADDED_COLOR = "\\x1b[38;5;150m"\n'
    'MODIFIED_COLOR = "\\x1b[38;5;222m"\n'
    'REMOVED_COLOR = "\\x1b[38;5;203m"\n'
    'HIGHLIGHT_BG = "\\x1b[48;5;236m"\n'
    'BOX_H, BOX_V = "─", "│"\n'
    'BOX_TL, BOX_TR, BOX_BL, BOX_BR = "╭", "╮", "╰", "╯"\n'
    'ANSI_RE = re.compile(r"\\x1b\\[[0-9;]*m")\n'
    '\n'
    '\n'
    '@dataclass\n'
    'class BatConfig:\n'
    '    files = field(default_factory=list)\n'
    '    language = None\n'
    '    theme = "monokai"\n'
    '    show_numbers = True\n'
    '    show_grid = True\n'
    '    show_header = True\n'
    '    show_changes = True\n'
    '    plain = False\n'
    '    line_range = None\n'
    '    highlight_lines = field(default_factory=set)\n'
    '    paging = "auto"\n'
    '    tab_width = 4\n'
    '    color = "auto"\n'
    '\n'
    '    def apply_plain(self):\n'
    '        if self.plain:\n'
    '            self.show_numbers = False\n'
    '            self.show_grid = False\n'
    '            self.show_header = False\n'
    '            self.show_changes = False\n'
    '\n'
    '\n'
    'class GitDiffCalculator:\n'
    '    def __init__(self, path):\n'
    '        self.path = path\n'
    '        self.added = set()\n'
    '        self.modified = set()\n'
    '        self.removed_before = {}\n'
    '        self._compute()\n'
    '\n'
    '    def _compute(self):\n'
    '        if not shutil.which("git"):\n'
    '            return\n'
    '        try:\n'
    '            top = subprocess.run(\n'
    '                [\n'
    '                    "git",\n'
    '                    "-C",\n'
    '                    str(self.path.parent),\n'
    '                    "rev-parse",\n'
    '                    "--show-toplevel",\n'
    '                ],\n'
    '                capture_output=True,\n'
    '                text=True,\n'
    '                timeout=5,\n'
    '            )\n'
    '            if top.returncode != 0:\n'
    '                return\n'
    '            result = subprocess.run(\n'
    '                [\n'
    '                    "git",\n'
    '                    "-C",\n'
    '                    str(self.path.parent),\n'
    '                    "diff",\n'
    '                    "--no-color",\n'
    '                    "-U0",\n'
    '                    "--",\n'
    '                    self.path.name,\n'
    '                ],\n'
    '                capture_output=True,\n'
    '                text=True,\n'
    '                timeout=5,\n'
    '            )\n'
    '            if result.stdout:\n'
    '                self._parse_hunks(result.stdout)\n'
    '        except Exception:\n'
    '            pass\n'
    '\n'
    '    def _parse_hunks(self, diff_text):\n'
    '        for line in diff_text.splitlines():\n'
    '            if not line.startswith("@@"):\n'
    '                continue\n'
    '            try:\n'
    '                parts = line.split()\n'
    '                old_part = parts[1].lstrip("-")\n'
    '                new_part = parts[2].lstrip("+")\n'
    '                old_count = int(old_part.split(",")[1]) if "," in old_part else 1\n'
    '                new_start_s, *rest = new_part.split(",")\n'
    '                new_start = int(new_start_s)\n'
    '                new_count = int(rest[0]) if rest else 1\n'
    '            except Exception:\n'
    '                continue\n'
    '            if old_count > 0 and new_count > 0:\n'
    '                for i in range(new_count):\n'
    '                    self.modified.add(new_start + i)\n'
    '            elif old_count > 0 and new_count == 0:\n'
    '                key = new_start + 1\n'
    '                self.removed_before[key] = self.removed_before.get(key, 0) + old_count\n'
    '            elif old_count == 0 and new_count > 0:\n'
    '                for i in range(new_count):\n'
    '                    self.added.add(new_start + i)\n'
    '\n'
    '    def status_for(self, line_no):\n'
    '        if line_no in self.added:\n'
    '            return "added"\n'
    '        if line_no in self.modified:\n'
    '            return "modified"\n'
    '        return None\n'
    '\n'
    '    def removed_marker(self, line_no):\n'
    '        return self.removed_before.get(line_no, 0)\n'
    '\n'
    '\n'
    'class Printer:\n'
    '    def __init__(self, config):\n'
    '        self.config = config\n'
    '\n'
    '    def print_file(self, path, content):\n'
    '        lines = content.splitlines()\n'
    '        total = len(lines)\n'
    '        lexer = self._get_lexer(path, content)\n'
    '        formatter = self._get_formatter()\n'
    '        git = GitDiffCalculator(path) if (path and self.config.show_changes) else None\n'
    '        start, end = self._resolve_range(total)\n'
    '        width = shutil.get_terminal_size((100, 24)).columns\n'
    '        out = io.StringIO()\n'
    '        if self.config.show_header:\n'
    '            self._print_header(out, path, width)\n'
    '        elif self.config.show_grid:\n'
    '            out.write(f"{GRID_COLOR}{BOX_H * width}{RESET}\\n")\n'
    '        highlighted = self._highlight_lines(lines, lexer, formatter)\n'
    '        for idx in range(start, end + 1):\n'
    '            if 1 <= idx <= total:\n'
    '                text = highlighted[idx - 1] if idx - 1 < len(highlighted) else ""\n'
    '                self._print_line(out, idx, text, git)\n'
    '        if self.config.show_grid:\n'
    '            out.write(f"{GRID_COLOR}{BOX_H * width}{RESET}\\n")\n'
    '        return out.getvalue()\n'
    '\n'
    '    def _get_lexer(self, path, content):\n'
    '        if self.config.language:\n'
    '            try:\n'
    '                return get_lexer_by_name(self.config.language, stripnl=False, tabsize=self.config.tab_width)\n'
    '            except ClassNotFound:\n'
    '                pass\n'
    '        if path:\n'
    '            try:\n'
    '                return get_lexer_for_filename(str(path), content, stripnl=False, tabsize=self.config.tab_width)\n'
    '            except ClassNotFound:\n'
    '                pass\n'
    '        try:\n'
    '            return guess_lexer(content, stripnl=False)\n'
    '        except ClassNotFound:\n'
    '            return TextLexer(stripnl=False)\n'
    '\n'
    '    def _get_formatter(self):\n'
    '        if self.config.color == "never":\n'
    '            return None\n'
    '        try:\n'
    '            style = get_style_by_name(self.config.theme)\n'
    '        except ClassNotFound:\n'
    '            style = get_style_by_name("default")\n'
    '        if "truecolor" in os.environ.get("COLORTERM", "") or "24bit" in os.environ.get("COLORTERM", ""):\n'
    '            return TerminalTrueColorFormatter(style=style)\n'
    '        return Terminal256Formatter(style=style)\n'
    '\n'
    '    def _highlight_lines(self, lines, lexer, formatter):\n'
    '        if self.config.plain or formatter is None:\n'
    '            return lines\n'
    '        code = "\\n".join(lines) + "\\n"\n'
    '        highlighted = pyg_highlight(code, lexer, formatter).split("\\n")\n'
    '        if highlighted and highlighted[-1] == "":\n'
    '            highlighted.pop()\n'
    '        return highlighted\n'
    '\n'
    '    def _resolve_range(self, total):\n'
    '        if self.config.line_range:\n'
    '            s, e = self.config.line_range\n'
    '            e = e if e is not None else total\n'
    '            return max(1, s), min(total, e)\n'
    '        return 1, total\n'
    '\n'
    '    def _print_header(self, out, path, width):\n'
    '        name = str(path) if path else "STDIN"\n'
    '        title = f" {name} "\n'
    '        left = BOX_H * 2\n'
    '        right = BOX_H * max(width - len(left) - len(title) - 2, 0)\n'
    '        out.write(f"{GRID_COLOR}{BOX_TL}{left}{RESET}{HEADER_COLOR}{title}{RESET}{GRID_COLOR}{right}{BOX_TR}{RESET}\\n")\n'
    '\n'
    '    def _print_line(self, out, line_no, text, git):\n'
    '        prefix_parts = []\n'
    '        if self.config.show_changes:\n'
    '            marker, color = " ", ""\n'
    '            if git:\n'
    '                if git.removed_marker(line_no):\n'
    '                    marker, color = "‾", REMOVED_COLOR\n'
    '                else:\n'
    '                    status = git.status_for(line_no)\n'
    '                    if status == "added":\n'
    '                        marker, color = "+", ADDED_COLOR\n'
    '                    elif status == "modified":\n'
    '                        marker, color = "~", MODIFIED_COLOR\n'
    '            prefix_parts.append(f"{color}{marker}{RESET}" if color else marker)\n'
    '        if self.config.show_numbers:\n'
    '            prefix_parts.append(f"{LINE_NUM_COLOR}{line_no:>4}{RESET}")\n'
    '        if self.config.show_grid:\n'
    '            prefix_parts.append(f"{GRID_COLOR}{BOX_V}{RESET}")\n'
    '        prefix = " ".join(prefix_parts)\n'
    '        line_out = f"{HIGHLIGHT_BG}{text}{RESET}" if line_no in self.config.highlight_lines else text\n'
    '        out.write(f"{prefix} {line_out}\\n" if prefix else f"{line_out}\\n")\n'
    '\n'
    '\n'
    'def parse_line_range(s):\n'
    '    if ":" in s:\n'
    '        a, b = s.split(":", 1)\n'
    '        return (int(a) if a else 1, int(b) if b else None)\n'
    '    n = int(s)\n'
    '    return (n, n)\n'
    '\n'
    '\n'
    'def read_input(path):\n'
    '    if path == "-":\n'
    '        return None, sys.stdin.read()\n'
    '    p = Path(path)\n'
    '    try:\n'
    '        data = p.read_bytes()\n'
    '    except OSError as e:\n'
    '        print(f"pybat: {path}: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    if b"\\x00" in data[:8192]:\n'
    '        print(\n'
    '            f"pybat: {path}: binary file detected, use --plain to force display",\n'
    '            file=sys.stderr,\n'
    '        )\n'
    '        sys.exit(1)\n'
    '    try:\n'
    '        return p, data.decode("utf-8")\n'
    '    except UnicodeDecodeError:\n'
    '        return p, data.decode("utf-8", errors="replace")\n'
    '\n'
    '\n'
    'def list_languages():\n'
    '    for name, aliases, _, _ in sorted(get_all_lexers(), key=lambda x: x[0].lower()):\n'
    '        print(f"{name:30} {\', \'.join(aliases)}")\n'
    '\n'
    '\n'
    'def list_themes():\n'
    '    for style in sorted(get_all_styles()):\n'
    '        print(style)\n'
    '\n'
    '\n'
    'def build_arg_parser():\n'
    '    p = argparse.ArgumentParser(\n'
    '        prog="pybat",\n'
    '        description="A Python port of the Rust `bat` crate — cat clone with syntax highlighting.",\n'
    '    )\n'
    '    p.add_argument("files", nargs="*", help="Files to display (use \'-\' for stdin)")\n'
    '    p.add_argument("-l", "--language", help="Set the language for syntax highlighting")\n'
    '    p.add_argument("--theme", default="monokai", help="Color theme (see --list-themes)")\n'
    '    p.add_argument(\n'
    '        "-p",\n'
    '        "--plain",\n'
    '        action="store_true",\n'
    '        help="Plain output: no line numbers, header, grid or git markers",\n'
    '    )\n'
    '    p.add_argument(\n'
    '        "--style",\n'
    '        default="full",\n'
    '        choices=["full", "plain", "numbers", "grid", "header", "changes"],\n'
    '        help="Output style",\n'
    '    )\n'
    '    p.add_argument(\n'
    '        "-r",\n'
    '        "--line-range",\n'
    '        help="Only show given line range, e.g. \'30:40\', \'30:\', \':40\'",\n'
    '    )\n'
    '    p.add_argument(\n'
    '        "-H",\n'
    '        "--highlight-line",\n'
    '        action="append",\n'
    '        default=[],\n'
    '        type=int,\n'
    '        help="Highlight a specific line (repeatable)",\n'
    '    )\n'
    '    p.add_argument("--paging", default="auto", choices=["auto", "always", "never"])\n'
    '    p.add_argument("--color", default="auto", choices=["auto", "always", "never"])\n'
    '    p.add_argument("--tabs", type=int, default=4, dest="tab_width")\n'
    '    p.add_argument("--list-languages", action="store_true")\n'
    '    p.add_argument("--list-themes", action="store_true")\n'
    '    return p\n'
    '\n'
    '\n'
    'def config_from_args(args):\n'
    '    cfg = BatConfig(\n'
    '        files=args.files,\n'
    '        language=args.language,\n'
    '        theme=args.theme,\n'
    '        paging=args.paging,\n'
    '        tab_width=args.tab_width,\n'
    '        color=args.color,\n'
    '        plain=args.plain,\n'
    '        highlight_lines=set(args.highlight_line),\n'
    '    )\n'
    '    style_reset = {\n'
    '        "show_numbers": False,\n'
    '        "show_grid": False,\n'
    '        "show_header": False,\n'
    '        "show_changes": False,\n'
    '    }\n'
    '    if args.style == "plain":\n'
    '        cfg.plain = True\n'
    '    elif args.style in ("numbers", "grid", "header", "changes"):\n'
    '        for k, v in style_reset.items():\n'
    '            setattr(cfg, k, v)\n'
    '        setattr(cfg, f"show_{args.style}", True)\n'
    '    cfg.apply_plain()\n'
    '    if args.line_range:\n'
    '        cfg.line_range = parse_line_range(args.line_range)\n'
    '    return cfg\n'
    '\n'
    '\n'
    'def should_page(cfg, line_count):\n'
    '    if cfg.paging == "always":\n'
    '        return True\n'
    '    if cfg.paging == "never":\n'
    '        return False\n'
    '    if not sys.stdout.isatty():\n'
    '        return False\n'
    '    return line_count > shutil.get_terminal_size((100, 24)).lines\n'
    '\n'
    '\n'
    'def page_output(text):\n'
    '    pager = os.environ.get("PAGER", "less")\n'
    '    try:\n'
    '        proc = subprocess.Popen([pager, "-R"], stdin=subprocess.PIPE)\n'
    '        proc.communicate(text.encode("utf-8"))\n'
    '    except FileNotFoundError:\n'
    '        sys.stdout.write(text)\n'
    '\n'
    '\n'
    'def main(argv=None):\n'
    '    args = build_arg_parser().parse_args(argv)\n'
    '    if args.list_languages:\n'
    '        list_languages()\n'
    '        return 0\n'
    '    if args.list_themes:\n'
    '        list_themes()\n'
    '        return 0\n'
    '    if not args.files:\n'
    '        args.files = ["-"]\n'
    '    cfg = config_from_args(args)\n'
    '    printer = Printer(cfg)\n'
    '    chunks = []\n'
    '    for f in cfg.files:\n'
    '        path, content = read_input(f)\n'
    '        chunks.append(printer.print_file(path, content))\n'
    '    final_text = "".join(chunks)\n'
    '    if cfg.color == "never":\n'
    '        final_text = ANSI_RE.sub("", final_text)\n'
    '    if should_page(cfg, final_text.count("\\n")):\n'
    '        page_output(final_text)\n'
    '    else:\n'
    '        sys.stdout.write(final_text)\n'
    '    return 0\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    sys.exit(main())\n'
)

_PYHEAD_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    fn = Path(sys.argv[1])\n'
    '    try:\n'
    '        with fn.open(encoding="utf-8", errors="ignore") as f:\n'
    '            print(f.read(1024))\n'
    '    except:\n'
    '        with fn.open("rb") as f:\n'
    '            print(f.read(1024))\n'
)

_QUICKVIEW_SOURCE: str = (
    'import curses\n'
    'from pathlib import Path\n'
    '\n'
    'LINES_PER_FILE = 20\n'
    '\n'
    '\n'
    'def list_files():\n'
    '    return sorted([p for p in Path().iterdir() if p.is_file()], key=lambda p: p.name.lower())\n'
    '\n'
    '\n'
    'def head_lines(path, n):\n'
    '    lines = []\n'
    '    try:\n'
    '        with Path(path).open(encoding="utf-8", errors="replace") as f:\n'
    '            for _ in range(n):\n'
    '                line = f.readline()\n'
    '                if not line:\n'
    '                    break\n'
    '                lines.append(line.rstrip("\\n"))\n'
    '    except Exception as e:\n'
    '        lines = [f"[Error reading file: {e}]"]\n'
    '    return lines\n'
    '\n'
    '\n'
    'def init_colors():\n'
    '    curses.start_color()\n'
    '    curses.use_default_colors()\n'
    '    curses.init_pair(1, curses.COLOR_CYAN, -1)\n'
    '    curses.init_pair(2, curses.COLOR_GREEN, -1)\n'
    '    curses.init_pair(3, curses.COLOR_YELLOW, -1)\n'
    '    curses.init_pair(4, curses.COLOR_RED, -1)\n'
    '\n'
    '\n'
    'def draw(stdscr, files, idx):\n'
    '    stdscr.clear()\n'
    '    h, w = stdscr.getmaxyx()\n'
    '    header = f"File {idx + 1}/{len(files)}: {files[idx].name}"\n'
    '    stdscr.attron(curses.color_pair(1) | curses.A_BOLD)\n'
    '    stdscr.addnstr(0, 0, header, w - 1)\n'
    '    stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)\n'
    '    lines = head_lines(files[idx], LINES_PER_FILE)\n'
    '    for i, line in enumerate(lines, start=2):\n'
    '        if i >= h - 1:\n'
    '            break\n'
    '        if line.startswith("[Error"):\n'
    '            stdscr.attron(curses.color_pair(4))\n'
    '            stdscr.addnstr(i, 0, line, w - 1)\n'
    '            stdscr.attroff(curses.color_pair(4))\n'
    '        else:\n'
    '            stdscr.attron(curses.color_pair(2))\n'
    '            stdscr.addnstr(i, 0, line, w - 1)\n'
    '            stdscr.attroff(curses.color_pair(2))\n'
    '    footer = "PgDown: next | PgUp: prev | q: quit"\n'
    '    stdscr.attron(curses.color_pair(3))\n'
    '    stdscr.addnstr(h - 1, 0, footer, w - 1)\n'
    '    stdscr.attroff(curses.color_pair(3))\n'
    '    stdscr.refresh()\n'
    '\n'
    '\n'
    'def main(stdscr):\n'
    '    curses.curs_set(0)\n'
    '    stdscr.keypad(True)\n'
    '    init_colors()\n'
    '    files = list_files()\n'
    '    if not files:\n'
    '        stdscr.addstr(0, 0, "No files in directory.")\n'
    '        stdscr.getch()\n'
    '        return\n'
    '    idx = 0\n'
    '    draw(stdscr, files, idx)\n'
    '    while True:\n'
    '        key = stdscr.getch()\n'
    '        if key in {ord("q"), ord("Q")}:\n'
    '            break\n'
    '        if key == curses.KEY_NPAGE:\n'
    '            if idx < len(files) - 1:\n'
    '                idx += 1\n'
    '                draw(stdscr, files, idx)\n'
    '        elif key == curses.KEY_PPAGE and idx > 0:\n'
    '            idx -= 1\n'
    '            draw(stdscr, files, idx)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    curses.wrapper(main)\n'
)

_QV_SOURCE: str = (
    'import argparse\n'
    'import pydoc\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def collect_files(root, recursive):\n'
    '    paths = root.rglob("*") if recursive else root.iterdir()\n'
    '    return sorted(\n'
    '        (path for path in paths if path.is_file()),\n'
    '        key=lambda path: str(path).lower(),\n'
    '    )\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(description="View files in the current directory with paging.")\n'
    '    parser.add_argument(\n'
    '        "-r",\n'
    '        "--recursive",\n'
    '        action="store_true",\n'
    '        help="include files in subdirectories",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    root = Path.cwd()\n'
    '    files = collect_files(root, args.recursive)\n'
    '    if not files:\n'
    '        print("No files found.")\n'
    '        return\n'
    '    output = []\n'
    '    for path in files:\n'
    '        try:\n'
    '            content = path.read_text(encoding="utf-8", errors="replace")\n'
    '        except OSError as exc:\n'
    '            content = f"[Could not read file: {exc}]"\n'
    '        output.append(f"\\n{\'=\' * 40}")\n'
    '        output.append(f"FILE: {path.relative_to(root)}")\n'
    '        output.append("=" * 40)\n'
    '        output.append(content)\n'
    '    pydoc.pager("\\n".join(output))\n'
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


class FaprinterTool(BaseTool):
    """Wrapper for original faprinter.py: ylines() + 0 more."""
    name: str = 'faprinter'
    source_file: str = 'faprinter.py'
    description: str = 'ylines() + 0 more'
    functions: list[str] = ['ylines']
    notes: str = ''
    source: str = _FAPRINTER_SOURCE

class FvTool(BaseTool):
    """Wrapper for original fv.py: main() + 0 more."""
    name: str = 'fv'
    source_file: str = 'fv.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _FV_SOURCE

class PbatTool(BaseTool):
    """Wrapper for original pbat.py: parse_line_range() + 8 more."""
    name: str = 'pbat'
    source_file: str = 'pbat.py'
    description: str = 'parse_line_range() + 8 more'
    functions: list[str] = ['parse_line_range', 'read_input', 'list_languages', 'list_themes', 'build_arg_parser', 'config_from_args', 'should_page', 'page_output', 'main']
    notes: str = ''
    source: str = _PBAT_SOURCE

class PyheadTool(BaseTool):
    """Wrapper for original pyhead.py: top-level script."""
    name: str = 'pyhead'
    source_file: str = 'pyhead.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _PYHEAD_SOURCE

class QuickviewTool(BaseTool):
    """Wrapper for original quickview.py: list_files() + 4 more."""
    name: str = 'quickview'
    source_file: str = 'quickview.py'
    description: str = 'list_files() + 4 more'
    functions: list[str] = ['list_files', 'head_lines', 'init_colors', 'draw', 'main']
    notes: str = ''
    source: str = _QUICKVIEW_SOURCE

class QvTool(BaseTool):
    """Wrapper for original qv.py: collect_files() + 1 more."""
    name: str = 'qv'
    source_file: str = 'qv.py'
    description: str = 'collect_files() + 1 more'
    functions: list[str] = ['collect_files', 'main']
    notes: str = ''
    source: str = _QV_SOURCE

class FileViewerPagerUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'faprinter': FaprinterTool,
        'fv': FvTool,
        'pbat': PbatTool,
        'pyhead': PyheadTool,
        'quickview': QuickviewTool,
        'qv': QvTool,
    }

    @classmethod
    def list_tools(cls: type[FileViewerPagerUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[FileViewerPagerUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[FileViewerPagerUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for file_viewer_pager (6 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[FileViewerPagerUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[FileViewerPagerUnified], argv: Sequence[str] | None = None) -> int:
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
    return FileViewerPagerUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

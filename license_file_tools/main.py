#!/usr/bin/env python3
"""LicenseFileToolsUnified for license_file_tools.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (3):
  collectlic <- collectlic.py (49L): read_file() + 2 more
  licr <- licr.py (25L): find_license_files() + 0 more [requires missing module 'dh' (ImportError at runtime)]
  rmlic <- rmlic.py (70L): load_patterns() + 4 more [requires missing module 'dh' (ImportError at runtime)]

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

_COLLECTLIC_SOURCE: str = (
    'from pathlib import Path\n'
    '\n'
    'EXCLUDE_DIRS = {".git"}\n'
    'OUTPUT_FILE = Path("/sdcard/all2.txt")\n'
    '\n'
    '\n'
    'def read_file(path):\n'
    '    try:\n'
    '        with path.open(encoding="utf-8", errors="ignore") as f:\n'
    '            return f.read()\n'
    '    except Exception:\n'
    '        return None\n'
    '\n'
    '\n'
    'def collect_files(root):\n'
    '    try:\n'
    '        for item in root.iterdir():\n'
    '            if item.is_dir():\n'
    '                if item.name not in EXCLUDE_DIRS:\n'
    '                    yield from collect_files(item)\n'
    '            elif item.is_file():\n'
    '                if item.resolve() == OUTPUT_FILE.resolve():\n'
    '                    continue\n'
    '                if "license" in item.name.lower():\n'
    '                    yield item\n'
    '    except PermissionError:\n'
    '        pass\n'
    '\n'
    '\n'
    'def build_all_txt(root_path):\n'
    '    root = Path(root_path)\n'
    '    files = list(collect_files(root))\n'
    '    print(f"Found {len(files)} files")\n'
    '    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)\n'
    '    with OUTPUT_FILE.open("w", encoding="utf-8") as out:\n'
    '        for i, path in enumerate(files, 1):\n'
    '            content = read_file(path)\n'
    '            if content is None:\n'
    '                print(f"Skipping unreadable file: {path}")\n'
    '                continue\n'
    '            out.write(content)\n'
    '            if i != len(files):\n'
    '                out.write("\\n\\n\\n")\n'
    '            print(f"Added: {path}")\n'
    '    print(f"\\nFinished: {OUTPUT_FILE} created.")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    build_all_txt(".")\n'
)

_LICR_SOURCE: str = (
    'from pathlib import Path\n'
    'import dh\n'
    '\n'
    'EXT = [".md", ".txt", ".rst"]\n'
    '\n'
    '\n'
    'def find_license_files():\n'
    '    lf = []\n'
    '    allfiles = dh.get_files(".")\n'
    '    for file in allfiles:\n'
    '        if Path(file).is_symlink():\n'
    '            continue\n'
    '        if Path(file).is_file():\n'
    '            fn = str(dh.get_fname(file))\n'
    '            ext = str(dh.get_ext(file))\n'
    '            if fn.lower().startswith("license") and (ext.lower() in EXT or not ext):\n'
    '                print(fn, ext)\n'
    '                lf.append(file)\n'
    '    print(f"Found {len(lf)} license files")\n'
    '    for path in lf:\n'
    '        Path(path).write_text("", encoding="utf-8")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    find_license_files()\n'
)

_RMLIC_SOURCE: str = (
    'import re\n'
    'from pathlib import Path\n'
    'from dh import cprint, fsz, get_nobinary, gsz\n'
    '\n'
    'LIC_FILE = Path("/sdcard/lic")\n'
    'MIN_BLANK_LINES = 3\n'
    'NUM_WORKERS = 8\n'
    '\n'
    '\n'
    'def load_patterns(lic_path):\n'
    '    try:\n'
    '        content = Path(lic_path).read_text(encoding="utf-8", errors="ignore")\n'
    '        pattern_separator = "\\\\n(?:\\\\s*\\\\n){" + str(MIN_BLANK_LINES) + ",}"\n'
    '        patterns = re.split(pattern_separator, content)\n'
    '        patterns = [p.strip() for p in patterns if p.strip()]\n'
    '        for pattern in patterns:\n'
    '            pattern[:50].replace("\\n", "\\\\n")\n'
    '        return patterns\n'
    '    except Exception as e:\n'
    '        print(f"Error loading patterns from {lic_path}: {e}")\n'
    '        return []\n'
    '\n'
    '\n'
    'def escape_for_regex(text):\n'
    '    escaped = re.escape(text)\n'
    '    return escaped.replace("\\\\n", "\\\\s*\\\\n\\\\s*")\n'
    '\n'
    '\n'
    'def remove_patterns_from_content(content, patterns):\n'
    '    cleaned = content\n'
    '    for pattern in patterns:\n'
    '        regex_pattern = escape_for_regex(pattern)\n'
    '        cleaned = re.sub(regex_pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)\n'
    '    return cleaned\n'
    '\n'
    '\n'
    'def process_file(path, patterns):\n'
    '    path = Path(path)\n'
    '    path = Path(path)\n'
    '    before = gsz(path)\n'
    '    original_content = path.read_text(encoding="utf-8")\n'
    '    cleaned_content = remove_patterns_from_content(original_content, patterns)\n'
    '    if len(cleaned_content) != len(original_content):\n'
    '        path.write_text(cleaned_content, encoding="utf-8")\n'
    '        cprint(f"{path.name} updated", "green", end=" | ")\n'
    '        ds = before - gsz(path)\n'
    '        cprint(f"{fsz(ds)}")\n'
    '        del before, ds, cleaned_content, original_content, path\n'
    '\n'
    '\n'
    'def main():\n'
    '    if not LIC_FILE.exists():\n'
    '        print(f"Error: License file not found: {LIC_FILE}")\n'
    '        return\n'
    '    patterns = load_patterns(LIC_FILE)\n'
    '    if not patterns:\n'
    '        print("No patterns found. Exiting.")\n'
    '        return\n'
    '    print()\n'
    '    cwd = Path.cwd()\n'
    '    all_files = get_nobinary(cwd)\n'
    '    if not all_files:\n'
    '        print("No files to process.")\n'
    '        return\n'
    '    for f in all_files:\n'
    '        process_file(f, patterns)\n'
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


class CollectlicTool(BaseTool):
    """Wrapper for original collectlic.py: read_file() + 2 more."""
    name: str = 'collectlic'
    source_file: str = 'collectlic.py'
    description: str = 'read_file() + 2 more'
    functions: list[str] = ['read_file', 'collect_files', 'build_all_txt']
    notes: str = ''
    source: str = _COLLECTLIC_SOURCE

class LicrTool(BaseTool):
    """Wrapper for original licr.py: find_license_files() + 0 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'licr'
    source_file: str = 'licr.py'
    description: str = 'find_license_files() + 0 more'
    functions: list[str] = ['find_license_files']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _LICR_SOURCE

class RmlicTool(BaseTool):
    """Wrapper for original rmlic.py: load_patterns() + 4 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'rmlic'
    source_file: str = 'rmlic.py'
    description: str = 'load_patterns() + 4 more'
    functions: list[str] = ['load_patterns', 'escape_for_regex', 'remove_patterns_from_content', 'process_file', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _RMLIC_SOURCE

class LicenseFileToolsUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'collectlic': CollectlicTool,
        'licr': LicrTool,
        'rmlic': RmlicTool,
    }

    @classmethod
    def list_tools(cls: type[LicenseFileToolsUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[LicenseFileToolsUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[LicenseFileToolsUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for license_file_tools (3 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[LicenseFileToolsUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[LicenseFileToolsUnified], argv: Sequence[str] | None = None) -> int:
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
    return LicenseFileToolsUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

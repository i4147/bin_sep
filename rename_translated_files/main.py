#!/usr/bin/env python3
"""RenameTranslatedFilesUnified for rename_translated_files.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (4):
  finglish <- finglish.py (83L): custom_persian_to_finglish() + 1 more
  renm <- renm.py (64L): is_english() + 2 more [requires missing module 'dh' (ImportError at runtime)]
  renneng <- renneng.py (59L): translate_if_needed() + 2 more
  translate_noneng_filenames <- translate_noneng_filenames.py (51L): is_english() + 2 more

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

_FINGLISH_SOURCE: str = (
    'import unicodedata\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def custom_persian_to_finglish(text):\n'
    '    persian_map = {\n'
    '        "ا": "a",\n'
    '        "آ": "a",\n'
    '        "ب": "b",\n'
    '        "پ": "p",\n'
    '        "ت": "t",\n'
    '        "ث": "s",\n'
    '        "ج": "j",\n'
    '        "چ": "ch",\n'
    '        "ح": "h",\n'
    '        "خ": "kh",\n'
    '        "د": "d",\n'
    '        "ذ": "z",\n'
    '        "ر": "r",\n'
    '        "ز": "z",\n'
    '        "ژ": "zh",\n'
    '        "س": "s",\n'
    '        "ش": "sh",\n'
    '        "ص": "s",\n'
    '        "ض": "z",\n'
    '        "ط": "t",\n'
    '        "ظ": "z",\n'
    '        "ع": "a",\n'
    '        "غ": "gh",\n'
    '        "ف": "f",\n'
    '        "ق": "gh",\n'
    '        "ک": "k",\n'
    '        "گ": "g",\n'
    '        "ل": "l",\n'
    '        "م": "m",\n'
    '        "ن": "n",\n'
    '        "ه": "h",\n'
    '    }\n'
    '    words = text.split(" ")\n'
    '    processed_words = []\n'
    '    for word in words:\n'
    '        if not word:\n'
    '            processed_words.append("")\n'
    '            continue\n'
    '        processed_word = ""\n'
    '        chars = list(word)\n'
    '        for i, char in enumerate(chars):\n'
    '            if char == "و":\n'
    '                if i == 0:\n'
    '                    processed_word += "v"\n'
    '                else:\n'
    '                    processed_word += "o"\n'
    '            elif char == "ی":\n'
    '                if i == 0 or i == len(chars) - 1:\n'
    '                    processed_word += "y"\n'
    '                else:\n'
    '                    processed_word += "i"\n'
    '            else:\n'
    '                processed_word += persian_map.get(char, char)\n'
    '        processed_words.append(processed_word)\n'
    '    return "_".join(processed_words)\n'
    '\n'
    '\n'
    'def convert_filenames_with_pathlib(directory="."):\n'
    '    start_path = Path(directory)\n'
    '    for path in start_path.rglob("*"):\n'
    '        original_filename_stem = path.stem\n'
    '        original_extension = path.suffix\n'
    '        normalized_stem = unicodedata.normalize("NFKD", original_filename_stem)\n'
    '        finglish_stem = custom_persian_to_finglish(normalized_stem)\n'
    '        finglish_stem_cleaned = "_".join(filter(None, finglish_stem.split("_")))\n'
    '        new_filename = finglish_stem_cleaned + original_extension\n'
    '        if new_filename != path.name:\n'
    '            new_path = path.with_name(new_filename)\n'
    '            try:\n'
    '                path.rename(new_path)\n'
    '                print(f"Renamed: {path} -> {new_path}")\n'
    '            except OSError as e:\n'
    '                print(f"Error renaming {path}: {e}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    convert_filenames_with_pathlib()\n'
)

_RENM_SOURCE: str = (
    'import os\n'
    'import re\n'
    'from concurrent.futures import ThreadPoolExecutor, as_completed\n'
    'from pathlib import Path\n'
    'from deep_translator import GoogleTranslator\n'
    'from dh import unique_path\n'
    'from fastwalk import walk_files\n'
    'from tqdm import tqdm\n'
    '\n'
    'DIRECTORY = "."\n'
    'non_english_pattern = re.compile(r"[^\\x00-\\x7F]")\n'
    '\n'
    '\n'
    'def is_english(text):\n'
    '    return not non_english_pattern.search(text)\n'
    '\n'
    '\n'
    'translation_cache = {}\n'
    '\n'
    '\n'
    'def translate_name(name):\n'
    '    base, ext = os.path.splitext(name)\n'
    '    if is_english(base):\n'
    '        return (name, name)\n'
    '    if base in translation_cache:\n'
    '        return (name, translation_cache[base] + ext)\n'
    '    try:\n'
    '        translated = GoogleTranslator(source="auto", target="en").translate(base)\n'
    '        translation_cache[base] = translated\n'
    '        return (name, translated + ext)\n'
    '    except Exception:\n'
    '        return (name, name)\n'
    '\n'
    '\n'
    'def rename_files(directory):\n'
    '    paths = [Path(p) for p in walk_files(directory)]\n'
    '    unique_names_to_translate = list({p.name for p in paths if not is_english(p.name)})\n'
    '    translation_map = {}\n'
    '    with ThreadPoolExecutor(8) as executor:\n'
    '        futures = [executor.submit(translate_name, name) for name in unique_names_to_translate]\n'
    '        for future in tqdm(\n'
    '            as_completed(futures),\n'
    '            total=len(unique_names_to_translate),\n'
    '            desc="Translating filenames",\n'
    '        ):\n'
    '            original, translated = future.result()\n'
    '            translation_map[original] = translated\n'
    '    for path in sorted(paths, key=lambda x: len(x.parts), reverse=True):\n'
    '        if path.name not in translation_map:\n'
    '            continue\n'
    '        new_name = translation_map[path.name]\n'
    '        if new_name == path.name:\n'
    '            continue\n'
    '        new_path = path.with_name(new_name)\n'
    '        new_path = unique_path(new_path)\n'
    '        try:\n'
    '            Path(path).rename(new_path)\n'
    '            print(f"Renamed: {path.name} -> {new_path.name}")\n'
    '        except OSError as e:\n'
    '            print(f"Error renaming {path.name}: {e}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    rename_files(DIRECTORY)\n'
)

_RENNENG_SOURCE: str = (
    'import os\n'
    'import re\n'
    'from pathlib import Path\n'
    'from deep_translator import GoogleTranslator\n'
    'from fastwalk import walk_files\n'
    '\n'
    'DIRECTORY = "."\n'
    'non_english_pattern = re.compile(r"[^\\x00-\\x7F]")\n'
    '\n'
    '\n'
    'def translate_if_needed(name):\n'
    '    base, ext = os.path.splitext(name)\n'
    '    if not non_english_pattern.search(base):\n'
    '        return name\n'
    '    try:\n'
    '        translated = GoogleTranslator(source="auto", target="en").translate(base)\n'
    '        return translated + ext\n'
    '    except Exception as e:\n'
    '        print(f"Translation error for \'{name}\': {e}")\n'
    '        return name\n'
    '\n'
    '\n'
    'def get_unique_path(path):\n'
    '    if not path.exists():\n'
    '        return path\n'
    '    base = path.stem\n'
    '    ext = path.suffix\n'
    '    parent = path.parent\n'
    '    counter = 1\n'
    '    while True:\n'
    '        new_path = parent / f"{base}_{counter}{ext}"\n'
    '        if not new_path.exists():\n'
    '            return new_path\n'
    '        counter += 1\n'
    '\n'
    '\n'
    'def rename_files(directory):\n'
    '    for pth in walk_files(directory):\n'
    '        path = Path(pth)\n'
    '        if path.is_file():\n'
    '            new_name = translate_if_needed(path.name)\n'
    '            if new_name == path.name:\n'
    '                continue\n'
    '            new_path = path.parent / new_name\n'
    '            new_path = get_unique_path(new_path)\n'
    '            Path(path).rename(new_path)\n'
    '            print(f"File renamed: {path.name} -> {new_path.name}")\n'
    '        elif path.is_dir():\n'
    '            new_name = translate_if_needed(path.name)\n'
    '            if new_name == path.name:\n'
    '                continue\n'
    '            new_path = path.parent / new_name\n'
    '            new_path = get_unique_path(new_path)\n'
    '            Path(path).rename(new_path)\n'
    '            print(f"Directory renamed: {path.name} -> {new_path.name}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    rename_files(DIRECTORY)\n'
)

_TRANSLATE_NONENG_FILENAMES_SOURCE: str = (
    'import os\n'
    'import re\n'
    'from pathlib import Path\n'
    'from deep_translator import GoogleTranslator\n'
    'from fastwalk import walk_files\n'
    '\n'
    'DIRECTORY = Path.cwd()\n'
    'non_english_pattern = re.compile(r"[^\\x00-\\x7F]")\n'
    '\n'
    '\n'
    'def is_english(text):\n'
    '    return not non_english_pattern.search(text)\n'
    '\n'
    '\n'
    'def translate_filename(filename):\n'
    '    try:\n'
    '        return GoogleTranslator(source="auto", target="en").translate(filename)\n'
    '    except Exception as e:\n'
    '        print(f"Translation error for {filename}: {e}")\n'
    '        return filename\n'
    '\n'
    '\n'
    'def rename_files(directory):\n'
    '    for path in walk_files(directory):\n'
    '        if is_english(path.stem):\n'
    '            continue\n'
    '        if path.is_file():\n'
    '            original_path = path\n'
    '            new_name = translate_filename(path.stem)\n'
    '            new_path = path.with_stem(new_name)\n'
    '            counter = 1\n'
    '            while new_path.exists():\n'
    '                name, ext = os.path.splitext(new_name)\n'
    '                new_path = path.with_name(f"{name}_{counter}{ext}")\n'
    '                counter += 1\n'
    '            Path(original_path).rename(new_path)\n'
    '            print(f"Renamed file: {original_path.name} -> {new_path.name}")\n'
    '        elif path.is_dir():\n'
    '            original_path = path\n'
    '            new_name = translate_filename(path.name)\n'
    '            new_path = path.with_name(new_name)\n'
    '            counter = 1\n'
    '            while new_path.exists():\n'
    '                new_path = Path(f"{original_path}_{counter}")\n'
    '                counter += 1\n'
    '            Path(original_path).rename(new_path)\n'
    '            print(f"Renamed directory: {original_path.name} -> {new_path.name}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    rename_files(DIRECTORY)\n'
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


class FinglishTool(BaseTool):
    """Wrapper for original finglish.py: custom_persian_to_finglish() + 1 more."""
    name: str = 'finglish'
    source_file: str = 'finglish.py'
    description: str = 'custom_persian_to_finglish() + 1 more'
    functions: list[str] = ['custom_persian_to_finglish', 'convert_filenames_with_pathlib']
    notes: str = ''
    source: str = _FINGLISH_SOURCE

class RenmTool(BaseTool):
    """Wrapper for original renm.py: is_english() + 2 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'renm'
    source_file: str = 'renm.py'
    description: str = 'is_english() + 2 more'
    functions: list[str] = ['is_english', 'translate_name', 'rename_files']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _RENM_SOURCE

class RennengTool(BaseTool):
    """Wrapper for original renneng.py: translate_if_needed() + 2 more."""
    name: str = 'renneng'
    source_file: str = 'renneng.py'
    description: str = 'translate_if_needed() + 2 more'
    functions: list[str] = ['translate_if_needed', 'get_unique_path', 'rename_files']
    notes: str = ''
    source: str = _RENNENG_SOURCE

class TranslateNonengFilenamesTool(BaseTool):
    """Wrapper for original translate_noneng_filenames.py: is_english() + 2 more."""
    name: str = 'translate_noneng_filenames'
    source_file: str = 'translate_noneng_filenames.py'
    description: str = 'is_english() + 2 more'
    functions: list[str] = ['is_english', 'translate_filename', 'rename_files']
    notes: str = ''
    source: str = _TRANSLATE_NONENG_FILENAMES_SOURCE

class RenameTranslatedFilesUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'finglish': FinglishTool,
        'renm': RenmTool,
        'renneng': RennengTool,
        'translate_noneng_filenames': TranslateNonengFilenamesTool,
    }

    @classmethod
    def list_tools(cls: type[RenameTranslatedFilesUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[RenameTranslatedFilesUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[RenameTranslatedFilesUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for rename_translated_files (4 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[RenameTranslatedFilesUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[RenameTranslatedFilesUnified], argv: Sequence[str] | None = None) -> int:
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
    return RenameTranslatedFilesUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

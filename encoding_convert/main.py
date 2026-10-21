#!/usr/bin/env python3
"""EncodingConvertUnified for encoding_convert.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (7):
  decode_phonetic <- decode_phonetic.py (13L): main() + 0 more
  decode_unicode <- decode_unicode.py (9L): top-level script
  iso8859toutf8 <- iso8859toutf8.py (16L): convert_in_place() + 0 more
  to_unicode <- to_unicode.py (34L): convert_to_readable() + 0 more
  toutf8 <- toutf8.py (122L): detect_encoding() + 3 more [requires missing module 'dh' (ImportError at runtime)]
  try_decode <- try_decode.py (166L): try_decode() + 3 more
  ufa <- ufa.py (38L): unicode_unescape() + 2 more [requires missing module 'dh' (ImportError at runtime)]

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

_DECODE_PHONETIC_SOURCE: str = (
    'import sys\n'
    'from html import unescape\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def main():\n'
    '    fn = Path(sys.argv[1])\n'
    '    content = fn.read_text(encoding="utf-8", errors="replace")\n'
    '    fn.write_text(unescape(content), encoding="utf-8")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_DECODE_UNICODE_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    path = Path(sys.argv[1].strip())\n'
    '    text = path.read_bytes()\n'
    '    decoded = text.encode("utf-8").decode("unicode_escape")\n'
    '    path.write_text(decoded, encoding="utf-8")\n'
    '    print(f"{path} updated")\n'
)

_ISO8859TOUTF8_SOURCE: str = (
    'import codecs\n'
    'import shutil\n'
    '\n'
    '\n'
    'def convert_in_place(filename):\n'
    '    backup = f"{filename}.bak"\n'
    '    shutil.copy2(filename, backup)\n'
    '    with codecs.open(backup, "r", encoding="iso-8859-1") as f:\n'
    '        content = f.read()\n'
    '    with codecs.open(filename, "w", encoding="utf-8") as f:\n'
    '        f.write(content)\n'
    '    print(f"Converted {filename} (backup saved as {backup})")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    convert_in_place("script.sh")\n'
)

_TO_UNICODE_SOURCE: str = (
    'import re\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def convert_to_readable(filename):\n'
    '    outfile = Path(filename)\n'
    '    try:\n'
    '        content = Path(filename).read_bytes()\n'
    '        try:\n'
    '            decoded_content = content.decode("utf-8", errors="ignore")\n'
    '        except:\n'
    '            decoded_content = content.decode("latin-1", errors="ignore")\n'
    '\n'
    '        def replace_hex(m):\n'
    '            try:\n'
    '                return chr(int(m.group(1), 16))\n'
    '            except ValueError:\n'
    '                return m.group(0)\n'
    '\n'
    '        readable_content = re.sub(r"\\x([0-9a-fA-F]{2})", replace_hex, decoded_content)\n'
    '        outfile.write_text(readable_content, encoding="utf-8")\n'
    '    except FileNotFoundError:\n'
    '        print(f"Error: File \'{filename}\' not found.")\n'
    '    except Exception as e:\n'
    '        print(f"An error occurred: {e}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) != 2:\n'
    '        print("Usage: python convert_script.py <filename>")\n'
    '    else:\n'
    '        fname = sys.argv[1]\n'
    '        convert_to_readable(fname)\n'
)

_TOUTF8_SOURCE: str = (
    'import argparse\n'
    'from collections.abc import Generator\n'
    'from multiprocessing import Pool\n'
    'from multiprocessing.pool import AsyncResult\n'
    'from pathlib import Path\n'
    'from typing import Final\n'
    'import chardet\n'
    'from dh import get_nobinary, is_binary\n'
    'from loguru import logger\n'
    '\n'
    'MAX_WORKERS = 8\n'
    'SAMPLE_SIZE = 100_000\n'
    'ConvertResult = tuple[Path, bool, str]\n'
    '\n'
    '\n'
    'def detect_encoding(file_path):\n'
    '    try:\n'
    '        with file_path.open("rb") as f:\n'
    '            raw_data = f.read(SAMPLE_SIZE)\n'
    '        result = chardet.detect(raw_data)\n'
    '        encoding = result.get("encoding")\n'
    '        if isinstance(encoding, str) and encoding:\n'
    '            return encoding\n'
    '        return "utf-8"\n'
    '    except Exception:\n'
    '        return "utf-8"\n'
    '\n'
    '\n'
    'def convert_file(file_path):\n'
    '    try:\n'
    '        if is_binary(file_path):\n'
    '            return file_path, False, "Skipped (binary/unsupported)"\n'
    '        encoding = detect_encoding(file_path)\n'
    '        if encoding.lower() == "utf-8":\n'
    '            return file_path, True, "Already UTF8"\n'
    '        with file_path.open("r", encoding=encoding, errors="replace") as f:\n'
    '            content = f.read()\n'
    '        with file_path.open("w", encoding="utf-8") as f:\n'
    '            f.write(content)\n'
    '        return file_path, True, f"Converted from {encoding}"\n'
    '    except Exception as exc:\n'
    '        return file_path, False, f"Error: {exc!s}"\n'
    '\n'
    '\n'
    'def collect_files(paths):\n'
    '    for path_str in paths:\n'
    '        path = Path(path_str).resolve()\n'
    '        if path.is_file():\n'
    '            yield path\n'
    '        elif path.is_dir():\n'
    '            for child in path.rglob("*"):\n'
    '                if child.is_file():\n'
    '                    yield child\n'
    '        else:\n'
    '            logger.warning(f"⚠ {path} not found")\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Convert non-UTF8 files to UTF8 encoding (in-place)",\n'
    '        formatter_class=argparse.RawDescriptionHelpFormatter,\n'
    '        epilog=(\n'
    '            "Examples:\\n"\n'
    '            "  python script.py                    # Process current directory\\n"\n'
    '            "  python script.py ./src ./docs       # Process specific directories\\n"\n'
    '            "  python script.py file.txt dir/      # Process file and directory"\n'
    '        ),\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "paths",\n'
    '        nargs="*",\n'
    '        help="Files or directories to process (default: current directory)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-v",\n'
    '        "--verbose",\n'
    '        action="store_true",\n'
    '        help="Show detailed output for each file",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    input_paths = list(args.paths) if args.paths else ["."]\n'
    '    cwd = Path.cwd()\n'
    '    if args.paths:\n'
    '        files = list(collect_files(input_paths))\n'
    '    else:\n'
    '        files = list(get_nobinary(cwd))\n'
    '    if not files:\n'
    '        print("No files to process.")\n'
    '        return 0\n'
    '    print(f"Processing {len(files)} file(s) with {MAX_WORKERS} worker(s)...\\n")\n'
    '    converted = 0\n'
    '    skipped = 0\n'
    '    errors = 0\n'
    '    with Pool(processes=MAX_WORKERS) as pool:\n'
    '        async_results = [pool.apply_async(convert_file, (f,)) for f in files]\n'
    '        for async_res in async_results:\n'
    '            file_path, success, message = async_res.get()\n'
    '            if args.verbose:\n'
    '                status = "✓" if success else "✗"\n'
    '                try:\n'
    '                    rel = file_path.relative_to(cwd)\n'
    '                except ValueError:\n'
    '                    rel = file_path\n'
    '                print(f"{status} {rel} - {message}")\n'
    '            if success:\n'
    '                if "Already UTF8" in message or "Skipped" in message:\n'
    '                    skipped += 1\n'
    '                else:\n'
    '                    converted += 1\n'
    '            else:\n'
    '                errors += 1\n'
    '    print("=" * 40)\n'
    '    print("Summary:")\n'
    '    print(f"  Converted: {converted}")\n'
    '    print(f"  Skipped:   {skipped}")\n'
    '    print(f"  Errors:    {errors}")\n'
    '    print("=" * 40)\n'
    '    return 0 if errors == 0 else 1\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_TRY_DECODE_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    'COMMON_ENCODINGS = [\n'
    '    "utf-8",\n'
    '    "utf-8-sig",\n'
    '    "latin-1",\n'
    '    "cp1252",\n'
    '    "cp1251",\n'
    '    "cp1256",\n'
    '    "iso-8859-1",\n'
    '    "iso-8859-2",\n'
    '    "iso-8859-5",\n'
    '    "iso-8859-6",\n'
    '    "iso-8859-7",\n'
    '    "iso-8859-8",\n'
    '    "iso-8859-9",\n'
    '    "cp437",\n'
    '    "cp850",\n'
    '    "cp866",\n'
    '    "mac_roman",\n'
    '    "utf-16",\n'
    '    "utf-16-le",\n'
    '    "utf-16-be",\n'
    '    "utf-32",\n'
    '    "utf-32-le",\n'
    '    "utf-32-be",\n'
    '    "gbk",\n'
    '    "gb2312",\n'
    '    "big5",\n'
    '    "shift_jis",\n'
    '    "euc_jp",\n'
    '    "euc_kr",\n'
    ']\n'
    'EXTRA_ENCODINGS = [\n'
    '    "ascii",\n'
    '    "cp775",\n'
    '    "cp852",\n'
    '    "cp855",\n'
    '    "cp857",\n'
    '    "cp860",\n'
    '    "cp861",\n'
    '    "cp862",\n'
    '    "cp863",\n'
    '    "cp865",\n'
    '    "cp869",\n'
    '    "cp874",\n'
    '    "cp949",\n'
    '    "cp950",\n'
    '    "koi8_r",\n'
    '    "koi8_u",\n'
    '    "mac_cyrillic",\n'
    '    "mac_greek",\n'
    '    "mac_iceland",\n'
    '    "mac_latin2",\n'
    ']\n'
    '\n'
    '\n'
    'def try_decode(file_content, encoding):\n'
    '    try:\n'
    '        decoded = file_content.decode(encoding)\n'
    '        return (True, decoded)\n'
    '    except (UnicodeDecodeError, LookupError):\n'
    '        return (False, None)\n'
    '\n'
    '\n'
    'def get_first_chunk(text, chunk_size=500):\n'
    '    if len(text) <= chunk_size:\n'
    '        return text\n'
    '    return text[:chunk_size] + "...\\n[truncated...]"\n'
    '\n'
    '\n'
    'def decode_file(path, output_path=None, show_chunk=500):\n'
    '    path = Path(path)\n'
    '    if not path.exists():\n'
    '        print(f"Error: File \'{path}\' not found.")\n'
    '        return False\n'
    '    try:\n'
    '        with open(path, "rb") as f:\n'
    '            file_content = f.read()\n'
    '    except Exception as e:\n'
    '        print(f"Error reading file: {e}")\n'
    '        return False\n'
    '    print(f"Processing: {path.name}")\n'
    '    print(f"File size: {len(file_content)} bytes")\n'
    '    print("-" * 40)\n'
    '    encodings_to_try = COMMON_ENCODINGS + EXTRA_ENCODINGS\n'
    '    successful_encodings = []\n'
    '    successful_text = None\n'
    '    best_encoding = None\n'
    '    for encoding in encodings_to_try:\n'
    '        success, decoded_text = try_decode(file_content, encoding)\n'
    '        if success:\n'
    '            successful_encodings.append(encoding)\n'
    '            if successful_text is None:\n'
    '                successful_text = decoded_text\n'
    '                best_encoding = encoding\n'
    '            print(f"✓ {encoding:15} - Successfully decoded!")\n'
    '            if show_chunk > 0:\n'
    '                chunk = get_first_chunk(decoded_text, show_chunk)\n'
    '                preview = chunk.replace("\\n", "\\n  ").replace("\\r", r"\\r")\n'
    '                print(f"  Preview:\\n  {preview}\\n")\n'
    '    print("-" * 40)\n'
    '    if not successful_encodings:\n'
    '        print("❌ No encoding could decode this file.")\n'
    '        return False\n'
    '    print(f"\\n✅ Found {len(successful_encodings)} successful encoding(s):")\n'
    '    for enc in successful_encodings:\n'
    '        print(f"  - {enc}")\n'
    '    print(f"\\n📌 Best match: {best_encoding}")\n'
    '    if len(successful_encodings) > 1:\n'
    '        print("\\nMultiple encodings found. Which one should be used for UTF-8 conversion?")\n'
    '        print("0: Cancel")\n'
    '        for i, enc in enumerate(successful_encodings, 1):\n'
    '            print(f"{i}: {enc}")\n'
    '        try:\n'
    '            choice = input(f"Enter choice (1-{len(successful_encodings)}): ").strip()\n'
    '            if not choice:\n'
    '                choice = "1"\n'
    '            choice_idx = int(choice) - 1\n'
    '            if 0 <= choice_idx < len(successful_encodings):\n'
    '                chosen_encoding = successful_encodings[choice_idx]\n'
    '            else:\n'
    '                print("Invalid choice. Using best match.")\n'
    '                chosen_encoding = best_encoding\n'
    '        except ValueError:\n'
    '            print("Invalid input. Using best match.")\n'
    '            chosen_encoding = best_encoding\n'
    '    else:\n'
    '        chosen_encoding = best_encoding\n'
    '    try:\n'
    '        decoded_text = file_content.decode(chosen_encoding)\n'
    '    except Exception as e:\n'
    '        print(f"Error decoding with {chosen_encoding}: {e}")\n'
    '        return False\n'
    '    if output_path is None:\n'
    '        output_path = path.stem + "_utf8" + path.suffix\n'
    '        if path.suffix.lower() == ".txt":\n'
    '            output_path = path.stem + "_utf8.txt"\n'
    '        else:\n'
    '            output_path = path.parent / f"{path.stem}_utf8{path.suffix}"\n'
    '    try:\n'
    '        with open(output_path, "w", encoding="utf-8") as f:\n'
    '            f.write(decoded_text)\n'
    '        print(f"\\n💾 Saved UTF-8 version to: {output_path}")\n'
    '        print(f"   Original encoding: {chosen_encoding}")\n'
    '        print(f"   Characters decoded: {len(decoded_text)}")\n'
    '        return True\n'
    '    except Exception as e:\n'
    '        print(f"Error saving file: {e}")\n'
    '        return False\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python decode_file.py <path> [output_path]")\n'
    '        print("Example: python decode_file.py mystery.txt")\n'
    '        print("Example: python decode_file.py mystery.txt decoded.txt")\n'
    '        sys.exit(1)\n'
    '    path = sys.argv[1]\n'
    '    output_path = sys.argv[2] if len(sys.argv) > 2 else None\n'
    '    decode_file(path, output_path)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_UFA_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from dh import get_nobinary, is_binary\n'
    '\n'
    '\n'
    'def unicode_unescape(text):\n'
    '    return bytes(text, "utf-8").decode("unicode_escape")\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    lines = path.read_text(encoding="utf-8").splitlines()\n'
    '    path = Path(path)\n'
    '    for line in lines:\n'
    '        nl = r"\\u" + str(line.strip())\n'
    '        decoded = unicode_unescape(nl)\n'
    '        print(nl)\n'
    '        print(decoded)\n'
    '\n'
    '\n'
    'def main():\n'
    '    args = sys.argv[1:]\n'
    '    cwd = Path.cwd()\n'
    '    files = []\n'
    '    if args:\n'
    '        for arg in args:\n'
    '            p = Path(arg)\n'
    '            if p.is_file() and (not is_binary(p)):\n'
    '                files.append(p)\n'
    '            if p.is_dir():\n'
    '                files.extend(get_nobinary(p))\n'
    '    else:\n'
    '        files = get_nobinary(cwd)\n'
    '    for f in files:\n'
    '        process_file(f)\n'
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


class DecodePhoneticTool(BaseTool):
    """Wrapper for original decode_phonetic.py: main() + 0 more."""
    name: str = 'decode_phonetic'
    source_file: str = 'decode_phonetic.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _DECODE_PHONETIC_SOURCE

class DecodeUnicodeTool(BaseTool):
    """Wrapper for original decode_unicode.py: top-level script."""
    name: str = 'decode_unicode'
    source_file: str = 'decode_unicode.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _DECODE_UNICODE_SOURCE

class Iso8859toutf8Tool(BaseTool):
    """Wrapper for original iso8859toutf8.py: convert_in_place() + 0 more."""
    name: str = 'iso8859toutf8'
    source_file: str = 'iso8859toutf8.py'
    description: str = 'convert_in_place() + 0 more'
    functions: list[str] = ['convert_in_place']
    notes: str = ''
    source: str = _ISO8859TOUTF8_SOURCE

class ToUnicodeTool(BaseTool):
    """Wrapper for original to_unicode.py: convert_to_readable() + 0 more."""
    name: str = 'to_unicode'
    source_file: str = 'to_unicode.py'
    description: str = 'convert_to_readable() + 0 more'
    functions: list[str] = ['convert_to_readable']
    notes: str = ''
    source: str = _TO_UNICODE_SOURCE

class Toutf8Tool(BaseTool):
    """Wrapper for original toutf8.py: detect_encoding() + 3 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'toutf8'
    source_file: str = 'toutf8.py'
    description: str = 'detect_encoding() + 3 more'
    functions: list[str] = ['detect_encoding', 'convert_file', 'collect_files', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _TOUTF8_SOURCE

class TryDecodeTool(BaseTool):
    """Wrapper for original try_decode.py: try_decode() + 3 more."""
    name: str = 'try_decode'
    source_file: str = 'try_decode.py'
    description: str = 'try_decode() + 3 more'
    functions: list[str] = ['try_decode', 'get_first_chunk', 'decode_file', 'main']
    notes: str = ''
    source: str = _TRY_DECODE_SOURCE

class UfaTool(BaseTool):
    """Wrapper for original ufa.py: unicode_unescape() + 2 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'ufa'
    source_file: str = 'ufa.py'
    description: str = 'unicode_unescape() + 2 more'
    functions: list[str] = ['unicode_unescape', 'process_file', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _UFA_SOURCE

class EncodingConvertUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'decode_phonetic': DecodePhoneticTool,
        'decode_unicode': DecodeUnicodeTool,
        'iso8859toutf8': Iso8859toutf8Tool,
        'to_unicode': ToUnicodeTool,
        'toutf8': Toutf8Tool,
        'try_decode': TryDecodeTool,
        'ufa': UfaTool,
    }

    @classmethod
    def list_tools(cls: type[EncodingConvertUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[EncodingConvertUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[EncodingConvertUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for encoding_convert (7 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[EncodingConvertUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[EncodingConvertUnified], argv: Sequence[str] | None = None) -> int:
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
    return EncodingConvertUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

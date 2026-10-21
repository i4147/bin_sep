#!/usr/bin/env python3
"""CsvConvertUnified for csv_convert.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (5):
  csv2json <- csv2json.py (40L): csv_to_json_map() + 1 more
  csv2json2 <- csv2json2.py (21L): main() + 0 more
  lcsv <- lcsv.py (70L): process_file() + 3 more
  ltxt <- ltxt.py (76L): process_file() + 3 more [requires missing module 'dh' (ImportError at runtime)]
  savepkgstocsv <- savepkgstocsv.py (79L): query_packages() + 3 more

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

_CSV2JSON_SOURCE: str = (
    'import csv\n'
    'import json\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def csv_to_json_map(csv_file):\n'
    '    csv_path = Path(csv_file)\n'
    '    if not csv_path.exists():\n'
    '        print(f"Error: file not found: {csv_path}")\n'
    '        sys.exit(1)\n'
    '    json_path = csv_path.with_suffix(".json")\n'
    '    result = {}\n'
    '    with csv_path.open(newline="", encoding="utf-8") as f:\n'
    '        reader = csv.reader(f)\n'
    '        header = next(reader, None)\n'
    '        if not header or len(header) < 2:\n'
    '            print("Error: CSV must have at least two columns")\n'
    '            sys.exit(1)\n'
    '        for row in reader:\n'
    '            if len(row) < 2:\n'
    '                continue\n'
    '            key = row[0].strip()\n'
    '            value = row[1].strip()\n'
    '            if key:\n'
    '                result[key] = value\n'
    '    with json_path.open("w", encoding="utf-8") as f:\n'
    '        json.dump(result, f, indent=2, ensure_ascii=False)\n'
    '    print(f"Converted : {csv_path} → {json_path}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) != 2:\n'
    '        print(f"Usage: {sys.argv[0]} <file.csv>")\n'
    '        sys.exit(1)\n'
    '    csv_to_json_map(sys.argv[1])\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_CSV2JSON2_SOURCE: str = (
    'import csv\n'
    'import json\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python csv_to_json.py <input.csv>")\n'
    '        sys.exit(1)\n'
    '    input_path = Path(sys.argv[1])\n'
    '    output_path = input_path.with_suffix(".json")\n'
    '    with open(input_path, newline="", encoding="utf-8") as csv_file:\n'
    '        reader = csv.DictReader(csv_file)\n'
    '        data = list(reader)\n'
    '    with open(output_path, mode="w", encoding="utf-8") as json_file:\n'
    '        json.dump(data, json_file, indent=2, ensure_ascii=False)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_LCSV_SOURCE: str = (
    'import csv\n'
    'import os\n'
    'from collections import Counter\n'
    'from concurrent.futures import ThreadPoolExecutor, as_completed\n'
    'from pathlib import Path\n'
    'from tqdm import tqdm\n'
    '\n'
    'binf = Path("/sdcard/bin").open(encoding="utf-8")\n'
    'EXCLUDED_EXTENSIONS = [line.strip() for line in binf]\n'
    'binf.close()\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    Path(path)\n'
    '    counter = Counter()\n'
    '    try:\n'
    '        with Path(path).open(encoding="utf-8", errors="ignore") as f:\n'
    '            for line in f:\n'
    '                line = line.strip()\n'
    '                if line:\n'
    '                    counter[line] += 1\n'
    '    except Exception as e:\n'
    '        print(f"Error reading {path}: {e}")\n'
    '    return counter\n'
    '\n'
    '\n'
    'def collect_files_by_extension():\n'
    '    ext_map = {}\n'
    '    for root, _, filenames in os.walk(Path.cwd()):\n'
    '        for fname in filenames:\n'
    '            if fname.startswith("."):\n'
    '                continue\n'
    '            full_path = os.path.join(root, fname)\n'
    '            ext = os.path.splitext(fname)[1].lower().lstrip(".")\n'
    '            if ext in EXCLUDED_EXTENSIONS:\n'
    '                continue\n'
    '            if not ext:\n'
    '                ext_map.setdefault(ext, []).append(full_path)\n'
    '    return ext_map\n'
    '\n'
    '\n'
    'def collect_lines_for_extension(ext, files):\n'
    '    if not files:\n'
    '        return\n'
    '    global_counter = Counter()\n'
    '    with ThreadPoolExecutor() as executor:\n'
    '        futures = {executor.submit(process_file, f): f for f in files}\n'
    '        for future in tqdm(as_completed(futures), total=len(futures), desc=f"Processing .{ext}  files"):\n'
    '            global_counter.update(future.result())\n'
    '    output_file = f"{ext}.csv"\n'
    '    with Path(output_file).open("w", newline="", encoding="utf-8") as csvfile:\n'
    '        writer = csv.writer(csvfile)\n'
    '        writer.writerow(["number_of_appearance", "line"])\n'
    '        for line, count in global_counter.most_common():\n'
    '            if count >= 2:\n'
    '                writer.writerow([count, line])\n'
    '    print(f"Saved results to {output_file}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    ext_map = collect_files_by_extension()\n'
    '    if not ext_map:\n'
    '        print("No eligible files found.")\n'
    '        return\n'
    '    for ext, files in ext_map.items():\n'
    '        collect_lines_for_extension(ext, files)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_LTXT_SOURCE: str = (
    'from collections import Counter\n'
    'from concurrent.futures import ThreadPoolExecutor, as_completed\n'
    'from pathlib import Path\n'
    'from dh import BIN_EXT\n'
    '\n'
    'EXCLUDED_EXTENSIONS = BIN_EXT\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    counter = Counter()\n'
    '    try:\n'
    '        with path.open(encoding="utf-8", errors="ignore") as f:\n'
    '            for line in f:\n'
    '                line = line.strip()\n'
    '                if line:\n'
    '                    counter[line] += 1\n'
    '    except Exception as e:\n'
    '        print(f"Error reading {path}: {e}")\n'
    '    return counter\n'
    '\n'
    '\n'
    'def collect_files_by_extension():\n'
    '    ext_map = {}\n'
    '    cwd = Path.cwd()\n'
    '    for root, _, filenames in cwd.walk():\n'
    '        for fname in filenames:\n'
    '            if fname.startswith("."):\n'
    '                continue\n'
    '            path = Path(root) / fname\n'
    '            ext = path.suffix\n'
    '            if ext in EXCLUDED_EXTENSIONS:\n'
    '                continue\n'
    '            if ext not in ext_map:\n'
    '                ext_map[ext] = []\n'
    '            ext_map[ext].append(path)\n'
    '    return ext_map\n'
    '\n'
    '\n'
    'def collect_lines_for_extension(ext, files):\n'
    '    if not files:\n'
    '        return\n'
    '    global_counter = Counter()\n'
    '    print(f"Processing {len(files)} files with extension \'{ext}\'")\n'
    '    with ThreadPoolExecutor(max_workers=8) as executor:\n'
    '        futures = {executor.submit(process_file, f): f for f in files}\n'
    '        for future in as_completed(futures):\n'
    '            try:\n'
    '                result = future.result()\n'
    '                global_counter.update(result)\n'
    '            except Exception as e:\n'
    '                print(f"Error processing file: {e}")\n'
    '    output_name = ext.lstrip(".")\n'
    '    if not output_name:\n'
    '        output_name = "no_extension"\n'
    '    output_file = Path(f"{output_name}.txt")\n'
    '    with output_file.open("w", encoding="utf-8") as fo:\n'
    '        written_lines = 0\n'
    '        for line, count in global_counter.most_common():\n'
    '            if count >= 2:\n'
    '                fo.write(line + "\\n")\n'
    '                written_lines += 1\n'
    '    print(f"Saved {written_lines} duplicate lines to {output_file}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    ext_map = collect_files_by_extension()\n'
    '    if not ext_map:\n'
    '        print("No eligible files found.")\n'
    '        return\n'
    '    for ext, files in ext_map.items():\n'
    '        collect_lines_for_extension(ext, files)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_SAVEPKGSTOCSV_SOURCE: str = (
    'import csv\n'
    'import subprocess\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    'OUTPUT_DIR = Path("/sdcard/backups")\n'
    'TSV_FILE = OUTPUT_DIR / "installed.tsv"\n'
    'CSV_FILE = OUTPUT_DIR / "installed.csv"\n'
    'FIELDS = [\n'
    '    "Package",\n'
    '    "Version",\n'
    '    "Architecture",\n'
    '    "Status",\n'
    '    "Priority",\n'
    '    "Section",\n'
    '    "Installed-Size",\n'
    '    "Maintainer",\n'
    '    "Homepage",\n'
    '    "Description",\n'
    '    "Source",\n'
    '    "Essential",\n'
    '    "Multi-Arch",\n'
    '    "Origin",\n'
    '    "Bugs",\n'
    ']\n'
    'FORMAT = """${binary:Package}\t${Version}\t${Architecture}\t${Status}\t${Priority}\t${Section}\t${Installed-Size}\t${Maintainer}\t${Homepage}\t${binary:Summary}\t${Source}\t${Essential}\t${Multi-Arch}\t${Origin}\t${Bugs}\n'
    '"""\n'
    '\n'
    '\n'
    'def query_packages():\n'
    '    try:\n'
    '        proc = subprocess.run(\n'
    '            ["dpkg-query", "-W", f"-f={FORMAT}"],\n'
    '            check=True,\n'
    '            capture_output=True,\n'
    '            text=True,\n'
    '        )\n'
    '    except FileNotFoundError:\n'
    '        sys.exit("dpkg-query not found (not a Debian-based system)")\n'
    '    except subprocess.CalledProcessError as exc:\n'
    '        sys.exit(exc.stderr.strip())\n'
    '    rows = []\n'
    '    for line in proc.stdout.splitlines():\n'
    '        if not line.strip():\n'
    '            continue\n'
    '        cols = line.split("\\t")\n'
    '        if len(cols) != len(FIELDS):\n'
    '            continue\n'
    '        print(cols)\n'
    '        rows.append(cols)\n'
    '    rows.sort(key=lambda r: int(r[6] or 0), reverse=True)\n'
    '    return rows\n'
    '\n'
    '\n'
    'def save_tsv(rows):\n'
    '    with TSV_FILE.open("w", encoding="utf-8") as f:\n'
    '        f.write("\\t".join(FIELDS) + "\\n")\n'
    '        for row in rows:\n'
    '            f.write("\\t".join(row) + "\\n")\n'
    '\n'
    '\n'
    'def save_csv(rows):\n'
    '    with CSV_FILE.open("w", encoding="utf-8", newline="") as f:\n'
    '        writer = csv.writer(f)\n'
    '        writer.writerow(FIELDS)\n'
    '        writer.writerows(rows)\n'
    '\n'
    '\n'
    'def main():\n'
    '    rows = query_packages()\n'
    '    save_tsv(rows)\n'
    '    save_csv(rows)\n'
    '    print(f"Saved {len(rows)} packages")\n'
    '    print(f"TSV: {TSV_FILE}")\n'
    '    print(f"CSV: {CSV_FILE}")\n'
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


class Csv2jsonTool(BaseTool):
    """Wrapper for original csv2json.py: csv_to_json_map() + 1 more."""
    name: str = 'csv2json'
    source_file: str = 'csv2json.py'
    description: str = 'csv_to_json_map() + 1 more'
    functions: list[str] = ['csv_to_json_map', 'main']
    notes: str = ''
    source: str = _CSV2JSON_SOURCE

class Csv2json2Tool(BaseTool):
    """Wrapper for original csv2json2.py: main() + 0 more."""
    name: str = 'csv2json2'
    source_file: str = 'csv2json2.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _CSV2JSON2_SOURCE

class LcsvTool(BaseTool):
    """Wrapper for original lcsv.py: process_file() + 3 more."""
    name: str = 'lcsv'
    source_file: str = 'lcsv.py'
    description: str = 'process_file() + 3 more'
    functions: list[str] = ['process_file', 'collect_files_by_extension', 'collect_lines_for_extension', 'main']
    notes: str = ''
    source: str = _LCSV_SOURCE

class LtxtTool(BaseTool):
    """Wrapper for original ltxt.py: process_file() + 3 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'ltxt'
    source_file: str = 'ltxt.py'
    description: str = 'process_file() + 3 more'
    functions: list[str] = ['process_file', 'collect_files_by_extension', 'collect_lines_for_extension', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _LTXT_SOURCE

class SavepkgstocsvTool(BaseTool):
    """Wrapper for original savepkgstocsv.py: query_packages() + 3 more."""
    name: str = 'savepkgstocsv'
    source_file: str = 'savepkgstocsv.py'
    description: str = 'query_packages() + 3 more'
    functions: list[str] = ['query_packages', 'save_tsv', 'save_csv', 'main']
    notes: str = ''
    source: str = _SAVEPKGSTOCSV_SOURCE

class CsvConvertUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'csv2json': Csv2jsonTool,
        'csv2json2': Csv2json2Tool,
        'lcsv': LcsvTool,
        'ltxt': LtxtTool,
        'savepkgstocsv': SavepkgstocsvTool,
    }

    @classmethod
    def list_tools(cls: type[CsvConvertUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[CsvConvertUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[CsvConvertUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for csv_convert (5 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[CsvConvertUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[CsvConvertUnified], argv: Sequence[str] | None = None) -> int:
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
    return CsvConvertUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

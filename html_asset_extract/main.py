#!/usr/bin/env python3
"""HtmlAssetExtractUnified for html_asset_extract.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (3):
  excss <- excss.py (47L): save_style() + 2 more [requires missing module 'dh' (ImportError at runtime)]
  exjs <- exjs.py (47L): save_script() + 2 more [requires missing module 'dh' (ImportError at runtime)]
  htmlcleaner <- htmlcleaner.py (328L): compute_content_hash() + 7 more

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

_EXCSS_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from bs4 import BeautifulSoup\n'
    'from bs4.element import PageElement\n'
    'from dh import cprint, get_files, get_random_filename, mpf3\n'
    '\n'
    '\n'
    'def save_style(str1):\n'
    '    if not str1 or len(str(str1)) < 2:\n'
    '        return\n'
    '    fn = "css/"\n'
    '    fn += get_random_filename(10)\n'
    '    fn += ".css"\n'
    '    path = Path(fn)\n'
    '    if path.exists():\n'
    '        cprint(f"[{fn}] exists.", "red")\n'
    '        path = unique_path(path)\n'
    '    path.write_text("\\n".join(list(str1)), encoding="utf-8")\n'
    '    cprint(f"{[fn]} created.", "cyan")\n'
    '    return\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    html_content = path.read_text(encoding="utf-8")\n'
    '    path = Path(path)\n'
    '    soup = BeautifulSoup(html_content, "html.parser")\n'
    '    styles = soup.find_all("style")\n'
    '    if styles:\n'
    '        cprint(f"{[path.name]} : {len(styles)} styles found.", "green")\n'
    '        for style in styles:\n'
    '            save_style(style.contents)\n'
    '    return True\n'
    '\n'
    '\n'
    'def main():\n'
    '    outpath = Path("css")\n'
    '    if not outpath.exists():\n'
    '        outpath.mkdir(exist_ok=True)\n'
    '    cwd = Path.cwd()\n'
    '    args = sys.argv[1:]\n'
    '    files = [Path(arg) for arg in args] if args else get_files(cwd, ext=[".html", ".htm"])\n'
    '    mpf3(process_file, files)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_EXJS_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from bs4 import BeautifulSoup\n'
    'from bs4.element import PageElement\n'
    'from dh import cprint, get_files, get_random_filename, mpf3\n'
    '\n'
    'MAX_QUEUE = 16\n'
    '\n'
    '\n'
    'def save_script(str1):\n'
    '    fn = "js/"\n'
    '    fn += get_random_filename(10)\n'
    '    fn += ".js"\n'
    '    fn = Path(fn)\n'
    '    if fn.exists():\n'
    '        cprint(f"[{fn}] exists.", "red")\n'
    '        return False\n'
    '    if not fn.exists():\n'
    '        fn.write_text("\\n".join(list(str1)), encoding="utf-8")\n'
    '        cprint(f"{[fn]} created.", "cyan")\n'
    '    return True\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    html_content = path.read_text(encoding="utf-8")\n'
    '    path = Path(path)\n'
    '    soup = BeautifulSoup(html_content, "html.parser")\n'
    '    scripts = soup.find_all("script")\n'
    '    if scripts:\n'
    '        cprint(f"{[path.name]} : {len(scripts)} scripts found.", "magenta")\n'
    '        for script in scripts:\n'
    '            save_script(script.contents)\n'
    '    return True\n'
    '\n'
    '\n'
    'def main():\n'
    '    if not Path("js").exists():\n'
    '        Path("js").mkdir()\n'
    '    cwd = Path.cwd()\n'
    '    args = sys.argv[1:]\n'
    '    files = [Path(f) for f in args] if args else get_files(cwd, ext=[".html", "htm"])\n'
    '    mpf3(process_file, files)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_HTMLCLEANER_SOURCE: str = (
    'import argparse\n'
    'import hashlib\n'
    'import html.parser\n'
    'import multiprocessing as mp\n'
    'import re\n'
    'import sys\n'
    'from collections.abc import Iterator\n'
    'from dataclasses import dataclass\n'
    'from pathlib import Path\n'
    'from typing import List, Tuple\n'
    '\n'
    'NUM_WORKERS = 8\n'
    'ASSETS_DIR_NAME = "assets"\n'
    'CSS_SUBDIR = "css"\n'
    'JS_SUBDIR = "js"\n'
    'HTML_EXTENSIONS = {".html", ".htm"}\n'
    'MIN_INLINE_SIZE = 0\n'
    '\n'
    '\n'
    '@dataclass\n'
    'class ExtractionResult:\n'
    '    css_count = 0\n'
    '    js_count = 0\n'
    '    error = None\n'
    '\n'
    '\n'
    'class HTMLExtractor(html.parser.HTMLParser):\n'
    '    def __init__(self):\n'
    '        super().__init__(convert_charrefs=False)\n'
    '        self.reset_state()\n'
    '        self.extractions = []\n'
    '\n'
    '    def reset_state(self):\n'
    '        self.current_tag = None\n'
    '        self.current_attrs = {}\n'
    '        self.current_content = []\n'
    '        self.in_style = False\n'
    '        self.in_script = False\n'
    '        self.script_has_src = False\n'
    '\n'
    '    def handle_starttag(self, tag, attrs):\n'
    '        tag_lower = tag.lower()\n'
    '        if tag_lower == "style":\n'
    '            self.in_style = True\n'
    '            self.current_attrs = dict(attrs)\n'
    '            self.current_content = []\n'
    '        elif tag_lower == "script":\n'
    '            attrs_dict = dict(attrs)\n'
    '            if "src" not in attrs_dict:\n'
    '                self.in_script = True\n'
    '                self.script_has_src = False\n'
    '                self.current_attrs = attrs_dict\n'
    '                self.current_content = []\n'
    '            else:\n'
    '                self.script_has_src = True\n'
    '\n'
    '    def handle_endtag(self, tag):\n'
    '        tag_lower = tag.lower()\n'
    '        if tag_lower == "style" and self.in_style:\n'
    '            content = "".join(self.current_content).strip()\n'
    '            if content and len(content) >= MIN_INLINE_SIZE:\n'
    '                self.extractions.append(("css", content, self.current_attrs))\n'
    '            self.in_style = False\n'
    '            self.current_content = []\n'
    '        elif tag_lower == "script" and self.in_script:\n'
    '            content = "".join(self.current_content).strip()\n'
    '            if content and len(content) >= MIN_INLINE_SIZE:\n'
    '                self.extractions.append(("js", content, self.current_attrs))\n'
    '            self.in_script = False\n'
    '            self.current_content = []\n'
    '\n'
    '    def handle_data(self, data):\n'
    '        if self.in_style or self.in_script:\n'
    '            self.current_content.append(data)\n'
    '\n'
    '    def handle_entityref(self, name):\n'
    '        if self.in_script:\n'
    '            self.current_content.append(f"&{name};")\n'
    '\n'
    '    def handle_charref(self, name):\n'
    '        if self.in_script:\n'
    '            self.current_content.append(f"&#{name};")\n'
    '\n'
    '    def error(self, message):\n'
    '        pass\n'
    '\n'
    '\n'
    'def compute_content_hash(content):\n'
    '    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]\n'
    '\n'
    '\n'
    'def get_unique_filename(base_name, extension, assets_dir):\n'
    '    filename = f"{base_name}{extension}"\n'
    '    counter = 1\n'
    '    while (assets_dir / filename).exists():\n'
    '        filename = f"{base_name}_{counter}{extension}"\n'
    '        counter += 1\n'
    '    return filename\n'
    '\n'
    '\n'
    'def extract_assets_from_html(html_content, html_path, assets_base_dir):\n'
    '    parser = HTMLExtractor()\n'
    '    try:\n'
    '        parser.feed(html_content)\n'
    '        parser.close()\n'
    '    except Exception:\n'
    '        return html_content, 0, 0\n'
    '    if not parser.extractions:\n'
    '        return html_content, 0, 0\n'
    '    css_dir = assets_base_dir / CSS_SUBDIR\n'
    '    js_dir = assets_base_dir / JS_SUBDIR\n'
    '    css_dir.mkdir(parents=True, exist_ok=True)\n'
    '    js_dir.mkdir(parents=True, exist_ok=True)\n'
    '    try:\n'
    '        rel_assets_path = assets_base_dir.relative_to(html_path.parent)\n'
    '    except ValueError:\n'
    '        rel_assets_path = Path(*[".."] * len(html_path.parent.parts)) / assets_base_dir\n'
    '    replacements = []\n'
    '    css_count = 0\n'
    '    js_count = 0\n'
    '    html_stem = html_path.stem\n'
    '    for asset_type, content, attrs in parser.extractions:\n'
    '        content_hash = compute_content_hash(content)\n'
    '        if asset_type == "css":\n'
    '            target_dir = css_dir\n'
    '            extension = ".css"\n'
    '            base_name = f"{html_stem}_{content_hash}"\n'
    '            rel_path = rel_assets_path / CSS_SUBDIR\n'
    '            css_count += 1\n'
    '        else:\n'
    '            target_dir = js_dir\n'
    '            extension = ".js"\n'
    '            base_name = f"{html_stem}_{content_hash}"\n'
    '            rel_path = rel_assets_path / JS_SUBDIR\n'
    '            js_count += 1\n'
    '        filename = get_unique_filename(base_name, extension, target_dir)\n'
    '        asset_file = target_dir / filename\n'
    '        try:\n'
    '            asset_file.write_text(content, encoding="utf-8")\n'
    '        except Exception:\n'
    '            if asset_type == "css":\n'
    '                css_count -= 1\n'
    '            else:\n'
    '                js_count -= 1\n'
    '            continue\n'
    '        rel_path = rel_path / filename\n'
    '        href = str(rel_path).replace("\\\\", "/")\n'
    '        if asset_type == "css":\n'
    '            other_attrs = " ".join(f\'{k}="{v}"\' if v else k for k, v in attrs.items() if k not in ("href", "rel"))\n'
    '            if other_attrs:\n'
    '                replacement = f\'<link rel="stylesheet" href="{href}" {other_attrs}>\'\n'
    '            else:\n'
    '                replacement = f\'<link rel="stylesheet" href="{href}">\'\n'
    '        else:\n'
    '            other_attrs = " ".join(f\'{k}="{v}"\' if v else k for k, v in attrs.items() if k != "src")\n'
    '            if other_attrs:\n'
    '                replacement = f\'<script src="{href}" {other_attrs}></script>\'\n'
    '            else:\n'
    '                replacement = f\'<script src="{href}"></script>\'\n'
    '        replacements.append((content, replacement))\n'
    '    modified_html = html_content\n'
    '    for original_content, replacement in replacements:\n'
    '        escaped_content = re.escape(original_content)\n'
    '        patterns = [\n'
    '            rf"(<style[^>]*>)\\s*{escaped_content}\\s*(</style>)",\n'
    '            rf"(<script[^>]*>)\\s*{escaped_content}\\s*(</script>)",\n'
    '        ]\n'
    '        for pattern in patterns:\n'
    '            try:\n'
    '                match = re.search(pattern, modified_html, re.DOTALL | re.IGNORECASE)\n'
    '                if match:\n'
    '                    if "<style" in match.group(1).lower():\n'
    '                        modified_html = modified_html[: match.start()] + replacement + modified_html[match.end() :]\n'
    '                    else:\n'
    '                        modified_html = modified_html[: match.start()] + replacement + modified_html[match.end() :]\n'
    '                    break\n'
    '            except re.error:\n'
    '                continue\n'
    '    return modified_html, css_count, js_count\n'
    '\n'
    '\n'
    'def process_html_file(path):\n'
    '    try:\n'
    '        if not path.is_file():\n'
    '            return ExtractionResult(path=path, success=False, error="Not a file")\n'
    '        MAX_FILE_SIZE = 50 * 1024 * 1024\n'
    '        file_size = path.stat().st_size\n'
    '        if file_size > MAX_FILE_SIZE:\n'
    '            return ExtractionResult(\n'
    '                path=path,\n'
    '                success=False,\n'
    '                error=f"File too large ({file_size / 1024 / 1024:.1f} MB)",\n'
    '            )\n'
    '        if file_size == 0:\n'
    '            return ExtractionResult(path=path, success=True, error="Empty file")\n'
    '        html_content = path.read_text(encoding="utf-8", errors="replace")\n'
    '        assets_dir = path.parent / ASSETS_DIR_NAME\n'
    '        modified_html, css_count, js_count = extract_assets_from_html(html_content, path, assets_dir)\n'
    '        if css_count > 0 or js_count > 0:\n'
    '            temp_path = path.with_suffix(path.suffix + ".tmp")\n'
    '            try:\n'
    '                temp_path.write_text(modified_html, encoding="utf-8")\n'
    '                temp_path.replace(path)\n'
    '            except Exception:\n'
    '                if temp_path.exists():\n'
    '                    temp_path.unlink()\n'
    '                raise\n'
    '        return ExtractionResult(path=path, success=True, css_count=css_count, js_count=js_count)\n'
    '    except UnicodeDecodeError as e:\n'
    '        return ExtractionResult(path=path, success=False, error=f"Encoding error: {e}")\n'
    '    except PermissionError as e:\n'
    '        return ExtractionResult(path=path, success=False, error=f"Permission denied: {e}")\n'
    '    except Exception as e:\n'
    '        return ExtractionResult(path=path, success=False, error=f"{type(e).__name__}: {e}")\n'
    '\n'
    '\n'
    'def find_html_files(paths):\n'
    '    seen = set()\n'
    '    for path in paths:\n'
    '        path = path.resolve()\n'
    '        if path.is_file():\n'
    '            if path.suffix.lower() in HTML_EXTENSIONS and path not in seen:\n'
    '                seen.add(path)\n'
    '                yield path\n'
    '        elif path.is_dir():\n'
    '            for html_file in path.rglob("*"):\n'
    '                if html_file.is_file() and html_file.suffix.lower() in HTML_EXTENSIONS:\n'
    '                    resolved = html_file.resolve()\n'
    '                    if resolved not in seen:\n'
    '                        seen.add(resolved)\n'
    '                        yield resolved\n'
    '        else:\n'
    '            print(f"Warning: Path does not exist: {path}", file=sys.stderr)\n'
    '\n'
    '\n'
    'def get_default_paths():\n'
    '    return [Path.cwd()]\n'
    '\n'
    '\n'
    'def parse_arguments():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Extract inline CSS and JavaScript from HTML files.",\n'
    '        formatter_class=argparse.RawDescriptionHelpFormatter,\n'
    '        epilog="""\n'
    'Examples:\n'
    '    %(prog)s                          # Process current directory recursively\n'
    '    %(prog)s index.html               # Process single file\n'
    '    %(prog)s src/ dist/               # Process multiple directories\n'
    '    %(prog)s *.html                   # Process multiple files (shell glob)\n'
    '        """,\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "paths",\n'
    '        nargs="*",\n'
    '        type=Path,\n'
    '        help="Files or directories to process (default: current directory)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-w",\n'
    '        "--workers",\n'
    '        type=int,\n'
    '        default=NUM_WORKERS,\n'
    '        help=f"Number of worker processes (default: {NUM_WORKERS})",\n'
    '    )\n'
    '    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")\n'
    '    parser.add_argument(\n'
    '        "--min-size",\n'
    '        type=int,\n'
    '        default=MIN_INLINE_SIZE,\n'
    '        help=f"Minimum inline content size to extract (default: {MIN_INLINE_SIZE})",\n'
    '    )\n'
    '    return parser.parse_args()\n'
    '\n'
    '\n'
    'def main():\n'
    '    args = parse_arguments()\n'
    '    global MIN_INLINE_SIZE\n'
    '    MIN_INLINE_SIZE = args.min_size\n'
    '    paths = args.paths if args.paths else get_default_paths()\n'
    '    if not args.quiet:\n'
    '        print("Scanning for HTML files...", file=sys.stderr)\n'
    '    html_files = list(find_html_files(paths))\n'
    '    if not html_files:\n'
    '        print("No HTML files found.", file=sys.stderr)\n'
    '        return 0\n'
    '    if not args.quiet:\n'
    '        print(f"Found {len(html_files)} HTML file(s) to process.", file=sys.stderr)\n'
    '    num_workers = min(args.workers, len(html_files), mp.cpu_count() * 2)\n'
    '    num_workers = max(1, num_workers)\n'
    '    if not args.quiet:\n'
    '        print(f"Using {num_workers} worker(s)...", file=sys.stderr)\n'
    '    total_css = 0\n'
    '    total_js = 0\n'
    '    total_processed = 0\n'
    '    total_errors = 0\n'
    '    with mp.Pool(processes=num_workers) as pool:\n'
    '        try:\n'
    '            for result in pool.imap_unordered(process_html_file, html_files, chunksize=4):\n'
    '                total_processed += 1\n'
    '                if result.success:\n'
    '                    total_css += result.css_count\n'
    '                    total_js += result.js_count\n'
    '                    if not args.quiet:\n'
    '                        if result.css_count > 0 or result.js_count > 0:\n'
    '                            print(\n'
    '                                f"✓ {result.path}: {result.css_count} CSS, {result.js_count} JS extracted",\n'
    '                                file=sys.stderr,\n'
    '                            )\n'
    '                        elif result.error:\n'
    '                            print(f"○ {result.path}: {result.error}", file=sys.stderr)\n'
    '                else:\n'
    '                    total_errors += 1\n'
    '                    print(f"✗ {result.path}: {result.error}", file=sys.stderr)\n'
    '        except KeyboardInterrupt:\n'
    '            print("\\nInterrupted by user.", file=sys.stderr)\n'
    '            pool.terminate()\n'
    '            return 130\n'
    '    print(\n'
    '        f"\\nSummary: {total_processed} file(s) processed, "\n'
    '        f"{total_css} CSS and {total_js} JS extracted, "\n'
    '        f"{total_errors} error(s).",\n'
    '        file=sys.stderr,\n'
    '    )\n'
    '    return 1 if total_errors > 0 else 0\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    sys.exit(main())\n'
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


class ExcssTool(BaseTool):
    """Wrapper for original excss.py: save_style() + 2 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'excss'
    source_file: str = 'excss.py'
    description: str = 'save_style() + 2 more'
    functions: list[str] = ['save_style', 'process_file', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _EXCSS_SOURCE

class ExjsTool(BaseTool):
    """Wrapper for original exjs.py: save_script() + 2 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'exjs'
    source_file: str = 'exjs.py'
    description: str = 'save_script() + 2 more'
    functions: list[str] = ['save_script', 'process_file', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _EXJS_SOURCE

class HtmlcleanerTool(BaseTool):
    """Wrapper for original htmlcleaner.py: compute_content_hash() + 7 more."""
    name: str = 'htmlcleaner'
    source_file: str = 'htmlcleaner.py'
    description: str = 'compute_content_hash() + 7 more'
    functions: list[str] = ['compute_content_hash', 'get_unique_filename', 'extract_assets_from_html', 'process_html_file', 'find_html_files', 'get_default_paths', 'parse_arguments', 'main']
    notes: str = ''
    source: str = _HTMLCLEANER_SOURCE

class HtmlAssetExtractUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'excss': ExcssTool,
        'exjs': ExjsTool,
        'htmlcleaner': HtmlcleanerTool,
    }

    @classmethod
    def list_tools(cls: type[HtmlAssetExtractUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[HtmlAssetExtractUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[HtmlAssetExtractUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for html_asset_extract (3 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[HtmlAssetExtractUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[HtmlAssetExtractUnified], argv: Sequence[str] | None = None) -> int:
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
    return HtmlAssetExtractUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

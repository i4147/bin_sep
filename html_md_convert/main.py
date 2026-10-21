#!/usr/bin/env python3
"""HtmlMdConvertUnified for html_md_convert.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (8):
  h2md <- h2md.py (28L): process_file() + 0 more [requires missing module 'dh' (ImportError at runtime)]
  htm2md <- htm2md.py (39L): process_file() + 1 more [requires missing module 'dh' (ImportError at runtime)]
  html_to_md <- html_to_md.py (46L): process_file() + 0 more [requires missing module 'dh' (ImportError at runtime)]
  html_to_text_with_pyppeteer <- html_to_text_with_pyppeteer.py (27L): top-level script [no __main__ guard (top-level script or library fragment; exec runs top-level code)]
  htmltomd <- htmltomd.py (151L): clean_html() + 4 more
  strip_html_tags <- strip_html_tags.py (210L): _find_safe_splits() + 3 more
  tomd <- tomd.py (40L): process_file() + 0 more [requires missing module 'dh' (ImportError at runtime)]
  trafila <- trafila.py (55L): process_file() + 0 more [requires missing module 'dh' (ImportError at runtime)]

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

_H2MD_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from dh import get_files, mpf3\n'
    'from markdownify import markdownify\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    md_path = path.with_suffix(".md")\n'
    '    content = path.read_text(encoding="utf8")\n'
    '    markdownify(content)\n'
    '    md_path.write_text(md_content, encoding="utf-8")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    args = sys.argv[1:]\n'
    '    files = []\n'
    '    if args:\n'
    '        for arg in args:\n'
    '            p = Path(arg)\n'
    '            if p.is_file():\n'
    '                files.append(p)\n'
    '            elif p.is_dir():\n'
    '                files.extend(get_files(p, ext=[".html"]))\n'
    '    else:\n'
    '        files.extend(get_files(p, ext=[".html"]))\n'
    '    mpf3(process_file, files)\n'
)

_HTM2MD_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from dh import get_files, mpf3, runcmd\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    if path.suffix.lower() in {".html", ".htm"}:\n'
    '        md_file = path.with_suffix(".md")\n'
    '    else:\n'
    '        return (path, False)\n'
    '    try:\n'
    '        _, txt, _ = runcmd(["rhtml2md", str(path)], show_output=False)\n'
    '        md_file.write_text(txt, encoding="utf-8")\n'
    '        print(f"✓ Converted: {path.name} -> {md_file.name}")\n'
    '        return (md_file, True)\n'
    '    except Exception as e:\n'
    '        print(f"✗ Unexpected error converting {path}: {e}", file=sys.stderr)\n'
    '        return (path, False)\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path.cwd()\n'
    '    args = sys.argv[1:]\n'
    '    files = []\n'
    '    if args:\n'
    '        for arg in args:\n'
    '            p = Path(arg)\n'
    '            if p.is_file():\n'
    '                files.append(p)\n'
    '            elif p.is_dir():\n'
    '                files.extend(get_files(p))\n'
    '    else:\n'
    '        files = get_files(cwd)\n'
    '    mpf3(process_file, files)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_HTML_TO_MD_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'import html2text\n'
    'from dh import get_files, mpf3\n'
    'from readability import Document\n'
    '\n'
    'remove_orig = True\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    md_file = path.with_suffix(".md")\n'
    '    if md_file.exists():\n'
    '        return (md_file, True)\n'
    '    try:\n'
    '        html_content = path.read_text(encoding="utf-8", errors="ignore")\n'
    '        doc = Document(html_content)\n'
    '        main_content = doc.summary()\n'
    '        h = html2text.HTML2Text()\n'
    '        h.ignore_links = False\n'
    '        h.ignore_images = False\n'
    '        h.ignore_tables = False\n'
    '        h.body_width = 0\n'
    '        markdown = h.handle(main_content)\n'
    '        if markdown and markdown.strip():\n'
    '            md_file.write_text(markdown, encoding="utf-8")\n'
    '            print(f"✓ Converted: {path.name} -> {md_file.name}")\n'
    '            if remove_orig:\n'
    '                path.unlink()\n'
    '            return (md_file, True)\n'
    '        print(f"✗ No content extracted from {path.name}")\n'
    '        return (path, False)\n'
    '    except Exception as e:\n'
    '        print(f"✗ Error: {e}")\n'
    '        return (path, False)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    args = sys.argv[1:]\n'
    '    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".html", ".htm", ".xhtml", ".xhtm"])\n'
    '    numf = len(files)\n'
    '    if numf == 1:\n'
    '        process_file(files[0])\n'
    '        sys.exit(0)\n'
    '    mpf3(process_file, files)\n'
)

_HTML_TO_TEXT_WITH_PYPPETEER_SOURCE: str = (
    'import asyncio\n'
    'import sys\n'
    'from pathlib import Path\n'
    'from pyppeteer import launch\n'
    '\n'
    '\n'
    'async def main():\n'
    '    url = sys.argv[1]\n'
    '    browser = await launch()\n'
    '    page = await browser.newPage()\n'
    '    await page.goto(url)\n'
    '    await page.screenshot({"path": "example.png"})\n'
    '    content = await page.evaluate("document.body.textContent", force_expr=True)\n'
    '    outfile = Path(url).with_suffix(".txt")\n'
    '    Path(outfile).write_text(content, encoding="utf-8")\n'
    '    dimensions = await page.evaluate("""() => {\n'
    '        return {\n'
    '            width: document.documentElement.clientWidth,\n'
    '            height: document.documentElement.clientHeight,\n'
    '            deviceScaleFactor: window.devicePixelRatio,\n'
    '        }\n'
    '    }""")\n'
    '    print(dimensions)\n'
    '    await browser.close()\n'
    '\n'
    '\n'
    'asyncio.get_event_loop().run_until_complete(main())\n'
)

_HTMLTOMD_SOURCE: str = (
    'import argparse\n'
    'import sys\n'
    'from multiprocessing import cpu_count\n'
    'from pathlib import Path\n'
    'from bs4 import BeautifulSoup\n'
    'from html_to_markdown import Options, convert\n'
    '\n'
    '\n'
    'def clean_html(html_content):\n'
    '    soup = BeautifulSoup(html_content, "html.parser")\n'
    '    for script in soup.find_all("script"):\n'
    '        script.decompose()\n'
    '    for style in soup.find_all("style"):\n'
    '        style.decompose()\n'
    '    for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith("<!--")):\n'
    '        comment.extract()\n'
    '    for tag in soup.find_all(["nav", "footer", "aside", "iframe", "noscript"]):\n'
    '        tag.decompose()\n'
    '    for form in soup.find_all("form"):\n'
    '        form.decompose()\n'
    '    return str(soup)\n'
    '\n'
    '\n'
    'def convert_html_to_md(html_file, options=None):\n'
    '    if html_file.suffix.lower() not in {".html", ".htm"}:\n'
    '        print(f"Warning: {html_file} doesn\'t have .html/.htm extension, skipping.")\n'
    '        return html_file, False\n'
    '    try:\n'
    '        html_content = html_file.read_text(encoding="utf-8")\n'
    '        cleaned_html = clean_html(html_content)\n'
    '        if options is None:\n'
    '            options = Options(\n'
    '                extract_headers=True,\n'
    '                extract_links=True,\n'
    '                extract_images=True,\n'
    '                extract_structured_data=False,\n'
    '                github_flavored=True,\n'
    '            )\n'
    '        markdown_content = convert(cleaned_html, options=options)\n'
    '        markdown_content = "\\n".join(line for line in markdown_content.split("\\n") if line.strip() or line == "")\n'
    '        import re\n'
    '\n'
    '        markdown_content = re.sub(r"\\n{3,}", "\\n\\n", markdown_content)\n'
    '        md_file = html_file.with_suffix(".md")\n'
    '        md_file.write_text(markdown_content, encoding="utf-8")\n'
    '        print(f"✓ Converted: {html_file.name} -> {md_file.name}")\n'
    '        return md_file, True\n'
    '    except Exception as e:\n'
    '        print(f"✗ Error converting {html_file.name}: {e}", file=sys.stderr)\n'
    '        return html_file, False\n'
    '\n'
    '\n'
    'def find_html_files(directory, recursive=True):\n'
    '    if recursive:\n'
    '        html_files = list(directory.rglob("*.html")) + list(directory.rglob("*.htm"))\n'
    '    else:\n'
    '        html_files = list(directory.glob("*.html")) + list(directory.glob("*.htm"))\n'
    '    return sorted(html_files)\n'
    '\n'
    '\n'
    'def process_file_wrapper(args):\n'
    '    html_file, options = args\n'
    '    return convert_html_to_md(html_file, options)\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Enhanced HTML to Markdown converter with better HTML5/JS/form handling",\n'
    '        formatter_class=argparse.RawDescriptionHelpFormatter,\n'
    '        epilog="""\n'
    'Examples:\n'
    '  %(prog)s\n'
    '  %(prog)s -r\n'
    '  %(prog)s file.html\n'
    '  %(prog)s /path/to/directory\n'
    '  %(prog)s --no-recursive\n'
    '        """,\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "path",\n'
    '        nargs="?",\n'
    '        default=".",\n'
    '        help="HTML file or directory to process (default: current directory)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-r",\n'
    '        "--recursive",\n'
    '        action="store_true",\n'
    '        default=True,\n'
    '        help="Process directories recursively (default: True)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--no-recursive",\n'
    '        action="store_false",\n'
    '        dest="recursive",\n'
    '        help="Disable recursive processing",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--workers",\n'
    '        type=int,\n'
    '        default=cpu_count(),\n'
    '        help=f"Number of worker processes (default: {cpu_count()})",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--keep-forms",\n'
    '        action="store_true",\n'
    '        help="Keep form elements (default: remove them)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--github-flavored",\n'
    '        action="store_true",\n'
    '        default=True,\n'
    '        help="Use GitHub-flavored Markdown (default: True)",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    options = Options(\n'
    '        extract_headers=True,\n'
    '        extract_links=True,\n'
    '        extract_images=True,\n'
    '        extract_structured_data=False,\n'
    '        github_flavored=args.github_flavored,\n'
    '    )\n'
    '    input_path = Path(args.path).resolve()\n'
    '    if not input_path.exists():\n'
    '        print(f"Error: Path \'{input_path}\' does not exist.", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    if input_path.is_file():\n'
    '        html_files = [input_path]\n'
    '    elif input_path.is_dir():\n'
    '        html_files = find_html_files(input_path, args.recursive)\n'
    '        if not html_files:\n'
    '            print(f"No HTML files found in {input_path}")\n'
    '            sys.exit(0)\n'
    '        print(f"Found {len(html_files)} HTML file(s) to process")\n'
    '    else:\n'
    '        print(f"Error: \'{input_path}\' is neither a file nor a directory.", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    if len(html_files) == 1:\n'
    '        convert_html_to_md(html_files[0], options)\n'
    '    else:\n'
    '        print(f"Using {args.workers} worker process(es)")\n'
    '        process_args = [(f, options) for f in html_files]\n'
    '        with Pool(processes=args.workers) as pool:\n'
    '            results = pool.map(process_file_wrapper, process_args)\n'
    '        successful = sum(1 for _, success in results if success)\n'
    '        print(f"\\n{\'=\' * 40}")\n'
    '        print(f"Conversion complete: {successful}/{len(html_files)} files converted successfully")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_STRIP_HTML_TAGS_SOURCE: str = (
    'import multiprocessing as mp\n'
    'import os\n'
    'import sys\n'
    'from html.parser import HTMLParser\n'
    'from pathlib import Path\n'
    'from tempfile import NamedTemporaryFile\n'
    '\n'
    'SKIP_CONTENT_TAGS = {"script", "style", "noscript", "template", "head"}\n'
    'BLOCK_TAGS = {\n'
    '    "address",\n'
    '    "article",\n'
    '    "aside",\n'
    '    "blockquote",\n'
    '    "br",\n'
    '    "dd",\n'
    '    "div",\n'
    '    "dl",\n'
    '    "dt",\n'
    '    "fieldset",\n'
    '    "figcaption",\n'
    '    "figure",\n'
    '    "footer",\n'
    '    "form",\n'
    '    "h1",\n'
    '    "h2",\n'
    '    "h3",\n'
    '    "h4",\n'
    '    "h5",\n'
    '    "h6",\n'
    '    "header",\n'
    '    "hr",\n'
    '    "li",\n'
    '    "main",\n'
    '    "nav",\n'
    '    "ol",\n'
    '    "p",\n'
    '    "pre",\n'
    '    "section",\n'
    '    "table",\n'
    '    "tbody",\n'
    '    "td",\n'
    '    "tfoot",\n'
    '    "th",\n'
    '    "thead",\n'
    '    "tr",\n'
    '    "ul",\n'
    '}\n'
    'RAWTEXT_TAGS = {"script", "style", "textarea", "title"}\n'
    '\n'
    '\n'
    'def _find_safe_splits(path, n):\n'
    '    size = path.stat().st_size\n'
    '    if n <= 1 or size == 0:\n'
    '        return []\n'
    '    targets = [size * i // n for i in range(1, n)]\n'
    '    splits = []\n'
    '    in_tag = False\n'
    '    raw_until_close = None\n'
    '    pos = 0\n'
    '    ti = 0\n'
    '    CHUNK = 1 << 20\n'
    '    with path.open("rb") as f:\n'
    '        buf = b""\n'
    '        buf_start = 0\n'
    '        while ti < len(targets):\n'
    '            if pos >= buf_start + len(buf):\n'
    '                buf_start = pos\n'
    '                buf = f.read(CHUNK)\n'
    '                if not buf:\n'
    '                    break\n'
    '            b = buf[pos - buf_start]\n'
    '            pos += 1\n'
    '            if raw_until_close is not None:\n'
    '                if b == ord("<"):\n'
    '                    end = buf_start + len(buf)\n'
    '                    window = buf[pos - 1 - buf_start : pos - 1 - buf_start + 16]\n'
    '                    if window.lower().startswith(raw_until_close):\n'
    '                        raw_until_close = None\n'
    '                        in_tag = True\n'
    '                continue\n'
    '            if in_tag:\n'
    '                if b == ord(">"):\n'
    '                    in_tag = False\n'
    '                continue\n'
    '            if b == ord("<"):\n'
    '                end = buf_start + len(buf)\n'
    '                window = buf[pos - 1 - buf_start : pos - 1 - buf_start + 16]\n'
    '                if window.startswith(b"</"):\n'
    '                    j = 2\n'
    '                    name = bytearray()\n'
    '                    while j < len(window) and window[j : j + 1].isalpha():\n'
    '                        name += window[j : j + 1]\n'
    '                        j += 1\n'
    '                    in_tag = True\n'
    '                else:\n'
    '                    j = 1\n'
    '                    name = bytearray()\n'
    '                    while j < len(window) and window[j : j + 1].isalpha():\n'
    '                        name += window[j : j + 1]\n'
    '                        j += 1\n'
    '                    tagname = bytes(name).lower()\n'
    '                    if tagname in RAWTEXT_TAGS:\n'
    '                        raw_until_close = b"</" + tagname\n'
    '                    in_tag = True\n'
    '                continue\n'
    '            while ti < len(targets) and pos >= targets[ti]:\n'
    '                splits.append(pos)\n'
    '                ti += 1\n'
    '    while len(splits) < n - 1:\n'
    '        splits.append(size)\n'
    '    return splits\n'
    '\n'
    '\n'
    'class _TextExtractor(HTMLParser):\n'
    '    def __init__(self):\n'
    '        super().__init__(convert_charrefs=True)\n'
    '        self._skip_depth = 0\n'
    '        self._chunks = []\n'
    '        self._pending_space = False\n'
    '\n'
    '    def handle_starttag(self, tag, attrs):\n'
    '        if tag in SKIP_CONTENT_TAGS:\n'
    '            self._skip_depth += 1\n'
    '        elif tag in BLOCK_TAGS:\n'
    '            self._pending_space = True\n'
    '\n'
    '    def handle_startendtag(self, tag, attrs):\n'
    '        if tag in BLOCK_TAGS:\n'
    '            self._pending_space = True\n'
    '\n'
    '    def handle_endtag(self, tag):\n'
    '        if tag in SKIP_CONTENT_TAGS and self._skip_depth:\n'
    '            self._skip_depth -= 1\n'
    '        elif tag in BLOCK_TAGS:\n'
    '            self._pending_space = True\n'
    '\n'
    '    def handle_data(self, data):\n'
    '        if self._skip_depth:\n'
    '            return\n'
    '        if self._pending_space:\n'
    '            self._chunks.append(" ")\n'
    '            self._pending_space = False\n'
    '        self._chunks.append(data)\n'
    '\n'
    '    def get_text(self):\n'
    '        return " ".join("".join(self._chunks).split())\n'
    '\n'
    '\n'
    'def _parse_slice(args):\n'
    '    path_str, start, end = args\n'
    '    parser = _TextExtractor()\n'
    '    CHUNK = 1 << 16\n'
    '    with open(path_str, "rb") as f:\n'
    '        f.seek(start)\n'
    '        remaining = end - start\n'
    '        while remaining > 0:\n'
    '            data = f.read(min(CHUNK, remaining))\n'
    '            if not data:\n'
    '                break\n'
    '            remaining -= len(data)\n'
    '            parser.feed(data.decode("utf-8", errors="replace"))\n'
    '    parser.close()\n'
    '    return parser.get_text()\n'
    '\n'
    '\n'
    'def process_file(path, workers=None):\n'
    '    if workers is None:\n'
    '        workers = min(4, os.cpu_count() or 1)\n'
    '    size = path.stat().st_size\n'
    '    if size == 0:\n'
    '        return True\n'
    '    splits = _find_safe_splits(path, workers)\n'
    '    bounds = [0, *splits, size]\n'
    '    ranges = [(str(path), bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]\n'
    '    try:\n'
    '        try:\n'
    '            ctx = mp.get_context("fork")\n'
    '        except ValueError:\n'
    '            ctx = mp.get_context()\n'
    '        with ctx.Pool(processes=workers) as pool:\n'
    '            pieces = pool.map(_parse_slice, ranges)\n'
    '        text = " ".join(p for p in pieces if p)\n'
    '        with NamedTemporaryFile(\n'
    '            "w",\n'
    '            encoding="utf-8",\n'
    '            dir=path.parent,\n'
    '            delete=False,\n'
    '            prefix=path.name + ".",\n'
    '            suffix=".tmp",\n'
    '        ) as tmp:\n'
    '            tmp_path = Path(tmp.name)\n'
    '            tmp.write(text)\n'
    '        os.replace(tmp_path, path)\n'
    '        return True\n'
    '    except Exception as e:\n'
    '        print(f"error: {e}", file=sys.stderr)\n'
    '        return False\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2:\n'
    '        print(f"usage: {sys.argv[0]} FILE [workers]", file=sys.stderr)\n'
    '        raise SystemExit(2)\n'
    '    path = Path(sys.argv[1])\n'
    '    workers = int(sys.argv[2]) if len(sys.argv) > 2 else None\n'
    '    raise SystemExit(0 if process_file(path, workers) else 1)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_TOMD_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from dh import get_files, mpf3\n'
    'from markdownify import markdownify as md\n'
    'from readability import Document\n'
    '\n'
    'remove_orig = True\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    md_file = path.with_suffix(".md")\n'
    '    if md_file.exists():\n'
    '        return (md_file, True)\n'
    '    try:\n'
    '        html_content = path.read_text(encoding="utf-8", errors="ignore")\n'
    '        doc = Document(html_content)\n'
    '        main_content = doc.summary()\n'
    '        markdown = md(main_content)\n'
    '        if markdown and markdown.strip():\n'
    '            md_file.write_text(markdown, encoding="utf-8")\n'
    '            print(f"✓ Converted: {path.name} -> {md_file.name}")\n'
    '            if remove_orig:\n'
    '                path.unlink()\n'
    '            return (md_file, True)\n'
    '        print(f"✗ No content extracted from {path.name}")\n'
    '        return (path, False)\n'
    '    except Exception as e:\n'
    '        print(f"✗ Error: {e}")\n'
    '        return (path, False)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    args = sys.argv[1:]\n'
    '    files = [Path(p) for p in args] if args else get_files(cwd, ext=[".html", ".htm", ".xhtml", ".xhtm"])\n'
    '    if len(files) == 1:\n'
    '        process_file(files[0])\n'
    '        sys.exit(0)\n'
    '    mpf3(process_file, files)\n'
)

_TRAFILA_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'import trafilatura\n'
    'from dh import get_files, mpf\n'
    '\n'
    'remove_orig = "-r" in sys.argv\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    md_file = path.with_suffix(".md")\n'
    '    if md_file.exists():\n'
    '        return md_file, True\n'
    '    try:\n'
    '        html_content = path.read_text(encoding="utf-8")\n'
    '        markdown = trafilatura.extract(\n'
    '            html_content,\n'
    '            output_format="markdown",\n'
    '            include_links=True,\n'
    '            include_images=True,\n'
    '            include_tables=True,\n'
    '            no_fallback=False,\n'
    '        )\n'
    '        if not markdown:\n'
    '            from bs4 import BeautifulSoup\n'
    '            from markdownify import markdownify\n'
    '\n'
    '            soup = BeautifulSoup(html_content, "html.parser")\n'
    '            markdown = markdownify(str(soup))\n'
    '        if markdown and markdown.strip():\n'
    '            md_file.write_text(markdown, encoding="utf-8")\n'
    '            print(f"✓ Converted: {path.name} -> {md_file.name}")\n'
    '            if remove_orig:\n'
    '                path.unlink()\n'
    '            return md_file, True\n'
    '        print(f"✗ No content extracted from {path.name}")\n'
    '        return path, False\n'
    '    except Exception as e:\n'
    '        print(f"✗ Error processing {path.name}: {e}")\n'
    '        return path, False\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    args = sys.argv[1:]\n'
    '    files = (\n'
    '        [Path(p) for p in args if p.strip() != "-r"]\n'
    '        if args and len(args) > 1\n'
    '        else get_files(cwd, [".html", ".htm", ".xhtml", ".xhtm"])\n'
    '    )\n'
    '    numf = len(files)\n'
    '    if numf == 1:\n'
    '        process_file(files[0])\n'
    '        sys.exit(0)\n'
    '    mpf(process_file, files)\n'
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


class H2mdTool(BaseTool):
    """Wrapper for original h2md.py: process_file() + 0 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'h2md'
    source_file: str = 'h2md.py'
    description: str = 'process_file() + 0 more'
    functions: list[str] = ['process_file']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _H2MD_SOURCE

class Htm2mdTool(BaseTool):
    """Wrapper for original htm2md.py: process_file() + 1 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'htm2md'
    source_file: str = 'htm2md.py'
    description: str = 'process_file() + 1 more'
    functions: list[str] = ['process_file', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _HTM2MD_SOURCE

class HtmlToMdTool(BaseTool):
    """Wrapper for original html_to_md.py: process_file() + 0 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'html_to_md'
    source_file: str = 'html_to_md.py'
    description: str = 'process_file() + 0 more'
    functions: list[str] = ['process_file']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _HTML_TO_MD_SOURCE

class HtmlToTextWithPyppeteerTool(BaseTool):
    """Wrapper for original html_to_text_with_pyppeteer.py: top-level script NOTE: no __main__ guard (top-level script or library fragment; exec runs top-level code)."""
    name: str = 'html_to_text_with_pyppeteer'
    source_file: str = 'html_to_text_with_pyppeteer.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = 'no __main__ guard (top-level script or library fragment; exec runs top-level code)'
    source: str = _HTML_TO_TEXT_WITH_PYPPETEER_SOURCE

class HtmltomdTool(BaseTool):
    """Wrapper for original htmltomd.py: clean_html() + 4 more."""
    name: str = 'htmltomd'
    source_file: str = 'htmltomd.py'
    description: str = 'clean_html() + 4 more'
    functions: list[str] = ['clean_html', 'convert_html_to_md', 'find_html_files', 'process_file_wrapper', 'main']
    notes: str = ''
    source: str = _HTMLTOMD_SOURCE

class StripHtmlTagsTool(BaseTool):
    """Wrapper for original strip_html_tags.py: _find_safe_splits() + 3 more."""
    name: str = 'strip_html_tags'
    source_file: str = 'strip_html_tags.py'
    description: str = '_find_safe_splits() + 3 more'
    functions: list[str] = ['_find_safe_splits', '_parse_slice', 'process_file', 'main']
    notes: str = ''
    source: str = _STRIP_HTML_TAGS_SOURCE

class TomdTool(BaseTool):
    """Wrapper for original tomd.py: process_file() + 0 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'tomd'
    source_file: str = 'tomd.py'
    description: str = 'process_file() + 0 more'
    functions: list[str] = ['process_file']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _TOMD_SOURCE

class TrafilaTool(BaseTool):
    """Wrapper for original trafila.py: process_file() + 0 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'trafila'
    source_file: str = 'trafila.py'
    description: str = 'process_file() + 0 more'
    functions: list[str] = ['process_file']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _TRAFILA_SOURCE

class HtmlMdConvertUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'h2md': H2mdTool,
        'htm2md': Htm2mdTool,
        'html_to_md': HtmlToMdTool,
        'html_to_text_with_pyppeteer': HtmlToTextWithPyppeteerTool,
        'htmltomd': HtmltomdTool,
        'strip_html_tags': StripHtmlTagsTool,
        'tomd': TomdTool,
        'trafila': TrafilaTool,
    }

    @classmethod
    def list_tools(cls: type[HtmlMdConvertUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[HtmlMdConvertUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[HtmlMdConvertUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for html_md_convert (8 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[HtmlMdConvertUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[HtmlMdConvertUnified], argv: Sequence[str] | None = None) -> int:
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
    return HtmlMdConvertUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

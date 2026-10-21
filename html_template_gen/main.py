#!/usr/bin/env python3
"""HtmlTemplateGenUnified for html_template_gen.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (4):
  codepener <- codepener.py (66L): top-level script [ORIGINAL SYNTAX ERROR on py3.11 (unterminated string literal (detected at line 6) line 6); likely needs Python 3.12+ (PEP 701 f-strings). Plainly broken here.]
  htnew <- htnew.py (14L): create_html_template() + 0 more
  make_template_html <- make_template_html.py (192L): find_html_files() + 4 more
  mkhtml <- mkhtml.py (20L): top-level script

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

_CODEPENER_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def convert_codepen_html(html_content, title="Document", charset="UTF-8"):\n'
    '    full_html = f\'<!DOCTYPE html>\\n<html lang="en">\\n<head>\\n    <meta charset="{\n'
    '        charset\n'
    '    }">\\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\\n    <title>{\n'
    '        title\n'
    '    }</title>\\n    <link rel="stylesheet" href="style.css">\\n</head>\\n<body>\\n{\n'
    '        html_content\n'
    '    }\\n    <script src="script.js"></script>\\n</body>\\n</html>\\n\'\n'
    '    return full_html\n'
    '\n'
    '\n'
    'def process_file(input_file, output_file=None, title=None):\n'
    '    try:\n'
    '        with open(input_file, encoding="utf-8") as f:\n'
    '            html_content = f.read()\n'
    '    except FileNotFoundError:\n'
    '        print(f"Error: File \'{input_file}\' not found.")\n'
    '        return False\n'
    '    except Exception as e:\n'
    '        print(f"Error reading file: {e}")\n'
    '        return False\n'
    '    if title is None:\n'
    '        title = Path(input_file).stem.replace("-", " ").title()\n'
    '    full_html = convert_codepen_html(html_content, title)\n'
    '    if output_file is None:\n'
    '        output_file = input_file\n'
    '    try:\n'
    '        with open(output_file, "w", encoding="utf-8") as f:\n'
    '            f.write(full_html)\n'
    '        print(f"✓ Successfully converted: {input_file}")\n'
    '        print(f"✓ Saved to: {output_file}")\n'
    '        return True\n'
    '    except Exception as e:\n'
    '        print(f"Error writing file: {e}")\n'
    '        return False\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python codepen_converter.py <input_file> [output_file] [--title \'Page Title\']")\n'
    '        print("\\nExample:")\n'
    '        print("  python codepen_converter.py index.html")\n'
    '        print("  python codepen_converter.py codepen.html output.html")\n'
    '        print("  python codepen_converter.py codepen.html --title \'My Project\'")\n'
    '        sys.exit(1)\n'
    '    input_file = sys.argv[1]\n'
    '    output_file = None\n'
    '    title = None\n'
    '    i = 2\n'
    '    while i < len(sys.argv):\n'
    '        if sys.argv[i] == "--title" and i + 1 < len(sys.argv):\n'
    '            title = sys.argv[i + 1]\n'
    '            i += 2\n'
    '        else:\n'
    '            output_file = sys.argv[i]\n'
    '            i += 1\n'
    '    success = process_file(input_file, output_file, title)\n'
    '    sys.exit(0 if success else 1)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_HTNEW_SOURCE: str = (
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def create_html_template(filename="index.html"):\n'
    '    html_template = \'<!DOCTYPE html>\\n<html lang="en">\\n<head>\\n    <meta charset="UTF-8">\\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\\n    <title>Document</title>\\n</head>\\n<body>\\n    <h1>Hello, World!</h1>\\n    <!-- Your content here -->\\n</body>\\n</html>\\n\'\n'
    '    try:\n'
    '        Path(filename).write_text(html_template, encoding="utf-8")\n'
    '        print(f"Successfully created {filename} in {Path.cwd()}")\n'
    '    except Exception as e:\n'
    '        print(f"Error: {e}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    create_html_template()\n'
)

_MAKE_TEMPLATE_HTML_SOURCE: str = (
    'from pathlib import Path\n'
    'from bs4 import BeautifulSoup\n'
    '\n'
    '\n'
    'def find_html_files(cwd="."):\n'
    '    root_path = Path(cwd).resolve()\n'
    '    html_files = [path for path in root_path.rglob("*.html") if path.name != "template.html"]\n'
    '    for path in root_path.rglob("*.htm"):\n'
    '        html_files.append(path)\n'
    '    return sorted(html_files)\n'
    '\n'
    '\n'
    'def extract_common_structure(html_files):\n'
    '    body_classes = []\n'
    '    meta_tags = []\n'
    '    link_tags = []\n'
    '    script_tags = []\n'
    '    for path in html_files:\n'
    '        try:\n'
    '            with Path(path).open(encoding="utf-8") as f:\n'
    '                soup = BeautifulSoup(f.read(), "html.parser")\n'
    '                if soup.head:\n'
    '                    meta_tags.extend(str(meta) for meta in soup.head.find_all("meta"))\n'
    '                    link_tags.extend(str(link) for link in soup.head.find_all("link"))\n'
    '                    script_tags.extend(str(script) for script in soup.head.find_all("script") if script.get("src"))\n'
    '                if soup.body and soup.body.get("class"):\n'
    '                    body_classes.extend(soup.body.get("class"))\n'
    '        except Exception as e:\n'
    '            print(f"Error processing {path}: {e}")\n'
    '    common_meta = list(set(meta_tags))\n'
    '    common_links = list(set(link_tags))\n'
    '    common_scripts = list(set(script_tags))\n'
    '    common_body_class = " ".join(set(body_classes)) if body_classes else ""\n'
    '    return {\n'
    '        "meta_tags": common_meta,\n'
    '        "link_tags": common_links,\n'
    '        "script_tags": common_scripts,\n'
    '        "body_class": common_body_class,\n'
    '    }\n'
    '\n'
    '\n'
    'def merge_html_content(html_files):\n'
    '    merged_sections = []\n'
    '    for path in html_files:\n'
    '        try:\n'
    '            with Path(path).open(encoding="utf-8") as f:\n'
    '                soup = BeautifulSoup(f.read(), "html.parser")\n'
    '                content = soup.body.decode_contents() if soup.body else str(soup)\n'
    '                section_html = f"""\n'
    '    <!-- Content from: {path.relative_to(Path.cwd())} -->\n'
    '    <section class="merged-content" data-source="{path.name}">\n'
    '        {content}\n'
    '    </section>\n'
    '"""\n'
    '                merged_sections.append(section_html)\n'
    '        except Exception as e:\n'
    '            print(f"Error merging {path}: {e}")\n'
    '    return "".join(merged_sections)\n'
    '\n'
    '\n'
    'def create_template_html(\n'
    '    html_files,\n'
    '    output_file="template.html",\n'
    '    title="Merged HTML Template",\n'
    '):\n'
    '    if not html_files:\n'
    '        print("No HTML files found")\n'
    '        return False\n'
    '    print(f"Processing {len(html_files)} HTML files...")\n'
    '    structure = extract_common_structure(html_files)\n'
    '    merged_content = merge_html_content(html_files)\n'
    '    template = f"""\n'
    '<!DOCTYPE html>\n'
    '<html lang="en">\n'
    '<head>\n'
    '    <meta charset="UTF-8">\n'
    '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    '    <title>{title}</title>\n'
    '    {chr(10).join("    " + tag for tag in structure["meta_tags"])}\n'
    '    {chr(10).join("    " + tag for tag in structure["link_tags"])}\n'
    '    <style>\n'
    '            body {{\n'
    '                font-family: Arial, sans-serif;\n'
    '                line-height: 1.6;\n'
    '                margin: 0;\n'
    '                padding: 20px;\n'
    '                background-color:\n'
    '            }}\n'
    '            .container {{\n'
    '                max-width: 1200px;\n'
    '                margin: 0 auto;\n'
    '                background: white;\n'
    '                padding: 20px;\n'
    '                box-shadow: 0 0 10px rgba(0,0,0,0.1);\n'
    '            }}\n'
    '            .merged-content {{\n'
    '                margin-bottom: 40px;\n'
    '                padding: 20px;\n'
    '                border-left: 4px solid\n'
    '                background:\n'
    '            }}\n'
    '            .merged-content::before {{\n'
    '                content: attr(data-source);\n'
    '            display: block;\n'
    '            font-weight: bold;\n'
    '            color:\n'
    '            margin-bottom: 10px;\n'
    '            font-size: 0.9em;\n'
    '        }}\n'
    '        h1, h2, h3 {{\n'
    '            color:\n'
    '        }}\n'
    '        .toc {{\n'
    '            background:\n'
    '            padding: 20px;\n'
    '            margin-bottom: 30px;\n'
    '            border-radius: 5px;\n'
    '        }}\n'
    '        .toc h2 {{\n'
    '            margin-top: 0;\n'
    '        }}\n'
    '        .toc ul {{\n'
    '            list-style: none;\n'
    '            padding-left: 0;\n'
    '        }}\n'
    '        .toc li {{\n'
    '            margin: 5px 0;\n'
    '        }}\n'
    '        .toc a {{\n'
    '            color:\n'
    '            text-decoration: none;\n'
    '        }}\n'
    '        .toc a:hover {{\n'
    '            text-decoration: underline;\n'
    '            }}\n'
    '    </style>\n'
    '    {chr(10).join("    " + tag for tag in structure["script_tags"])}\n'
    '</head>\n'
    '<body{\' class="\' + structure["body_class"] + \'"\' if structure["body_class"] else ""}>\n'
    '    <div class="container">\n'
    '        <h1>{title}</h1>\n'
    '        <div class="toc">\n'
    '            <h2>Table of Contents</h2>\n'
    '            <ul>\n'
    '        {\n'
    '        chr(10).join(\n'
    '            f\'                <li><a href="#{Path(f).stem}">{Path(f).relative_to(Path.cwd())}</a></li>\'\n'
    '            for f in html_files\n'
    '        )\n'
    '    }\n'
    '            </ul>\n'
    '        </div>\n'
    '{merged_content}\n'
    '    </div>\n'
    '    <script>\n'
    "        document.querySelectorAll('.toc a').forEach(anchor => {{\n"
    "            anchor.addEventListener('click', function (e) {{\n"
    '                e.preventDefault();\n'
    "                const target = document.querySelector(this.getAttribute('href'));\n"
    '                if (target) {{\n'
    "                    target.scrollIntoView({{ behavior: 'smooth' }});\n"
    '                }}\n'
    '            }});\n'
    '        }});\n'
    "        document.querySelectorAll('.merged-content').forEach((section, index) => {{\n"
    "            const source = section.getAttribute('data-source');\n"
    "            const id = source.replace(/\\\\.html?$/, '');\n"
    '            section.id = id;\n'
    '        }});\n'
    '    </script>\n'
    '</body>\n'
    '</html>\n'
    '"""\n'
    '    try:\n'
    '        Path(output_file).write_text(template, encoding="utf-8")\n'
    '        print(f"Template created successfully: {output_file}")\n'
    '        print(f"Merged {len(html_files)} HTML files")\n'
    '        return True\n'
    '    except Exception as e:\n'
    '        print(f"Error writing template: {e}")\n'
    '        return False\n'
    '\n'
    '\n'
    'def main():\n'
    '    html_files = find_html_files()\n'
    '    success = create_template_html(html_files, output_file="template.html", title="Merged HTML Template")\n'
    '    if success:\n'
    '        print("Output file: template.html")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_MKHTML_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    'HTML_TEMPLATE = """<!doctype html>\n'
    '<html>\n'
    '  <head>\n'
    '    <link rel="stylesheet" href="style.css" />\n'
    '    <script src="script.js"></script>\n'
    '    <title>html template</title>\n'
    '  </head>\n'
    '  <body>\n'
    '    <div>\n'
    '      <h2>Heading2</h2>\n'
    '    </div>\n'
    '  </body>\n'
    '</html>\n'
    '"""\n'
    'if __name__ == "__main__":\n'
    '    file_name = Path(sys.argv[1]) or Path("index.html")\n'
    '    file_name.write_text(HTML_TEMPLATE, encoding="utf-8")\n'
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


class CodepenerTool(BaseTool):
    """Wrapper for original codepener.py: top-level script NOTE: ORIGINAL SYNTAX ERROR on py3.11 (unterminated string literal (detected at line 6) line 6); likely needs Python 3.12+ (PEP 701 f-strings). Plainly broken here.."""
    name: str = 'codepener'
    source_file: str = 'codepener.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = 'ORIGINAL SYNTAX ERROR on py3.11 (unterminated string literal (detected at line 6) line 6); likely needs Python 3.12+ (PEP 701 f-strings). Plainly broken here.'
    source: str = _CODEPENER_SOURCE

class HtnewTool(BaseTool):
    """Wrapper for original htnew.py: create_html_template() + 0 more."""
    name: str = 'htnew'
    source_file: str = 'htnew.py'
    description: str = 'create_html_template() + 0 more'
    functions: list[str] = ['create_html_template']
    notes: str = ''
    source: str = _HTNEW_SOURCE

class MakeTemplateHtmlTool(BaseTool):
    """Wrapper for original make_template_html.py: find_html_files() + 4 more."""
    name: str = 'make_template_html'
    source_file: str = 'make_template_html.py'
    description: str = 'find_html_files() + 4 more'
    functions: list[str] = ['find_html_files', 'extract_common_structure', 'merge_html_content', 'create_template_html', 'main']
    notes: str = ''
    source: str = _MAKE_TEMPLATE_HTML_SOURCE

class MkhtmlTool(BaseTool):
    """Wrapper for original mkhtml.py: top-level script."""
    name: str = 'mkhtml'
    source_file: str = 'mkhtml.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _MKHTML_SOURCE

class HtmlTemplateGenUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'codepener': CodepenerTool,
        'htnew': HtnewTool,
        'make_template_html': MakeTemplateHtmlTool,
        'mkhtml': MkhtmlTool,
    }

    @classmethod
    def list_tools(cls: type[HtmlTemplateGenUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[HtmlTemplateGenUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[HtmlTemplateGenUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for html_template_gen (4 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[HtmlTemplateGenUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[HtmlTemplateGenUnified], argv: Sequence[str] | None = None) -> int:
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
    return HtmlTemplateGenUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

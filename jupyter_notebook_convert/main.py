#!/usr/bin/env python3
"""JupyterNotebookConvertUnified for jupyter_notebook_convert.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (6):
  ipynb2md <- ipynb2md.py (19L): top-level script
  meta_to_ipynb <- meta_to_ipynb.py (152L): parse_metadata_section() + 3 more
  nb2py <- nb2py.py (124L): is_import_line() + 5 more
  py2ipynb <- py2ipynb.py (77L): py_to_ipynb() + 1 more
  pytoipynb <- pytoipynb.py (24L): simple_convert() + 0 more
  strip_notebooks <- strip_notebooks.py (121L): find_notebook_files() + 3 more

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

_IPYNB2MD_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'import nbformat\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    fn = Path(sys.argv[1])\n'
    '    with Path(fn).open(encoding="utf-8") as f:\n'
    '        nb = nbformat.read(f, as_version=4)\n'
    '    fo = fn.with_suffix(".md")\n'
    '    with Path(fo).open("w", encoding="utf-8") as out:\n'
    '        for _i, cell in enumerate(nb.cells, 1):\n'
    '            out.write("\\n")\n'
    '            if cell.cell_type == "markdown":\n'
    '                out.write(cell.source + "\\n\\n")\n'
    '            elif cell.cell_type == "code":\n'
    '                out.write("```python\\n")\n'
    '                out.write(cell.source + "\\n")\n'
    '                out.write("```\\n\\n")\n'
    '    print(f"Exported → {fo}")\n'
)

_META_TO_IPYNB_SOURCE: str = (
    'import json\n'
    'import re\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def parse_metadata_section(lines):\n'
    '    metadata = {}\n'
    '    current_key = None\n'
    '    end_line = 0\n'
    '    for i, line in enumerate(lines):\n'
    '        line_stripped = line.strip()\n'
    '        if line.startswith((" ", "\\t")):\n'
    '            if (\n'
    '                current_key\n'
    '                and current_key\n'
    '                not in [\n'
    '                    "Requires-Dist",\n'
    '                    "Provides-Extra",\n'
    '                    "Dynamic",\n'
    '                    "Classifier",\n'
    '                    "Keywords",\n'
    '                    "Project-URL",\n'
    '                ]\n'
    '                and current_key in metadata\n'
    '            ):\n'
    '                metadata[current_key] += " " + line_stripped\n'
    '            continue\n'
    '        if not line_stripped or ":" not in line_stripped:\n'
    '            end_line = i\n'
    '            break\n'
    '        if ":" in line_stripped:\n'
    '            key, value = line_stripped.split(":", 1)\n'
    '            key = key.strip()\n'
    '            value = value.strip()\n'
    '            if key not in [\n'
    '                "Author",\n'
    '                "Author-Email",\n'
    '                "Maintainer",\n'
    '                "Maintainer-Email",\n'
    '                "Home-Page",\n'
    '                "Download-URL",\n'
    '                "Project-URL",\n'
    '                "Requires-Dist",\n'
    '                "Provides-Extra",\n'
    '                "Dynamic",\n'
    '                "Classifier",\n'
    '                "Keywords",\n'
    '                "License",\n'
    '                "License-Expression",\n'
    '            ]:\n'
    '                metadata[key] = value\n'
    '                current_key = key\n'
    '            else:\n'
    '                current_key = None\n'
    '        else:\n'
    '            current_key = None\n'
    '        end_line = i + 1\n'
    '    return metadata, end_line\n'
    '\n'
    '\n'
    'def find_section_boundaries(content, start_pos=0):\n'
    '    sections = []\n'
    '    pos = start_pos\n'
    '    code_pattern = re.compile(r"```(python|shell|bash|sh|py)\\s*\\n(.*?)```", re.DOTALL)\n'
    '    while pos < len(content):\n'
    '        code_match = code_pattern.search(content, pos)\n'
    '        if code_match:\n'
    '            if code_match.start() > pos:\n'
    '                md_text = content[pos : code_match.start()].strip()\n'
    '                if md_text:\n'
    '                    sections.append(("markdown", md_text))\n'
    '            code_text = code_match.group(2).strip()\n'
    '            sections.append(("code", code_text))\n'
    '            pos = code_match.end()\n'
    '        else:\n'
    '            remaining = content[pos:].strip()\n'
    '            if remaining:\n'
    '                sections.append(("markdown", remaining))\n'
    '            break\n'
    '    return sections\n'
    '\n'
    '\n'
    'def convert_metadata_to_notebook(metadata_path):\n'
    '    with open(metadata_path, "r", encoding="utf-8") as f:\n'
    '        content = f.read()\n'
    '    lines = content.split("\\n")\n'
    '    metadata, content_start = parse_metadata_section(lines)\n'
    '    pkg_name = metadata.get("Name", "unknown_package")\n'
    '    pkg_version = metadata.get("Version", "0.0.0")\n'
    '    safe_pkg_name = re.sub(r"[^\\w\\-_]", "_", pkg_name)\n'
    '    output_path = f"{safe_pkg_name}.ipynb"\n'
    '    remaining_content = "\\n".join(lines[content_start:])\n'
    '    sections = find_section_boundaries(remaining_content)\n'
    '    notebook = {\n'
    '        "cells": [],\n'
    '        "metadata": {\n'
    '            "kernelspec": {\n'
    '                "display_name": "Python 3",\n'
    '                "language": "python",\n'
    '                "name": "python3",\n'
    '            },\n'
    '            "language_info": {\n'
    '                "codemirror_mode": {"name": "ipython", "version": 3},\n'
    '                "file_extension": ".py",\n'
    '                "mimetype": "text/x-python",\n'
    '                "name": "python",\n'
    '                "nbconvert_exporter": "python",\n'
    '                "pygments_lexer": "ipython3",\n'
    '                "version": "3.8.0",\n'
    '            },\n'
    '        },\n'
    '        "nbformat": 4,\n'
    '        "nbformat_minor": 4,\n'
    '    }\n'
    '    title_content = f"# {pkg_name} v{pkg_version}\\n\\nConverted from METADATA file"\n'
    '    title_cell = {"cell_type": "markdown", "metadata": {}, "source": [title_content]}\n'
    '    notebook["cells"].append(title_cell)\n'
    '    for cell_type, content in sections:\n'
    '        if cell_type == "markdown":\n'
    '            cell = {"cell_type": "markdown", "metadata": {}, "source": [content]}\n'
    '        else:\n'
    '            cell = {\n'
    '                "cell_type": "code",\n'
    '                "execution_count": None,\n'
    '                "metadata": {},\n'
    '                "outputs": [],\n'
    '                "source": [content],\n'
    '            }\n'
    '        notebook["cells"].append(cell)\n'
    '    with open(output_path, "w", encoding="utf-8") as f:\n'
    '        json.dump(notebook, f, indent=1, ensure_ascii=False)\n'
    '    print(f"Package: {pkg_name} v{pkg_version}")\n'
    '    print(f"Notebook created: {output_path}")\n'
    '    print(f"Total cells: {len(notebook[\'cells\'])}")\n'
    '    return output_path\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python metadata_to_notebook.py <METADATA_file>")\n'
    '        print("Output will be saved as <package_name>.ipynb")\n'
    '        sys.exit(1)\n'
    '    input_file = Path(sys.argv[1])\n'
    '    if not input_file.exists():\n'
    '        print(f"Error: File \'{input_file}\' not found")\n'
    '        sys.exit(1)\n'
    '    convert_metadata_to_notebook(input_file)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_NB2PY_SOURCE: str = (
    'import sys\n'
    'from collections.abc import Iterable, Sequence\n'
    'from multiprocessing import Pool\n'
    'from pathlib import Path\n'
    'from typing import List, Optional\n'
    'import nbformat\n'
    'from loguru import logger\n'
    'from nbformat import NotebookNode\n'
    '\n'
    'POOL_SIZE = 8\n'
    'MAGIC_PREFIXES = ("%", "!", "%%")\n'
    'IMPORT_PREFIXES = ("import ", "from ")\n'
    '\n'
    '\n'
    'def is_import_line(line):\n'
    '    return line.startswith(IMPORT_PREFIXES)\n'
    '\n'
    '\n'
    'def strip_magics(source):\n'
    '    lines = source.split("\\n")\n'
    '    result = []\n'
    '    i = 0\n'
    '    while i < len(lines):\n'
    '        line = lines[i]\n'
    '        stripped = line.lstrip()\n'
    '        if stripped.startswith(MAGIC_PREFIXES):\n'
    '            result.append(f"# [MAGIC] {line.rstrip()}")\n'
    '            while i < len(lines) - 1 and line.rstrip().endswith("\\\\"):\n'
    '                i += 1\n'
    '                line = lines[i]\n'
    '                result.append(f"# [MAGIC] {line.rstrip()}")\n'
    '        else:\n'
    '            result.append(line)\n'
    '        i += 1\n'
    '    return "\\n".join(result)\n'
    '\n'
    '\n'
    'def nb2py(notebook):\n'
    '    imports = []\n'
    '    os_mods = []\n'
    '    sys_mods = []\n'
    '    main_code = []\n'
    '    for cell in notebook.cells:\n'
    '        if cell.cell_type == "markdown":\n'
    '            md_text = str(cell.source).replace("\\n", "\\n# ")\n'
    '            main_code.append(f"# {md_text}\\n")\n'
    '        elif cell.cell_type == "code":\n'
    '            cell_code = str(cell.source)\n'
    '            for line in cell_code.split("\\n"):\n'
    '                if line.strip().startswith("!nb2py"):\n'
    '                    continue\n'
    '                if is_import_line(line):\n'
    '                    imports.append(line)\n'
    '                    continue\n'
    '                if line.startswith("os.environ"):\n'
    '                    os_mods.append(line)\n'
    '                    continue\n'
    '                if line.startswith("sys.path"):\n'
    '                    sys_mods.append(line)\n'
    '                    continue\n'
    '                cleaned = strip_magics(line)\n'
    '                main_code.append(cleaned)\n'
    '    line = ""\n'
    '    for idx, line in enumerate(imports):\n'
    '        if "import os" in line or "from os import" in line:\n'
    '            for mod in sorted(os_mods, reverse=True):\n'
    '                imports.insert(idx + 1, mod)\n'
    '            break\n'
    '    for idx, line in enumerate(imports):\n'
    '        if "import sys" in line or "from sys import" in line:\n'
    '            for mod in sorted(sys_mods, reverse=True):\n'
    '                imports.insert(idx + 1, mod)\n'
    '            break\n'
    '    imports_str = "\\n".join(imports) + "\\n\\n"\n'
    '    main_str = "\\n".join(main_code)\n'
    '    indent = "    "\n'
    '    main_indented = "\\n".join(f"{indent}{ln}" for ln in main_str.split("\\n"))\n'
    '    return f"{imports_str}if __name__ == \'__main__\':\\n{main_indented}"\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    fo = path.with_suffix(".py")\n'
    '    if fo.exists():\n'
    '        return None\n'
    '    with path.open(encoding="utf-8") as f:\n'
    '        nb = nbformat.read(f, as_version=4)\n'
    '    py_code = nb2py(nb)\n'
    '    with fo.open("w", encoding="utf-8") as out:\n'
    '        out.write(py_code)\n'
    '    return f"Exported → {fo.name}"\n'
    '\n'
    '\n'
    'def _collect_files(args):\n'
    '    if not args:\n'
    '        return list(Path.cwd().rglob("*.ipynb"))\n'
    '    files = []\n'
    '    for arg in args:\n'
    '        p = Path(arg)\n'
    '        if p.is_file():\n'
    '            files.append(p)\n'
    '        elif p.is_dir():\n'
    '            files.extend(p.rglob("*.ipynb"))\n'
    '    return files\n'
    '\n'
    '\n'
    'def main(argv=None):\n'
    '    args = list(argv) if argv is not None else sys.argv[1:]\n'
    '    files = _collect_files(args)\n'
    '    if not files:\n'
    '        logger.info("No .ipynb files found")\n'
    '        return 0\n'
    '    logger.info("Found {} notebook(s) to convert using {} workers", len(files), POOL_SIZE)\n'
    '    with Pool(processes=POOL_SIZE) as pool:\n'
    '        results = [pool.apply_async(process_file, (f,)) for f in files]\n'
    '        for result in results:\n'
    '            message = result.get()\n'
    '            if message:\n'
    '                logger.info("{}", message)\n'
    '    return 0\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_PY2IPYNB_SOURCE: str = (
    'import argparse\n'
    'import json\n'
    'from pathlib import Path\n'
    'import nbformat as nbf\n'
    '\n'
    '\n'
    'def py_to_ipynb(input_file, output_file=None):\n'
    '    if not Path(input_file).exists():\n'
    '        print(f"Error: File \'{input_file}\' not found.")\n'
    '        return False\n'
    '    code = Path(input_file).read_text(encoding="utf-8")\n'
    '    nb = nbf.v4.new_notebook()\n'
    '    cells = []\n'
    '    current_cell = []\n'
    '    lines = code.split("\\n")\n'
    '    i = 0\n'
    '    while i < len(lines):\n'
    '        line = lines[i]\n'
    '        if (\n'
    '            i > 0\n'
    '            and (\n'
    '                line.startswith(("def ", "class "))\n'
    '                or (line.startswith(("import ", "from ")) and not current_cell[-1].startswith(("import ", "from ")))\n'
    '                or (\n'
    '                    line.strip() == ""\n'
    '                    and current_cell\n'
    '                    and i + 1 < len(lines)\n'
    '                    and lines[i + 1].strip()\n'
    '                    and not lines[i + 1].startswith((" ", "\\t"))\n'
    '                )\n'
    '            )\n'
    '            and current_cell\n'
    '        ):\n'
    '            cell_code = "\\n".join(current_cell).strip()\n'
    '            if cell_code:\n'
    '                cells.append(nbf.v4.new_code_cell(cell_code))\n'
    '            current_cell = []\n'
    '        current_cell.append(line.rstrip())\n'
    '        i += 1\n'
    '    if current_cell:\n'
    '        cell_code = "\\n".join(current_cell).strip()\n'
    '        if cell_code:\n'
    '            cells.append(nbf.v4.new_code_cell(cell_code))\n'
    '    nb["cells"] = cells\n'
    '    if output_file is None:\n'
    '        output_file = Path(input_file).stem + ".ipynb"\n'
    '    with Path(output_file).open("w", encoding="utf-8") as f:\n'
    '        json.dump(nb, f, indent=1, ensure_ascii=False)\n'
    '    print(f"Successfully converted \'{input_file}\' to \'{output_file}\'")\n'
    '    print(f"Created {len(cells)} cell(s)")\n'
    '    return True\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(description="Convert a Python script to a Jupyter notebook")\n'
    '    parser.add_argument("input", help="Input Python file (.py)")\n'
    '    parser.add_argument("output", nargs="?", help="Output notebook file (.ipynb) (optional)")\n'
    '    parser.add_argument(\n'
    '        "--no-split",\n'
    '        action="store_true",\n'
    '        help="Don\'t split code into multiple cells (one cell only)",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    if args.no_split:\n'
    '        code = Path(args.input).read_text(encoding="utf-8")\n'
    '        nb = nbf.v4.new_notebook()\n'
    '        nb["cells"] = [nbf.v4.new_code_cell(code)]\n'
    '        output_file = args.output or Path(args.input).stem + ".ipynb"\n'
    '        with Path(output_file).open("w", encoding="utf-8") as f:\n'
    '            json.dump(nb, f, indent=1, ensure_ascii=False)\n'
    '        print(f"Successfully converted \'{args.input}\' to \'{output_file}\' (single cell)")\n'
    '    else:\n'
    '        py_to_ipynb(args.input, args.output)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_PYTOIPYNB_SOURCE: str = (
    'import json\n'
    'import sys\n'
    'from pathlib import Path\n'
    'import nbformat as nbf\n'
    '\n'
    '\n'
    'def simple_convert(py_file, ipynb_file=None):\n'
    '    if not ipynb_file:\n'
    '        ipynb_file = Path(py_file).stem + ".ipynb"\n'
    '    code = Path(py_file).read_text(encoding="utf-8")\n'
    '    nb = nbf.v4.new_notebook()\n'
    '    nb["cells"] = [nbf.v4.new_code_cell(code)]\n'
    '    with Path(ipynb_file).open("w", encoding="utf-8") as f:\n'
    '        json.dump(nb, f, indent=1)\n'
    '    print(f"Converted {py_file} to {ipynb_file}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python simple_convert.py input.py [output.ipynb]")\n'
    '        sys.exit(1)\n'
    '    py_file = sys.argv[1]\n'
    '    ipynb_file = sys.argv[2] if len(sys.argv) > 2 else None\n'
    '    simple_convert(py_file, ipynb_file)\n'
)

_STRIP_NOTEBOOKS_SOURCE: str = (
    'import argparse\n'
    'import json\n'
    'import sys\n'
    'from multiprocessing import Pool\n'
    'from multiprocessing.pool import AsyncResult\n'
    'from pathlib import Path\n'
    'from typing import Final\n'
    'from loguru import logger\n'
    '\n'
    'MAX_WORKERS = 8\n'
    'StripResult = tuple[Path, bool, str]\n'
    '\n'
    '\n'
    'def find_notebook_files(paths):\n'
    '    notebook_files = set()\n'
    '    for path in paths:\n'
    '        if not path.exists():\n'
    '            logger.warning(f"{path} does not exist, skipping.")\n'
    '            continue\n'
    '        if path.is_file():\n'
    '            if path.suffix == ".ipynb":\n'
    '                notebook_files.add(path.resolve())\n'
    '            else:\n'
    '                logger.warning(f"{path} is not a .ipynb file, skipping.")\n'
    '        elif path.is_dir():\n'
    '            for nb_file in path.rglob("*.ipynb"):\n'
    '                if ".ipynb_checkpoints" not in str(nb_file):\n'
    '                    notebook_files.add(nb_file.resolve())\n'
    '    return notebook_files\n'
    '\n'
    '\n'
    'def strip_notebook_output(notebook_path):\n'
    '    try:\n'
    '        with notebook_path.open("r", encoding="utf-8") as f:\n'
    '            notebook = json.load(f)\n'
    '        if "cells" not in notebook:\n'
    '            return (notebook_path, False, "Not a valid notebook (no \'cells\' key)")\n'
    '        cells = notebook["cells"]\n'
    '        if not isinstance(cells, list):\n'
    '            return (\n'
    '                notebook_path,\n'
    '                False,\n'
    '                "Not a valid notebook (\'cells\' is not a list)",\n'
    '            )\n'
    '        modified = False\n'
    '        for cell in cells:\n'
    '            if not isinstance(cell, dict):\n'
    '                continue\n'
    '            if cell.get("cell_type") == "code":\n'
    '                if cell.get("outputs"):\n'
    '                    cell["outputs"] = []\n'
    '                    modified = True\n'
    '                if "execution_count" in cell and cell["execution_count"] is not None:\n'
    '                    cell["execution_count"] = None\n'
    '                    modified = True\n'
    '        if modified:\n'
    '            with notebook_path.open("w", encoding="utf-8") as f:\n'
    '                json.dump(notebook, f, indent=1, ensure_ascii=False)\n'
    '                f.write("\\n")\n'
    '            return (notebook_path, True, "Outputs stripped")\n'
    '        return (notebook_path, True, "No outputs to strip")\n'
    '    except json.JSONDecodeError as exc:\n'
    '        return (notebook_path, False, f"Invalid JSON: {exc}")\n'
    '    except Exception as exc:\n'
    '        return (notebook_path, False, f"Error: {exc}")\n'
    '\n'
    '\n'
    'def process_notebooks(paths):\n'
    '    notebook_files = find_notebook_files(paths)\n'
    '    if not notebook_files:\n'
    '        print("No .ipynb files found to process.")\n'
    '        return\n'
    '    print(f"Found {len(notebook_files)} notebook(s) to process...")\n'
    '    ordered = sorted(notebook_files)\n'
    '    results = []\n'
    '    with Pool(processes=MAX_WORKERS) as pool:\n'
    '        async_results = [pool.apply_async(strip_notebook_output, (path,)) for path in ordered]\n'
    '        for async_res in async_results:\n'
    '            path, success, message = async_res.get()\n'
    '            results.append((path, success, message))\n'
    '            status = "✓" if success else "✗"\n'
    '            relative_path = path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path\n'
    '            print(f"{status} {relative_path}: {message}")\n'
    '    successful = sum(1 for _, success, _ in results if success)\n'
    '    failed = len(results) - successful\n'
    '    if failed > 0:\n'
    '        logger.warning(f"Processed: {successful} succeeded, {failed} failed")\n'
    '    else:\n'
    '        print(f"Successfully processed {successful} notebook(s)")\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Strip outputs from Jupyter notebook (.ipynb) files",\n'
    '        formatter_class=argparse.RawDescriptionHelpFormatter,\n'
    '        epilog="""\n'
    'Examples:\n'
    '  %(prog)s\n'
    '  %(prog)s notebook.ipynb\n'
    '  %(prog)s dir1/ dir2/\n'
    '  %(prog)s *.ipynb\n'
    '  %(prog)s .\n'
    '        """,\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "paths",\n'
    '        nargs="*",\n'
    '        default=["."],\n'
    '        help="Files or directories to process (default: current directory)",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    paths = [Path(p) for p in args.paths]\n'
    '    try:\n'
    '        process_notebooks(paths)\n'
    '    except KeyboardInterrupt:\n'
    '        logger.warning("Interrupted by user")\n'
    '        sys.exit(1)\n'
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


class Ipynb2mdTool(BaseTool):
    """Wrapper for original ipynb2md.py: top-level script."""
    name: str = 'ipynb2md'
    source_file: str = 'ipynb2md.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _IPYNB2MD_SOURCE

class MetaToIpynbTool(BaseTool):
    """Wrapper for original meta_to_ipynb.py: parse_metadata_section() + 3 more."""
    name: str = 'meta_to_ipynb'
    source_file: str = 'meta_to_ipynb.py'
    description: str = 'parse_metadata_section() + 3 more'
    functions: list[str] = ['parse_metadata_section', 'find_section_boundaries', 'convert_metadata_to_notebook', 'main']
    notes: str = ''
    source: str = _META_TO_IPYNB_SOURCE

class Nb2pyTool(BaseTool):
    """Wrapper for original nb2py.py: is_import_line() + 5 more."""
    name: str = 'nb2py'
    source_file: str = 'nb2py.py'
    description: str = 'is_import_line() + 5 more'
    functions: list[str] = ['is_import_line', 'strip_magics', 'nb2py', 'process_file', '_collect_files', 'main']
    notes: str = ''
    source: str = _NB2PY_SOURCE

class Py2ipynbTool(BaseTool):
    """Wrapper for original py2ipynb.py: py_to_ipynb() + 1 more."""
    name: str = 'py2ipynb'
    source_file: str = 'py2ipynb.py'
    description: str = 'py_to_ipynb() + 1 more'
    functions: list[str] = ['py_to_ipynb', 'main']
    notes: str = ''
    source: str = _PY2IPYNB_SOURCE

class PytoipynbTool(BaseTool):
    """Wrapper for original pytoipynb.py: simple_convert() + 0 more."""
    name: str = 'pytoipynb'
    source_file: str = 'pytoipynb.py'
    description: str = 'simple_convert() + 0 more'
    functions: list[str] = ['simple_convert']
    notes: str = ''
    source: str = _PYTOIPYNB_SOURCE

class StripNotebooksTool(BaseTool):
    """Wrapper for original strip_notebooks.py: find_notebook_files() + 3 more."""
    name: str = 'strip_notebooks'
    source_file: str = 'strip_notebooks.py'
    description: str = 'find_notebook_files() + 3 more'
    functions: list[str] = ['find_notebook_files', 'strip_notebook_output', 'process_notebooks', 'main']
    notes: str = ''
    source: str = _STRIP_NOTEBOOKS_SOURCE

class JupyterNotebookConvertUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'ipynb2md': Ipynb2mdTool,
        'meta_to_ipynb': MetaToIpynbTool,
        'nb2py': Nb2pyTool,
        'py2ipynb': Py2ipynbTool,
        'pytoipynb': PytoipynbTool,
        'strip_notebooks': StripNotebooksTool,
    }

    @classmethod
    def list_tools(cls: type[JupyterNotebookConvertUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[JupyterNotebookConvertUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[JupyterNotebookConvertUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for jupyter_notebook_convert (6 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[JupyterNotebookConvertUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[JupyterNotebookConvertUnified], argv: Sequence[str] | None = None) -> int:
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
    return JupyterNotebookConvertUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

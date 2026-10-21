#!/usr/bin/env python3
"""ExtractImportsPyUnified for extract_imports_py.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (7):
  ex_imports <- ex_imports.py (39L): process_file() + 1 more [requires missing module 'dh' (ImportError at runtime)]
  eximports <- eximports.py (114L): _make_parser() + 7 more
  eximports2 <- eximports2.py (57L): extract_file() + 1 more [no __main__ guard (top-level script or library fragment; exec runs top-level code)]
  eximports3 <- eximports3.py (38L): process_file() + 0 more [requires missing module 'dh' (ImportError at runtime)]
  fimport <- fimport.py (125L): find_python_files() + 3 more
  import_collector <- import_collector.py (90L): get_imports_from_file() + 2 more [requires missing module 'dh' (ImportError at runtime)]
  importz <- importz.py (55L): is_python_file() + 2 more

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

_EX_IMPORTS_SOURCE: str = (
    'from pathlib import Path\n'
    'import tree_sitter_python as tsp\n'
    'from dh import get_files, mpf3, unique_path\n'
    'from tree_sitter import Language, Parser\n'
    '\n'
    'OUTPUT_DIR = Path.home() / "tmp" / "output"\n'
    'parser = Parser()\n'
    'parser.language = Language(tsp.language())\n'
    'VALID = {"import_statement", "import_from_statement"}\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    src = path.read_bytes()\n'
    '    tree = parser.parse(src)\n'
    '    root = tree.root_node\n'
    '    return [src[node.start_byte : node.end_byte].decode() for node in root.children if node.type in VALID]\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path.cwd()\n'
    '    outfile = OUTPUT_DIR / f"{cwd.name}_importz.py"\n'
    '    if outfile.exists():\n'
    '        outfile = unique_path(outfile)\n'
    '    all_imports = []\n'
    '    files = get_files(cwd, ext=[".py"])\n'
    '    results = mpf3(process_file, files)\n'
    '    for imports in results:\n'
    '        if imports:\n'
    '            for k in imports:\n'
    '                if not k.startswith("from .") and k not in all_imports:\n'
    '                    all_imports.append(k)\n'
    '    all_imports = sorted(set(all_imports))\n'
    '    outfile.write_text("\\n".join(all_imports), encoding="utf-8")\n'
    '    print("done.")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_EXIMPORTS_SOURCE: str = (
    'import sys\n'
    'from collections.abc import Iterable\n'
    'from importlib.metadata import distributions\n'
    'from multiprocessing import Pool\n'
    'from pathlib import Path\n'
    'from typing import Final, List, Optional, Set\n'
    'import tree_sitter_python as tsp\n'
    'from loguru import logger\n'
    'from tree_sitter import Language, Parser\n'
    '\n'
    'POOL_SIZE = 8\n'
    'OUTPUT_FILE = "importz.txt"\n'
    'VALID_NODE_TYPES = frozenset({"import_statement", "import_from_statement"})\n'
    'STDLIB = frozenset(getattr(sys, "stdlib_module_names", ()))\n'
    '\n'
    '\n'
    'def _make_parser():\n'
    '    parser = Parser()\n'
    '    parser.language = Language(tsp.language())\n'
    '    return parser\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    file_path = Path(path)\n'
    '    src = file_path.read_bytes()\n'
    '    parser = _make_parser()\n'
    '    tree = parser.parse(src)\n'
    '    root = tree.root_node\n'
    '    results = []\n'
    '    child = None\n'
    '    for child in root.children:\n'
    '        if child.type in VALID_NODE_TYPES:\n'
    '            results.append(src[child.start_byte : child.end_byte].decode())\n'
    '    return results\n'
    '\n'
    '\n'
    'def normalize_import(import_line):\n'
    '    line = import_line.lower().strip()\n'
    '    if line.startswith("import "):\n'
    '        module = line[7:]\n'
    '        if " as " in module:\n'
    '            module = module[: module.index(" as ")]\n'
    '        if "." in module:\n'
    '            module = module[: module.index(".")]\n'
    '        return module if module and not module.startswith("_") else None\n'
    '    if line.startswith("from "):\n'
    '        module = line[5:]\n'
    '        if module.startswith("."):\n'
    '            return None\n'
    '        if " import" in module:\n'
    '            module = module[: module.index(" import")]\n'
    '        if " as " in module:\n'
    '            module = module[: module.index(" as ")]\n'
    '        if "." in module:\n'
    '            module = module[: module.index(".")]\n'
    '        return module if module and not module.startswith("_") else None\n'
    '    return None\n'
    '\n'
    '\n'
    'def _get_installed_pkgs():\n'
    '    pkgs = set()\n'
    '    dist = None\n'
    '    for dist in distributions():\n'
    '        name = None\n'
    '        try:\n'
    '            name = dist.metadata["Name"]\n'
    '        except Exception:\n'
    '            name = None\n'
    '        if name:\n'
    '            pkgs.add(name.replace("-", "_").lower())\n'
    '    return pkgs\n'
    '\n'
    '\n'
    'def process_files_parallel(files):\n'
    '    all_imports = set()\n'
    '    if not files:\n'
    '        return all_imports\n'
    '    with Pool(processes=POOL_SIZE) as pool:\n'
    '        for result in pool.imap_unordered(process_file, files):\n'
    '            all_imports.update(result)\n'
    '    return all_imports\n'
    '\n'
    '\n'
    'def filter_imports(imports):\n'
    '    installed_pkgs = _get_installed_pkgs()\n'
    '    excluded = set(STDLIB) | installed_pkgs\n'
    '    filtered = []\n'
    '    for imp in imports:\n'
    '        normalized = normalize_import(imp)\n'
    '        if normalized and normalized not in excluded:\n'
    '            filtered.append(normalized + "\\n")\n'
    '    return sorted(set(filtered))\n'
    '\n'
    '\n'
    'def get_pyfiles(root):\n'
    '    return [p for p in root.rglob("*.py") if p.is_file()]\n'
    '\n'
    '\n'
    'def main(argv=None):\n'
    '    _ = list(argv) if argv is not None else sys.argv[1:]\n'
    '    outfile = Path(OUTPUT_FILE)\n'
    '    cwd = Path.cwd()\n'
    '    pyfiles = get_pyfiles(cwd)\n'
    '    logger.info("{} python files found", len(pyfiles))\n'
    '    all_imports = process_files_parallel(pyfiles)\n'
    '    filtered_imports = filter_imports(all_imports)\n'
    '    outfile.write_text("".join(filtered_imports), encoding="utf-8")\n'
    '    for imp in filtered_imports:\n'
    '        logger.info("{}", imp.strip())\n'
    '    return 0\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_EXIMPORTS2_SOURCE: str = (
    'from collections import defaultdict\n'
    'from pathlib import Path\n'
    'import tree_sitter_python as tsp\n'
    'from tree_sitter import Language, Parser, Tree\n'
    '\n'
    'parser = Parser()\n'
    'parser.language = Language(tsp.language())\n'
    'OUT_DIR = Path("output")\n'
    'OUT_DIR.mkdir(exist_ok=True)\n'
    'VALID = {"import_statement", "import_from_statement"}\n'
    '\n'
    '\n'
    'def extract_file(src, tree):\n'
    '    root = tree.root_node\n'
    '    return [src[node.start_byte : node.end_byte].decode() for node in root.children if node.type in VALID]\n'
    '\n'
    '\n'
    'def get_relative_path(path, base_path):\n'
    '    try:\n'
    '        return path.relative_to(base_path)\n'
    '    except ValueError:\n'
    '        return path\n'
    '\n'
    '\n'
    'folder_imports = defaultdict(list)\n'
    'processed_files_count = 0\n'
    'folders_found = set()\n'
    'for py in Path().rglob("*.py"):\n'
    '    if any(part.startswith(".") for part in py.parts) or "site-packages" in py.parts:\n'
    '        continue\n'
    '    if OUT_DIR in py.parents:\n'
    '        continue\n'
    '    try:\n'
    '        src = py.read_bytes()\n'
    '        tree = parser.parse(src)\n'
    '        imports = extract_file(src, tree)\n'
    '        if imports:\n'
    '            folder_path = py.parent\n'
    '            relative_folder = get_relative_path(folder_path, Path())\n'
    '            folders_found.add(str(relative_folder))\n'
    '            file_header = f"# === {py.name} ===\\n"\n'
    '            folder_imports[relative_folder].append(file_header + "\\n".join(imports))\n'
    '            processed_files_count += 1\n'
    '    except Exception as e:\n'
    '        print(f"⚠️  Error processing {py}: {e}")\n'
    'for folder, imports_list in folder_imports.items():\n'
    '    if not imports_list:\n'
    '        continue\n'
    '    out_file = OUT_DIR / folder / "imports.py"\n'
    '    out_file.parent.mkdir(parents=True, exist_ok=True)\n'
    '    content = "\\n\\n".join(imports_list)\n'
    '    header = f"# Auto-generated imports file for folder: {folder}\\n"\n'
    '    out_file.write_text(header + content)\n'
    '    print(f"✅ saved: {out_file} ({len(imports_list)} files)")\n'
    'print(f"""\n'
    '✨ Done! Processed {processed_files_count} files in {len(folder_imports)} folder(s)""")\n'
    'print(f"📁 Folders: {\', \'.join(sorted(folders_found))}")\n'
)

_EXIMPORTS3_SOURCE: str = (
    'import ast\n'
    'from pathlib import Path\n'
    'from dh import get_files, mpf3, unique_path\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    Path(path)\n'
    '    imports = set()\n'
    '    try:\n'
    '        with Path(path).open(encoding="utf-8") as f:\n'
    '            tree = ast.parse(f.read(), filename=str(path))\n'
    '        for node in ast.walk(tree):\n'
    '            if isinstance(node, ast.Import):\n'
    '                imports.update(n.name.split(".")[0] for n in node.names)\n'
    '            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:\n'
    '                imports.add(node.module.split(".")[0])\n'
    '    except (SyntaxError, UnicodeDecodeError):\n'
    '        pass\n'
    '    return imports\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    files = get_files(cwd, ext=[".py"])\n'
    '    results = mpf3(process_file, files)\n'
    '    uniq_imports = set()\n'
    '    for k in results:\n'
    '        if k:\n'
    '            for x in k:\n'
    '                if x not in uniq_imports:\n'
    '                    uniq_imports.add(x)\n'
    '    output_path = Path("requirements.txt")\n'
    '    if output_path.exists():\n'
    '        output_path = unique_path(output_path)\n'
    '    with open(output_path, "w") as f:\n'
    '        for k in uniq_imports:\n'
    '            f.write(f"{k}\\n")\n'
    '    print(f"{output_path.name} created.")\n'
)

_FIMPORT_SOURCE: str = (
    'import ast\n'
    'from pathlib import Path\n'
    'from typing import TYPE_CHECKING\n'
    '\n'
    'if TYPE_CHECKING:\n'
    '    from collections.abc import Iterable\n'
    '\n'
    '\n'
    'class ImportVisitor(ast.NodeVisitor):\n'
    '    def __init__(self):\n'
    '        self._nesting_level = 0\n'
    '        self.non_top_level_imports = []\n'
    '\n'
    '    def _is_top_level(self):\n'
    '        return self._nesting_level == 0\n'
    '\n'
    '    def _visit_nested(self, node):\n'
    '        self._nesting_level += 1\n'
    '        self.generic_visit(node)\n'
    '        self._nesting_level -= 1\n'
    '\n'
    '    def visit_FunctionDef(self, node):\n'
    '        self._visit_nested(node)\n'
    '\n'
    '    def visit_AsyncFunctionDef(self, node):\n'
    '        self._visit_nested(node)\n'
    '\n'
    '    def visit_ClassDef(self, node):\n'
    '        self._visit_nested(node)\n'
    '\n'
    '    def visit_For(self, node):\n'
    '        self._visit_nested(node)\n'
    '\n'
    '    def visit_AsyncFor(self, node):\n'
    '        self._visit_nested(node)\n'
    '\n'
    '    def visit_While(self, node):\n'
    '        self._visit_nested(node)\n'
    '\n'
    '    def visit_If(self, node):\n'
    '        self._visit_nested(node)\n'
    '\n'
    '    def visit_With(self, node):\n'
    '        self._visit_nested(node)\n'
    '\n'
    '    def visit_AsyncWith(self, node):\n'
    '        self._visit_nested(node)\n'
    '\n'
    '    def visit_Try(self, node):\n'
    '        self._visit_nested(node)\n'
    '\n'
    '    def visit_Import(self, node):\n'
    '        if not self._is_top_level():\n'
    '            self.non_top_level_imports.append(node)\n'
    '        self.generic_visit(node)\n'
    '\n'
    '    def visit_ImportFrom(self, node):\n'
    '        if not self._is_top_level():\n'
    '            self.non_top_level_imports.append(node)\n'
    '        self.generic_visit(node)\n'
    '\n'
    '\n'
    'def find_python_files(root):\n'
    '    return root.rglob("*.py")\n'
    '\n'
    '\n'
    'def format_import(node):\n'
    '    if isinstance(node, ast.Import):\n'
    '        parts = []\n'
    '        for alias in node.names:\n'
    '            if alias.asname:\n'
    '                parts.append(f"{alias.name} as {alias.asname}")\n'
    '            else:\n'
    '                parts.append(alias.name)\n'
    '        return "import " + ", ".join(parts)\n'
    '    if isinstance(node, ast.ImportFrom):\n'
    '        module = node.module or ""\n'
    '        parts = []\n'
    '        for alias in node.names:\n'
    '            if alias.asname:\n'
    '                parts.append(f"{alias.name} as {alias.asname}")\n'
    '            else:\n'
    '                parts.append(alias.name)\n'
    '        level_dots = "." * (node.level or 0)\n'
    '        module_str = level_dots + module if module else level_dots\n'
    '        return f"from {module_str} import " + ", ".join(parts)\n'
    '    return "<unknown import>"\n'
    '\n'
    '\n'
    'def inspect_file(path):\n'
    '    try:\n'
    '        source = path.read_text(encoding="utf-8")\n'
    '    except UnicodeDecodeError:\n'
    '        source = path.read_text(encoding="utf-8", errors="ignore")\n'
    '    try:\n'
    '        tree = ast.parse(source, filename=str(path))\n'
    '    except SyntaxError as e:\n'
    '        print(f"[WARN] Skipping {path} (syntax error: {e})")\n'
    '        return []\n'
    '    visitor = ImportVisitor()\n'
    '    visitor.visit(tree)\n'
    '    results = []\n'
    '    for node in visitor.non_top_level_imports:\n'
    '        lineno = getattr(node, "lineno", "?")\n'
    '        results.append((lineno, format_import(node)))\n'
    '    return results\n'
    '\n'
    '\n'
    'def main():\n'
    '    root = Path.cwd()\n'
    '    any_found = False\n'
    '    for py_file in find_python_files(root):\n'
    '        imports = inspect_file(py_file)\n'
    '        if not imports:\n'
    '            continue\n'
    '        any_found = True\n'
    '        print(f"\\n{py_file}:")\n'
    '        for lineno, stmt in imports:\n'
    '            print(f"  line {lineno}: {stmt}")\n'
    '    if not any_found:\n'
    '        print("No non-top-level imports found.")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_IMPORT_COLLECTOR_SOURCE: str = (
    'import ast\n'
    'import importlib.metadata\n'
    'import importlib.util\n'
    'import sys\n'
    'from pathlib import Path\n'
    'from dh import is_python_file\n'
    '\n'
    'PACKAGE_MAPPING = {\n'
    '    "cv2": "opencv-python",\n'
    '    "PIL": "Pillow",\n'
    '    "sklearn": "scikit-learn",\n'
    '    "yaml": "PyYAML",\n'
    '    "google": "google-cloud-storage",\n'
    '    "dotenv": "python-dotenv",\n'
    '    "bs4": "beautifulsoup4",\n'
    '    "fitz": "pymupdf",\n'
    '    "skimage": "scikit-image",\n'
    '    "telegram": "python-telegram-bot",\n'
    '    "dateutil": "python-dateutil",\n'
    '    "git": "GitPython",\n'
    '    "jwt": "PyJWT",\n'
    '    "OpenGL": "PyOpenGL",\n'
    '}\n'
    '\n'
    '\n'
    'def get_imports_from_file(path):\n'
    '    imports = set()\n'
    '    try:\n'
    '        with Path(path).open(encoding="utf-8") as f:\n'
    '            tree = ast.parse(f.read(), filename=str(path))\n'
    '        for node in ast.walk(tree):\n'
    '            if isinstance(node, ast.Import):\n'
    '                imports.update(n.name.split(".")[0] for n in node.names)\n'
    '            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:\n'
    '                imports.add(node.module.split(".")[0])\n'
    '    except (SyntaxError, UnicodeDecodeError):\n'
    '        pass\n'
    '    return imports\n'
    '\n'
    '\n'
    'def check_status(module_name):\n'
    '    try:\n'
    '        importlib.metadata.distribution(module_name)\n'
    '        return True\n'
    '    except importlib.metadata.PackageNotFoundError:\n'
    '        spec = importlib.util.find_spec(module_name)\n'
    '        return spec is not None\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path()\n'
    '    output_file = cwd / "importz.txt"\n'
    '    pip_script = cwd / "install_deps.sh"\n'
    '    all_imports = set()\n'
    '    local_names = {p.stem for p in cwd.glob("*.py")}\n'
    '    local_names.update({p.name for p in cwd.iterdir() if p.is_dir() and (p / "__init__.py").exists()})\n'
    '    std_libs = getattr(sys, "stdlib_module_names", set())\n'
    '    for path in cwd.rglob("*"):\n'
    '        if is_python_file(path) and path.name not in {"importz.txt", "install_deps.sh"}:\n'
    '            all_imports.update(get_imports_from_file(path))\n'
    '    third_party = [imp for imp in all_imports if imp not in std_libs and imp not in local_names and imp != "__future__"]\n'
    '    missing_for_pip = []\n'
    '    already_installed = []\n'
    '    for imp in sorted(third_party):\n'
    '        if check_status(imp):\n'
    '            already_installed.append(imp)\n'
    '        else:\n'
    '            pip_name = PACKAGE_MAPPING.get(imp, imp)\n'
    '            missing_for_pip.append(pip_name)\n'
    '    if third_party:\n'
    '        output_file.write_text("\\n".join(sorted(third_party)), encoding="utf-8")\n'
    '        print(f"✅ Found {len(third_party)} 3rd-party dependencies.")\n'
    '        if already_installed:\n'
    '            print(f"📦 Already installed: {\', \'.join(already_installed)}")\n'
    '        if missing_for_pip:\n'
    '            install_cmd = f"pip install {\' \'.join(missing_for_pip)}"\n'
    '            pip_script.write_text(f"#!/bin/sh\\n{install_cmd}\\n", encoding="utf-8")\n'
    '            pip_script.chmod(pip_script.stat().st_mode | 73)\n'
    '            print(f"⚠️  Missing: {\', \'.join(missing_for_pip)}")\n'
    '            print(f"🚀 Run this to install missing: ./{pip_script.name}")\n'
    '        else:\n'
    '            if pip_script.exists():\n'
    '                pip_script.unlink()\n'
    '            print("✨ Environment is fully satisfied!")\n'
    '    else:\n'
    '        print("ℹ️ No 3rd-party imports found.")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_IMPORTZ_SOURCE: str = (
    'import ast\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def is_python_file(path):\n'
    '    if path.suffix == ".py":\n'
    '        return True\n'
    '    if path.is_file() and not path.suffix:\n'
    '        try:\n'
    '            with Path(path).open(encoding="utf-8") as f:\n'
    '                first_line = f.readline()\n'
    '                return "python" in first_line\n'
    '        except Exception:\n'
    '            return False\n'
    '    return False\n'
    '\n'
    '\n'
    'def get_imports_from_file(path):\n'
    '    imports = set()\n'
    '    try:\n'
    '        with Path(path).open(encoding="utf-8") as f:\n'
    '            tree = ast.parse(f.read(), filename=str(path))\n'
    '        for node in ast.walk(tree):\n'
    '            if isinstance(node, ast.Import):\n'
    '                imports.update(n.name.split(".")[0] for n in node.names)\n'
    '            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:\n'
    '                imports.add(node.module.split(".")[0])\n'
    '    except (SyntaxError, UnicodeDecodeError):\n'
    '        pass\n'
    '    return imports\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path()\n'
    '    output_file = cwd / "importz.txt"\n'
    '    all_imports = set()\n'
    '    local_names = {p.stem for p in cwd.glob("*.py")}\n'
    '    local_names.update({p.name for p in cwd.iterdir() if p.is_dir() and (p / "__init__.py").exists()})\n'
    '    std_libs = getattr(sys, "stdlib_module_names", set())\n'
    '    for path in cwd.rglob("*"):\n'
    '        if is_python_file(path) and path.name != "importz.txt":\n'
    '            all_imports.update(get_imports_from_file(path))\n'
    '    third_party = sorted([\n'
    '        imp for imp in all_imports if imp not in std_libs and imp not in local_names and imp != "__future__"\n'
    '    ])\n'
    '    if third_party:\n'
    '        output_file.write_text("\\n".join(third_party), encoding="utf-8")\n'
    '        print(f"✅ Saved {len(third_party)} 3rd-party imports to {output_file}")\n'
    '    else:\n'
    '        print("ℹ️ No 3rd-party imports found.")\n'
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


class ExImportsTool(BaseTool):
    """Wrapper for original ex_imports.py: process_file() + 1 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'ex_imports'
    source_file: str = 'ex_imports.py'
    description: str = 'process_file() + 1 more'
    functions: list[str] = ['process_file', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _EX_IMPORTS_SOURCE

class EximportsTool(BaseTool):
    """Wrapper for original eximports.py: _make_parser() + 7 more."""
    name: str = 'eximports'
    source_file: str = 'eximports.py'
    description: str = '_make_parser() + 7 more'
    functions: list[str] = ['_make_parser', 'process_file', 'normalize_import', '_get_installed_pkgs', 'process_files_parallel', 'filter_imports', 'get_pyfiles', 'main']
    notes: str = ''
    source: str = _EXIMPORTS_SOURCE

class Eximports2Tool(BaseTool):
    """Wrapper for original eximports2.py: extract_file() + 1 more NOTE: no __main__ guard (top-level script or library fragment; exec runs top-level code)."""
    name: str = 'eximports2'
    source_file: str = 'eximports2.py'
    description: str = 'extract_file() + 1 more'
    functions: list[str] = ['extract_file', 'get_relative_path']
    notes: str = 'no __main__ guard (top-level script or library fragment; exec runs top-level code)'
    source: str = _EXIMPORTS2_SOURCE

class Eximports3Tool(BaseTool):
    """Wrapper for original eximports3.py: process_file() + 0 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'eximports3'
    source_file: str = 'eximports3.py'
    description: str = 'process_file() + 0 more'
    functions: list[str] = ['process_file']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _EXIMPORTS3_SOURCE

class FimportTool(BaseTool):
    """Wrapper for original fimport.py: find_python_files() + 3 more."""
    name: str = 'fimport'
    source_file: str = 'fimport.py'
    description: str = 'find_python_files() + 3 more'
    functions: list[str] = ['find_python_files', 'format_import', 'inspect_file', 'main']
    notes: str = ''
    source: str = _FIMPORT_SOURCE

class ImportCollectorTool(BaseTool):
    """Wrapper for original import_collector.py: get_imports_from_file() + 2 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'import_collector'
    source_file: str = 'import_collector.py'
    description: str = 'get_imports_from_file() + 2 more'
    functions: list[str] = ['get_imports_from_file', 'check_status', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _IMPORT_COLLECTOR_SOURCE

class ImportzTool(BaseTool):
    """Wrapper for original importz.py: is_python_file() + 2 more."""
    name: str = 'importz'
    source_file: str = 'importz.py'
    description: str = 'is_python_file() + 2 more'
    functions: list[str] = ['is_python_file', 'get_imports_from_file', 'main']
    notes: str = ''
    source: str = _IMPORTZ_SOURCE

class ExtractImportsPyUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'ex_imports': ExImportsTool,
        'eximports': EximportsTool,
        'eximports2': Eximports2Tool,
        'eximports3': Eximports3Tool,
        'fimport': FimportTool,
        'import_collector': ImportCollectorTool,
        'importz': ImportzTool,
    }

    @classmethod
    def list_tools(cls: type[ExtractImportsPyUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[ExtractImportsPyUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[ExtractImportsPyUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for extract_imports_py (7 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[ExtractImportsPyUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[ExtractImportsPyUnified], argv: Sequence[str] | None = None) -> int:
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
    return ExtractImportsPyUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

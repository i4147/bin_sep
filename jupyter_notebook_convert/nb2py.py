import sys
from collections.abc import Iterable, Sequence
from multiprocessing import Pool
from pathlib import Path
from typing import List, Optional
import nbformat
from loguru import logger
from nbformat import NotebookNode
POOL_SIZE = 8
MAGIC_PREFIXES = ("%", "!", "%%")
IMPORT_PREFIXES = ("import ", "from ")
def is_import_line(line):
    return line.startswith(IMPORT_PREFIXES)
def strip_magics(source):
    lines = source.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if stripped.startswith(MAGIC_PREFIXES):
            result.append(f"# [MAGIC] {line.rstrip()}")
            while i < len(lines) - 1 and line.rstrip().endswith("\\"):
                i += 1
                line = lines[i]
                result.append(f"# [MAGIC] {line.rstrip()}")
        else:
            result.append(line)
        i += 1
    return "\n".join(result)
def nb2py(notebook):
    imports = []
    os_mods = []
    sys_mods = []
    main_code = []
    for cell in notebook.cells:
        if cell.cell_type == "markdown":
            md_text = str(cell.source).replace("\n", "\n# ")
            main_code.append(f"# {md_text}\n")
        elif cell.cell_type == "code":
            cell_code = str(cell.source)
            for line in cell_code.split("\n"):
                if line.strip().startswith("!nb2py"):
                    continue
                if is_import_line(line):
                    imports.append(line)
                    continue
                if line.startswith("os.environ"):
                    os_mods.append(line)
                    continue
                if line.startswith("sys.path"):
                    sys_mods.append(line)
                    continue
                cleaned = strip_magics(line)
                main_code.append(cleaned)
    line = ""
    for idx, line in enumerate(imports):
        if "import os" in line or "from os import" in line:
            for mod in sorted(os_mods, reverse=True):
                imports.insert(idx + 1, mod)
            break
    for idx, line in enumerate(imports):
        if "import sys" in line or "from sys import" in line:
            for mod in sorted(sys_mods, reverse=True):
                imports.insert(idx + 1, mod)
            break
    imports_str = "\n".join(imports) + "\n\n"
    main_str = "\n".join(main_code)
    indent = "    "
    main_indented = "\n".join(f"{indent}{ln}" for ln in main_str.split("\n"))
    return f"{imports_str}if __name__ == '__main__':\n{main_indented}"
def process_file(path):
    path = Path(path)
    fo = path.with_suffix(".py")
    if fo.exists():
        return None
    with path.open(encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)
    py_code = nb2py(nb)
    with fo.open("w", encoding="utf-8") as out:
        out.write(py_code)
    return f"Exported → {fo.name}"
def _collect_files(args):
    if not args:
        return list(Path.cwd().rglob("*.ipynb"))
    files = []
    for arg in args:
        p = Path(arg)
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(p.rglob("*.ipynb"))
    return files
def main(argv=None):
    args = list(argv) if argv is not None else sys.argv[1:]
    files = _collect_files(args)
    if not files:
        logger.info("No .ipynb files found")
        return 0
    logger.info(
        "Found {} notebook(s) to convert using {} workers", len(files), POOL_SIZE
    )
    with Pool(processes=POOL_SIZE) as pool:
        results = [pool.apply_async(process_file, (f,)) for f in files]
        for result in results:
            message = result.get()
            if message:
                logger.info("{}", message)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())

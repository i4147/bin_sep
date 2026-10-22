import sys
from collections.abc import Iterable
from importlib.metadata import distributions
from multiprocessing import Pool
from pathlib import Path
from typing import Final, List, Optional, Set
import tree_sitter_python as tsp
from loguru import logger
from tree_sitter import Language, Parser

POOL_SIZE = 8
OUTPUT_FILE = "importz.txt"
VALID_NODE_TYPES = frozenset({"import_statement", "import_from_statement"})
STDLIB = frozenset(getattr(sys, "stdlib_module_names", ()))


def _make_parser():
    parser = Parser()
    parser.language = Language(tsp.language())
    return parser


def process_file(path):
    file_path = Path(path)
    src = file_path.read_bytes()
    parser = _make_parser()
    tree = parser.parse(src)
    root = tree.root_node
    results = []
    child = None
    for child in root.children:
        if child.type in VALID_NODE_TYPES:
            results.append(src[child.start_byte : child.end_byte].decode())
    return results


def normalize_import(import_line):
    line = import_line.lower().strip()
    if line.startswith("import "):
        module = line[7:]
        if " as " in module:
            module = module[: module.index(" as ")]
        if "." in module:
            module = module[: module.index(".")]
        return module if module and not module.startswith("_") else None
    if line.startswith("from "):
        module = line[5:]
        if module.startswith("."):
            return None
        if " import" in module:
            module = module[: module.index(" import")]
        if " as " in module:
            module = module[: module.index(" as ")]
        if "." in module:
            module = module[: module.index(".")]
        return module if module and not module.startswith("_") else None
    return None


def _get_installed_pkgs():
    pkgs = set()
    dist = None
    for dist in distributions():
        name = None
        try:
            name = dist.metadata["Name"]
        except Exception:
            name = None
        if name:
            pkgs.add(name.replace("-", "_").lower())
    return pkgs


def process_files_parallel(files):
    all_imports = set()
    if not files:
        return all_imports
    with Pool(processes=POOL_SIZE) as pool:
        for result in pool.imap_unordered(process_file, files):
            all_imports.update(result)
    return all_imports


def filter_imports(imports):
    installed_pkgs = _get_installed_pkgs()
    excluded = set(STDLIB) | installed_pkgs
    filtered = []
    for imp in imports:
        normalized = normalize_import(imp)
        if normalized and normalized not in excluded:
            filtered.append(normalized + "\n")
    return sorted(set(filtered))


def get_pyfiles(root):
    return [p for p in root.rglob("*.py") if p.is_file()]


def main(argv=None):
    _ = list(argv) if argv is not None else sys.argv[1:]
    outfile = Path(OUTPUT_FILE)
    cwd = Path.cwd()
    pyfiles = get_pyfiles(cwd)
    logger.info("{} python files found", len(pyfiles))
    all_imports = process_files_parallel(pyfiles)
    filtered_imports = filter_imports(all_imports)
    outfile.write_text("".join(filtered_imports), encoding="utf-8")
    for imp in filtered_imports:
        logger.info("{}", imp.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

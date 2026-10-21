#!/usr/bin/env python3
"""MergeSplitPythonPkgUnified for merge_split_python_pkg.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (4):
  merge_pkg <- merge_pkg.py (147L): parse_module() + 3 more
  mergepy <- mergepy.py (33L): resolve_imports() + 1 more
  prefactor <- prefactor.py (282L): find_py_files() + 6 more
  unmerger <- unmerger.py (52L): parse_merged_file() + 2 more

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

_MERGE_PKG_SOURCE: str = (
    'import ast\n'
    'import base64\n'
    'import json\n'
    'import os\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'class Module:\n'
    '    def __init__(self, name, path):\n'
    '        self.name = name\n'
    '        self.path = path\n'
    '        self.imports = []\n'
    '        self.functions = []\n'
    '        self.classes = []\n'
    '        self.assignments = []\n'
    '        self.main_body = []\n'
    '        self.dunder_all = None\n'
    '\n'
    '\n'
    'def parse_module(module):\n'
    '    source = module.path.read_text(encoding="utf-8")\n'
    '    tree = ast.parse(source, filename=str(module.path))\n'
    '    for node in tree.body:\n'
    '        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):\n'
    '            module.dunder_all = node\n'
    '            module.assignments.append(node)\n'
    '            continue\n'
    '        if isinstance(node, (ast.Import, ast.ImportFrom)):\n'
    '            module.imports.append(node)\n'
    '            continue\n'
    '        if isinstance(node, ast.If):\n'
    '            test = ast.unparse(node.test)\n'
    '            if "__name__" in test and "__main__" in test:\n'
    '                module.main_body.extend(node.body)\n'
    '                continue\n'
    '        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n'
    '            module.functions.append(node)\n'
    '        elif isinstance(node, ast.ClassDef):\n'
    '            module.classes.append(node)\n'
    '        else:\n'
    '            module.assignments.append(node)\n'
    '\n'
    '\n'
    'def resolve_imports(modules, root_pkg_name):\n'
    '    final_imports = []\n'
    '    for mod in modules.values():\n'
    '        for imp in mod.imports:\n'
    '            if isinstance(imp, ast.ImportFrom) and imp.level > 0:\n'
    '                parts = mod.name.split(".")\n'
    '                if imp.level > 1:\n'
    '                    base_parts = parts[: -(imp.level - 1)]\n'
    '                else:\n'
    '                    base_parts = parts[:-1]\n'
    '                base_pkg = ".".join(base_parts)\n'
    '                if imp.module:\n'
    '                    abs_module = f"{base_pkg}.{imp.module}" if base_pkg else imp.module\n'
    '                else:\n'
    '                    abs_module = base_pkg\n'
    '                imp.module = abs_module\n'
    '                imp.level = 0\n'
    '                if abs_module == root_pkg_name and not imp.names[0].name == "*":\n'
    '                    new_imports = []\n'
    '                    for alias in imp.names:\n'
    '                        new_imports.append(\n'
    '                            ast.parse(f"import {root_pkg_name}.{alias.name} as {alias.asname or alias.name}").body[0]\n'
    '                        )\n'
    '                    final_imports.extend(new_imports)\n'
    '                    continue\n'
    '            final_imports.append(imp)\n'
    '        mod.imports = []\n'
    '    return final_imports\n'
    '\n'
    '\n'
    'def package_assets(asset_dir, root_pkg_name):\n'
    '    assets = {}\n'
    '    for root, _, files in os.walk(asset_dir):\n'
    '        for f in files:\n'
    '            fp = Path(root) / f\n'
    '            rel_path = fp.relative_to(asset_dir.parent)\n'
    '            assets[str(rel_path)] = base64.b64encode(fp.read_bytes()).decode("utf-8")\n'
    '    assets_json = json.dumps(assets, indent=4)\n'
    '    loader_code = f"""\n'
    'import os, base64, tempfile\n'
    '_ASSETS = {assets_json}\n'
    '_TEMP_DIR = tempfile.mkdtemp()\n'
    'for _rel_path, _b64 in _ASSETS.items():\n'
    '    _abs_path = os.path.join(_TEMP_DIR, _rel_path)\n'
    '    os.makedirs(os.path.dirname(_abs_path), exist_ok=True)\n'
    "    with open(_abs_path, 'wb') as _f:\n"
    '        _f.write(base64.b64decode(_b64))\n'
    '_orig_open = open\n'
    "def _patched_open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):\n"
    '    _str_file = str(file)\n'
    '    if isinstance(file, str) and (_str_file.startswith("{root_pkg_name}/") or _str_file.startswith("{root_pkg_name}\\\\\\\\")):\n'
    '        _new_path = os.path.join(_TEMP_DIR, _str_file)\n'
    '        return _orig_open(_new_path, mode, buffering, encoding, errors, newline, closefd, opener)\n'
    '    return _orig_open(file, mode, buffering, encoding, errors, newline, closefd, opener)\n'
    'import builtins\n'
    'builtins.open = _patched_open\n'
    '"""\n'
    '    return ast.parse(loader_code).body\n'
    '\n'
    '\n'
    'def merge_package(project_dir, output_file):\n'
    '    project_path = Path(project_dir).resolve()\n'
    '    root_pkg_name = project_path.name\n'
    '    py_files = list(project_path.rglob("*.py"))\n'
    '    asset_dir = project_path / "assets"\n'
    '    modules = {}\n'
    '    for py_file in py_files:\n'
    '        if py_file.name == "__pycache__":\n'
    '            continue\n'
    '        rel_path = py_file.relative_to(project_path.parent)\n'
    '        mod_name = ".".join(rel_path.with_suffix("").parts)\n'
    '        mod_name = mod_name.removesuffix(".__init__")\n'
    '        mod = Module(mod_name, py_file)\n'
    '        parse_module(mod)\n'
    '        modules[mod_name] = mod\n'
    '    all_imports = resolve_imports(modules, root_pkg_name)\n'
    '    asset_nodes = []\n'
    '    if asset_dir.exists():\n'
    '        asset_nodes = package_assets(asset_dir, root_pkg_name)\n'
    '    final_body = []\n'
    '    final_body.extend(asset_nodes)\n'
    '    final_body.extend(all_imports)\n'
    '    for mod in modules.values():\n'
    '        final_body.extend(mod.assignments)\n'
    '    for mod in modules.values():\n'
    '        final_body.extend(mod.classes)\n'
    '    for mod in modules.values():\n'
    '        final_body.extend(mod.functions)\n'
    '    for mod in modules.values():\n'
    '        if mod.main_body:\n'
    '            final_body.append(ast.parse("if __name__ == \'__main__\':").body[0])\n'
    '            final_body[-1].body = mod.main_body\n'
    '    header = f\'"""Single-file build of {root_pkg_name}"""\\n\'\n'
    '    final_code = header + ast.unparse(ast.Module(body=final_body, type_ignores=[]))\n'
    '    Path(output_file).write_text(final_code, encoding="utf-8")\n'
    '    print(f"Successfully merged {root_pkg_name} into {output_file}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) < 3:\n'
    '        print("Usage: python merge_package.py <project_dir> <output_file>")\n'
    '        sys.exit(1)\n'
    '    merge_package(sys.argv[1], sys.argv[2])\n'
)

_MERGEPY_SOURCE: str = (
    'import os\n'
    'import re\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def resolve_imports(content, cwd):\n'
    '    folder_name = Path(cwd).name\n'
    '    content = re.sub(r"from \\. import ([a-zA-Z0-9_]+)", f"from {folder_name} import \\\\1", content)\n'
    '    content = re.sub(\n'
    '        r"from \\.([a-zA-Z0-9_]+) import ([a-zA-Z0-9_]+)",\n'
    '        f"from {folder_name}.\\\\1 import \\\\2",\n'
    '        content,\n'
    '    )\n'
    '    return re.sub(r"import \\.", f"import {folder_name}", content)\n'
    '\n'
    '\n'
    'def merge_python_files():\n'
    '    cwd = Path.cwd()\n'
    '    folder_name = Path(cwd).name\n'
    '    output_filename = f"{folder_name}.py"\n'
    '    py_files = [f for f in os.listdir(cwd) if f.endswith(".py") and f != output_filename]\n'
    '    py_files.sort()\n'
    '    with Path(output_filename).open("w", encoding="utf-8") as outfile:\n'
    '        for py_file in py_files:\n'
    '            with Path(py_file).open(encoding="utf-8") as infile:\n'
    '                content = infile.read()\n'
    '                content = resolve_imports(content, cwd)\n'
    '                outfile.write(content)\n'
    '    print(f"Merged {len(py_files)} files into {output_filename}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    merge_python_files()\n'
)

_PREFACTOR_SOURCE: str = (
    'import argparse\n'
    'import ast\n'
    'import sys\n'
    'from collections import deque\n'
    'from dataclasses import dataclass\n'
    'from multiprocessing import Pool, cpu_count\n'
    'from pathlib import Path\n'
    '\n'
    'MAX_DEFAULT = 10\n'
    '\n'
    '\n'
    '@dataclass\n'
    'class ModuleInfo:\n'
    '    pass\n'
    '\n'
    '\n'
    'def find_py_files(root, exclude=None):\n'
    '    files = []\n'
    '    for p in sorted(root.rglob("*.py")):\n'
    '        if "__pycache__" in p.parts:\n'
    '            continue\n'
    '        if exclude:\n'
    '            try:\n'
    '                if p.resolve().is_relative_to(exclude.resolve()):\n'
    '                    continue\n'
    '            except Exception:\n'
    '                if str(p.resolve()).startswith(str(exclude.resolve())):\n'
    '                    continue\n'
    '        files.append(p)\n'
    '    return files\n'
    '\n'
    '\n'
    'def module_fullname_for_path(root, path, package_mode, package_name):\n'
    '    rel = path.relative_to(root)\n'
    '    parts = list(rel.with_suffix("").parts)\n'
    '    if parts and parts[-1] == "__init__":\n'
    '        parts = parts[:-1]\n'
    '        if package_mode:\n'
    '            return package_name if package_name else root.name\n'
    '        else:\n'
    '            return ".".join(parts) if parts else root.name\n'
    '    elif package_mode:\n'
    '        prefix = package_name if package_name else root.name\n'
    '        return ".".join([prefix] + parts)\n'
    '    else:\n'
    '        return ".".join(parts)\n'
    '\n'
    '\n'
    'def resolve_relative_import(curr_fullname, module, level):\n'
    '    if level == 0:\n'
    '        return module\n'
    '    cur_parts = curr_fullname.split(".")\n'
    '    parent_parts = cur_parts[:-1]\n'
    '    if level - 1 > len(parent_parts):\n'
    '        return None\n'
    '    target_parts = parent_parts[: len(parent_parts) - (level - 1)]\n'
    '    if module:\n'
    '        target_parts += module.split(".")\n'
    '    if not target_parts:\n'
    '        return None\n'
    '    return ".".join(target_parts)\n'
    '\n'
    '\n'
    'def analyze_file(args):\n'
    '    path, root, package_mode, package_name, full_map = args\n'
    '    src = path.read_text(encoding="utf8")\n'
    '    try:\n'
    '        tree = ast.parse(src)\n'
    '    except SyntaxError:\n'
    '        return ModuleInfo(path=path, fullname="", source=src, deps=set())\n'
    '    fullname = module_fullname_for_path(root, path, package_mode, package_name)\n'
    '    deps = set()\n'
    '    for node in ast.walk(tree):\n'
    '        if isinstance(node, ast.Import):\n'
    '            for alias in node.names:\n'
    '                name = alias.name\n'
    '                if package_mode:\n'
    '                    prefix = package_name if package_name else root.name\n'
    '                    if name == prefix or name.startswith(prefix + "."):\n'
    '                        deps.add(name)\n'
    '                else:\n'
    '                    base = name.split(".")[0]\n'
    '                    if base in full_map:\n'
    '                        deps.add(name)\n'
    '        elif isinstance(node, ast.ImportFrom):\n'
    '            mod = node.module\n'
    '            level = node.level or 0\n'
    '            resolved = resolve_relative_import(fullname, mod, level)\n'
    '            if resolved:\n'
    '                deps.add(resolved)\n'
    '            elif package_mode and mod:\n'
    '                prefix = package_name if package_name else root.name\n'
    '                if mod == prefix or mod.startswith(prefix + "."):\n'
    '                    deps.add(mod)\n'
    '    normalized = set()\n'
    '    for d in deps:\n'
    '        if d in full_map:\n'
    '            normalized.add(d)\n'
    '        else:\n'
    '            for candidate in full_map:\n'
    '                if candidate == d or candidate.startswith(d + ".") or d.startswith(candidate + "."):\n'
    '                    normalized.add(candidate)\n'
    '    return ModuleInfo(path=path, fullname=fullname, source=src, deps=normalized)\n'
    '\n'
    '\n'
    'def topological_sort(\n'
    '    modules,\n'
    '):\n'
    '    edges = {name: set(info.deps) for name, info in modules.items()}\n'
    '    for name in edges:\n'
    '        edges[name] = {d for d in edges[name] if d in modules}\n'
    '    in_deg = {n: len(ds) for n, ds in edges.items()}\n'
    '    q = deque([n for n, deg in in_deg.items() if deg == 0])\n'
    '    ordered = []\n'
    '    while q:\n'
    '        n = q.popleft()\n'
    '        ordered.append(n)\n'
    '        for m, ds in edges.items():\n'
    '            if n in ds:\n'
    '                ds.remove(n)\n'
    '                in_deg[m] -= 1\n'
    '                if in_deg[m] == 0:\n'
    '                    q.append(m)\n'
    '    cycles = []\n'
    '    if len(ordered) != len(edges):\n'
    '        remaining = set(edges) - set(ordered)\n'
    '        ordered += sorted(remaining)\n'
    '        cycles = [remaining]\n'
    '    return ordered, cycles\n'
    '\n'
    '\n'
    'def build_merged_source(modules, ordered, out_module_name):\n'
    '    lines = []\n'
    '    lines.append("# Auto-generated single-file package by merge_to_single.py")\n'
    '    lines.append(f"# Reconstructed modules: {\', \'.join(ordered)}")\n'
    '    lines.append("import sys, types")\n'
    '    lines.append("")\n'
    '    lines.append("_orig_sources = {")\n'
    '    for name in ordered:\n'
    '        src = modules[name].source\n'
    '        lines.append(f"    {name!r}: {src!r},")\n'
    '    lines.append("}")\n'
    '    lines.append("")\n'
    '    lines.append("def get_original_source(module_name):")\n'
    '    lines.append(\'    """Return the original source (as a string) for a merged module, or None."""\')\n'
    '    lines.append("    return _orig_sources.get(module_name)")\n'
    '    lines.append("")\n'
    '    lines.append("# Pre-create module objects and insert into sys.modules")\n'
    '    lines.append("for _name in _orig_sources:")\n'
    '    lines.append("    mod = types.ModuleType(_name)")\n'
    '    lines.append(\'    mod.__file__ = f"<merged:{_name}>"\')\n'
    '    lines.append("    mod.__package__ = _name.rpartition(\'.\')[0]")\n'
    '    lines.append("    sys.modules[_name] = mod")\n'
    '    lines.append("")\n'
    '    lines.append("_order = [")\n'
    '    for name in ordered:\n'
    '        lines.append(f"    {name!r},")\n'
    '    lines.append("]")\n'
    '    lines.append("")\n'
    '    lines.append("for _name in _order:")\n'
    '    lines.append("    src = _orig_sources[_name]")\n'
    '    lines.append("    mod = sys.modules[_name]")\n'
    '    lines.append("    # compile with a synthetic filename so tracebacks mention the original module name")\n'
    '    lines.append("    exec(compile(src, f\\"<merged:{_name}>\\", \'exec\'), mod.__dict__)")\n'
    '    lines.append("")\n'
    '    if out_module_name in modules:\n'
    '        lines.append("try:")\n'
    '        lines.append(f"    import {out_module_name} as _top")\n'
    '        lines.append("    # re-export public names (non-underscore) into the merged-file global namespace")\n'
    '        lines.append("    for _k, _v in vars(_top).items():")\n'
    '        lines.append("        if not _k.startswith(\'_\'):")\n'
    '        lines.append("            globals()[_k] = _v")\n'
    '        lines.append("except Exception:")\n'
    '        lines.append("    # best-effort; ignore runtime errors during re-export")\n'
    '        lines.append("    pass")\n'
    '    lines.append("")\n'
    '    lines.append("# End of merged package")\n'
    '    return "\\n".join(lines)\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(description="Merge a small Python library into a single-file package.")\n'
    '    parser.add_argument(\n'
    '        "input",\n'
    '        nargs="?",\n'
    '        type=Path,\n'
    '        default=Path.cwd(),\n'
    '        help="Input directory containing .py files or a package. Defaults to current directory.",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "output_dir",\n'
    '        nargs="?",\n'
    '        type=Path,\n'
    '        default=Path.cwd() / "out",\n'
    '        help="Directory to write merged file to. Defaults to ./out.",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--out-name",\n'
    '        type=str,\n'
    '        default=None,\n'
    '        help="Output filename (defaults to <pkg>_single.py).",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--max-files",\n'
    '        type=int,\n'
    '        default=MAX_DEFAULT,\n'
    '        help="Max number of files allowed (default: 10).",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--package-name",\n'
    '        type=str,\n'
    '        default=None,\n'
    '        help="Force package name (defaults to input folder name if package).",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--force",\n'
    '        action="store_true",\n'
    '        help="Force merge even if file count > max-files.",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-j",\n'
    '        "--jobs",\n'
    '        type=int,\n'
    '        default=0,\n'
    '        help="Number of worker processes to use (default: auto cpu count).",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    root = args.input.resolve()\n'
    '    if not root.exists() or not root.is_dir():\n'
    '        print("Input must be an existing directory.", file=sys.stderr)\n'
    '        sys.exit(2)\n'
    '    out_dir = args.output_dir.resolve()\n'
    '    out_dir.mkdir(parents=True, exist_ok=True)\n'
    '    files = find_py_files(root, exclude=out_dir)\n'
    '    if not files:\n'
    '        print("No Python files found under input directory.", file=sys.stderr)\n'
    '        sys.exit(2)\n'
    '    package_mode = (root / "__init__.py").exists()\n'
    '    package_name = args.package_name if args.package_name else root.name if package_mode else None\n'
    '    if len(files) > args.max_files and not args.force:\n'
    '        print(\n'
    '            f"Found {len(files)} files which is > {args.max_files}. Use --force to override.",\n'
    '            file=sys.stderr,\n'
    '        )\n'
    '        sys.exit(2)\n'
    '    full_map_candidates = {}\n'
    '    for p in files:\n'
    '        name = module_fullname_for_path(root, p, package_mode, package_name)\n'
    '        full_map_candidates[name] = p\n'
    '    pool_args = [(p, root, package_mode, package_name, full_map_candidates) for p in files]\n'
    '    if args.jobs and args.jobs > 0:\n'
    '        workers = min(args.jobs, max(1, len(files)))\n'
    '    else:\n'
    '        workers = min(cpu_count(), max(1, len(files)))\n'
    '    if workers == 1:\n'
    '        results = list(map(analyze_file, pool_args))\n'
    '    else:\n'
    '        with Pool(processes=workers) as pool:\n'
    '            results = pool.map(analyze_file, pool_args)\n'
    '    modules = {}\n'
    '    for mi in results:\n'
    '        if not mi.fullname:\n'
    '            mi.fullname = module_fullname_for_path(root, mi.path, package_mode, package_name)\n'
    '        modules[mi.fullname] = mi\n'
    '    ordered, cycles = topological_sort(modules)\n'
    '    if cycles:\n'
    '        print(\n'
    '            "Warning: cycles detected among modules; attempting best-effort merge.",\n'
    '            file=sys.stderr,\n'
    '        )\n'
    '    out_name = args.out_name or f"{package_name or root.name}_single.py"\n'
    '    out_path = out_dir / out_name\n'
    '    merged = build_merged_source(modules, ordered, package_name or root.name)\n'
    '    out_path.write_text(merged, encoding="utf8")\n'
    '    print(f"Wrote merged file to: {out_path}")\n'
    '    print(f"Modules merged ({len(modules)}): {\', \'.join(ordered)}")\n'
    '    if cycles:\n'
    '        print("Cycles (approx):", cycles)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_UNMERGER_SOURCE: str = (
    'import re\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def parse_merged_file(path):\n'
    '    with open(path, "r") as f:\n'
    '        content = f.read()\n'
    '    pattern = r"^# File: (.+?)$"\n'
    '    parts = re.split(pattern, content, flags=re.MULTILINE)\n'
    '    files = {}\n'
    '    for i in range(1, len(parts), 2):\n'
    '        if i + 1 < len(parts):\n'
    '            path = parts[i].strip()\n'
    '            file_content = parts[i + 1].lstrip("\\n").rstrip()\n'
    '            files[path] = file_content\n'
    '    return files\n'
    '\n'
    '\n'
    'def get_unique_path(path):\n'
    '    path = Path(path)\n'
    '    if not path.exists():\n'
    '        return path\n'
    '    stem = path.stem\n'
    '    suffix = path.suffix\n'
    '    parent = path.parent\n'
    '    counter = 1\n'
    '    while True:\n'
    '        new_name = f"{stem}_{counter}{suffix}"\n'
    '        new_path = parent / new_name\n'
    '        if not new_path.exists():\n'
    '            return new_path\n'
    '        counter += 1\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python script.py <input_file>")\n'
    '        sys.exit(1)\n'
    '    input_file = sys.argv[1]\n'
    '    files = parse_merged_file(input_file)\n'
    '    for path, file_content in files.items():\n'
    '        path = Path(path)\n'
    '        path.parent.mkdir(parents=True, exist_ok=True)\n'
    '        unique_path = get_unique_path(path)\n'
    '        unique_path.write_text(file_content)\n'
    '        status = "Renamed to" if unique_path.name != path.name else "Created"\n'
    '        print(f"{status}: {unique_path}")\n'
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


class MergePkgTool(BaseTool):
    """Wrapper for original merge_pkg.py: parse_module() + 3 more."""
    name: str = 'merge_pkg'
    source_file: str = 'merge_pkg.py'
    description: str = 'parse_module() + 3 more'
    functions: list[str] = ['parse_module', 'resolve_imports', 'package_assets', 'merge_package']
    notes: str = ''
    source: str = _MERGE_PKG_SOURCE

class MergepyTool(BaseTool):
    """Wrapper for original mergepy.py: resolve_imports() + 1 more."""
    name: str = 'mergepy'
    source_file: str = 'mergepy.py'
    description: str = 'resolve_imports() + 1 more'
    functions: list[str] = ['resolve_imports', 'merge_python_files']
    notes: str = ''
    source: str = _MERGEPY_SOURCE

class PrefactorTool(BaseTool):
    """Wrapper for original prefactor.py: find_py_files() + 6 more."""
    name: str = 'prefactor'
    source_file: str = 'prefactor.py'
    description: str = 'find_py_files() + 6 more'
    functions: list[str] = ['find_py_files', 'module_fullname_for_path', 'resolve_relative_import', 'analyze_file', 'topological_sort', 'build_merged_source', 'main']
    notes: str = ''
    source: str = _PREFACTOR_SOURCE

class UnmergerTool(BaseTool):
    """Wrapper for original unmerger.py: parse_merged_file() + 2 more."""
    name: str = 'unmerger'
    source_file: str = 'unmerger.py'
    description: str = 'parse_merged_file() + 2 more'
    functions: list[str] = ['parse_merged_file', 'get_unique_path', 'main']
    notes: str = ''
    source: str = _UNMERGER_SOURCE

class MergeSplitPythonPkgUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'merge_pkg': MergePkgTool,
        'mergepy': MergepyTool,
        'prefactor': PrefactorTool,
        'unmerger': UnmergerTool,
    }

    @classmethod
    def list_tools(cls: type[MergeSplitPythonPkgUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[MergeSplitPythonPkgUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[MergeSplitPythonPkgUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for merge_split_python_pkg (4 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[MergeSplitPythonPkgUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[MergeSplitPythonPkgUnified], argv: Sequence[str] | None = None) -> int:
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
    return MergeSplitPythonPkgUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

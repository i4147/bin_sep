#!/usr/bin/env python3
"""CheckPyExportsUnified for check_py_exports.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (2):
  check_exports <- check_exports.py (279L): extract_definitions() + 6 more
  check_funcs <- check_funcs.py (135L): extract_definitions() + 3 more

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

_CHECK_EXPORTS_SOURCE: str = (
    'import argparse\n'
    'import ast\n'
    'from pathlib import Path\n'
    'from typing import Dict\n'
    'from loguru import logger\n'
    '\n'
    '\n'
    'def extract_definitions(path):\n'
    '    definitions = {"functions": [], "classes": [], "constants": []}\n'
    '    try:\n'
    '        with open(path, "r", encoding="utf-8") as f:\n'
    '            tree = ast.parse(f.read(), filename=str(path))\n'
    '    except (SyntaxError, UnicodeDecodeError) as e:\n'
    '        logger.error(f"Failed to parse {path}: {e}")\n'
    '        return definitions\n'
    '    except Exception as e:\n'
    '        logger.error(f"Unexpected error reading {path}: {e}")\n'
    '        return definitions\n'
    '    for node in tree.body:\n'
    '        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n'
    '            if not node.name.startswith("_"):\n'
    '                definitions["functions"].append(node.name)\n'
    '        elif isinstance(node, ast.ClassDef):\n'
    '            if not node.name.startswith("_"):\n'
    '                definitions["classes"].append(node.name)\n'
    '        elif isinstance(node, ast.Assign):\n'
    '            for target in node.targets:\n'
    '                if isinstance(target, ast.Name):\n'
    '                    name = target.id\n'
    '                    if name.isupper() and not name.startswith("_"):\n'
    '                        definitions["constants"].append(name)\n'
    '        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):\n'
    '            name = node.target.id\n'
    '            if name.isupper() and not name.startswith("_"):\n'
    '                definitions["constants"].append(name)\n'
    '    return definitions\n'
    '\n'
    '\n'
    'def extract_exports_from_init(init_path):\n'
    '    exported = set()\n'
    '    try:\n'
    '        with open(init_path, "r", encoding="utf-8") as f:\n'
    '            content = f.read()\n'
    '        tree = ast.parse(content, filename=str(init_path))\n'
    '    except (SyntaxError, UnicodeDecodeError) as e:\n'
    '        logger.error(f"Failed to parse {init_path}: {e}")\n'
    '        return exported\n'
    '    except Exception as e:\n'
    '        logger.error(f"Unexpected error reading {init_path}: {e}")\n'
    '        return exported\n'
    '    for node in tree.body:\n'
    '        if isinstance(node, ast.Assign):\n'
    '            for target in node.targets:\n'
    '                if isinstance(target, ast.Name) and target.id == "__all__":\n'
    '                    if isinstance(node.value, (ast.List, ast.Tuple)):\n'
    '                        for elt in node.value.elts:\n'
    '                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):\n'
    '                                exported.add(elt.value)\n'
    '        elif isinstance(node, ast.ImportFrom):\n'
    '            for alias in node.names:\n'
    '                if alias.name == "*":\n'
    '                    logger.warning(f"Wildcard import found in {init_path}")\n'
    '                    continue\n'
    '                exported.add(alias.asname or alias.name)\n'
    '        elif isinstance(node, ast.Import):\n'
    '            for alias in node.names:\n'
    '                name = alias.asname or alias.name.split(".")[0]\n'
    '                exported.add(name)\n'
    '    return exported\n'
    '\n'
    '\n'
    'def check_directory(directory=None):\n'
    '    if directory is None:\n'
    '        directory = Path.cwd()\n'
    '    init_path = directory / "__init__.py"\n'
    '    if not init_path.exists():\n'
    '        logger.error(f"No __init__.py found in {directory}")\n'
    '        return {}\n'
    '    print(f"Reading exports from {init_path}")\n'
    '    exported = extract_exports_from_init(init_path)\n'
    '    logger.debug(f"Found {len(exported)} exported names: {sorted(exported)}")\n'
    '    missing = {}\n'
    '    python_files = [f for f in directory.glob("*.py") if f.name != "__init__.py" and not f.name.startswith("_")]\n'
    '    if not python_files:\n'
    '        logger.warning(f"No Python module files found in {directory}")\n'
    '        return {}\n'
    '    for py_file in sorted(python_files):\n'
    '        logger.debug(f"Scanning {py_file.name}")\n'
    '        definitions = extract_definitions(py_file)\n'
    '        module_name = py_file.stem\n'
    '        file_missing = {"functions": [], "classes": [], "constants": []}\n'
    '        for category, names in definitions.items():\n'
    '            for name in names:\n'
    '                if name not in exported and module_name not in exported:\n'
    '                    file_missing[category].append(name)\n'
    '        if any(file_missing.values()):\n'
    '            missing[py_file.name] = file_missing\n'
    '    return missing\n'
    '\n'
    '\n'
    'def build_import_block(missing):\n'
    '    import_lines = []\n'
    '    all_names = []\n'
    '    for filename in sorted(missing.keys()):\n'
    '        module_name = Path(filename).stem\n'
    '        categories = missing[filename]\n'
    '        names = sorted(categories["classes"] + categories["constants"] + categories["functions"])\n'
    '        if not names:\n'
    '            continue\n'
    '        if len(names) == 1:\n'
    '            import_lines.append(f"from .{module_name} import {names[0]}")\n'
    '        else:\n'
    '            names_str = ", ".join(names)\n'
    '            import_lines.append(f"from .{module_name} import ({names_str})")\n'
    '        all_names.extend(names)\n'
    '    all_names.sort()\n'
    '    all_block_lines = ["", "__all__ = ["]\n'
    '    for name in all_names:\n'
    '        all_block_lines.append(f\'    "{name}",\')\n'
    '    all_block_lines.append("]")\n'
    '    return "\\n".join(import_lines) + "\\n" + "\\n".join(all_block_lines) + "\\n"\n'
    '\n'
    '\n'
    'def autofix_init(init_path, missing, dry_run=False):\n'
    '    if not missing:\n'
    '        return True\n'
    '    try:\n'
    '        original = init_path.read_text(encoding="utf-8")\n'
    '    except Exception as e:\n'
    '        logger.error(f"Failed to read {init_path}: {e}")\n'
    '        return False\n'
    '    try:\n'
    '        tree = ast.parse(original, filename=str(init_path))\n'
    '    except SyntaxError as e:\n'
    '        logger.error(f"Cannot autofix, {init_path} has a syntax error: {e}")\n'
    '        return False\n'
    '    all_node = None\n'
    '    for node in tree.body:\n'
    '        if isinstance(node, ast.Assign):\n'
    '            for target in node.targets:\n'
    '                if isinstance(target, ast.Name) and target.id == "__all__":\n'
    '                    all_node = node\n'
    '                    break\n'
    '        if all_node:\n'
    '            break\n'
    '    new_names = sorted({name for categories in missing.values() for names in categories.values() for name in names})\n'
    '    import_lines = []\n'
    '    for filename in sorted(missing.keys()):\n'
    '        module_name = Path(filename).stem\n'
    '        categories = missing[filename]\n'
    '        names = sorted(categories["classes"] + categories["constants"] + categories["functions"])\n'
    '        if not names:\n'
    '            continue\n'
    '        if len(names) == 1:\n'
    '            import_lines.append(f"from .{module_name} import {names[0]}")\n'
    '        else:\n'
    '            names_str = ", ".join(names)\n'
    '            import_lines.append(f"from .{module_name} import ({names_str})")\n'
    '    if all_node is not None:\n'
    '        existing_names = set()\n'
    '        if isinstance(all_node.value, (ast.List, ast.Tuple)):\n'
    '            for elt in all_node.value.elts:\n'
    '                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):\n'
    '                    existing_names.add(elt.value)\n'
    '        combined = sorted(existing_names | set(new_names))\n'
    '        new_all_block = "__all__ = [\\n"\n'
    '        for name in combined:\n'
    '            new_all_block += f\'    "{name}",\\n\'\n'
    '        new_all_block += "]"\n'
    '        lines = original.splitlines(keepends=True)\n'
    '        start = all_node.lineno - 1\n'
    '        end = all_node.end_lineno\n'
    '        new_lines = lines[:start] + [new_all_block + "\\n"] + lines[end:]\n'
    '        updated = "".join(new_lines)\n'
    '        if import_lines:\n'
    '            if not updated.endswith("\\n"):\n'
    '                updated += "\\n"\n'
    '            updated += "\\n" + "\\n".join(import_lines) + "\\n"\n'
    '    else:\n'
    '        updated = original\n'
    '        if not updated.endswith("\\n"):\n'
    '            updated += "\\n"\n'
    '        updated += "\\n"\n'
    '        updated += "\\n".join(import_lines) + "\\n"\n'
    '        updated += "\\n__all__ = [\\n"\n'
    '        for name in new_names:\n'
    '            updated += f\'    "{name}",\\n\'\n'
    '        updated += "]\\n"\n'
    '    if dry_run:\n'
    '        print("\\n" + "=" * 70)\n'
    '        print(f"DRY RUN — would write to {init_path}:")\n'
    '        print("=" * 70)\n'
    '        print("--- Proposed additions ---")\n'
    '        print("\\n".join(import_lines))\n'
    '        print()\n'
    '        print("__all__ entries added:", new_names)\n'
    '        return True\n'
    '    try:\n'
    '        init_path.write_text(updated, encoding="utf-8")\n'
    '        logger.success(f"Updated {init_path} with {len(new_names)} new export(s)")\n'
    '        return True\n'
    '    except Exception as e:\n'
    '        logger.error(f"Failed to write {init_path}: {e}")\n'
    '        return False\n'
    '\n'
    '\n'
    'def parse_args():\n'
    '    parser = argparse.ArgumentParser(description="Check and optionally autofix __init__.py exports.")\n'
    '    parser.add_argument(\n'
    '        "-a",\n'
    '        "--autofix",\n'
    '        action="store_true",\n'
    '        help="Automatically add missing definitions to __init__.py",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--dry-run",\n'
    '        action="store_true",\n'
    '        help="With -a, show what would be changed without writing",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-d",\n'
    '        "--directory",\n'
    '        type=Path,\n'
    '        default=Path.cwd(),\n'
    '        help="Directory to scan (default: current directory)",\n'
    '    )\n'
    '    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")\n'
    '    return parser.parse_args()\n'
    '\n'
    '\n'
    'def main():\n'
    '    args = parse_args()\n'
    '    logger.remove()\n'
    '    logger.add(\n'
    '        lambda msg: print(msg, end=""),\n'
    '        format="<level>{level: <8}</level> | <level>{message}</level>",\n'
    '        level="DEBUG" if args.verbose else "INFO",\n'
    '        colorize=True,\n'
    '    )\n'
    '    directory = args.directory.resolve()\n'
    '    print(f"Checking package definitions in: {directory}")\n'
    '    missing = check_directory(directory)\n'
    '    if not missing:\n'
    '        logger.success("All definitions are exported in __init__.py")\n'
    '        return 0\n'
    '    print()\n'
    '    print("=" * 70)\n'
    '    print("DEFINITIONS NOT EXPORTED IN __init__.py")\n'
    '    print("=" * 70)\n'
    '    total = 0\n'
    '    for filename, categories in missing.items():\n'
    '        print(f"\\n📄 {filename}")\n'
    '        for category, names in categories.items():\n'
    '            if names:\n'
    '                total += len(names)\n'
    '                icon = {"functions": "🔧", "classes": "🏛️ ", "constants": "📌"}[category]\n'
    '                print(f"  {icon} {category.capitalize()}:")\n'
    '                for name in sorted(names):\n'
    '                    print(f"      - {name}")\n'
    '    print()\n'
    '    print("=" * 70)\n'
    '    logger.warning(f"Total missing definitions: {total}")\n'
    '    if args.autofix:\n'
    '        print()\n'
    '        if args.dry_run:\n'
    '            print("Dry-run mode enabled — no files will be modified")\n'
    '        else:\n'
    '            print("Autofix enabled — updating __init__.py")\n'
    '        init_path = directory / "__init__.py"\n'
    '        success = autofix_init(init_path, missing, dry_run=args.dry_run)\n'
    '        return 0 if success else 1\n'
    '    else:\n'
    '        print()\n'
    '        print("Run with -a to automatically add these to __init__.py")\n'
    '        return 1\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_CHECK_FUNCS_SOURCE: str = (
    'import ast\n'
    'from pathlib import Path\n'
    'from typing import Dict\n'
    'from loguru import logger\n'
    '\n'
    '\n'
    'def extract_definitions(path):\n'
    '    definitions = {"functions": [], "classes": [], "constants": []}\n'
    '    try:\n'
    '        with open(path, "r", encoding="utf-8") as f:\n'
    '            tree = ast.parse(f.read(), filename=str(path))\n'
    '    except (SyntaxError, UnicodeDecodeError) as e:\n'
    '        logger.error(f"Failed to parse {path}: {e}")\n'
    '        return definitions\n'
    '    except Exception as e:\n'
    '        logger.error(f"Unexpected error reading {path}: {e}")\n'
    '        return definitions\n'
    '    for node in tree.body:\n'
    '        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n'
    '            if not node.name.startswith("_"):\n'
    '                definitions["functions"].append(node.name)\n'
    '        elif isinstance(node, ast.ClassDef):\n'
    '            if not node.name.startswith("_"):\n'
    '                definitions["classes"].append(node.name)\n'
    '        elif isinstance(node, ast.Assign):\n'
    '            for target in node.targets:\n'
    '                if isinstance(target, ast.Name):\n'
    '                    name = target.id\n'
    '                    if name.isupper() and not name.startswith("_"):\n'
    '                        definitions["constants"].append(name)\n'
    '        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):\n'
    '            name = node.target.id\n'
    '            if name.isupper() and not name.startswith("_"):\n'
    '                definitions["constants"].append(name)\n'
    '    return definitions\n'
    '\n'
    '\n'
    'def extract_exports_from_init(init_path):\n'
    '    exported = set()\n'
    '    try:\n'
    '        with open(init_path, "r", encoding="utf-8") as f:\n'
    '            content = f.read()\n'
    '        tree = ast.parse(content, filename=str(init_path))\n'
    '    except (SyntaxError, UnicodeDecodeError) as e:\n'
    '        logger.error(f"Failed to parse {init_path}: {e}")\n'
    '        return exported\n'
    '    except Exception as e:\n'
    '        logger.error(f"Unexpected error reading {init_path}: {e}")\n'
    '        return exported\n'
    '    for node in tree.body:\n'
    '        if isinstance(node, ast.Assign):\n'
    '            for target in node.targets:\n'
    '                if isinstance(target, ast.Name) and target.id == "__all__":\n'
    '                    if isinstance(node.value, (ast.List, ast.Tuple)):\n'
    '                        for elt in node.value.elts:\n'
    '                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):\n'
    '                                exported.add(elt.value)\n'
    '        elif isinstance(node, ast.ImportFrom):\n'
    '            for alias in node.names:\n'
    '                if alias.name == "*":\n'
    '                    logger.warning(f"Wildcard import found in {init_path}")\n'
    '                    continue\n'
    '                exported.add(alias.asname or alias.name)\n'
    '        elif isinstance(node, ast.Import):\n'
    '            for alias in node.names:\n'
    '                name = alias.asname or alias.name.split(".")[0]\n'
    '                exported.add(name)\n'
    '    return exported\n'
    '\n'
    '\n'
    'def check_directory(directory=None):\n'
    '    if directory is None:\n'
    '        directory = Path.cwd()\n'
    '    init_path = directory / "__init__.py"\n'
    '    if not init_path.exists():\n'
    '        logger.error(f"No __init__.py found in {directory}")\n'
    '        return {}\n'
    '    print(f"Reading exports from {init_path}")\n'
    '    exported = extract_exports_from_init(init_path)\n'
    '    logger.debug(f"Found {len(exported)} exported names: {sorted(exported)}")\n'
    '    missing = {}\n'
    '    python_files = [f for f in directory.glob("*.py") if f.name != "__init__.py" and not f.name.startswith("_")]\n'
    '    if not python_files:\n'
    '        logger.warning(f"No Python module files found in {directory}")\n'
    '        return {}\n'
    '    for py_file in sorted(python_files):\n'
    '        logger.debug(f"Scanning {py_file.name}")\n'
    '        definitions = extract_definitions(py_file)\n'
    '        module_name = py_file.stem\n'
    '        file_missing = {"functions": [], "classes": [], "constants": []}\n'
    '        for category, names in definitions.items():\n'
    '            for name in names:\n'
    '                if name not in exported and module_name not in exported:\n'
    '                    file_missing[category].append(name)\n'
    '        if any(file_missing.values()):\n'
    '            missing[py_file.name] = file_missing\n'
    '    return missing\n'
    '\n'
    '\n'
    'def main():\n'
    '    logger.remove()\n'
    '    logger.add(\n'
    '        lambda msg: print(msg, end=""),\n'
    '        format="<level>{level: <8}</level> | <level>{message}</level>",\n'
    '        level="INFO",\n'
    '        colorize=True,\n'
    '    )\n'
    '    directory = Path.cwd()\n'
    '    print(f"Checking package definitions in: {directory}")\n'
    '    missing = check_directory(directory)\n'
    '    if not missing:\n'
    '        logger.success("All definitions are exported in __init__.py")\n'
    '        return 0\n'
    '    print()\n'
    '    print("=" * 70)\n'
    '    print("DEFINITIONS NOT EXPORTED IN __init__.py")\n'
    '    print("=" * 70)\n'
    '    total = 0\n'
    '    for filename, categories in missing.items():\n'
    '        print(f"\\n📄 {filename}")\n'
    '        for category, names in categories.items():\n'
    '            if names:\n'
    '                total += len(names)\n'
    '                icon = {"functions": "🔧", "classes": "🏛️ ", "constants": "📌"}[category]\n'
    '                print(f"  {icon} {category.capitalize()}:")\n'
    '                for name in sorted(names):\n'
    '                    print(f"      - {name}")\n'
    '    print()\n'
    '    print("=" * 70)\n'
    '    logger.warning(f"Total missing definitions: {total}")\n'
    '    return 1\n'
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


class CheckExportsTool(BaseTool):
    """Wrapper for original check_exports.py: extract_definitions() + 6 more."""
    name: str = 'check_exports'
    source_file: str = 'check_exports.py'
    description: str = 'extract_definitions() + 6 more'
    functions: list[str] = ['extract_definitions', 'extract_exports_from_init', 'check_directory', 'build_import_block', 'autofix_init', 'parse_args', 'main']
    notes: str = ''
    source: str = _CHECK_EXPORTS_SOURCE

class CheckFuncsTool(BaseTool):
    """Wrapper for original check_funcs.py: extract_definitions() + 3 more."""
    name: str = 'check_funcs'
    source_file: str = 'check_funcs.py'
    description: str = 'extract_definitions() + 3 more'
    functions: list[str] = ['extract_definitions', 'extract_exports_from_init', 'check_directory', 'main']
    notes: str = ''
    source: str = _CHECK_FUNCS_SOURCE

class CheckPyExportsUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'check_exports': CheckExportsTool,
        'check_funcs': CheckFuncsTool,
    }

    @classmethod
    def list_tools(cls: type[CheckPyExportsUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[CheckPyExportsUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[CheckPyExportsUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for check_py_exports (2 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[CheckPyExportsUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[CheckPyExportsUnified], argv: Sequence[str] | None = None) -> int:
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
    return CheckPyExportsUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""FolderizeByRuleUnified for folderize_by_rule.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (7):
  foext <- foext.py (11L): top-level script [no __main__ guard (top-level script or library fragment; exec runs top-level code)]
  folderize <- folderize.py (91L): get_target_folder_name() + 2 more
  folderize_by_sim_names <- folderize_by_sim_names.py (82L): normalize_name() + 3 more
  foldext <- foldext.py (58L): folderize_by_extension() + 0 more [requires missing module 'dh' (ImportError at runtime)]
  foldimension <- foldimension.py (83L): collect_images() + 3 more
  nosubdir <- nosubdir.py (63L): check_directory() + 1 more
  rename_by_parent <- rename_by_parent.py (43L): top-level script

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

_FOEXT_SOURCE: str = (
    'import shutil\n'
    'from pathlib import Path\n'
    '\n'
    'BASE_DIR = Path.cwd()\n'
    'for item in BASE_DIR.iterdir():\n'
    '    if not item.is_file():\n'
    '        continue\n'
    '    ext = item.suffix.lower().lstrip(".") or "no_extension"\n'
    '    target_dir = BASE_DIR / ext\n'
    '    target_dir.mkdir(exist_ok=True)\n'
    '    shutil.move(str(item), target_dir / item.name)\n'
)

_FOLDERIZE_SOURCE: str = (
    'import shutil\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def get_target_folder_name(filename):\n'
    '    if not filename:\n'
    '        return "0-9"\n'
    '    first_char = filename[0].lower()\n'
    '    if first_char.isalpha():\n'
    '        return first_char\n'
    '    elif first_char.isdigit():\n'
    '        return "0-9"\n'
    '    else:\n'
    '        return "0-9"\n'
    '\n'
    '\n'
    'def cleanup_empty_dirs(root):\n'
    '    for dir_path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):\n'
    '        if dir_path.is_dir() and dir_path != root:\n'
    '            try:\n'
    '                dir_path.rmdir()\n'
    '                print(f"Removed empty directory: {dir_path}")\n'
    '            except OSError:\n'
    '                pass\n'
    '\n'
    '\n'
    'def folderize_files(root=Path.cwd()):\n'
    '    files_to_move = []\n'
    '    for item in root.rglob("*"):\n'
    '        if ".git" in item.parts:\n'
    '            continue\n'
    '        if item.is_file():\n'
    '            files_to_move.append(item)\n'
    '    if not files_to_move:\n'
    '        print("No files found to organize.")\n'
    '        return\n'
    '    print(f"Found {len(files_to_move)} files to organize.")\n'
    '    renamed_count = 0\n'
    '    for path in files_to_move:\n'
    '        original_name = path.name\n'
    '        folder_name = get_target_folder_name(original_name)\n'
    '        target_dir = root / folder_name\n'
    '        target_dir.mkdir(exist_ok=True)\n'
    '        target_path = target_dir / original_name\n'
    '        counter = 1\n'
    '        while target_path.exists():\n'
    '            stem = path.stem\n'
    '            suffix = path.suffix\n'
    '            new_name = f"{stem}_{counter}{suffix}"\n'
    '            target_path = target_dir / new_name\n'
    '            counter += 1\n'
    '        if target_path != path:\n'
    '            shutil.move(str(path), str(target_path))\n'
    '            if counter > 1:\n'
    '                renamed_count += 1\n'
    '                print(f"Moved and renamed: {original_name} -> {target_path.name} (duplicate avoided)")\n'
    '            else:\n'
    '                print(f"Moved: {path} -> {target_path}")\n'
    '    print("\\nCleaning up empty directories...")\n'
    '    cleanup_empty_dirs(root)\n'
    '    print("\\n✓ Organization complete!")\n'
    '    print(f"  - Files processed: {len(files_to_move)}")\n'
    '    print(f"  - Files renamed: {renamed_count}")\n'
    '    print("  - Folders created: a, b, c, ..., 0-9")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    import argparse\n'
    '\n'
    '    parser = argparse.ArgumentParser(description="Organize files recursively into alphabetical folders")\n'
    '    parser.add_argument(\n'
    '        "directory",\n'
    '        nargs="?",\n'
    '        default=".",\n'
    '        help="Directory to organize (default: current directory)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--dry-run",\n'
    '        action="store_true",\n'
    '        help="Show what would be moved without actually moving files",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    target_dir = Path(args.directory).resolve()\n'
    '    if args.dry_run:\n'
    '        print(f"DRY RUN - Would organize files in: {target_dir}")\n'
    '        file_count = sum(1 for _ in target_dir.rglob("*") if _.is_file())\n'
    '        print(f"Would process {file_count} files")\n'
    '        print("Folders would be created: a/, b/, c/, ..., 0-9/")\n'
    '    else:\n'
    '        print(f"Organizing files in: {target_dir}")\n'
    '        folderize_files(target_dir)\n'
)

_FOLDERIZE_BY_SIM_NAMES_SOURCE: str = (
    'import argparse\n'
    'import re\n'
    'import shutil\n'
    'from collections import defaultdict\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def normalize_name(path):\n'
    '    name = path.name\n'
    '    name = re.sub(r"(?:\\.lua)+$", "", name, flags=re.IGNORECASE)\n'
    '    name = re.sub(r"_\\d+$", "", name)\n'
    '    name = name.strip().lower()\n'
    '    name = re.sub(r"\\s+", "-", name)\n'
    '    name = re.sub(r"[^\\w.-]+", "-", name)\n'
    '    name = re.sub(r"-+", "-", name)\n'
    '    return name.strip("-._") or "ungrouped"\n'
    '\n'
    '\n'
    'def unique_destination(destination):\n'
    '    if not destination.exists():\n'
    '        return destination\n'
    '    counter = 1\n'
    '    while True:\n'
    '        candidate = destination.with_name(f"{destination.stem}_{counter}{destination.suffix}")\n'
    '        if not candidate.exists():\n'
    '            return candidate\n'
    '        counter += 1\n'
    '\n'
    '\n'
    'def find_lua_files(root, script_path):\n'
    '    files = []\n'
    '    for path in root.rglob("*.lua"):\n'
    '        if not path.is_file():\n'
    '            continue\n'
    '        if path.resolve() == script_path.resolve():\n'
    '            continue\n'
    '        files.append(path)\n'
    '    return files\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(description="Group recursively collected Lua files into named folders.")\n'
    '    parser.add_argument(\n'
    '        "--apply",\n'
    '        action="store_true",\n'
    '        help="Actually move files. Without this flag, only show planned moves.",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--root",\n'
    '        type=Path,\n'
    '        default=Path("."),\n'
    '        help="Directory to scan. Defaults to the current directory.",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    root = args.root.expanduser().resolve()\n'
    '    script_path = Path(__file__).resolve()\n'
    '    if not root.is_dir():\n'
    '        raise SystemExit(f"Not a directory: {root}")\n'
    '    groups = defaultdict(list)\n'
    '    for path in find_lua_files(root, script_path):\n'
    '        group_name = normalize_name(path)\n'
    '        groups[group_name].append(path)\n'
    '    if not groups:\n'
    '        print("No Lua files found.")\n'
    '        return\n'
    '    for group_name, files in sorted(groups.items()):\n'
    '        destination_dir = root / group_name\n'
    '        print(f"\\n[{group_name}]")\n'
    '        if args.apply:\n'
    '            destination_dir.mkdir(parents=True, exist_ok=True)\n'
    '        for source in sorted(files):\n'
    '            destination = destination_dir / source.name\n'
    '            destination = unique_destination(destination)\n'
    '            print(f"  {source.relative_to(root)} -> {destination.relative_to(root)}")\n'
    '            if args.apply:\n'
    '                shutil.move(str(source), str(destination))\n'
    '    if not args.apply:\n'
    '        print("\\nDry run only. Use --apply to perform the moves.")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    main()\n'
)

_FOLDEXT_SOURCE: str = (
    'import contextlib\n'
    'import shutil\n'
    'from pathlib import Path\n'
    'from dh import gsz\n'
    '\n'
    '\n'
    'def folderize_by_extension(cwd):\n'
    '    root_path = Path(cwd)\n'
    '    extension_stats = {}\n'
    '    for path in root_path.rglob("*"):\n'
    '        if ".git" in path.parts:\n'
    '            continue\n'
    '        if path.is_file():\n'
    '            ext = path.suffix.lower()[1:] if path.suffix else "no_extension"\n'
    '            size = path.stat().st_size\n'
    '            if ext not in extension_stats:\n'
    '                extension_stats[ext] = {"count": 0, "total_size": 0, "files": []}\n'
    '            extension_stats[ext]["count"] += 1\n'
    '            extension_stats[ext]["total_size"] += size\n'
    '            extension_stats[ext]["files"].append(path)\n'
    '    created_dirs = set()\n'
    '    for ext, stats in extension_stats.items():\n'
    '        target_dir = root_path / ext\n'
    '        target_dir.mkdir(exist_ok=True)\n'
    '        created_dirs.add(ext)\n'
    '        for path in stats["files"]:\n'
    '            if path.parent == target_dir:\n'
    '                continue\n'
    '            target_path = target_dir / path.name\n'
    '            counter = 1\n'
    '            while target_path.exists():\n'
    '                target_path = target_dir / f"{path.stem}_{counter}{path.suffix}"\n'
    '                counter += 1\n'
    '            with contextlib.suppress(BaseException):\n'
    '                shutil.move(str(path), str(target_path))\n'
    '    for dir_path in sorted(root_path.glob("**/*"), key=lambda p: len(p.parts), reverse=True):\n'
    '        if dir_path.is_dir() and dir_path != root_path:\n'
    '            with contextlib.suppress(OSError):\n'
    '                dir_path.rmdir()\n'
    '    total_files = 0\n'
    '    total_size = 0\n'
    '    for ext in sorted(extension_stats.keys()):\n'
    '        stats = extension_stats[ext]\n'
    '        total_files += stats["count"]\n'
    '        total_size += stats["total_size"]\n'
    '        ext_display = ext if ext else "no_extension"\n'
    '        size_str = gsz(stats["total_size"])\n'
    '        print(f"{ext_display:<15} : {stats[\'count\']:4} file{\'s\' if stats[\'count\'] != 1 else \' \'}  {size_str:>8}")\n'
    '    print("-" * 40)\n'
    '    print(f"{\'TOTAL\':<15} : {total_files:4} files  {gsz(total_size):>8}")\n'
    '    print("=" * 40)\n'
    '    return created_dirs, extension_stats\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    target_dir = Path.cwd()\n'
    '    created_dirs, stats = folderize_by_extension(target_dir)\n'
    '    print(f"\\nCreated {len(created_dirs)} extension folders.")\n'
)

_FOLDIMENSION_SOURCE: str = (
    'import shutil\n'
    'import sys\n'
    'from collections import defaultdict\n'
    'from pathlib import Path\n'
    '\n'
    'try:\n'
    '    from PIL import Image\n'
    'except ImportError:\n'
    '    print("Error: This script requires Pillow. Install it with: pip install Pillow")\n'
    '    sys.exit(1)\n'
    'IMAGE_EXTENSIONS = {\n'
    '    ".jpg",\n'
    '    ".jpeg",\n'
    '    ".png",\n'
    '    ".gif",\n'
    '    ".bmp",\n'
    '    ".tiff",\n'
    '    ".tif",\n'
    '    ".webp",\n'
    '    ".ico",\n'
    '}\n'
    '\n'
    '\n'
    'def collect_images(root):\n'
    '    size_to_files = defaultdict(list)\n'
    '    for path in root.rglob("*"):\n'
    '        if not path.is_file():\n'
    '            continue\n'
    '        if path.suffix.lower() not in IMAGE_EXTENSIONS:\n'
    '            continue\n'
    '        try:\n'
    '            with Image.open(path) as img:\n'
    '                width, height = img.size\n'
    '            size_to_files[width, height].append(path)\n'
    '        except Exception as e:\n'
    '            print(f"Warning: Skipping {path} - {e}")\n'
    '    return size_to_files\n'
    '\n'
    '\n'
    'def unique_destination(dest):\n'
    '    if not dest.exists():\n'
    '        return dest\n'
    '    stem = dest.stem\n'
    '    suffix = dest.suffix\n'
    '    parent = dest.parent\n'
    '    counter = 1\n'
    '    while True:\n'
    '        new_dest = parent / f"{stem}_{counter}{suffix}"\n'
    '        if not new_dest.exists():\n'
    '            return new_dest\n'
    '        counter += 1\n'
    '\n'
    '\n'
    'def organize_images(root, size_to_files):\n'
    '    for (width, height), files in size_to_files.items():\n'
    '        if len(files) == 1:\n'
    '            folder = "other"\n'
    '        else:\n'
    '            folder = f"{width}x{height}"\n'
    '        folder_path = root / folder\n'
    '        folder_path.mkdir(parents=True, exist_ok=True)\n'
    '        for src in files:\n'
    '            dest = folder_path / src.name\n'
    '            dest = unique_destination(dest)\n'
    '            shutil.move(src, dest)\n'
    '            print(f"Moved: {src} -> {dest}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    root = Path.cwd()\n'
    '    print(f"Scanning {root} for image files...")\n'
    '    size_to_files = collect_images(root)\n'
    '    total_files = sum(len(v) for v in size_to_files.values())\n'
    '    if total_files == 0:\n'
    '        print("No image files found.")\n'
    '        return\n'
    '    print(f"Found {total_files} image(s) in {len(size_to_files)} resolution group(s).")\n'
    '    organize_images(root, size_to_files)\n'
    '    print("Done.")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_NOSUBDIR_SOURCE: str = (
    'import argparse\n'
    'import pathlib\n'
    'from concurrent.futures import ProcessPoolExecutor, as_completed\n'
    'from functools import partial\n'
    '\n'
    '\n'
    'def check_directory(dir_path, max_size_kb=None):\n'
    '    try:\n'
    '        contents = list(dir_path.iterdir())\n'
    '        has_subdirs = any(item.is_dir() for item in contents)\n'
    '        if has_subdirs:\n'
    '            return None\n'
    '        py_files = [item for item in contents if item.is_file() and item.suffix == ".py"]\n'
    '        if not py_files:\n'
    '            return None\n'
    '        if max_size_kb is not None:\n'
    '            total_size = sum(f.stat().st_size for f in contents if f.is_file()) + sum(\n'
    '                f.stat().st_size for f in py_files if f.is_file()\n'
    '            )\n'
    '            total_size_kb = total_size / 1024\n'
    '            if total_size_kb > max_size_kb:\n'
    '                return None\n'
    '        return dir_path.name\n'
    '    except (PermissionError, OSError):\n'
    '        return None\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(description="Find top-level directories without subdirs that contain .py files")\n'
    '    parser.add_argument(\n'
    '        "-s",\n'
    '        "--size",\n'
    '        type=float,\n'
    '        help="Maximum directory size in KB (e.g., -s 100 for 100KB)",\n'
    '        default=None,\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    current_dir = pathlib.Path(".")\n'
    '    dirs = [item for item in current_dir.iterdir() if item.is_dir()]\n'
    '    if not dirs:\n'
    '        print("No directories found in current directory.")\n'
    '        return\n'
    '    check_func = partial(check_directory, max_size_kb=args.size)\n'
    '    matching_dirs = []\n'
    '    with ProcessPoolExecutor() as executor:\n'
    '        future_to_dir = {executor.submit(check_func, d): d for d in dirs}\n'
    '        for future in as_completed(future_to_dir):\n'
    '            result = future.result()\n'
    '            if result is not None:\n'
    '                matching_dirs.append(result)\n'
    '    if matching_dirs:\n'
    '        size_info = f" (max {args.size}KB)" if args.size else ""\n'
    '        print(f"Directories without subdirs containing .py files{size_info}:")\n'
    '        for dir_name in sorted(matching_dirs):\n'
    '            print(f"  - {dir_name}")\n'
    '        print(f"\\nTotal: {len(matching_dirs)} directory(ies)")\n'
    '    else:\n'
    '        size_info = f" under {args.size}KB" if args.size else ""\n'
    '        print(f"No matching directories found{size_info}.")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_RENAME_BY_PARENT_SOURCE: str = (
    'import os\n'
    'from os.path import dirname as dirn, isfile as isf, join as jn\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'class DirectoryWalker:\n'
    '    def __init__(self, directory):\n'
    '        self.stack = [directory]\n'
    '        self.files = []\n'
    '        self.index = 0\n'
    '\n'
    '    def __getitem__(self, index):\n'
    '        while 1:\n'
    '            try:\n'
    '                file = self.files[self.index]\n'
    '                self.index = self.index + 1\n'
    '            except IndexError:\n'
    '                self.directory = self.stack.pop()\n'
    '                self.files = os.listdir(self.directory)\n'
    '                self.index = 0\n'
    '            else:\n'
    '                fullname = jn(self.directory, file)\n'
    '                if os.path.isdir(fullname) and not os.path.islink(fullname):\n'
    '                    self.stack.append(fullname)\n'
    '                return fullname\n'
    '        return None\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    for file in DirectoryWalker(str(cwd)):\n'
    '        if isf(file) and file.endswith("README.pdf"):\n'
    '            dirname1 = dirn(file)\n'
    '            full_name = file\n'
    '            dirs = dirname1.split("/")\n'
    '            last_dir = dirs[len(dirs) - 1]\n'
    '            new_name = last_dir + ".pdf"\n'
    '            if not os.path.exists(new_name):\n'
    '                try:\n'
    '                    os.rename(file, jn(dirname1, new_name))\n'
    '                    print(f"file {full_name} renamed to {new_name}")\n'
    '                except OSError as e:\n'
    '                    print(e)\n'
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


class FoextTool(BaseTool):
    """Wrapper for original foext.py: top-level script NOTE: no __main__ guard (top-level script or library fragment; exec runs top-level code)."""
    name: str = 'foext'
    source_file: str = 'foext.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = 'no __main__ guard (top-level script or library fragment; exec runs top-level code)'
    source: str = _FOEXT_SOURCE

class FolderizeTool(BaseTool):
    """Wrapper for original folderize.py: get_target_folder_name() + 2 more."""
    name: str = 'folderize'
    source_file: str = 'folderize.py'
    description: str = 'get_target_folder_name() + 2 more'
    functions: list[str] = ['get_target_folder_name', 'cleanup_empty_dirs', 'folderize_files']
    notes: str = ''
    source: str = _FOLDERIZE_SOURCE

class FolderizeBySimNamesTool(BaseTool):
    """Wrapper for original folderize_by_sim_names.py: normalize_name() + 3 more."""
    name: str = 'folderize_by_sim_names'
    source_file: str = 'folderize_by_sim_names.py'
    description: str = 'normalize_name() + 3 more'
    functions: list[str] = ['normalize_name', 'unique_destination', 'find_lua_files', 'main']
    notes: str = ''
    source: str = _FOLDERIZE_BY_SIM_NAMES_SOURCE

class FoldextTool(BaseTool):
    """Wrapper for original foldext.py: folderize_by_extension() + 0 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'foldext'
    source_file: str = 'foldext.py'
    description: str = 'folderize_by_extension() + 0 more'
    functions: list[str] = ['folderize_by_extension']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _FOLDEXT_SOURCE

class FoldimensionTool(BaseTool):
    """Wrapper for original foldimension.py: collect_images() + 3 more."""
    name: str = 'foldimension'
    source_file: str = 'foldimension.py'
    description: str = 'collect_images() + 3 more'
    functions: list[str] = ['collect_images', 'unique_destination', 'organize_images', 'main']
    notes: str = ''
    source: str = _FOLDIMENSION_SOURCE

class NosubdirTool(BaseTool):
    """Wrapper for original nosubdir.py: check_directory() + 1 more."""
    name: str = 'nosubdir'
    source_file: str = 'nosubdir.py'
    description: str = 'check_directory() + 1 more'
    functions: list[str] = ['check_directory', 'main']
    notes: str = ''
    source: str = _NOSUBDIR_SOURCE

class RenameByParentTool(BaseTool):
    """Wrapper for original rename_by_parent.py: top-level script."""
    name: str = 'rename_by_parent'
    source_file: str = 'rename_by_parent.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _RENAME_BY_PARENT_SOURCE

class FolderizeByRuleUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'foext': FoextTool,
        'folderize': FolderizeTool,
        'folderize_by_sim_names': FolderizeBySimNamesTool,
        'foldext': FoldextTool,
        'foldimension': FoldimensionTool,
        'nosubdir': NosubdirTool,
        'rename_by_parent': RenameByParentTool,
    }

    @classmethod
    def list_tools(cls: type[FolderizeByRuleUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[FolderizeByRuleUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[FolderizeByRuleUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for folderize_by_rule (7 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[FolderizeByRuleUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[FolderizeByRuleUnified], argv: Sequence[str] | None = None) -> int:
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
    return FolderizeByRuleUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

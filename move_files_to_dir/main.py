#!/usr/bin/env python3
"""MoveFilesToDirUnified for move_files_to_dir.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (11):
  collect_files <- collect_files.py (43L): unique_destination_path() + 1 more
  dir_mover <- dir_mover.py (75L): validate_dirs() + 3 more
  docer <- docer.py (21L): process_file() + 0 more
  flaten <- flaten.py (59L): flatten_directory() + 1 more
  move_tests_dirs <- move_tests_dirs.py (60L): move_tests_folder() + 1 more [requires missing module 'dh' (ImportError at runtime)]
  move_tests_files <- move_tests_files.py (171L): is_test_file() + 8 more
  movebin <- movebin.py (25L): main() + 0 more
  pycp <- pycp.py (8L): top-level script [no __main__ guard (top-level script or library fragment; exec runs top-level code)]
  tobin <- tobin.py (31L): get_sha256() + 1 more
  tosc <- tosc.py (19L): main() + 0 more [requires missing module 'dh' (ImportError at runtime)]
  www <- www.py (15L): top-level script

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

_COLLECT_FILES_SOURCE: str = (
    'import shutil\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def unique_destination_path(dest_dir, filename):\n'
    '    candidate = dest_dir / filename\n'
    '    if not candidate.exists():\n'
    '        return candidate\n'
    '    stem = Path(filename).stem\n'
    '    suffix = Path(filename).suffix\n'
    '    counter = 1\n'
    '    while True:\n'
    '        candidate = dest_dir / f"{stem}_{counter}{suffix}"\n'
    '        if not candidate.exists():\n'
    '            return candidate\n'
    '        counter += 1\n'
    '\n'
    '\n'
    'def collect_files_by_extension(extension):\n'
    '    cwd = Path.cwd()\n'
    '    target_dir = cwd / extension\n'
    '    target_dir.mkdir(parents=True, exist_ok=True)\n'
    '    copied_count = 0\n'
    '    for path in cwd.rglob(f"*.{extension}"):\n'
    '        if path.is_file() and target_dir not in path.parents:\n'
    '            try:\n'
    '                destination_path = unique_destination_path(target_dir, path.name)\n'
    '                shutil.copy2(path, destination_path)\n'
    '                print(f"Copied: {path} -> {destination_path}")\n'
    '                copied_count += 1\n'
    '            except Exception as e:\n'
    '                print(f"Error copying {path}: {e}")\n'
    '    print("\\nFinished collecting files.")\n'
    '    print(f"Total files copied: {copied_count}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) != 2:\n'
    '        print("Usage: python collect_files.py <extension>")\n'
    '        sys.exit(1)\n'
    '    file_extension = sys.argv[1].lower().strip(".")\n'
    '    collect_files_by_extension(file_extension)\n'
)

_DIR_MOVER_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from shutil import move\n'
    '\n'
    '\n'
    'def validate_dirs(source, dest):\n'
    '    if not source.is_dir():\n'
    '        print(f"❌ Source directory does not exist: {source}")\n'
    '        return False\n'
    '    if not dest.is_dir():\n'
    '        print(f"❌ Destination directory does not exist: {dest}")\n'
    '        return False\n'
    '    if source == dest:\n'
    '        print("❌ Source and destination cannot be the same directory")\n'
    '        return False\n'
    '    return True\n'
    '\n'
    '\n'
    'def get_top_level_subdirs(directory):\n'
    '    subdirs = [p for p in directory.iterdir() if p.is_dir()]\n'
    '    return sorted(subdirs)\n'
    '\n'
    '\n'
    'def move_subdirs(source, dest):\n'
    '    print(f"📂 Source directory: {source.resolve()}")\n'
    '    print(f"📂 Destination directory: {dest.resolve()}")\n'
    '    print("-" * 40)\n'
    '    source_subdirs = get_top_level_subdirs(source)\n'
    '    if not source_subdirs:\n'
    '        print("⚠️  No subdirectories found in source")\n'
    '        return\n'
    '    dest_subdir_names = {p.name for p in get_top_level_subdirs(dest)}\n'
    '    moved = []\n'
    '    skipped = []\n'
    '    for subdir in source_subdirs:\n'
    '        if subdir.name in dest_subdir_names:\n'
    '            print(f"⏭️  SKIP: {subdir.name} (already exists in destination)")\n'
    '            skipped.append(subdir.name)\n'
    '        else:\n'
    '            try:\n'
    '                new_path = dest / subdir.name\n'
    '                print(f"➡️  MOVE: {subdir.name}")\n'
    '                print(f"   From: {subdir.resolve()}")\n'
    '                print(f"   To:   {new_path.resolve()}")\n'
    '                move(str(subdir), str(new_path))\n'
    '                moved.append(subdir.name)\n'
    '                print(f"   ✅ Success")\n'
    '            except Exception as e:\n'
    '                print(f"   ❌ Error: {e}")\n'
    '    print("-" * 40)\n'
    '    print(f"\\n📊 Summary:")\n'
    '    print(f"✅ Moved: {len(moved)}")\n'
    '    if moved:\n'
    '        for name in moved:\n'
    '            print(f"   • {name}")\n'
    '    print(f"⏭️  Skipped: {len(skipped)}")\n'
    '    if skipped:\n'
    '        for name in skipped:\n'
    '            print(f"   • {name}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) != 3:\n'
    '        print("Usage: python dir_mver.py <source_dir> <dest_dir>")\n'
    '        print("Example: python dir_mver.py ~/repos/projects ~/isaac")\n'
    '        sys.exit(1)\n'
    '    source = Path(sys.argv[1]).expanduser().resolve()\n'
    '    dest = Path(sys.argv[2]).expanduser().resolve()\n'
    '    if not validate_dirs(source, dest):\n'
    '        sys.exit(1)\n'
    '    move_subdirs(source, dest)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_DOCER_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    content = path.read_bytes()\n'
    '    target_dir = Path("/sdcard/doc")\n'
    '    if not target_dir.exists():\n'
    '        target_dir.mkdir(exist_ok=True)\n'
    '    target_path = target_dir / path.name\n'
    '    if not target_path.exists():\n'
    '        target_path.write_bytes(content)\n'
    '        path.unlink()\n'
    '        print("done.")\n'
    '    else:\n'
    '        print(f"target file : {target_path.name} exists. remove it and try again")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    fn = Path(sys.argv[1])\n'
    '    process_file(fn)\n'
)

_FLATEN_SOURCE: str = (
    'import shutil\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def flatten_directory(directory="."):\n'
    '    root = Path(directory).resolve()\n'
    '    if not root.is_dir():\n'
    '        print(f"Error: {root} is not a valid directory")\n'
    '        return\n'
    '    print(f"Flattening directory: {root}")\n'
    '    files_to_move = []\n'
    '    for subdir in root.iterdir():\n'
    '        if subdir.is_dir():\n'
    '            for path in subdir.iterdir():\n'
    '                if path.is_file():\n'
    '                    files_to_move.append(path)\n'
    '    if not files_to_move:\n'
    '        print("No files found in subdirectories.")\n'
    '        return\n'
    '    print(f"Found {len(files_to_move)} file(s) to move")\n'
    '    moved_count = 0\n'
    '    skipped_count = 0\n'
    '    for path in files_to_move:\n'
    '        target_path = root / path.name\n'
    '        if target_path.exists():\n'
    '            print(f"Skipping: {path} -> {target_path} (file already exists)")\n'
    '            skipped_count += 1\n'
    '            continue\n'
    '        try:\n'
    '            shutil.move(str(path), str(target_path))\n'
    '            print(f"Moved: {path} -> {target_path}")\n'
    '            moved_count += 1\n'
    '        except Exception as e:\n'
    '            print(f"Error moving {path}: {e}")\n'
    '    print(f"\\nMoved {moved_count} file(s), skipped {skipped_count} file(s)")\n'
    '    removed_dirs = 0\n'
    '    for subdir in root.iterdir():\n'
    '        if subdir.is_dir():\n'
    '            try:\n'
    '                if not any(subdir.iterdir()):\n'
    '                    subdir.rmdir()\n'
    '                    print(f"Removed empty directory: {subdir}")\n'
    '                    removed_dirs += 1\n'
    '                else:\n'
    '                    print(f"Directory not empty (skipping): {subdir}")\n'
    '            except Exception as e:\n'
    '                print(f"Error removing {subdir}: {e}")\n'
    '    print(f"\\nRemoved {removed_dirs} empty directory(ies)")\n'
    '    print("Flattening complete!")\n'
    '\n'
    '\n'
    'def main():\n'
    '    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."\n'
    '    flatten_directory(target_dir)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    main()\n'
)

_MOVE_TESTS_DIRS_SOURCE: str = (
    'import shutil\n'
    'import sys\n'
    'from concurrent.futures import ProcessPoolExecutor, as_completed\n'
    'from pathlib import Path\n'
    'from dh import cprint\n'
    '\n'
    'DRY_RUN = "-d" in sys.argv\n'
    'EXCLUDED = ["numpy", "pandas", "scipy"]\n'
    'SRC = Path.home() / ".local" / "lib" / "python3.12" / "site-packages"\n'
    '\n'
    '\n'
    'def move_tests_folder(tests_path, base_src, base_dst):\n'
    '    strp = str(tests_path)\n'
    '    if "numpy" in strp or "scipy" in strp or "pandas" in strp or "numba" in strp:\n'
    '        return False, f"excluded path"\n'
    '    try:\n'
    '        relative_path = tests_path.relative_to(base_src)\n'
    '        parent_relative = relative_path.parent\n'
    '        dst_path = base_dst / parent_relative / tests_path.name\n'
    '        dst_path.parent.mkdir(parents=True, exist_ok=True)\n'
    '        if DRY_RUN:\n'
    '            cprint(f"will Move: {tests_path} -> {dst_path}")\n'
    '            return True, f"Moved: {tests_path} -> {dst_path}"\n'
    '        shutil.move(str(tests_path), str(dst_path))\n'
    '        return True, f"Moved: {tests_path} -> {dst_path}"\n'
    '    except Exception as e:\n'
    '        return False, f"Error moving {tests_path}: {e}"\n'
    '\n'
    '\n'
    'def move_tests_recursive(source_dir=SRC, max_workers=4):\n'
    '    source = Path(source_dir).resolve()\n'
    '    destination = Path.home() / "tmp" / "tests_dirs"\n'
    '    tests_folders = list(source.rglob("tests"))\n'
    '    tests_folders = [p for p in tests_folders if p.is_dir()]\n'
    '    if not tests_folders:\n'
    '        print("No \'tests\' folders found.")\n'
    '        return 0\n'
    '    print(f"Found {len(tests_folders)} \'tests\' folder(s) to move")\n'
    '    print(f"Source: {source}")\n'
    '    print(f"Destination: {destination}")\n'
    '    print()\n'
    '    destination.parent.mkdir(parents=True, exist_ok=True)\n'
    '    moved_count = 0\n'
    '    with ProcessPoolExecutor(max_workers=max_workers) as executor:\n'
    '        futures = {\n'
    '            executor.submit(move_tests_folder, tests_path, source, destination): tests_path\n'
    '            for tests_path in tests_folders\n'
    '        }\n'
    '        for future in as_completed(futures):\n'
    '            success, message = future.result()\n'
    '            print(message)\n'
    '            if success:\n'
    '                moved_count += 1\n'
    '    print()\n'
    '    print(f"✓ Successfully moved {moved_count}/{len(tests_folders)} directories")\n'
    '    return moved_count\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    move_tests_recursive()\n'
)

_MOVE_TESTS_FILES_SOURCE: str = (
    'import argparse\n'
    'import json\n'
    'import shutil\n'
    'from multiprocessing import Pool\n'
    'from pathlib import Path\n'
    'from typing import Any\n'
    'from loguru import logger\n'
    '\n'
    'TESTS_DIR = Path.home() / "tmp" / "tests"\n'
    'MOVED_FILES_LOG = Path.home() / "tmp" / "moved_files.json"\n'
    'POOL_WORKERS = 8\n'
    'MoveResult = tuple[str, bool, str]\n'
    '\n'
    '\n'
    'def is_test_file(path):\n'
    '    stem = path.stem\n'
    '    return "_test" in stem or "test_" in stem\n'
    '\n'
    '\n'
    'def get_relative_path(path, base_dir):\n'
    '    try:\n'
    '        return path.relative_to(base_dir)\n'
    '    except ValueError:\n'
    '        return path\n'
    '\n'
    '\n'
    'def move_file(source, dest):\n'
    '    try:\n'
    '        dest.parent.mkdir(parents=True, exist_ok=True)\n'
    '        shutil.move(str(source), str(dest))\n'
    '        return str(source), True, f"Moved to {dest}"\n'
    '    except Exception as e:\n'
    '        return str(source), False, f"Error: {e!s}"\n'
    '\n'
    '\n'
    'def find_test_files(base_dir):\n'
    '    test_files = []\n'
    '    for py_file in base_dir.rglob("*.py"):\n'
    '        if is_test_file(py_file):\n'
    '            test_files.append(py_file)\n'
    '    return test_files\n'
    '\n'
    '\n'
    'def move_files_parallel(\n'
    '    test_files,\n'
    '    base_dir,\n'
    '):\n'
    '    file_mapping = {}\n'
    '    results = []\n'
    '    pool = Pool(processes=POOL_WORKERS)\n'
    '    try:\n'
    '        async_results = []\n'
    '        for source_file in test_files:\n'
    '            relative_path = get_relative_path(source_file, base_dir)\n'
    '            dest_file = TESTS_DIR / relative_path\n'
    '            async_result = pool.apply_async(move_file, (source_file, dest_file))\n'
    '            async_results.append((async_result, source_file, dest_file))\n'
    '        for async_result, source_file, dest_file in async_results:\n'
    '            _source_str, success, message = async_result.get()\n'
    '            if success:\n'
    '                file_mapping[str(source_file)] = str(dest_file)\n'
    '                results.append((str(source_file), message))\n'
    '                logger.success(message)\n'
    '            else:\n'
    '                results.append((str(source_file), message))\n'
    '                logger.error(message)\n'
    '    finally:\n'
    '        pool.close()\n'
    '        pool.join()\n'
    '    return file_mapping, results\n'
    '\n'
    '\n'
    'def reverse_move(moved_files_log):\n'
    '    if not moved_files_log.exists():\n'
    '        raise FileNotFoundError(f"Log file not found: {moved_files_log}")\n'
    '    with open(moved_files_log) as f:\n'
    '        file_mapping = json.load(f)\n'
    '    results = []\n'
    '    pool = Pool(processes=POOL_WORKERS)\n'
    '    try:\n'
    '        async_results = []\n'
    '        for original_path, moved_path in file_mapping.items():\n'
    '            moved_file = Path(moved_path)\n'
    '            original_file = Path(original_path)\n'
    '            if moved_file.exists():\n'
    '                async_result = pool.apply_async(move_file, (moved_file, original_file))\n'
    '                async_results.append((async_result, moved_file, original_file))\n'
    '        for async_result, source_file, _dest_file in async_results:\n'
    '            _source_str, success, message = async_result.get()\n'
    '            if success:\n'
    '                results.append((str(source_file), message))\n'
    '                logger.success(message)\n'
    '            else:\n'
    '                results.append((str(source_file), message))\n'
    '                logger.error(message)\n'
    '    finally:\n'
    '        pool.close()\n'
    '        pool.join()\n'
    '    return file_mapping, results\n'
    '\n'
    '\n'
    'def save_log(file_mapping, log_path):\n'
    '    log_path.parent.mkdir(parents=True, exist_ok=True)\n'
    '    with open(log_path, "w") as f:\n'
    '        json.dump(file_mapping, f, indent=2)\n'
    '    print(f"📋 Log saved to: {log_path}")\n'
    '\n'
    '\n'
    'def cleanup_empty_dirs(root):\n'
    '    try:\n'
    '        for parent in sorted(root.rglob("*"), reverse=True):\n'
    '            if parent.is_dir():\n'
    '                try:\n'
    '                    if not any(parent.iterdir()):\n'
    '                        parent.rmdir()\n'
    '                except OSError:\n'
    '                    continue\n'
    '    except OSError:\n'
    '        pass\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description=("Move Python test files to ~/tmp/tests with directory structure preservation.")\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--reverse",\n'
    '        action="store_true",\n'
    '        help="Reverse the move operation (return files to original locations).",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--dir",\n'
    '        type=Path,\n'
    '        default=Path.cwd(),\n'
    '        help="Base directory to search for test files (default: current directory).",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "--log",\n'
    '        type=Path,\n'
    '        default=MOVED_FILES_LOG,\n'
    '        help=f"Path to log file (default: {MOVED_FILES_LOG}).",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    try:\n'
    '        if args.reverse:\n'
    '            print(f"🔄 Reversing move operation from log: {args.log}")\n'
    '            _file_mapping, results = reverse_move(args.log)\n'
    '            print(f"✅ Reversed {len(results)} files")\n'
    '            cleanup_empty_dirs(TESTS_DIR)\n'
    '        else:\n'
    '            print(f"🔍 Searching for test files in: {args.dir}")\n'
    '            test_files = find_test_files(args.dir)\n'
    '            if not test_files:\n'
    '                logger.warning("❌ No test files found.")\n'
    '                return 0\n'
    '            print(f"📦 Found {len(test_files)} test file(s)")\n'
    '            print(f"📍 Destination: {TESTS_DIR}")\n'
    '            file_mapping, _results = move_files_parallel(test_files, args.dir)\n'
    '            save_log(file_mapping, args.log)\n'
    '            print(f"✅ Moved {len(file_mapping)} file(s)")\n'
    '    except FileNotFoundError as e:\n'
    '        logger.error(f"❌ Error: {e}")\n'
    '        return 1\n'
    '    except Exception as e:\n'
    '        logger.error(f"❌ Unexpected error: {e}")\n'
    '        return 1\n'
    '    return 0\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_MOVEBIN_SOURCE: str = (
    'import shutil\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path.cwd()\n'
    '    binary_dir = cwd / "binary"\n'
    '    binary_dir.mkdir(exist_ok=True)\n'
    '    files_moved = 0\n'
    '    for f in cwd.iterdir():\n'
    '        if f.is_file() and is_binary(Path(f)):\n'
    '            try:\n'
    '                shutil.move(str(f), binary_dir / f.name)\n'
    '                print(f"Moved: {f.name} -> binary/{f.name}")\n'
    '                files_moved += 1\n'
    '            except Exception as e:\n'
    '                print(f"Failed to move {f.name}: {e}")\n'
    '    if files_moved == 0:\n'
    '        print("No binary files found to move.")\n'
    '    else:\n'
    '        print(f"Total binary files moved: {files_moved}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_PYCP_SOURCE: str = (
    'import shutil\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    'src = Path(sys.argv[1].strip())\n'
    'dest = Path("/data/data/com.termux/files/usr")\n'
    'shutil.copy2(str(src), dest)\n'
    'print("done")\n'
)

_TOBIN_SOURCE: str = (
    'import sys\n'
    'from hashlib import sha256\n'
    'from pathlib import Path\n'
    '\n'
    'CHUNK_SIZE = 32768\n'
    'dest = Path.home() / "sbin"\n'
    '\n'
    '\n'
    'def get_sha256(path):\n'
    '    path = Path(path)\n'
    '    h = sha256()\n'
    '    with path.open("rb") as f:\n'
    '        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):\n'
    '            h.update(chunk)\n'
    '    return h.hexdigest()\n'
    '\n'
    '\n'
    'def main():\n'
    '    fn = Path(sys.argv[1])\n'
    '    dest_path = dest / fn.name\n'
    '    if dest_path.exists():\n'
    '        print("target exists")\n'
    '        if get_sha256(dest_path) == get_sha256(fn):\n'
    '            print("the target hash and source are equal")\n'
    '            fn.unlink()\n'
    '            sys.exit(1)\n'
    '    fn.rename(dest_path)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_TOSC_SOURCE: str = (
    'import shutil\n'
    'import sys\n'
    'from pathlib import Path\n'
    'from dh import unique_path\n'
    '\n'
    'dest = Path.home() / "isaac" / "may" / "scripts"\n'
    '\n'
    '\n'
    'def main():\n'
    '    fn = Path(sys.argv[1])\n'
    '    dest_path = dest / fn.name\n'
    '    if dest_path.exists():\n'
    '        dest_path = unique_path(dest_path)\n'
    '    shutil.move(str(fn), str(dest_path))\n'
    '    print(f"{fn.name} --> {dest_path.name}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_WWW_SOURCE: str = (
    'from pathlib import Path\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    for path in cwd.rglob("*.whl"):\n'
    '        fname = path.name\n'
    '        target_dir = Path("/sdcard/whl")\n'
    '        target_path = target_dir / fname\n'
    '        if target_path.exists():\n'
    '            target_path.unlink()\n'
    '        data = path.read_bytes()\n'
    '        target_path.write_bytes(data)\n'
    '        path.unlink()\n'
    '        print(f"{path.name} -> {target_path.name}")\n'
    '    print("done")\n'
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


class CollectFilesTool(BaseTool):
    """Wrapper for original collect_files.py: unique_destination_path() + 1 more."""
    name: str = 'collect_files'
    source_file: str = 'collect_files.py'
    description: str = 'unique_destination_path() + 1 more'
    functions: list[str] = ['unique_destination_path', 'collect_files_by_extension']
    notes: str = ''
    source: str = _COLLECT_FILES_SOURCE

class DirMoverTool(BaseTool):
    """Wrapper for original dir_mover.py: validate_dirs() + 3 more."""
    name: str = 'dir_mover'
    source_file: str = 'dir_mover.py'
    description: str = 'validate_dirs() + 3 more'
    functions: list[str] = ['validate_dirs', 'get_top_level_subdirs', 'move_subdirs', 'main']
    notes: str = ''
    source: str = _DIR_MOVER_SOURCE

class DocerTool(BaseTool):
    """Wrapper for original docer.py: process_file() + 0 more."""
    name: str = 'docer'
    source_file: str = 'docer.py'
    description: str = 'process_file() + 0 more'
    functions: list[str] = ['process_file']
    notes: str = ''
    source: str = _DOCER_SOURCE

class FlatenTool(BaseTool):
    """Wrapper for original flaten.py: flatten_directory() + 1 more."""
    name: str = 'flaten'
    source_file: str = 'flaten.py'
    description: str = 'flatten_directory() + 1 more'
    functions: list[str] = ['flatten_directory', 'main']
    notes: str = ''
    source: str = _FLATEN_SOURCE

class MoveTestsDirsTool(BaseTool):
    """Wrapper for original move_tests_dirs.py: move_tests_folder() + 1 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'move_tests_dirs'
    source_file: str = 'move_tests_dirs.py'
    description: str = 'move_tests_folder() + 1 more'
    functions: list[str] = ['move_tests_folder', 'move_tests_recursive']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _MOVE_TESTS_DIRS_SOURCE

class MoveTestsFilesTool(BaseTool):
    """Wrapper for original move_tests_files.py: is_test_file() + 8 more."""
    name: str = 'move_tests_files'
    source_file: str = 'move_tests_files.py'
    description: str = 'is_test_file() + 8 more'
    functions: list[str] = ['is_test_file', 'get_relative_path', 'move_file', 'find_test_files', 'move_files_parallel', 'reverse_move', 'save_log', 'cleanup_empty_dirs', 'main']
    notes: str = ''
    source: str = _MOVE_TESTS_FILES_SOURCE

class MovebinTool(BaseTool):
    """Wrapper for original movebin.py: main() + 0 more."""
    name: str = 'movebin'
    source_file: str = 'movebin.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _MOVEBIN_SOURCE

class PycpTool(BaseTool):
    """Wrapper for original pycp.py: top-level script NOTE: no __main__ guard (top-level script or library fragment; exec runs top-level code)."""
    name: str = 'pycp'
    source_file: str = 'pycp.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = 'no __main__ guard (top-level script or library fragment; exec runs top-level code)'
    source: str = _PYCP_SOURCE

class TobinTool(BaseTool):
    """Wrapper for original tobin.py: get_sha256() + 1 more."""
    name: str = 'tobin'
    source_file: str = 'tobin.py'
    description: str = 'get_sha256() + 1 more'
    functions: list[str] = ['get_sha256', 'main']
    notes: str = ''
    source: str = _TOBIN_SOURCE

class ToscTool(BaseTool):
    """Wrapper for original tosc.py: main() + 0 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'tosc'
    source_file: str = 'tosc.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _TOSC_SOURCE

class WwwTool(BaseTool):
    """Wrapper for original www.py: top-level script."""
    name: str = 'www'
    source_file: str = 'www.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _WWW_SOURCE

class MoveFilesToDirUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'collect_files': CollectFilesTool,
        'dir_mover': DirMoverTool,
        'docer': DocerTool,
        'flaten': FlatenTool,
        'move_tests_dirs': MoveTestsDirsTool,
        'move_tests_files': MoveTestsFilesTool,
        'movebin': MovebinTool,
        'pycp': PycpTool,
        'tobin': TobinTool,
        'tosc': ToscTool,
        'www': WwwTool,
    }

    @classmethod
    def list_tools(cls: type[MoveFilesToDirUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[MoveFilesToDirUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[MoveFilesToDirUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for move_files_to_dir (11 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[MoveFilesToDirUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[MoveFilesToDirUnified], argv: Sequence[str] | None = None) -> int:
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
    return MoveFilesToDirUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

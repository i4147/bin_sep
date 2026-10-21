#!/usr/bin/env python3
"""FileWatcherUnified for file_watcher.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (6):
  dw <- dw.py (99L): tail_file() + 3 more
  fwatcher <- fwatcher.py (59L): watch_tor_log() + 1 more
  watch_file <- watch_file.py (43L): tail_file() + 1 more
  watcher <- watcher.py (8L): top-level script
  where <- where.py (264L): parse_csv_exts() + 5 more [requires missing module 'dh' (ImportError at runtime)]
  wtmp <- wtmp.py (71L): copy_if_match() + 1 more

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

_DW_SOURCE: str = (
    'import argparse\n'
    'import contextlib\n'
    'import shutil\n'
    'import sys\n'
    'import time\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def tail_file(fname, n=10):\n'
    '    try:\n'
    '        with open(fname) as f:\n'
    '            lines = f.readlines()\n'
    '            return lines[-n:] if lines else []\n'
    '    except OSError as e:\n'
    '        print(f"Error reading file: {e}", file=sys.stderr)\n'
    '        return []\n'
    '\n'
    '\n'
    'def get_all_files(folder):\n'
    '    files = {}\n'
    '    try:\n'
    '        base = Path(folder)\n'
    '        for p in base.rglob("*"):\n'
    '            if p.is_file():\n'
    '                with contextlib.suppress(OSError):\n'
    '                    files[str(p)] = p.stat().st_mtime\n'
    '    except OSError as e:\n'
    '        print(f"Error scanning folder: {e}", file=sys.stderr)\n'
    '    return files\n'
    '\n'
    '\n'
    'def copy_file(src, dst_folder):\n'
    '    try:\n'
    '        if dst_folder:\n'
    '            dst_folder.mkdir(parents=True, exist_ok=True)\n'
    '            shutil.copy2(src, dst_folder)\n'
    '        return True\n'
    '    except OSError as e:\n'
    '        print(f"Error copying file: {e}", file=sys.stderr)\n'
    '        return False\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(description="Recursively watch folder for file changes")\n'
    '    parser.add_argument("folder", help="Folder to watch")\n'
    '    parser.add_argument("-c", "--copy", action="store_true", help="Copy changed files to ~/tmp/tmp")\n'
    '    args = parser.parse_args()\n'
    '    folder = Path(args.folder)\n'
    '    copy_enabled = args.copy\n'
    '    if not folder.is_dir():\n'
    '        print(f"Error: Folder \'{folder}\' not found", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    copy_dest = None\n'
    '    if copy_enabled:\n'
    '        copy_dest = Path.home() / "tmp" / "tmp"\n'
    '        print(f"Copy mode enabled. Destination: {copy_dest}\\n")\n'
    '    file_mtimes = get_all_files(folder)\n'
    '    print(f"Watching folder \'{folder}\' recursively...")\n'
    '    print(f"Tracking {len(file_mtimes)} files\\n")\n'
    '    print("(Press Ctrl+C to exit)\\n")\n'
    '    try:\n'
    '        while True:\n'
    '            current_files = get_all_files(folder)\n'
    '            for path_str, current_mtime in current_files.items():\n'
    '                path = Path(path_str)\n'
    '                last_mtime = file_mtimes.get(path_str)\n'
    '                if last_mtime is None or current_mtime > last_mtime:\n'
    '                    file_mtimes[path_str] = current_mtime\n'
    '                    if last_mtime is not None:\n'
    '                        try:\n'
    '                            rel_path = path.relative_to(folder)\n'
    '                        except ValueError:\n'
    '                            rel_path = path\n'
    '                        event = "CREATED" if last_mtime is None else "MODIFIED"\n'
    '                        print(f"[{event}] {rel_path}")\n'
    '                        if copy_enabled:\n'
    '                            copy_file(path, copy_dest)\n'
    '                        lines = tail_file(path, n=10)\n'
    '                        tail_text = "".join(lines)\n'
    '                        if "boostraped 100%" in tail_text:\n'
    '                            print("\\n✓ Bootstrap complete detected! Exiting...\\n")\n'
    '                            sys.exit(0)\n'
    '            deleted = set(file_mtimes.keys()) - set(current_files.keys())\n'
    '            for path_str in deleted:\n'
    '                path = Path(path_str)\n'
    '                try:\n'
    '                    rel_path = path.relative_to(folder)\n'
    '                except ValueError:\n'
    '                    rel_path = path\n'
    '                print(f"[DELETED] {rel_path}")\n'
    '                del file_mtimes[path_str]\n'
    '            time.sleep(1)\n'
    '    except KeyboardInterrupt:\n'
    '        print("\\n\\nWatcher stopped.")\n'
    '        sys.exit(0)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_FWATCHER_SOURCE: str = (
    'import os\n'
    'import time\n'
    '\n'
    '\n'
    'def watch_tor_log(log_path="~/.tor/tor.log"):\n'
    '    log_path = os.path.expanduser(log_path)\n'
    '    if not os.path.exists(log_path):\n'
    '        print(f"Log file not found: {log_path}")\n'
    '        print("Waiting for file to be created...")\n'
    '    last_position = 0\n'
    '    try:\n'
    '        if os.path.exists(log_path):\n'
    '            with open(log_path) as f:\n'
    '                lines = f.readlines()\n'
    '                print("=== Last 5 lines of Tor log ===")\n'
    '                for line in lines[-5:]:\n'
    '                    print(line.rstrip())\n'
    '                last_position = f.tell()\n'
    '                f.close()\n'
    '    except Exception as e:\n'
    '        print(f"Error reading file: {e}")\n'
    '    print("\\n=== Watching for \'100% (done)\' ===")\n'
    '    try:\n'
    '        while True:\n'
    '            if not os.path.exists(log_path):\n'
    '                time.sleep(0.5)\n'
    '                continue\n'
    '            with open(log_path) as f:\n'
    '                f.seek(last_position)\n'
    '                new_lines = f.readlines()\n'
    '                last_position = f.tell()\n'
    '                if new_lines:\n'
    '                    f.seek(0, os.SEEK_END)\n'
    '                    file_size = f.tell()\n'
    '                    f.seek(max(0, file_size - 4096))\n'
    '                    content = f.read()\n'
    '                    lines = content.splitlines()\n'
    '                    print(f"\\n--- Update at {time.strftime(\'%H:%M:%S\')} ---")\n'
    '                    for line in lines[-5:]:\n'
    '                        print(line)\n'
    '                    for line in lines[-10:]:\n'
    '                        if "100%" in line.lower() or "(done)" in line.lower():\n'
    '                            print("\\n✓ Bootstrap complete! Exiting...")\n'
    '                            return\n'
    '                time.sleep(0.5)\n'
    '    except KeyboardInterrupt:\n'
    '        print("\\n\\nMonitoring stopped by user")\n'
    '        return\n'
    '\n'
    '\n'
    'def main():\n'
    '    import sys\n'
    '\n'
    '    log_path = sys.argv[1] if len(sys.argv) > 1 else "~/.tor/tor.log"\n'
    '    watch_tor_log(log_path)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_WATCH_FILE_SOURCE: str = (
    'import os\n'
    'import sys\n'
    'import time\n'
    '\n'
    '\n'
    'def tail_file(fname, n=10):\n'
    '    try:\n'
    '        with open(fname) as f:\n'
    '            lines = f.readlines()\n'
    '            return lines[-n:] if lines else []\n'
    '    except OSError as e:\n'
    '        print(f"Error reading file: {e}", file=sys.stderr)\n'
    '        return []\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python script.py <filename>", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    fname = sys.argv[1]\n'
    '    last_mtime = os.stat(fname).st_mtime\n'
    '    print(f"Watching \'{fname}\'... (Press Ctrl+C to exit)\\n")\n'
    '    try:\n'
    '        while True:\n'
    '            current_mtime = os.stat(fname).st_mtime\n'
    '            if current_mtime > last_mtime:\n'
    '                last_mtime = current_mtime\n'
    '                print(f"\\n--- Change detected at {time.strftime(\'%H:%M:%S\')} ---")\n'
    '                lines = tail_file(fname, n=10)\n'
    '                for line in lines:\n'
    '                    print(line.rstrip("\\n"))\n'
    '                tail_text = "".join(lines)\n'
    '                if "boostraped 100%" in tail_text:\n'
    '                    print("\\n✓ Bootstrap complete detected! Exiting...\\n")\n'
    '                    sys.exit(0)\n'
    '            time.sleep(1)\n'
    '    except KeyboardInterrupt:\n'
    '        print("\\n\\nWatcher stopped.")\n'
    '        sys.exit(0)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_WATCHER_SOURCE: str = (
    'from pathlib import Path\n'
    'from watchfiles import watch\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd().resolve()\n'
    '    print(f"watching {cwd} for changes ...")\n'
    '    for change in watch(str(cwd)):\n'
    '        print(change)\n'
)

_WHERE_SOURCE: str = (
    'import argparse\n'
    'import contextlib\n'
    'import shutil\n'
    'import sys\n'
    'import time\n'
    'import traceback\n'
    'from pathlib import Path\n'
    'from dh import fsz\n'
    'from watchdog.events import FileSystemEventHandler\n'
    'from watchdog.observers import Observer\n'
    '\n'
    '\n'
    'def parse_csv_exts(s):\n'
    '    if not s:\n'
    '        return None\n'
    '    parts = [p.strip().lower() for p in s.split(",") if p.strip()]\n'
    '    if not parts:\n'
    '        return None\n'
    '    norm = set()\n'
    '    for p in parts:\n'
    '        if not p.startswith("."):\n'
    '            p = "." + p\n'
    '        norm.add(p)\n'
    '    return norm\n'
    '\n'
    '\n'
    'def file_matches_extensions(path, allowed_exts):\n'
    '    if allowed_exts is None:\n'
    '        return True\n'
    '    return path.suffix.lower() in allowed_exts\n'
    '\n'
    '\n'
    'def file_matches_exclude(path, excluded_exts):\n'
    '    if excluded_exts is None:\n'
    '        return False\n'
    '    return path.suffix.lower() in excluded_exts\n'
    '\n'
    '\n'
    'def safe_copy_file(src, dst_root, rel_path, errors):\n'
    '    try:\n'
    '        dst_path = dst_root / rel_path\n'
    '        dst_path.parent.mkdir(parents=True, exist_ok=True)\n'
    '        shutil.copy2(src, dst_path)\n'
    '    except Exception as e:\n'
    '        msg = f"[copy-error] {src} -> {dst_root / rel_path}\\n{e}\\n{traceback.format_exc()}"\n'
    '        errors.append(msg)\n'
    '\n'
    '\n'
    'class ChangeHandler(FileSystemEventHandler):\n'
    '    def __init__(\n'
    '        self,\n'
    '        cwd,\n'
    '        copy_enabled,\n'
    '        dest_dir,\n'
    '        allowed_exts,\n'
    '        excluded_exts,\n'
    '        interval_sec,\n'
    '        print_lock=None,\n'
    '    ):\n'
    '        super().__init__()\n'
    '        self.cwd = cwd\n'
    '        self.copy_enabled = copy_enabled\n'
    '        self.dest_dir = dest_dir\n'
    '        self.allowed_exts = allowed_exts\n'
    '        self.excluded_exts = excluded_exts\n'
    '        self.interval_sec = interval_sec\n'
    '        self._errors = []\n'
    '        self._pending = {}\n'
    '        self._last_flush = time.time()\n'
    '\n'
    '    def _rel(self, p):\n'
    '        try:\n'
    '            return p.relative_to(self.cwd)\n'
    '        except ValueError:\n'
    '            return Path(p.name)\n'
    '\n'
    '    def _should_process(self, src_path):\n'
    '        if (src_path.exists() and src_path.is_file()) or not src_path.exists():\n'
    '            if self.allowed_exts is not None and not file_matches_extensions(src_path, self.allowed_exts):\n'
    '                return False\n'
    '            return not (self.excluded_exts is not None and file_matches_exclude(src_path, self.excluded_exts))\n'
    '        return False\n'
    '\n'
    '    def _queue(self, src_path, reason):\n'
    '        if not self._should_process(src_path):\n'
    '            return\n'
    '        if src_path.exists() and src_path.is_dir():\n'
    '            return\n'
    '        self._pending[src_path] = reason\n'
    '        self._maybe_flush()\n'
    '\n'
    '    def _maybe_flush(self):\n'
    '        now = time.time()\n'
    '        if now - self._last_flush >= self.interval_sec:\n'
    '            self.flush()\n'
    '\n'
    '    def flush(self):\n'
    '        if not self._pending:\n'
    '            self._last_flush = time.time()\n'
    '            return\n'
    '        for src_path, reason in list(self._pending.items()):\n'
    '            try:\n'
    '                rel_path = self._rel(src_path)\n'
    '                if src_path.exists() and src_path.is_file():\n'
    '                    try:\n'
    '                        sz = src_path.stat().st_size\n'
    '                        size_str = fsz(sz)\n'
    '                    except Exception:\n'
    '                        size_str = "unknown-size"\n'
    '                    print(f"-  /{rel_path.as_posix()} | {reason} | {size_str}")\n'
    '                    if self.copy_enabled:\n'
    '                        safe_copy_file(\n'
    '                            src=src_path,\n'
    '                            dst_root=self.dest_dir,\n'
    '                            rel_path=rel_path,\n'
    '                            errors=self._errors,\n'
    '                        )\n'
    '                elif not src_path.exists():\n'
    '                    print(f"-  /{rel_path.as_posix()} | {reason} | deleted")\n'
    '                    if self.copy_enabled:\n'
    '                        dst_file = self.dest_dir / rel_path\n'
    '                        if dst_file.exists():\n'
    '                            try:\n'
    '                                dst_file.unlink()\n'
    '                                print(f"  → removed from destination: /{rel_path.as_posix()}")\n'
    '                            except Exception as e:\n'
    '                                msg = f"[delete-error] {dst_file}\\n{e}"\n'
    '                                self._errors.append(msg)\n'
    '            except Exception as e:\n'
    '                msg = f"[processing-error] {src_path}\\n{e}"\n'
    '                self._errors.append(msg)\n'
    '        self._pending.clear()\n'
    '        self._last_flush = time.time()\n'
    '        if self._errors:\n'
    '            print("\\n[errors] copy operation errors:")\n'
    '            for msg in self._errors:\n'
    '                print(msg)\n'
    '            print("-" * 40)\n'
    '            self._errors.clear()\n'
    '\n'
    '    def on_created(self, event):\n'
    '        if event.is_directory:\n'
    '            return\n'
    '        self._queue(Path(event.src_path), "create")\n'
    '\n'
    '    def on_modified(self, event):\n'
    '        if event.is_directory:\n'
    '            return\n'
    '        self._queue(Path(event.src_path), "change")\n'
    '\n'
    '    def on_deleted(self, event):\n'
    '        if event.is_directory:\n'
    '            return\n'
    '        self._queue(Path(event.src_path), "delete")\n'
    '\n'
    '    def on_moved(self, event):\n'
    '        if event.is_directory:\n'
    '            return\n'
    '        self._queue(Path(event.src_path), "moved-out")\n'
    '        self._queue(Path(event.dest_path), "moved-in")\n'
    '\n'
    '\n'
    'def build_parser():\n'
    '    p = argparse.ArgumentParser(\n'
    '        description="Watch a folder recursively, print changes, and optionally copy changed/created files."\n'
    '    )\n'
    '    p.add_argument(\n'
    '        "folder",\n'
    '        nargs="?",\n'
    '        default=str(Path.cwd()),\n'
    '        help="Folder to watch (default: current working directory).",\n'
    '    )\n'
    '    p.add_argument(\n'
    '        "-c",\n'
    '        "--copy",\n'
    '        action="store_true",\n'
    '        help="Copy changed/created files to destination.",\n'
    '    )\n'
    '    p.add_argument(\n'
    '        "-d",\n'
    '        "--dest",\n'
    '        default=str(Path.home() / "tmp" / "tgz"),\n'
    '        help="Destination folder for copies (default: ~/tmp/tgz).",\n'
    '    )\n'
    '    p.add_argument(\n'
    '        "-e",\n'
    '        "--extensions",\n'
    '        default=None,\n'
    '        help="Comma-separated allowlist of file extensions to copy, e.g. \'svg,png,txt\'. If omitted, copy all changed/created file types.",\n'
    '    )\n'
    '    p.add_argument(\n'
    '        "-x",\n'
    '        "--exclude",\n'
    '        default=None,\n'
    '        help="Comma-separated list of file extensions to exclude from copying, e.g. \'log,tmp\'.",\n'
    '    )\n'
    '    p.add_argument(\n'
    '        "-i",\n'
    '        "--interval",\n'
    '        type=float,\n'
    '        default=1.0,\n'
    '        help="Watch interval (seconds) for batching/printing and copying (default: 1.0).",\n'
    '    )\n'
    '    p.add_argument(\n'
    '        "--no-recursive",\n'
    '        action="store_true",\n'
    '        help="Disable recursive watching (watch only top-level directory).",\n'
    '    )\n'
    '    return p\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = build_parser()\n'
    '    args = parser.parse_args()\n'
    '    cwd = Path(args.folder).expanduser().resolve()\n'
    '    dest_dir = Path(args.dest).expanduser().resolve()\n'
    '    if not cwd.is_dir():\n'
    '        print(f"Error: folder does not exist or is not a directory: {cwd}")\n'
    '        sys.exit(2)\n'
    '    allowed_exts = parse_csv_exts(args.extensions)\n'
    '    excluded_exts = parse_csv_exts(args.exclude)\n'
    '    interval_sec = max(0.1, float(args.interval))\n'
    '    if args.copy:\n'
    '        dest_dir.mkdir(parents=True, exist_ok=True)\n'
    '    handler = ChangeHandler(\n'
    '        cwd=cwd,\n'
    '        copy_enabled=bool(args.copy),\n'
    '        dest_dir=dest_dir,\n'
    '        allowed_exts=allowed_exts,\n'
    '        excluded_exts=excluded_exts,\n'
    '        interval_sec=interval_sec,\n'
    '    )\n'
    '    observer = Observer()\n'
    '    observer.schedule(handler, str(cwd), recursive=not args.no_recursive)\n'
    '    observer.start()\n'
    '    print(f"Watching: {cwd}")\n'
    '    if args.no_recursive:\n'
    '        print("Mode: Non-recursive (top-level only)")\n'
    '    else:\n'
    '        print("Mode: Recursive (all subdirectories)")\n'
    '    if args.copy:\n'
    '        print(f"Copy enabled: destination = {dest_dir}")\n'
    '    else:\n'
    '        print("Copy disabled (printing only).")\n'
    '    if allowed_exts is not None:\n'
    '        print(f"Allowed extensions: {sorted(allowed_exts)}")\n'
    '    if excluded_exts is not None:\n'
    '        print(f"Excluded extensions: {sorted(excluded_exts)}")\n'
    '    print(f"Interval: {interval_sec} sec (batch flush)\\n")\n'
    '    try:\n'
    '        while True:\n'
    '            time.sleep(interval_sec)\n'
    '            handler.flush()\n'
    '    except KeyboardInterrupt:\n'
    '        print("\\nStopping...")\n'
    '    finally:\n'
    '        with contextlib.suppress(Exception):\n'
    '            handler.flush()\n'
    '        observer.stop()\n'
    '        observer.join()\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_WTMP_SOURCE: str = (
    'import shutil\n'
    'import sys\n'
    'import time\n'
    'from pathlib import Path\n'
    'from watchdog.events import FileSystemEventHandler\n'
    'from watchdog.observers import Observer\n'
    '\n'
    'TEMPDIR = Path("/data/data/com.termux/files/usr/tmp")\n'
    'DEST_DIR = Path("~/tmp/tgz").expanduser()\n'
    'ALLOWED_EXTENSIONS = (\n'
    '    ".tar.gz",\n'
    '    ".whl",\n'
    '    ".tar.xz",\n'
    '    ".zip",\n'
    '    ".tar.bz2",\n'
    '    ".tar.lzma",\n'
    '    ".tar.lz4",\n'
    '    ".tgz",\n'
    '    ".txz",\n'
    '    ".tbz2",\n'
    '    ".tbr",\n'
    ')\n'
    '\n'
    '\n'
    'def copy_if_match(src):\n'
    '    if any(str(src).endswith(ext) for ext in ALLOWED_EXTENSIONS):\n'
    '        try:\n'
    '            DEST_DIR.mkdir(parents=True, exist_ok=True)\n'
    '            dest = DEST_DIR / src.name\n'
    '            shutil.copy2(src, dest)\n'
    '            print(f"Copied: {src}")\n'
    '        except Exception as e:\n'
    '            print(f"Failed to copy {src}: {e}")\n'
    '\n'
    '\n'
    'def startup_scan(root):\n'
    '    for path in root.rglob("*"):\n'
    '        if path.is_file():\n'
    '            copy_if_match(path)\n'
    '\n'
    '\n'
    'class CopyEventHandler(FileSystemEventHandler):\n'
    '    def on_created(self, event):\n'
    '        if not event.is_directory:\n'
    '            copy_if_match(Path(event.src_path))\n'
    '\n'
    '    def on_modified(self, event):\n'
    '        if not event.is_directory:\n'
    '            copy_if_match(Path(event.src_path))\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    watch_path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else TEMPDIR\n'
    '    if not watch_path.exists():\n'
    '        print(f"Error: Path {watch_path} does not exist")\n'
    '        sys.exit(1)\n'
    '    print(f"Watching: {watch_path}")\n'
    '    print(f"Destination: {DEST_DIR}")\n'
    '    startup_scan(watch_path)\n'
    '    event_handler = CopyEventHandler()\n'
    '    observer = Observer()\n'
    '    observer.schedule(event_handler, str(watch_path), recursive=True)\n'
    '    observer.start()\n'
    '    try:\n'
    '        while True:\n'
    '            time.sleep(1)\n'
    '    except KeyboardInterrupt:\n'
    '        print("\\nStopping observer...")\n'
    '        observer.stop()\n'
    '        observer.join()\n'
    '        print("Script terminated.")\n'
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


class DwTool(BaseTool):
    """Wrapper for original dw.py: tail_file() + 3 more."""
    name: str = 'dw'
    source_file: str = 'dw.py'
    description: str = 'tail_file() + 3 more'
    functions: list[str] = ['tail_file', 'get_all_files', 'copy_file', 'main']
    notes: str = ''
    source: str = _DW_SOURCE

class FwatcherTool(BaseTool):
    """Wrapper for original fwatcher.py: watch_tor_log() + 1 more."""
    name: str = 'fwatcher'
    source_file: str = 'fwatcher.py'
    description: str = 'watch_tor_log() + 1 more'
    functions: list[str] = ['watch_tor_log', 'main']
    notes: str = ''
    source: str = _FWATCHER_SOURCE

class WatchFileTool(BaseTool):
    """Wrapper for original watch_file.py: tail_file() + 1 more."""
    name: str = 'watch_file'
    source_file: str = 'watch_file.py'
    description: str = 'tail_file() + 1 more'
    functions: list[str] = ['tail_file', 'main']
    notes: str = ''
    source: str = _WATCH_FILE_SOURCE

class WatcherTool(BaseTool):
    """Wrapper for original watcher.py: top-level script."""
    name: str = 'watcher'
    source_file: str = 'watcher.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _WATCHER_SOURCE

class WhereTool(BaseTool):
    """Wrapper for original where.py: parse_csv_exts() + 5 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'where'
    source_file: str = 'where.py'
    description: str = 'parse_csv_exts() + 5 more'
    functions: list[str] = ['parse_csv_exts', 'file_matches_extensions', 'file_matches_exclude', 'safe_copy_file', 'build_parser', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _WHERE_SOURCE

class WtmpTool(BaseTool):
    """Wrapper for original wtmp.py: copy_if_match() + 1 more."""
    name: str = 'wtmp'
    source_file: str = 'wtmp.py'
    description: str = 'copy_if_match() + 1 more'
    functions: list[str] = ['copy_if_match', 'startup_scan']
    notes: str = ''
    source: str = _WTMP_SOURCE

class FileWatcherUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'dw': DwTool,
        'fwatcher': FwatcherTool,
        'watch_file': WatchFileTool,
        'watcher': WatcherTool,
        'where': WhereTool,
        'wtmp': WtmpTool,
    }

    @classmethod
    def list_tools(cls: type[FileWatcherUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[FileWatcherUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[FileWatcherUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for file_watcher (6 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[FileWatcherUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[FileWatcherUnified], argv: Sequence[str] | None = None) -> int:
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
    return FileWatcherUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""CCppCompileUnified for c_cpp_compile.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (4):
  compile_c_cpp_files <- compile_c_cpp_files.py (67L): compile_file() + 1 more
  crun <- crun.py (52L): get_filez() + 2 more [requires missing module 'dh' (ImportError at runtime)]
  cytonizer <- cytonizer.py (35L): process_file() + 1 more [requires missing module 'dh' (ImportError at runtime)]
  mkc <- mkc.py (37L): compile_file() + 0 more

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

_COMPILE_C_CPP_FILES_SOURCE: str = (
    'import subprocess\n'
    'import sys\n'
    'from multiprocessing import Pool\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def compile_file(args):\n'
    '    path, compiler, output_path = args\n'
    '    try:\n'
    '        cmd = [compiler, str(path), "-o", str(output_path)]\n'
    '        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)\n'
    '        if result.returncode == 0:\n'
    '            return (\n'
    '                str(path),\n'
    '                True,\n'
    '                f"✓ Compiled: {path.name} -> {output_path.name}",\n'
    '            )\n'
    '        else:\n'
    '            return (\n'
    '                str(path),\n'
    '                False,\n'
    '                f"✗ Failed: {path.name}\\n{result.stderr}",\n'
    '            )\n'
    '    except subprocess.TimeoutExpired:\n'
    '        return (str(path), False, f"✗ Timeout: {path.name}")\n'
    '    except Exception as e:\n'
    '        return (str(path), False, f"✗ Error: {path.name} - {e!s}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    root_dir = Path.cwd()\n'
    '    print(f"Scanning directory: {root_dir}\\n")\n'
    '    c_files = list(root_dir.rglob("*.c"))\n'
    '    cpp_files = list(root_dir.rglob("*.cpp"))\n'
    '    tasks = []\n'
    '    for c_file in c_files:\n'
    '        output_path = c_file.with_suffix("")\n'
    '        tasks.append((c_file, "clang", output_path))\n'
    '    for cpp_file in cpp_files:\n'
    '        output_path = cpp_file.with_suffix("")\n'
    '        tasks.append((cpp_file, "clang++", output_path))\n'
    '    if not tasks:\n'
    '        print("No .c or .cpp files found.")\n'
    '        return\n'
    '    print(f"Found {len(c_files)} .c file(s) and {len(cpp_files)} .cpp file(s)")\n'
    '    print(f"Starting compilation with 4 workers...\\n")\n'
    '    with Pool(processes=4) as pool:\n'
    '        results = pool.map(compile_file, tasks)\n'
    '    print("\\n" + "=" * 40)\n'
    '    print("Compilation Results:")\n'
    '    print("=" * 40 + "\\n")\n'
    '    successful = 0\n'
    '    failed = 0\n'
    '    for _path, success, message in results:\n'
    '        print(message)\n'
    '        if success:\n'
    '            successful += 1\n'
    '        else:\n'
    '            failed += 1\n'
    '    print("\\n" + "=" * 40)\n'
    '    print(f"Summary: {successful} successful, {failed} failed")\n'
    '    print("=" * 40)\n'
    '    sys.exit(0 if failed == 0 else 1)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_CRUN_SOURCE: str = (
    'from pathlib import Path\n'
    'from dh import fsz, gsz, mpf3, should_skip\n'
    '\n'
    '\n'
    'def get_filez(root_dir):\n'
    '    from os import walk as os_walk\n'
    '\n'
    '    visited_dirs = set()\n'
    '    root_dir = Path(root_dir)\n'
    '    if root_dir.is_dir():\n'
    '        for dirpath, dirnames, filenames in os_walk(root_dir, topdown=True):\n'
    '            base_path = Path(dirpath)\n'
    '            for dirname in list(dirnames):\n'
    '                full_path = base_path / dirname\n'
    '                resolved_path = full_path.resolve()\n'
    '                if should_skip(full_path) or resolved_path in visited_dirs:\n'
    '                    dirnames.remove(dirname)\n'
    '                visited_dirs.add(resolved_path)\n'
    '            for filename in filenames:\n'
    '                path = Path(dirpath) / filename\n'
    '                if not should_skip(path):\n'
    '                    yield path\n'
    '    else:\n'
    '        yield root_dir\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    if not path.exists():\n'
    '        return False\n'
    '    if path.suffix == ".c":\n'
    '        cmd = f"clang {path!s} -o {path.with_suffix(\'\')!s}"\n'
    '    if path.suffix == ".cpp":\n'
    '        cmd = f"clang++ {path!s} -o {path.with_suffix(\'\')!s}"\n'
    '    ret, txt, _err = run_command(cmd)\n'
    '    print(txt)\n'
    '    return ret\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path().cwd()\n'
    '    start_size = gsz(cwd)\n'
    '    files = []\n'
    '    for path in get_filez(cwd):\n'
    '        if path.is_file() and path.suffix in {".c", ".cpp"}:\n'
    '            files.append(path)\n'
    '    mpf3(process_file, files)\n'
    '    print(f"{fsz(start_size - gsz(cwd))}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_CYTONIZER_SOURCE: str = (
    'import os\n'
    'import sys\n'
    'from os import chdir as os_chdir\n'
    'from pathlib import Path\n'
    'from dh import get_files, mpf3\n'
    '\n'
    'START_DIR = Path.cwd()\n'
    'NUM_PROCESSES = 4\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    pardir = path.parent\n'
    '    os_chdir(pardir)\n'
    '    os.system(f"cythonize {path.name}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path.cwd()\n'
    '    args = sys.argv[1:]\n'
    '    files = []\n'
    '    if args:\n'
    '        for arg in args:\n'
    '            p = Path(arg)\n'
    '            if p.is_file():\n'
    '                files.append(p)\n'
    '            elif p.is_dir():\n'
    '                files.extend(get_files(p, ext=[".pyx"]))\n'
    '    else:\n'
    '        files = get_files(cwd, ext=[".pyx"])\n'
    '    _ = mpf3(process_file, files)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_MKC_SOURCE: str = (
    'import subprocess\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def compile_file(source_path):\n'
    '    source = Path(source_path)\n'
    '    if not source.exists():\n'
    '        print(f"Error: {source_path} not found", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    if source.suffix == ".c":\n'
    '        compiler = "clang"\n'
    '    elif source.suffix == ".cpp":\n'
    '        compiler = "clang++"\n'
    '    else:\n'
    '        print(f"Error: unsupported file type {source.suffix}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    output = source.stem\n'
    '    compile_cmd = [compiler, str(source), "-o", output]\n'
    '    try:\n'
    '        result = subprocess.run(compile_cmd, check=True, capture_output=True, text=True)\n'
    '        print(f"Compiled {source_path} → {output}")\n'
    '        strip_cmd = ["strip", output]\n'
    '        subprocess.run(strip_cmd, check=True, capture_output=True)\n'
    '        print(f"Stripped {output}")\n'
    '    except subprocess.CalledProcessError as e:\n'
    '        print("Error: Compilation failed", file=sys.stderr)\n'
    '        if e.stderr:\n'
    '            print(e.stderr, file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python mkc.py <file.c or file.cpp>", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    compile_file(sys.argv[1])\n'
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


class CompileCCppFilesTool(BaseTool):
    """Wrapper for original compile_c_cpp_files.py: compile_file() + 1 more."""
    name: str = 'compile_c_cpp_files'
    source_file: str = 'compile_c_cpp_files.py'
    description: str = 'compile_file() + 1 more'
    functions: list[str] = ['compile_file', 'main']
    notes: str = ''
    source: str = _COMPILE_C_CPP_FILES_SOURCE

class CrunTool(BaseTool):
    """Wrapper for original crun.py: get_filez() + 2 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'crun'
    source_file: str = 'crun.py'
    description: str = 'get_filez() + 2 more'
    functions: list[str] = ['get_filez', 'process_file', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _CRUN_SOURCE

class CytonizerTool(BaseTool):
    """Wrapper for original cytonizer.py: process_file() + 1 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'cytonizer'
    source_file: str = 'cytonizer.py'
    description: str = 'process_file() + 1 more'
    functions: list[str] = ['process_file', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _CYTONIZER_SOURCE

class MkcTool(BaseTool):
    """Wrapper for original mkc.py: compile_file() + 0 more."""
    name: str = 'mkc'
    source_file: str = 'mkc.py'
    description: str = 'compile_file() + 0 more'
    functions: list[str] = ['compile_file']
    notes: str = ''
    source: str = _MKC_SOURCE

class CCppCompileUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'compile_c_cpp_files': CompileCCppFilesTool,
        'crun': CrunTool,
        'cytonizer': CytonizerTool,
        'mkc': MkcTool,
    }

    @classmethod
    def list_tools(cls: type[CCppCompileUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[CCppCompileUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[CCppCompileUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for c_cpp_compile (4 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[CCppCompileUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[CCppCompileUnified], argv: Sequence[str] | None = None) -> int:
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
    return CCppCompileUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

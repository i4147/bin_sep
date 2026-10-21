#!/usr/bin/env python3
"""PickleConvertUnified for pickle_convert.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (3):
  pkl2json <- pkl2json.py (12L): top-level script
  pkltojson <- pkltojson.py (76L): is_json_serializable() + 2 more
  upkl <- upkl.py (12L): top-level script

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

_PKL2JSON_SOURCE: str = (
    'import json\n'
    'import pickle\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    fn = Path(sys.argv[1])\n'
    '    outf = fn.with_suffix(".json")\n'
    '    with open(fn, "rb") as f:\n'
    '        data = pickle.load(f)\n'
    '        with open(outf, "w") as fo:\n'
    '            json.dump(data, fo, ensure_ascii=False, indent=2)\n'
)

_PKLTOJSON_SOURCE: str = (
    'import json\n'
    'import pickle\n'
    'import sys\n'
    'from pathlib import Path\n'
    'from typing import Any\n'
    '\n'
    '\n'
    'def is_json_serializable(obj):\n'
    '    try:\n'
    '        json.dumps(obj)\n'
    '        return True\n'
    '    except (TypeError, ValueError):\n'
    '        return False\n'
    '\n'
    '\n'
    'def serialize_for_json(obj):\n'
    '    if isinstance(obj, (str, int, float, bool, type(None))):\n'
    '        return obj\n'
    '    elif isinstance(obj, (list, tuple)):\n'
    '        return [serialize_for_json(item) for item in obj]\n'
    '    elif isinstance(obj, dict):\n'
    '        return {str(k): serialize_for_json(v) for k, v in obj.items()}\n'
    '    elif isinstance(obj, set):\n'
    '        return list(obj)\n'
    '    elif hasattr(obj, "__dict__"):\n'
    '        return str(obj)\n'
    '    else:\n'
    '        return str(obj)\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python script.py <pickle_file>")\n'
    '        sys.exit(1)\n'
    '    pkl_path = Path(sys.argv[1])\n'
    '    if not pkl_path.exists():\n'
    '        print(f"Error: File not found: {pkl_path}")\n'
    '        sys.exit(1)\n'
    '    if pkl_path.suffix != ".pkl":\n'
    '        print(f"Warning: Expected .pkl file, got {pkl_path.suffix}")\n'
    '    try:\n'
    '        with open(pkl_path, "rb") as f:\n'
    '            data = pickle.load(f)\n'
    '    except Exception as e:\n'
    '        print(f"Error loading pickle: {e}")\n'
    '        sys.exit(1)\n'
    '    print(f"✓ Loaded: {pkl_path}")\n'
    '    print(f"  Type: {type(data).__name__}")\n'
    '    print(f"  Size: {len(str(data))} chars\\n")\n'
    '    print("Content:")\n'
    '    print("-" * 40)\n'
    '    if isinstance(data, dict):\n'
    '        print(json.dumps(data, indent=2, default=str))\n'
    '    else:\n'
    '        print(json.dumps(data, indent=2, default=str))\n'
    '    print("-" * 40)\n'
    '    json_path = pkl_path.with_suffix(".json")\n'
    '    if is_json_serializable(data):\n'
    '        try:\n'
    '            with open(json_path, "w") as f:\n'
    '                json.dump(data, f, indent=2)\n'
    '            print(f"\\n✓ Saved to: {json_path}")\n'
    '        except Exception as e:\n'
    '            print(f"\\n✗ Failed to save JSON: {e}")\n'
    '    else:\n'
    '        try:\n'
    '            serialized = serialize_for_json(data)\n'
    '            with open(json_path, "w") as f:\n'
    '                json.dump(serialized, f, indent=2)\n'
    '            print(f"\\n⚠ Converted non-serializable objects → {json_path}")\n'
    '        except Exception as e:\n'
    '            print(f"\\n✗ Cannot convert to JSON: {e}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    main()\n'
)

_UPKL_SOURCE: str = (
    'import pickle as pkl\n'
    'from pathlib import Path\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    import sys\n'
    '\n'
    '    fn = Path(sys.argv[1].strip())\n'
    '    with fn.open("rb") as f:\n'
    '        data = pkl.load(f)\n'
    '    outf = fn.with_suffix(".raw")\n'
    '    outf.write_bytes(data)\n'
    '    print(data)\n'
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


class Pkl2jsonTool(BaseTool):
    """Wrapper for original pkl2json.py: top-level script."""
    name: str = 'pkl2json'
    source_file: str = 'pkl2json.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _PKL2JSON_SOURCE

class PkltojsonTool(BaseTool):
    """Wrapper for original pkltojson.py: is_json_serializable() + 2 more."""
    name: str = 'pkltojson'
    source_file: str = 'pkltojson.py'
    description: str = 'is_json_serializable() + 2 more'
    functions: list[str] = ['is_json_serializable', 'serialize_for_json', 'main']
    notes: str = ''
    source: str = _PKLTOJSON_SOURCE

class UpklTool(BaseTool):
    """Wrapper for original upkl.py: top-level script."""
    name: str = 'upkl'
    source_file: str = 'upkl.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = ''
    source: str = _UPKL_SOURCE

class PickleConvertUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'pkl2json': Pkl2jsonTool,
        'pkltojson': PkltojsonTool,
        'upkl': UpklTool,
    }

    @classmethod
    def list_tools(cls: type[PickleConvertUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[PickleConvertUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[PickleConvertUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for pickle_convert (3 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[PickleConvertUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[PickleConvertUnified], argv: Sequence[str] | None = None) -> int:
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
    return PickleConvertUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""QrcodeToolsUnified for qrcode_tools.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (2):
  qrcode_reader <- qrcode_reader.py (47L): read_qr_code() + 1 more
  qrcoder <- qrcoder.py (43L): extract_qr_data_zbar() + 1 more

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

_QRCODE_READER_SOURCE: str = (
    'import sys\n'
    'from PIL import Image\n'
    'from pyzbar.pyzbar import decode\n'
    '\n'
    '\n'
    'def read_qr_code(image_path):\n'
    '    try:\n'
    '        img = Image.open(image_path)\n'
    '        decoded_objects = decode(img)\n'
    '        if not decoded_objects:\n'
    '            print("No QR code found in the image.")\n'
    '            return []\n'
    '        print(f"Found {len(decoded_objects)} QR code(s):\\n")\n'
    '        results = []\n'
    '        for i, obj in enumerate(decoded_objects, 1):\n'
    '            data = obj.data.decode("utf-8")\n'
    '            rect = obj.rect\n'
    '            print(f"QR Code {i}:")\n'
    '            print(f"  Data: {data}")\n'
    '            print(f"  Type: {obj.type}")\n'
    '            print(f"  Position: (left={rect.left}, top={rect.top}, width={rect.width}, height={rect.height})")\n'
    '            print()\n'
    '            results.append(data)\n'
    '        return results\n'
    '    except FileNotFoundError:\n'
    '        print(f"Error: Image file \'{image_path}\' not found.")\n'
    '        sys.exit(1)\n'
    '    except Exception as e:\n'
    '        print(f"Error processing image: {e}")\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python qr_reader.py <image_path>")\n'
    '        print("Example: python qr_reader.py qrcode.png")\n'
    '        sys.exit(1)\n'
    '    img_path = sys.argv[1]\n'
    '    print(f"Reading QR code from: {img_path}\\n")\n'
    '    results = read_qr_code(img_path)\n'
    '    if results:\n'
    '        print("First QR code data only:")\n'
    '        print(results[0])\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_QRCODER_SOURCE: str = (
    'import os\n'
    'import sys\n'
    'from PIL import Image\n'
    'from pyzbar import pyzbar\n'
    '\n'
    '\n'
    'def extract_qr_data_zbar(image_path):\n'
    '    try:\n'
    '        with Image.open(image_path) as img:\n'
    '            if img.mode != "RGB":\n'
    '                img = img.convert("RGB")\n'
    '            decoded = pyzbar.decode(img)\n'
    '            results = []\n'
    '            for obj in decoded:\n'
    '                if obj.type == "QRCODE":\n'
    '                    results.append(obj.data.decode("utf-8"))\n'
    '            return results\n'
    '    except Exception as e:\n'
    '        print(f"Error: {e}", file=sys.stderr)\n'
    '        return []\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) != 2:\n'
    '        print("Usage: python qr_extractor.py <path_to_qrcode_image>")\n'
    '        sys.exit(1)\n'
    '    image_path = sys.argv[1]\n'
    '    if not os.path.exists(image_path):\n'
    '        print(f"Error: File \'{image_path}\' not found.")\n'
    '        sys.exit(1)\n'
    '    results = extract_qr_data_zbar(image_path)\n'
    '    if results:\n'
    '        print(f"\\nFound {len(results)} QR code(s):")\n'
    '        print("-" * 40)\n'
    '        for i, data in enumerate(results, 1):\n'
    '            print(f"QR #{i}: {data}")\n'
    '        print("-" * 40)\n'
    '    else:\n'
    '        print("No QR codes found in the image.")\n'
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


class QrcodeReaderTool(BaseTool):
    """Wrapper for original qrcode_reader.py: read_qr_code() + 1 more."""
    name: str = 'qrcode_reader'
    source_file: str = 'qrcode_reader.py'
    description: str = 'read_qr_code() + 1 more'
    functions: list[str] = ['read_qr_code', 'main']
    notes: str = ''
    source: str = _QRCODE_READER_SOURCE

class QrcoderTool(BaseTool):
    """Wrapper for original qrcoder.py: extract_qr_data_zbar() + 1 more."""
    name: str = 'qrcoder'
    source_file: str = 'qrcoder.py'
    description: str = 'extract_qr_data_zbar() + 1 more'
    functions: list[str] = ['extract_qr_data_zbar', 'main']
    notes: str = ''
    source: str = _QRCODER_SOURCE

class QrcodeToolsUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'qrcode_reader': QrcodeReaderTool,
        'qrcoder': QrcoderTool,
    }

    @classmethod
    def list_tools(cls: type[QrcodeToolsUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[QrcodeToolsUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[QrcodeToolsUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for qrcode_tools (2 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[QrcodeToolsUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[QrcodeToolsUnified], argv: Sequence[str] | None = None) -> int:
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
    return QrcodeToolsUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

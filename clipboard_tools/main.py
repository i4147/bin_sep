#!/usr/bin/env python3
"""ClipboardToolsUnified for clipboard_tools.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (5):
  f2l <- f2l.py (31L): main() + 0 more
  l2c <- l2c.py (26L): copy_line_to_clipboard() + 1 more
  tcg <- tcg.py (116L): get_clipboard_content() + 5 more
  tcg3 <- tcg3.py (168L): get_clipboard_content() + 5 more
  tcs <- tcs.py (130L): send_to_process() + 3 more

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

_F2L_SOURCE: str = (
    'import subprocess\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def main():\n'
    '    fn = sys.argv[1]\n'
    '    path = Path(fn)\n'
    '    with path.open(encoding="utf-8") as f:\n'
    '        lines = [line.strip() for line in f]\n'
    '    items = []\n'
    '    for line in lines:\n'
    '        quote_char = "\'" if \'"\' in line else \'"\'\n'
    '        items.append(f"{quote_char}{line}{quote_char}")\n'
    '    formatted_content = "{" + ", ".join(items) + "}"\n'
    '    path.write_text(formatted_content, encoding="utf-8")\n'
    '    try:\n'
    '        subprocess.run(\n'
    '            ["termux-clipboard-set"],\n'
    '            input=formatted_content,\n'
    '            text=True,\n'
    '            capture_output=True,\n'
    '        )\n'
    '        print(f"✓ Updated and copied: {path}")\n'
    '    except FileNotFoundError:\n'
    '        print(f"✓ File updated: {path}")\n'
    '        print("⚠ Install termux-api for clipboard support")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_L2C_SOURCE: str = (
    'import subprocess\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def copy_line_to_clipboard(filename, indx):\n'
    '    input_file = Path(filename)\n'
    '    with input_file.open("r", encoding="utf-8") as f:\n'
    '        lines = f.readlines()\n'
    '    content_to_copy = lines[indx].strip()\n'
    '    process = subprocess.Popen(\n'
    '        ["termux-clipboard-set"],\n'
    '        stdin=subprocess.PIPE,\n'
    '        text=True,\n'
    '        stderr=subprocess.PIPE,\n'
    '    )\n'
    '\n'
    '\n'
    'def main():\n'
    '    fn = sys.argv[1].strip()\n'
    '    lindex = int(sys.argv[2].strip())\n'
    '    copy_line_to_clipboard(fn, lindex)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_TCG_SOURCE: str = (
    'import shutil\n'
    'import subprocess\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    'TERMUX_SHEBANGS = {\n'
    '    "python": "#!/data/data/com.termux/ust",\n'
    '    "bash": "#!/data/data/com.termux/files/usr/bin/bash",\n'
    '    "sh": "#!/data/data/com.termux/files/usr/bin/sh",\n'
    '    "rust": "#!/data/data/com.termux/files/home/.cargo/bin/rust-script",\n'
    '}\n'
    'EXTENSION_MAP = {\n'
    '    ".py": "python",\n'
    '    ".sh": "bash",\n'
    '    ".bash": "bash",\n'
    '    ".rs": "rust",\n'
    '}\n'
    'SCRIPT_DIRS = {\n'
    '    Path.home() / "bin",\n'
    '    Path.home() / "bashbin",\n'
    '    Path.home() / ".cargo" / "bin",\n'
    '}\n'
    'ARCHIVE_DIR = Path.home() / "isaac" / "may" / "scripts"\n'
    '\n'
    '\n'
    'def get_clipboard_content():\n'
    '    try:\n'
    '        result = subprocess.run(["termux-clipboard-get"], capture_output=True, text=True, check=True)\n'
    '        return result.stdout\n'
    '    except subprocess.CalledProcessError as e:\n'
    '        print(f"Failed to read clipboard: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    except FileNotFoundError:\n'
    '        print("Error: termux-clipboard-get not found", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'def get_language_from_extension(filename):\n'
    '    return EXTENSION_MAP.get(Path(filename).suffix.lower(), "bash")\n'
    '\n'
    '\n'
    'def replace_shebang(content, lang):\n'
    '    lines = content.splitlines()\n'
    '    if lines and lines[0].startswith("#!"):\n'
    '        lines.pop(0)\n'
    '    lines.insert(0, TERMUX_SHEBANGS[lang])\n'
    '    result = "\\n".join(lines)\n'
    '    return result if result.endswith("\\n") else result + "\\n"\n'
    '\n'
    '\n'
    'def archive_existing_file(path):\n'
    '    if not path.exists():\n'
    '        return\n'
    '    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)\n'
    '    archive_path = ARCHIVE_DIR / path.name\n'
    '    counter = 1\n'
    '    while archive_path.exists():\n'
    '        archive_name = f"{path.stem}_{counter}{path.suffix}"\n'
    '        archive_path = ARCHIVE_DIR / archive_name\n'
    '        counter += 1\n'
    '    try:\n'
    '        shutil.move(str(path), str(archive_path))\n'
    '        print(f"📦 Archived to: {archive_path}")\n'
    '    except OSError as e:\n'
    '        print(f"❌ Failed to archive: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'def create_symlink(script_path):\n'
    '    if script_path.suffix.lower() == ".rs":\n'
    '        return\n'
    '    symlink_path = script_path.parent / script_path.stem\n'
    '    if symlink_path.exists() and symlink_path.is_symlink():\n'
    '        symlink_path.unlink()\n'
    '    if not symlink_path.exists():\n'
    '        try:\n'
    '            symlink_path.symlink_to(script_path)\n'
    '            print(f"  → Symlink: {symlink_path.name}")\n'
    '        except OSError as e:\n'
    '            print(f"  ⚠️  Symlink failed: {e}", file=sys.stderr)\n'
    '\n'
    '\n'
    'def main():\n'
    '    archive = True\n'
    '    args = [arg for arg in sys.argv[1:] if arg != "-a"]\n'
    '    if len(args) != 1:\n'
    '        print(f"Usage: {sys.argv[0]} [-a] <filename>", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    filename = args[0]\n'
    '    if not "." in filename.strip():\n'
    '        print("you didnt provide an extension,continue?")\n'
    '        ans = input("y/n")\n'
    '        if not ans == "y":\n'
    '            sys.exit(0)\n'
    '    output_path = Path(filename)\n'
    '    is_script_dir = Path.cwd() in SCRIPT_DIRS or Path.cwd().name == "bin"\n'
    '    if archive and output_path.exists():\n'
    '        archive_existing_file(output_path)\n'
    '    content = get_clipboard_content()\n'
    '    if not content.strip():\n'
    '        content = (TERMUX_SHEBANGS[get_language_from_extension(filename)] + "\\n\\n") if is_script_dir else "\\n"\n'
    '    elif is_script_dir:\n'
    '        lang = get_language_from_extension(filename)\n'
    '        content = replace_shebang(content, lang)\n'
    '    try:\n'
    '        output_path.write_text(content)\n'
    '    except OSError as e:\n'
    '        print(f"Error writing file: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    if is_script_dir:\n'
    '        output_path.chmod(0o755)\n'
    '        create_symlink(output_path)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_TCG3_SOURCE: str = (
    'import subprocess\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    'TERMUX_SHEBANGS = {\n'
    '    "python": "#!/data/data/com.termux/files/usr/bin/python",\n'
    '    "bash": "#!/data/data/com.termux/files/usr/bin/bash",\n'
    '    "sh": "#!/data/data/com.termux/files/usr/bin/sh",\n'
    '}\n'
    'SCRIPT_DIRS = {\n'
    '    Path.home() / "bin",\n'
    '    Path.home() / "bashbin",\n'
    '    Path.home() / ".local" / "bin",\n'
    '}\n'
    '\n'
    '\n'
    'def get_clipboard_content():\n'
    '    try:\n'
    '        result = subprocess.run(["termux-clipboard-get"], capture_output=True, text=True, check=True)\n'
    '        return result.stdout\n'
    '    except subprocess.CalledProcessError as e:\n'
    '        print(f"Failed to read clipboard: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    except FileNotFoundError:\n'
    '        print("Error: termux-clipboard-get not found", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'def detect_script_type(content):\n'
    '    if not content.strip():\n'
    '        return "unknown"\n'
    '    first_line = content.lstrip().split("\\n")[0] if content else ""\n'
    '    if first_line.startswith("#!"):\n'
    '        if "python" in first_line.lower():\n'
    '            return "python"\n'
    '        elif "bash" in first_line.lower() or "sh" in first_line.lower():\n'
    '            return "bash"\n'
    '    preview = content[:500].lower()\n'
    '    python_indicators = [\n'
    '        "import ",\n'
    '        "from ",\n'
    '        "def ",\n'
    '        "class ",\n'
    '        "if __name__",\n'
    '        "print(",\n'
    '        "self.",\n'
    '        "__init__",\n'
    '        "async def",\n'
    '        "await ",\n'
    '    ]\n'
    '    bash_indicators = [\n'
    '        "echo ",\n'
    '        "cd ",\n'
    '        "export ",\n'
    '        "if [",\n'
    '        "if [[",\n'
    '        "then",\n'
    '        "elif",\n'
    '        "fi",\n'
    '        "done",\n'
    '        "while ",\n'
    '        "for ",\n'
    '        "case ",\n'
    '        "esac",\n'
    '        "$(",\n'
    '        "${",\n'
    '        "`",\n'
    '        "#!/bin/bash",\n'
    '        "#!/bin/sh",\n'
    '    ]\n'
    '    python_score = sum(1 for ind in python_indicators if ind in preview)\n'
    '    bash_score = sum(1 for ind in bash_indicators if ind in preview)\n'
    '    if python_score > bash_score:\n'
    '        return "python"\n'
    '    elif bash_score > python_score:\n'
    '        return "bash"\n'
    '    else:\n'
    '        return "bash"\n'
    '\n'
    '\n'
    'def get_shebang_from_filename(filename):\n'
    '    path = Path(filename)\n'
    '    suffix = path.suffix.lower()\n'
    '    if suffix in [".py", ".pyw"]:\n'
    '        return "python"\n'
    '    elif suffix in [".sh", ".bash"] or suffix in [".rb", ".pl", ".js", ".go", ".rs"]:\n'
    '        return "bash"\n'
    '    return None\n'
    '\n'
    '\n'
    'def replace_shebang(content, script_type):\n'
    '    lines = content.splitlines()\n'
    '    if lines and lines[0].startswith("#!"):\n'
    '        lines.pop(0)\n'
    '        if lines and lines[0].startswith("#!"):\n'
    '            lines.pop(0)\n'
    '    if script_type == "python":\n'
    '        lines.insert(0, TERMUX_SHEBANGS["python"])\n'
    '    elif script_type == "bash":\n'
    '        lines.insert(0, TERMUX_SHEBANGS["bash"])\n'
    '    else:\n'
    '        lines.insert(0, TERMUX_SHEBANGS["bash"])\n'
    '    result = "\\n".join(lines)\n'
    '    return result if result.endswith("\\n") else result + "\\n"\n'
    '\n'
    '\n'
    'def create_symlink(script_path):\n'
    '    if script_path.suffix:\n'
    '        symlink_path = script_path.parent / script_path.stem\n'
    '        if not symlink_path.exists():\n'
    '            try:\n'
    '                symlink_path.symlink_to(script_path)\n'
    '                print(f"  → Created symlink: {symlink_path.name}")\n'
    '            except OSError as e:\n'
    '                print(f"  ⚠️  Failed to create symlink: {e}", file=sys.stderr)\n'
    '        elif symlink_path.is_symlink():\n'
    '            print(f"  → Symlink already exists: {symlink_path.name}")\n'
    '        else:\n'
    '            print(f"  ⚠️  {symlink_path.name} exists but is not a symlink")\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) != 2:\n'
    '        print(f"Usage: {sys.argv[0]} <filename>", file=sys.stderr)\n'
    '        print(f"Example: {sys.argv[0]} myscript.py", file=sys.stderr)\n'
    '        print(f"Example: {sys.argv[0]} mytool", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    filename = sys.argv[1]\n'
    '    output_path = Path(filename)\n'
    '    cwd = Path.cwd()\n'
    '    is_script_dir = cwd in SCRIPT_DIRS\n'
    '    content = get_clipboard_content()\n'
    '    if not content.strip():\n'
    '        print("⚠️  Clipboard is empty, creating empty file")\n'
    '        content = "\\n"\n'
    '        if is_script_dir:\n'
    '            script_type = get_shebang_from_filename(filename) or "bash"\n'
    '            content = replace_shebang(content, script_type)\n'
    '            print(f"✓ Added {script_type} shebang (inferred from filename)")\n'
    '    else:\n'
    '        script_type = None\n'
    '        if is_script_dir:\n'
    '            script_type = get_shebang_from_filename(filename)\n'
    '            if not script_type:\n'
    '                script_type = detect_script_type(content)\n'
    '                print(f"✓ Detected {script_type} script from content")\n'
    '            else:\n'
    '                print(f"✓ Detected {script_type} script from filename extension")\n'
    '        if is_script_dir and script_type:\n'
    '            content = replace_shebang(content, script_type)\n'
    '    try:\n'
    '        output_path.write_text(content)\n'
    '        print(f"✓ Created: {output_path}")\n'
    '    except OSError as e:\n'
    '        print(f"Error writing file: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    if is_script_dir:\n'
    '        output_path.chmod(0o755)\n'
    '        print("✓ Made executable (755)")\n'
    '        create_symlink(output_path)\n'
    '    if content.strip():\n'
    '        first_line = content.split("\\n")[0]\n'
    '        if first_line.startswith("#!"):\n'
    '            print(f"\\n📄 Shebang: {first_line}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_TCS_SOURCE: str = (
    'import subprocess\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def send_to_process(txt):\n'
    '    try:\n'
    '        process = subprocess.Popen(\n'
    '            ["termux-clipboard-set"],\n'
    '            stdin=subprocess.PIPE,\n'
    '            text=True,\n'
    '            stderr=subprocess.PIPE,\n'
    '        )\n'
    '        _stdout, stderr = process.communicate(input=txt)\n'
    '        if process.returncode != 0:\n'
    '            print(f"Error: Failed to copy to clipboard. STDERR: {stderr}", file=sys.stderr)\n'
    '            sys.exit(1)\n'
    '    except FileNotFoundError:\n'
    '        print(\n'
    '            "Error: \'termux-clipboard-set\' command not found. Is Termux:API installed?",\n'
    '            file=sys.stderr,\n'
    '        )\n'
    '        sys.exit(1)\n'
    '    except Exception as e:\n'
    '        print(\n'
    '            f"An unexpected error occurred while copying to clipboard: {e}",\n'
    '            file=sys.stderr,\n'
    '        )\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'def selective_copy(path, lines):\n'
    '    cl = [p for p in lines if p != "-s"]\n'
    '    selected = []\n'
    '    nl = path.read_text(encoding="utf-8").splitlines()\n'
    '    total = len(nl)\n'
    '    for k in cl:\n'
    '        if 0 <= k <= total:\n'
    '            selected.append(nl[k])\n'
    '    content = "".join(selected)\n'
    '    send_to_process(content)\n'
    '\n'
    '\n'
    'def copy_lines_to_clipboard(path, start_line=None, end_line=None):\n'
    '    content = ""\n'
    '    path = Path(path)\n'
    '    if not path.is_file():\n'
    '        print(f"Error: File not found at \'{path}\'", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    try:\n'
    '        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)\n'
    '    except OSError as e:\n'
    '        print(f"Error reading file \'{path}\': {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    except Exception as e:\n'
    '        print(f"error occurred while reading the file: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    total_lines = len(lines)\n'
    '    if start_line is None:\n'
    '        content = "".join(lines)\n'
    '    else:\n'
    '        start_index = start_line - 1\n'
    '        end_index = total_lines if end_line is None else end_line\n'
    '        if not 0 <= start_index <= total_lines:\n'
    '            start_index = 0\n'
    '        if not 0 <= end_index <= total_lines:\n'
    '            end_index = total_lines\n'
    '        if start_index >= end_index:\n'
    '            start_index, end_index = end_index, start_index\n'
    '        selected_lines = lines[start_index:end_index]\n'
    '        content = "".join(selected_lines)\n'
    '    if not content:\n'
    '        print("No content selected to copy.", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    send_to_process(content)\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2 or len(sys.argv) > 5:\n'
    '        print(f"Usage: {sys.argv[0]} <path> [start_line] [end_line]", file=sys.stderr)\n'
    '        print("  <path>: Path to the input file.", file=sys.stderr)\n'
    '        print(\n'
    '            "  [start_line]: The first line number to copy (1-based index). If omitted, copies the entire file.",\n'
    '            file=sys.stderr,\n'
    '        )\n'
    '        print(\n'
    '            "  [end_line]: The last line number to copy (1-based index). If omitted and start_line is given, copies to the end of the file.",\n'
    '            file=sys.stderr,\n'
    '        )\n'
    '        sys.exit(1)\n'
    '    selective = "-s" in sys.argv[1:]\n'
    '    path = Path(sys.argv[1])\n'
    '    start_line = None\n'
    '    end_line = None\n'
    '    if len(sys.argv) >= 3:\n'
    '        try:\n'
    '            start_line = int(sys.argv[2])\n'
    '        except ValueError:\n'
    '            print("Error: <start_line> must be an integer.", file=sys.stderr)\n'
    '            sys.exit(1)\n'
    '    if len(sys.argv) == 4:\n'
    '        try:\n'
    '            end_line = int(sys.argv[3])\n'
    '        except ValueError:\n'
    '            print("Error: <end_line> must be an integer.", file=sys.stderr)\n'
    '            sys.exit(1)\n'
    '    if start_line is not None and end_line is None and len(sys.argv) == 3:\n'
    '        if not path.is_file():\n'
    '            print(f"Error: File not found at \'{path}\'", file=sys.stderr)\n'
    '            sys.exit(1)\n'
    '        try:\n'
    '            with path.open("r", encoding="utf-8") as f:\n'
    '                total_lines = len(f.readlines())\n'
    '            if not 1 <= start_line <= total_lines:\n'
    '                print(\n'
    '                    f"Error: Start line ({start_line}) is out of bounds. File has {total_lines} lines.",\n'
    '                    file=sys.stderr,\n'
    '                )\n'
    '                sys.exit(1)\n'
    '        except OSError as e:\n'
    '            print(f"Error reading file \'{path}\' for validation: {e}", file=sys.stderr)\n'
    '            sys.exit(1)\n'
    '    if not selective:\n'
    '        copy_lines_to_clipboard(path, start_line, end_line)\n'
    '    else:\n'
    '        selective_copy(path, sys.argv[2:])\n'
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


class F2lTool(BaseTool):
    """Wrapper for original f2l.py: main() + 0 more."""
    name: str = 'f2l'
    source_file: str = 'f2l.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _F2L_SOURCE

class L2cTool(BaseTool):
    """Wrapper for original l2c.py: copy_line_to_clipboard() + 1 more."""
    name: str = 'l2c'
    source_file: str = 'l2c.py'
    description: str = 'copy_line_to_clipboard() + 1 more'
    functions: list[str] = ['copy_line_to_clipboard', 'main']
    notes: str = ''
    source: str = _L2C_SOURCE

class TcgTool(BaseTool):
    """Wrapper for original tcg.py: get_clipboard_content() + 5 more."""
    name: str = 'tcg'
    source_file: str = 'tcg.py'
    description: str = 'get_clipboard_content() + 5 more'
    functions: list[str] = ['get_clipboard_content', 'get_language_from_extension', 'replace_shebang', 'archive_existing_file', 'create_symlink', 'main']
    notes: str = ''
    source: str = _TCG_SOURCE

class Tcg3Tool(BaseTool):
    """Wrapper for original tcg3.py: get_clipboard_content() + 5 more."""
    name: str = 'tcg3'
    source_file: str = 'tcg3.py'
    description: str = 'get_clipboard_content() + 5 more'
    functions: list[str] = ['get_clipboard_content', 'detect_script_type', 'get_shebang_from_filename', 'replace_shebang', 'create_symlink', 'main']
    notes: str = ''
    source: str = _TCG3_SOURCE

class TcsTool(BaseTool):
    """Wrapper for original tcs.py: send_to_process() + 3 more."""
    name: str = 'tcs'
    source_file: str = 'tcs.py'
    description: str = 'send_to_process() + 3 more'
    functions: list[str] = ['send_to_process', 'selective_copy', 'copy_lines_to_clipboard', 'main']
    notes: str = ''
    source: str = _TCS_SOURCE

class ClipboardToolsUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'f2l': F2lTool,
        'l2c': L2cTool,
        'tcg': TcgTool,
        'tcg3': Tcg3Tool,
        'tcs': TcsTool,
    }

    @classmethod
    def list_tools(cls: type[ClipboardToolsUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[ClipboardToolsUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[ClipboardToolsUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for clipboard_tools (5 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[ClipboardToolsUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[ClipboardToolsUnified], argv: Sequence[str] | None = None) -> int:
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
    return ClipboardToolsUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

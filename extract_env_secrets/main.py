#!/usr/bin/env python3
"""ExtractEnvSecretsUnified for extract_env_secrets.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (4):
  collect_env_vars <- collect_env_vars.py (19L): top-level script [no __main__ guard (top-level script or library fragment; exec runs top-level code)]
  secretleak <- secretleak.py (174L): _read_file_text() + 6 more
  to_env <- to.env.py (151L): extract_tokens_with_models() + 3 more
  xenv_vars <- xenv_vars.py (25L): top-level script [no __main__ guard (top-level script or library fragment; exec runs top-level code)]

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

_COLLECT_ENV_VARS_SOURCE: str = (
    'import re\n'
    'from pathlib import Path\n'
    '\n'
    'env_vars = set()\n'
    'env_var_pattern = re.compile("^([A-Z_0-9]+)=")\n'
    'for path in Path().rglob("*"):\n'
    '    if path.is_file():\n'
    '        try:\n'
    '            with open(path, encoding="utf-8") as f:\n'
    '                for line in f:\n'
    '                    match = env_var_pattern.match(line)\n'
    '                    if match:\n'
    '                        env_vars.add(match.group(1))\n'
    '        except Exception as e:\n'
    '            print(f"Could not process file {path}: {e}")\n'
    'output_filename = "env_vars.txt"\n'
    'with open(output_filename, "w", encoding="utf-8") as f:\n'
    '    f.writelines(var + "\\n" for var in sorted(env_vars))\n'
    'print(f"Found {len(env_vars)} unique environment variable names. Saved to {output_filename}")\n'
)

_SECRETLEAK_SOURCE: str = (
    'import re\n'
    'import sys\n'
    'from multiprocessing import Pool\n'
    'from pathlib import Path\n'
    'from typing import Any\n'
    'from loguru import logger\n'
    '\n'
    'SECRET_PATTERNS = {\n'
    '    "AWS Key": "AKIA[0-9A-Z]{16}",\n'
    '    "Private Key": "-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",\n'
    '    "GitHub Token": "ghp_[A-Za-z0-9_]{36,255}",\n'
    '    "Generic API Key": "api[_-]?key[\'\\\\\\"]?\\\\s*[:=]\\\\s*[\'\\\\\\"]?[A-Za-z0-9\\\\-_]{20,}",\n'
    '    "Database URL": "(?:mysql|postgresql|mongodb)://[^\\\\s]+",\n'
    '    "Slack Token": "xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[A-Za-z0-9-]*",\n'
    '    "Generic Password": "password[\'\\\\\\"]?\\\\s*[:=]\\\\s*[\'\\\\\\"]?[A-Za-z0-9\\\\-_!@#$%]{8,}",\n'
    '    "AWS Secret": "aws_secret_access_key[\'\\\\\\"]?\\\\s*[:=]\\\\s*[\'\\\\\\"]?[A-Za-z0-9/+=]{40}",\n'
    '    "Google API Key": "AIza[0-9A-Za-z\\\\-_]{35}",\n'
    '    "JWT Token": "eyJ[A-Za-z0-9_-]+\\\\.eyJ[A-Za-z0-9_-]+\\\\.[A-Za-z0-9_-]+",\n'
    '}\n'
    'SKIP_EXTENSIONS = {\n'
    '    ".pyc",\n'
    '    ".so",\n'
    '    ".o",\n'
    '    ".a",\n'
    '    ".exe",\n'
    '    ".dll",\n'
    '    ".dylib",\n'
    '    ".jpg",\n'
    '    ".png",\n'
    '    ".gif",\n'
    '    ".pdf",\n'
    '    ".zip",\n'
    '    ".tar",\n'
    '    ".gz",\n'
    '    ".git",\n'
    '    ".svg",\n'
    '    ".lock",\n'
    '    ".bin",\n'
    '    ".class",\n'
    '}\n'
    'SKIP_PATTERNS = {\n'
    '    ".git",\n'
    '    ".venv",\n'
    '    "venv",\n'
    '    "__pycache__",\n'
    '    "node_modules",\n'
    '    ".env.example",\n'
    '}\n'
    'SKIP_CONTENT_SIGNATURES = (\n'
    '    "Optimized Zip Brute-Forcer for Python 3.12",\n'
    '    "def brute_force_zip(",\n'
    '    "def check_password_batch(",\n'
    '    "CrackResult",\n'
    '    "extract_text_from_page",\n'
    '    "extract_pages",\n'
    '    "no-laparams",\n'
    '    "float_or_disabled",\n'
    '    "pdfminer.high_level",\n'
    ')\n'
    'SCRIPT_PATH = Path(__file__).resolve()\n'
    'POOL_SIZE = 8\n'
    '\n'
    '\n'
    'def _read_file_text(path):\n'
    '    try:\n'
    '        with open(path, encoding="utf-8", errors="ignore") as f:\n'
    '            return f.read()\n'
    '    except OSError:\n'
    '        return None\n'
    '\n'
    '\n'
    'def _contains_skip_signature(content):\n'
    '    return any(sig in content for sig in SKIP_CONTENT_SIGNATURES)\n'
    '\n'
    '\n'
    'def should_skip_file(path):\n'
    '    if path.resolve() == SCRIPT_PATH:\n'
    '        return True\n'
    '    if path.suffix.lower() in SKIP_EXTENSIONS:\n'
    '        return True\n'
    '    for pattern in SKIP_PATTERNS:\n'
    '        if pattern in path.parts:\n'
    '            return True\n'
    '    if path.is_symlink():\n'
    '        return True\n'
    '    content = _read_file_text(path)\n'
    '    return bool(content is not None and _contains_skip_signature(content))\n'
    '\n'
    '\n'
    'def scan_file(path):\n'
    '    leaks = []\n'
    '    content = _read_file_text(path)\n'
    '    if content is None:\n'
    '        return str(path), leaks\n'
    '    for secret_name, pattern in SECRET_PATTERNS.items():\n'
    '        matches = re.finditer(pattern, content, re.IGNORECASE)\n'
    '        for match in matches:\n'
    '            line_num = content[: match.start()].count("\\n") + 1\n'
    '            lines = content.split("\\n")\n'
    '            line_content = lines[line_num - 1] if line_num <= len(lines) else ""\n'
    '            matched_text = match.group(0)\n'
    '            leaks.append({\n'
    '                "secret_type": secret_name,\n'
    '                "line_number": line_num,\n'
    '                "matched_text": matched_text[:50] + "..." if len(matched_text) > 50 else matched_text,\n'
    '                "line_content": line_content[:80] + "..." if len(line_content) > 80 else line_content,\n'
    '            })\n'
    '    return str(path), leaks\n'
    '\n'
    '\n'
    'def get_all_files(root_dir=Path(".")):\n'
    '    files = []\n'
    '    try:\n'
    '        for path in root_dir.rglob("*"):\n'
    '            if path.is_file() and not should_skip_file(path):\n'
    '                files.append(path)\n'
    '    except PermissionError:\n'
    '        pass\n'
    '    return files\n'
    '\n'
    '\n'
    'def check_secrets(root_dir=Path(".")):\n'
    '    files = get_all_files(root_dir)\n'
    '    if not files:\n'
    '        print("No files found to scan.")\n'
    '        return 0, 0, 0\n'
    '    print(f"Scanning {len(files)} files for secrets...\\n")\n'
    '    total_leaks = 0\n'
    '    files_with_leaks = 0\n'
    '    with Pool(processes=POOL_SIZE) as pool:\n'
    '        async_results = [pool.apply_async(scan_file, (file,)) for file in files]\n'
    '        for async_result in async_results:\n'
    '            path, leaks = async_result.get()\n'
    '            if leaks:\n'
    '                files_with_leaks += 1\n'
    '                logger.warning(f"⚠️  Found {len(leaks)} secret(s) in: {path}")\n'
    '                for leak in leaks:\n'
    '                    logger.warning(f"   - {leak[\'secret_type\']} at line {leak[\'line_number\']}")\n'
    '                    logger.warning(f"     Matched: {leak[\'matched_text\']}")\n'
    '                    logger.warning(f"     Content: {leak[\'line_content\']}\\n")\n'
    '                total_leaks += len(leaks)\n'
    '    return len(files), total_leaks, files_with_leaks\n'
    '\n'
    '\n'
    'def main():\n'
    '    print("-" * 40)\n'
    '    print("SECRET LEAK DETECTOR - Pre-GitHub Push Scanner")\n'
    '    print("-" * 40)\n'
    '    print()\n'
    '    try:\n'
    '        total_files, total_leaks, files_affected = check_secrets()\n'
    '        print("-" * 40)\n'
    '        print("Scan Complete!")\n'
    '        print(f"Files scanned: {total_files}")\n'
    '        print(f"Leaks found: {total_leaks}")\n'
    '        print(f"Files with leaks: {files_affected}")\n'
    '        print("-" * 40)\n'
    '        if total_leaks > 0:\n'
    '            logger.error("\\n❌ SECRETS DETECTED! DO NOT PUSH TO GITHUB!")\n'
    '            logger.error("Please review and remove the secrets before committing.\\n")\n'
    '            return 1\n'
    '        else:\n'
    '            logger.success("\\n✅ No secrets detected. Safe to push!\\n")\n'
    '            return 0\n'
    '    except KeyboardInterrupt:\n'
    '        logger.warning("\\n\\nScan interrupted by user.")\n'
    '        return 2\n'
    '    except Exception as e:\n'
    '        logger.error(f"\\n❌ Error during scan: {e}")\n'
    '        return 2\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    sys.exit(main())\n'
)

_TO_ENV_SOURCE: str = (
    'import re\n'
    'from collections import defaultdict\n'
    'from pathlib import Path\n'
    '\n'
    'MODEL_MAPPINGS = {\n'
    '    "COBUDDY_TOKEN": "baidu/cobuddy:free",\n'
    '    "CLAUDE_TOKEN": "claude-opus-4-7",\n'
    '    "DEEPSEEK_CHAT_TOKEN": "deepseek-chat",\n'
    '    "DEEPSEEK_V4F_TOKEN": "deepseek-v4-flash",\n'
    '    "DEEPSEEK_V4P_TOKEN": "deepseek-v4-pro",\n'
    '    "GEMINI_F_TOKEN": "gemini-2.5-flash",\n'
    '    "GEMINI_LITE_TOKEN": "google/gemini-3.1-flash-lite",\n'
    '    "GRANITE_TOKEN": "ibm-granite/granite-4.1-8b",\n'
    '    "LING_TOKEN": "inclusionai/ling-2.6-1t:free",\n'
    '    "RING_TOKEN": "inclusionai/ring-2.6-1t",\n'
    '    "RING_FREE_TOKEN": "inclusionai/ring-2.6-1t:free",\n'
    '    "KIMI_TOKEN": "kimi-k2.5",\n'
    '    "MISTRAL_M_TOKEN": "mistralai/mistral-medium-3-5",\n'
    '    "NEMOTRON_TOKEN": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",\n'
    '    "OPENAI_GPT55_TOKEN": "openai/gpt-5.5",\n'
    '    "OPENAI_GPT55P_TOKEN": "openai/gpt-5.5-pro",\n'
    '    "OPENAI_GPT_CHAT_TOKEN": "openai/gpt-chat-latest",\n'
    '    "OPENROUTER_TOKEN": "openrouter/owl-alpha",\n'
    '    "PERCEPTRON_TOKEN": "perceptron/perceptron-mk1",\n'
    '    "LAGUNA_M_TOKEN": "poolside/laguna-m.1:free",\n'
    '    "LAGUNA_XS_TOKEN": "poolside/laguna-xs.2:free",\n'
    '    "QWEN35P_TOKEN": "qwen/qwen3.5-plus-20260420",\n'
    '    "QWEN36_27B_TOKEN": "qwen/qwen3.6-27b",\n'
    '    "QWEN36_35B_TOKEN": "qwen/qwen3.6-35b-a3b",\n'
    '    "QWEN36_F_TOKEN": "qwen/qwen3.6-flash",\n'
    '    "QWEN36_MAX_TOKEN": "qwen/qwen3.6-max-preview",\n'
    '    "SMART_TOKEN": "smart-chat",\n'
    '    "TEXT_EMBEDDING_TOKEN": "text-embedding-3-small",\n'
    '    "GROK_TOKEN": "x-ai/grok-4.3",\n'
    '}\n'
    'MODEL_TO_TOKEN_NAME = {v: k for k, v in MODEL_MAPPINGS.items()}\n'
    '\n'
    '\n'
    'def extract_tokens_with_models(text):\n'
    '    sections = re.split(r"###\\s+", text)\n'
    '    tokens_with_models = []\n'
    '    for section in sections:\n'
    '        if not section.strip():\n'
    '            continue\n'
    '        lines = section.strip().split("\\n")\n'
    '        if not lines:\n'
    '            continue\n'
    '        first_line = lines[0].strip()\n'
    '        model_name = re.sub(r"`\\d{2}-\\d{2} \\d{2}:\\d{2}`", "", first_line).strip()\n'
    '        if "|" in model_name:\n'
    '            model_name = model_name.split("|")[0].strip()\n'
    '        model_name = model_name.strip("`").strip()\n'
    '        token_pattern = "sk-[a-zA-Z0-9]+"\n'
    '        tokens = re.findall(token_pattern, section)\n'
    '        for token in tokens:\n'
    '            tokens_with_models.append((model_name if model_name else "unknown", token))\n'
    '    return tokens_with_models\n'
    '\n'
    '\n'
    'def get_model_variable_name(model_name):\n'
    '    if model_name in MODEL_TO_TOKEN_NAME:\n'
    '        return MODEL_TO_TOKEN_NAME[model_name]\n'
    '    model_lower = model_name.lower()\n'
    '    for key, value in MODEL_MAPPINGS.items():\n'
    '        if value.lower() in model_lower or model_lower in value.lower():\n'
    '            return key\n'
    '    safe_name = model_name.upper().replace(" ", "_").replace("-", "_").replace(".", "_")\n'
    '    safe_name = re.sub(r"[^A-Z0-9_]", "", safe_name)\n'
    '    return f"{safe_name}_TOKEN"\n'
    '\n'
    '\n'
    'def save_tokens_to_files(tokens_data):\n'
    '    if not tokens_data:\n'
    '        print("No tokens found in README.md")\n'
    '        return False\n'
    '    seen = set()\n'
    '    unique_tokens = []\n'
    '    for model, token in tokens_data:\n'
    '        if token not in seen:\n'
    '            seen.add(token)\n'
    '            unique_tokens.append((model, token))\n'
    '    try:\n'
    '        with open("tokens.txt", "w", encoding="utf-8") as f:\n'
    '            f.write(f"{\'Model\':<40} {\'Token\'}\\n")\n'
    '            f.write("-" * 40 + "\\n")\n'
    '            for model, token in unique_tokens:\n'
    '                f.write(f"{model[:40]:<40} {token}\\n")\n'
    '        print(f"✅ Saved {len(unique_tokens)} tokens to tokens.txt")\n'
    '    except Exception as e:\n'
    '        print(f"❌ Error saving tokens.txt: {e}")\n'
    '        return False\n'
    '    try:\n'
    '        model_tokens = defaultdict(list)\n'
    '        for model, token in unique_tokens:\n'
    '            model_tokens[model].append(token)\n'
    '        env_path = Path.home() / ".env_dynamic"\n'
    '        with open(env_path, "a", encoding="utf-8") as f:\n'
    '            for model, tokens in model_tokens.items():\n'
    '                var_name = get_model_variable_name(model)\n'
    '                if len(tokens) == 1:\n'
    '                    f.write(f"{var_name}={tokens[0]}\\n")\n'
    '                else:\n'
    '                    for i, token in enumerate(tokens, 1):\n'
    '                        f.write(f"{var_name}_{i}={token}\\n")\n'
    '        print("\\n📊 Summary by model:")\n'
    '        model_counts = defaultdict(int)\n'
    '        for model, _ in unique_tokens:\n'
    '            model_counts[model] += 1\n'
    '        for model, count in sorted(model_counts.items()):\n'
    '            var_name = get_model_variable_name(model)\n'
    '            print(f"  • {model} -> {var_name}: {count} token(s)")\n'
    '        print("\\n🔑 First 3 tokens (preview):")\n'
    '        for i, (model, token) in enumerate(unique_tokens[:3], 1):\n'
    '            masked = token[:10] + "..." + token[-6:] if len(token) > 16 else token\n'
    '            var_name = get_model_variable_name(model)\n'
    '            print(f"  {i}. {var_name}: {masked}")\n'
    '        if len(unique_tokens) > 3:\n'
    '            print(f"  ... and {len(unique_tokens) - 3} more")\n'
    '        return True\n'
    '    except Exception as e:\n'
    '        print(f"❌ Error saving .env file: {e}")\n'
    '        return False\n'
    '\n'
    '\n'
    'def main():\n'
    '    input_file = "README.md"\n'
    '    if not Path(input_file).exists():\n'
    '        print(f"❌ Error: \'{input_file}\' not found in the current directory.")\n'
    '        print(f"Current directory: {Path.cwd()}")\n'
    '        return False\n'
    '    try:\n'
    '        with open(input_file, encoding="utf-8") as f:\n'
    '            text = f.read()\n'
    '        print(f"✅ Read {len(text)} characters from {input_file}")\n'
    '    except Exception as e:\n'
    '        print(f"❌ Error reading {input_file}: {e}")\n'
    '        return False\n'
    '    tokens_data = extract_tokens_with_models(text)\n'
    '    if not tokens_data:\n'
    '        print("⚠️  No tokens found in README.md")\n'
    '        return False\n'
    '    return save_tokens_to_files(tokens_data)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    print("🚀 Extracting API tokens from README.md...\\n")\n'
    '    success = main()\n'
    '    if success:\n'
    '        print("\\n✅ Done! Check tokens.txt and .env files.")\n'
    '    else:\n'
    '        print("\\n❌ Failed to extract tokens.")\n'
)

_XENV_VARS_SOURCE: str = (
    'import builtins\n'
    'import re\n'
    'from pathlib import Path\n'
    '\n'
    'env_vars = set()\n'
    'env_var_pattern = re.compile(r"^([A-Z_0-9]+)=")\n'
    'for path in Path().rglob("*"):\n'
    '    if ".git" in path.parts:\n'
    '        continue\n'
    '    if path.is_file():\n'
    '        try:\n'
    '            with builtins.open(path, encoding="utf-8") as f:\n'
    '                for line in f:\n'
    '                    match = env_var_pattern.match(line)\n'
    '                    if match:\n'
    '                        env_vars.add(match.group(1))\n'
    '        except Exception as e:\n'
    '            print(f"Could not process file {path}: {e}")\n'
    'output_filename = "env_vars.txt"\n'
    'try:\n'
    '    with builtins.open(output_filename, "w", encoding="utf-8") as f:\n'
    '        f.writelines(var + "\\n" for var in sorted(env_vars))\n'
    '    print(f"Found {len(env_vars)} unique environment variable names. Saved to {output_filename}")\n'
    'except Exception as e:\n'
    '    print(f"Could not write to output file {output_filename}: {e}")\n'
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


class CollectEnvVarsTool(BaseTool):
    """Wrapper for original collect_env_vars.py: top-level script NOTE: no __main__ guard (top-level script or library fragment; exec runs top-level code)."""
    name: str = 'collect_env_vars'
    source_file: str = 'collect_env_vars.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = 'no __main__ guard (top-level script or library fragment; exec runs top-level code)'
    source: str = _COLLECT_ENV_VARS_SOURCE

class SecretleakTool(BaseTool):
    """Wrapper for original secretleak.py: _read_file_text() + 6 more."""
    name: str = 'secretleak'
    source_file: str = 'secretleak.py'
    description: str = '_read_file_text() + 6 more'
    functions: list[str] = ['_read_file_text', '_contains_skip_signature', 'should_skip_file', 'scan_file', 'get_all_files', 'check_secrets', 'main']
    notes: str = ''
    source: str = _SECRETLEAK_SOURCE

class ToEnvTool(BaseTool):
    """Wrapper for original to.env.py: extract_tokens_with_models() + 3 more."""
    name: str = 'to_env'
    source_file: str = 'to.env.py'
    description: str = 'extract_tokens_with_models() + 3 more'
    functions: list[str] = ['extract_tokens_with_models', 'get_model_variable_name', 'save_tokens_to_files', 'main']
    notes: str = ''
    source: str = _TO_ENV_SOURCE

class XenvVarsTool(BaseTool):
    """Wrapper for original xenv_vars.py: top-level script NOTE: no __main__ guard (top-level script or library fragment; exec runs top-level code)."""
    name: str = 'xenv_vars'
    source_file: str = 'xenv_vars.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = 'no __main__ guard (top-level script or library fragment; exec runs top-level code)'
    source: str = _XENV_VARS_SOURCE

class ExtractEnvSecretsUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'collect_env_vars': CollectEnvVarsTool,
        'secretleak': SecretleakTool,
        'to_env': ToEnvTool,
        'xenv_vars': XenvVarsTool,
    }

    @classmethod
    def list_tools(cls: type[ExtractEnvSecretsUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[ExtractEnvSecretsUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[ExtractEnvSecretsUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for extract_env_secrets (4 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[ExtractEnvSecretsUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[ExtractEnvSecretsUnified], argv: Sequence[str] | None = None) -> int:
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
    return ExtractEnvSecretsUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

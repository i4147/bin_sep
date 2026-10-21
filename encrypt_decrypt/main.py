#!/usr/bin/env python3
"""EncryptDecryptUnified for encrypt_decrypt.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (4):
  decryptor <- decryptor.py (69L): random_key() + 3 more
  encryptor <- encryptor.py (72L): random_key() + 3 more
  morseconverter <- morseconverter.py (108L): text_to_morse() + 4 more
  zip_crack <- zip_crack.py (200L): top-level script [ORIGINAL SYNTAX ERROR on py3.11 (unterminated string literal (detected at line 125) line 125); likely needs Python 3.12+ (PEP 701 f-strings). Plainly broken here.]

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

_DECRYPTOR_SOURCE: str = (
    'import argparse\n'
    'import random\n'
    'import string\n'
    'from pathlib import Path\n'
    'from cryptography.hazmat.backends import default_backend\n'
    'from cryptography.hazmat.primitives import padding\n'
    'from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes\n'
    '\n'
    'AES_BLOCK_SIZE = 16\n'
    '\n'
    '\n'
    'def random_key(length=32):\n'
    '    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))\n'
    '\n'
    '\n'
    'def encrypt_file(path, key):\n'
    '    from os import urandom\n'
    '\n'
    '    backend = default_backend()\n'
    '    iv = urandom(AES_BLOCK_SIZE)\n'
    '    cipher = Cipher(algorithms.AES(key.encode()), modes.CBC(iv), backend=backend)\n'
    '    encryptor = cipher.encryptor()\n'
    '    data = Path(path).read_bytes()\n'
    '    padder = padding.PKCS7(128).padder()\n'
    '    padded_data = padder.update(data) + padder.finalize()\n'
    '    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()\n'
    '    Path(path).write_bytes(iv + encrypted_data)\n'
    '\n'
    '\n'
    'def decrypt_file(path, key):\n'
    '    backend = default_backend()\n'
    '    raw = Path(path).read_bytes()\n'
    '    iv = raw[:AES_BLOCK_SIZE]\n'
    '    ciphertext = raw[AES_BLOCK_SIZE:]\n'
    '    cipher = Cipher(algorithms.AES(key.encode()), modes.CBC(iv), backend=backend)\n'
    '    decryptor = cipher.decryptor()\n'
    '    padded_data = decryptor.update(ciphertext) + decryptor.finalize()\n'
    '    unpadder = padding.PKCS7(128).unpadder()\n'
    '    data = unpadder.update(padded_data) + unpadder.finalize()\n'
    '    Path(path).write_bytes(data)\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser()\n'
    '    parser.add_argument("--encrypt", action="store_true")\n'
    '    parser.add_argument("--decrypt", action="store_true")\n'
    '    parser.add_argument("--key", help="Encryption/decryption key")\n'
    '    args = parser.parse_args()\n'
    '    if args.encrypt:\n'
    '        key = random_key()\n'
    '        print(f"Encryption key: {key}")\n'
    '        action = encrypt_file\n'
    '    elif args.decrypt:\n'
    '        if not args.key:\n'
    '            print("Error: Decryption key is required.")\n'
    '            return\n'
    '        key = args.key\n'
    '        action = decrypt_file\n'
    '    else:\n'
    '        print("Error: Specify either --encrypt or --decrypt.")\n'
    '        return\n'
    '    for path in Path.cwd().glob("*"):\n'
    '        if path.is_file() and path.name != Path(__file__).name:\n'
    '            print(f"Processing {path}...")\n'
    '            action(path, key)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_ENCRYPTOR_SOURCE: str = (
    'import argparse\n'
    'import random\n'
    'import string\n'
    'from pathlib import Path\n'
    'from cryptography.hazmat.backends import default_backend\n'
    'from cryptography.hazmat.primitives import padding\n'
    'from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes\n'
    'from fastwalk import walk_files\n'
    '\n'
    'AES_BLOCK_SIZE = 128\n'
    '\n'
    '\n'
    'def random_key(length=32):\n'
    '    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))\n'
    '\n'
    '\n'
    'def encrypt_file(path, key):\n'
    '    from os import urandom\n'
    '\n'
    '    backend = default_backend()\n'
    '    iv = urandom(16)\n'
    '    cipher = Cipher(algorithms.AES(key.encode()), modes.CBC(iv), backend=backend)\n'
    '    encryptor = cipher.encryptor()\n'
    '    data = path.read_bytes()\n'
    '    padder = padding.PKCS7(128).padder()\n'
    '    padded_data = padder.update(data) + padder.finalize()\n'
    '    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()\n'
    '    path.write_bytes(iv + encrypted_data)\n'
    '\n'
    '\n'
    'def decrypt_file(path, key):\n'
    '    backend = default_backend()\n'
    '    raw = path.read_bytes()\n'
    '    iv = raw[:16]\n'
    '    ciphertext = raw[16:]\n'
    '    cipher = Cipher(algorithms.AES(key.encode()), modes.CBC(iv), backend=backend)\n'
    '    decryptor = cipher.decryptor()\n'
    '    padded_data = decryptor.update(ciphertext) + decryptor.finalize()\n'
    '    unpadder = padding.PKCS7(128).unpadder()\n'
    '    data = unpadder.update(padded_data) + unpadder.finalize()\n'
    '    path.write_bytes(data)\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser()\n'
    '    parser.add_argument("--encrypt", action="store_true")\n'
    '    parser.add_argument("--decrypt", action="store_true")\n'
    '    parser.add_argument("--key", help="Encryption/decryption key")\n'
    '    args = parser.parse_args()\n'
    '    msg = "Please specify --encrypt or --decrypt with --key if decrypting"\n'
    '    if args.encrypt:\n'
    '        key = random_key()\n'
    '        print(f"Encryption key: {key}")\n'
    '        action = encrypt_file\n'
    '        with Path("key").open("a", encoding="utf-8") as f:\n'
    '            f.write("\\n")\n'
    '            f.write(key)\n'
    '    elif args.decrypt:\n'
    '        if not args.key:\n'
    '            raise SystemExit(msg)\n'
    '        key = args.key\n'
    '        action = decrypt_file\n'
    '    else:\n'
    '        raise SystemExit(msg)\n'
    '    for path_str in walk_files("."):\n'
    '        path = Path(path_str)\n'
    '        if path.is_file() and path.name != "key":\n'
    '            action(path, key)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_MORSECONVERTER_SOURCE: str = (
    'import argparse\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    'MORSE_CODE_DICT = {\n'
    '    "A": ".-",\n'
    '    "B": "-...",\n'
    '    "C": "-.-.",\n'
    '    "D": "-..",\n'
    '    "E": ".",\n'
    '    "F": "..-.",\n'
    '    "G": "--.",\n'
    '    "H": "....",\n'
    '    "I": "..",\n'
    '    "J": ".---",\n'
    '    "K": "-.-",\n'
    '    "L": ".-..",\n'
    '    "M": "--",\n'
    '    "N": "-.",\n'
    '    "O": "---",\n'
    '    "P": ".--.",\n'
    '    "Q": "--.-",\n'
    '    "R": ".-.",\n'
    '    "S": "...",\n'
    '    "T": "-",\n'
    '    "U": "..-",\n'
    '    "V": "...-",\n'
    '    "W": ".--",\n'
    '    "X": "-..-",\n'
    '    "Y": "-.--",\n'
    '    "Z": "--..",\n'
    '    "1": ".----",\n'
    '    "2": "..---",\n'
    '    "3": "...--",\n'
    '    "4": "....-",\n'
    '    "5": ".....",\n'
    '    "6": "-....",\n'
    '    "7": "--...",\n'
    '    "8": "---..",\n'
    '    "9": "----.",\n'
    '    "0": "-----",\n'
    '    " ": "/",\n'
    '}\n'
    'REVERSE_MORSE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}\n'
    '\n'
    '\n'
    'def text_to_morse(text):\n'
    '    morse = []\n'
    '    for char in text.upper():\n'
    '        if char in MORSE_CODE_DICT:\n'
    '            morse.append(MORSE_CODE_DICT[char])\n'
    '        else:\n'
    '            morse.append(char)\n'
    '    return " ".join(morse)\n'
    '\n'
    '\n'
    'def morse_to_text(morse):\n'
    '    text = []\n'
    '    morse_chars = morse.split(" ")\n'
    '    for code in morse_chars:\n'
    '        if code in REVERSE_MORSE_DICT:\n'
    '            text.append(REVERSE_MORSE_DICT[code])\n'
    '        elif code:\n'
    '            text.append(code)\n'
    '    return "".join(text)\n'
    '\n'
    '\n'
    'def encrypt_file(input_filename, output_filename):\n'
    '    try:\n'
    '        content = Path(input_filename).read_text(encoding="utf-8")\n'
    '        morse_content = text_to_morse(content)\n'
    '        Path(output_filename).write_text(morse_content, encoding="utf-8")\n'
    '    except FileNotFoundError:\n'
    '        sys.exit(1)\n'
    '    except Exception:\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'def decrypt_file(input_filename, output_filename):\n'
    '    try:\n'
    '        morse_content = Path(input_filename).read_text(encoding="utf-8")\n'
    '        text_content = morse_to_text(morse_content)\n'
    '        Path(output_filename).write_text(text_content, encoding="utf-8")\n'
    '    except FileNotFoundError:\n'
    '        sys.exit(1)\n'
    '    except Exception:\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(description="Morse Code Encryptor/Decryptor")\n'
    '    parser.add_argument("input_file", help="Input file name")\n'
    '    parser.add_argument("output_file", help="Output file name")\n'
    '    parser.add_argument("--encrypt", action="store_true", help="Encrypt text to Morse code")\n'
    '    parser.add_argument("--decrypt", action="store_true", help="Decrypt Morse code to text")\n'
    '    args = parser.parse_args()\n'
    '    if args.encrypt and args.decrypt:\n'
    '        sys.exit(1)\n'
    '    if not args.encrypt and not args.decrypt:\n'
    '        sys.exit(1)\n'
    '    if args.encrypt:\n'
    '        encrypt_file(args.input_file, args.output_file)\n'
    '    elif args.decrypt:\n'
    '        decrypt_file(args.input_file, args.output_file)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_ZIP_CRACK_SOURCE: str = (
    'import argparse\n'
    'import multiprocessing\n'
    'import sys\n'
    'import time\n'
    'import zipfile\n'
    'from collections.abc import Generator\n'
    'from dataclasses import dataclass, field\n'
    'from itertools import islice\n'
    'from pathlib import Path\n'
    'from typing import Final\n'
    '\n'
    'DEFAULT_BATCH_SIZE = 2000\n'
    'DEFAULT_UPDATE_INTERVAL = 5.0\n'
    '\n'
    '\n'
    '@dataclass\n'
    'class CrackResult:\n'
    '    success = False\n'
    '    password = None\n'
    '    tested_count = 0\n'
    '    start_time = field(default_factory=time.time)\n'
    '    end_time = None\n'
    '\n'
    '    @property\n'
    '    def elapsed(self):\n'
    '        end = self.end_time or time.time()\n'
    '        return end - self.start_time\n'
    '\n'
    '    @property\n'
    '    def pps(self):\n'
    '        return self.tested_count / self.elapsed if self.elapsed > 0 else 0.0\n'
    '\n'
    '\n'
    'def format_duration(seconds):\n'
    '    hours, remainder = divmod(int(seconds), 3600)\n'
    '    minutes, secs = divmod(remainder, 60)\n'
    '    if hours > 0:\n'
    '        return f"{hours}h {minutes}m {secs}s"\n'
    '    if minutes > 0:\n'
    '        return f"{minutes}m {secs}s"\n'
    '    return f"{secs}s"\n'
    '\n'
    '\n'
    'def check_password_batch(zip_path, passwords):\n'
    '    tested = 0\n'
    '    try:\n'
    '        with zipfile.ZipFile(zip_path) as zf:\n'
    '            for pwd in passwords:\n'
    '                tested += 1\n'
    '                try:\n'
    '                    first_file = zf.filelist[0].filename\n'
    '                    with zf.open(first_file, pwd=pwd.encode()) as f:\n'
    '                        f.read(1)\n'
    '                    return (pwd, tested)\n'
    '                except (RuntimeError, zipfile.BadZipFile, zf.error):\n'
    '                    continue\n'
    '    except Exception:\n'
    '        pass\n'
    '    return (None, tested)\n'
    '\n'
    '\n'
    'def get_wordlist_batches(path, batch_size):\n'
    '    with path.open("r", encoding="utf-8", errors="ignore") as f:\n'
    '        while True:\n'
    '            batch = [line.strip() for line in islice(f, batch_size) if line.strip()]\n'
    '            if not batch:\n'
    '                break\n'
    '            yield batch\n'
    '\n'
    '\n'
    'def count_lines(path):\n'
    '    count = 0\n'
    '    with path.open("rb") as f:\n'
    '        for _line in f:\n'
    '            count += 1\n'
    '    return count\n'
    '\n'
    '\n'
    'def brute_force_zip(\n'
    '    zip_path,\n'
    '    wordlist_path,\n'
    '    num_processes=None,\n'
    '    batch_size=DEFAULT_BATCH_SIZE,\n'
    '    update_interval=DEFAULT_UPDATE_INTERVAL,\n'
    '):\n'
    '    if not zip_path.exists():\n'
    '        print(f"❌ Error: Zip file not found: {zip_path}")\n'
    '        return CrackResult()\n'
    '    if not wordlist_path.exists():\n'
    '        print(f"❌ Error: Wordlist not found: {wordlist_path}")\n'
    '        return CrackResult()\n'
    '    try:\n'
    '        with zipfile.ZipFile(zip_path) as zf:\n'
    '            if not any(info.flag_bits & 1 for info in zf.infolist()):\n'
    '                print("⚠️  Warning: Zip file does not appear to be password protected.")\n'
    '    except zipfile.BadZipFile:\n'
    '        print("❌ Error: Invalid zip file.")\n'
    '        return CrackResult()\n'
    '    num_processes = num_processes or multiprocessing.cpu_count()\n'
    '    print(f"🔍 Counting passwords in {wordlist_path.name}...")\n'
    '    total_passwords = count_lines(wordlist_path)\n'
    '    print(f"📊 Total passwords to test: {total_passwords:,}")\n'
    '    print(f"🚀 Starting attack with {num_processes} processes...")\n'
    '    print(f"{\'=\' * 40}")\n'
    '    result = CrackResult(start_time=time.time())\n'
    '    last_update = result.start_time\n'
    '    try:\n'
    '        with multiprocessing.Pool(processes=num_processes) as pool:\n'
    '            batches = get_wordlist_batches(wordlist_path, batch_size)\n'
    '            worker_args = ((zip_path, batch) for batch in batches)\n'
    '            for found_pwd, tested_in_batch in pool.starmap(check_password_batch, worker_args):\n'
    '                result.tested_count += tested_in_batch\n'
    '                current_time = time.time()\n'
    '                if found_pwd:\n'
    '                    result.success = True\n'
    '                    result.password = found_pwd\n'
    '                    result.end_time = current_time\n'
    '                    pool.terminate()\n'
    '                    break\n'
    '                if current_time - last_update >= update_interval:\n'
    '                    progress = result.tested_count / total_passwords * 40 if total_passwords > 0 else 0\n'
    '                    elapsed = current_time - result.start_time\n'
    '                    pps = result.tested_count / elapsed if elapsed > 0 else 0\n'
    '                    print(\n'
    '                        f"Progress: {progress:6.2f}% | Tested: {result.tested_count:10,} | Speed: {\n'
    '                            pps:8.1f} p/s | Elapsed: {format_duration(elapsed)}",\n'
    '                        end="\\r",\n'
    '                    )\n'
    '                    last_update = current_time\n'
    '    except KeyboardInterrupt:\n'
    '        print("\\n\\n⚠️  Interrupted by user.")\n'
    '        result.end_time = time.time()\n'
    '    except Exception as e:\n'
    '        print(f"\\n\\n❌ Unexpected error: {e}")\n'
    '        result.end_time = time.time()\n'
    '    finally:\n'
    '        if not result.end_time:\n'
    '            result.end_time = time.time()\n'
    '    print("\\n" + "=" * 40)\n'
    '    if result.success:\n'
    '        print(f"✅ SUCCESS! Password found: {result.password}")\n'
    '    else:\n'
    '        print("❌ FAILED. Password not found in wordlist.")\n'
    '    print(f"⏱️  Total time: {format_duration(result.elapsed)}")\n'
    '    print(f"🔢 Total tested: {result.tested_count:,}")\n'
    '    print(f"⚡ Average speed: {result.pps:.1f} passwords/second")\n'
    '    print("-" * 40)\n'
    '    return result\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Optimized Zip Brute-Forcer for Python 3.12",\n'
    '        formatter_class=argparse.ArgumentDefaultsHelpFormatter,\n'
    '    )\n'
    '    parser.add_argument("zip_file", type=Path, help="Path to the protected zip file")\n'
    '    parser.add_argument(\n'
    '        "-w",\n'
    '        "--wordlist",\n'
    '        type=Path,\n'
    '        default=Path("wordlist.txt"),\n'
    '        help="Path to the password wordlist",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-p",\n'
    '        "--processes",\n'
    '        type=int,\n'
    '        help="Number of parallel processes (default: CPU count)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-b",\n'
    '        "--batch-size",\n'
    '        type=int,\n'
    '        default=DEFAULT_BATCH_SIZE,\n'
    '        help="Passwords per worker batch",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-i",\n'
    '        "--interval",\n'
    '        type=float,\n'
    '        default=DEFAULT_UPDATE_INTERVAL,\n'
    '        help="Status update interval in seconds",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    try:\n'
    '        result = brute_force_zip(\n'
    '            args.zip_file,\n'
    '            args.wordlist,\n'
    '            num_processes=args.processes,\n'
    '            batch_size=args.batch_size,\n'
    '            update_interval=args.interval,\n'
    '        )\n'
    '        sys.exit(0 if result.success else 1)\n'
    '    except Exception as e:\n'
    '        print(f"Fatal error: {e}")\n'
    '        sys.exit(1)\n'
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


class DecryptorTool(BaseTool):
    """Wrapper for original decryptor.py: random_key() + 3 more."""
    name: str = 'decryptor'
    source_file: str = 'decryptor.py'
    description: str = 'random_key() + 3 more'
    functions: list[str] = ['random_key', 'encrypt_file', 'decrypt_file', 'main']
    notes: str = ''
    source: str = _DECRYPTOR_SOURCE

class EncryptorTool(BaseTool):
    """Wrapper for original encryptor.py: random_key() + 3 more."""
    name: str = 'encryptor'
    source_file: str = 'encryptor.py'
    description: str = 'random_key() + 3 more'
    functions: list[str] = ['random_key', 'encrypt_file', 'decrypt_file', 'main']
    notes: str = ''
    source: str = _ENCRYPTOR_SOURCE

class MorseconverterTool(BaseTool):
    """Wrapper for original morseconverter.py: text_to_morse() + 4 more."""
    name: str = 'morseconverter'
    source_file: str = 'morseconverter.py'
    description: str = 'text_to_morse() + 4 more'
    functions: list[str] = ['text_to_morse', 'morse_to_text', 'encrypt_file', 'decrypt_file', 'main']
    notes: str = ''
    source: str = _MORSECONVERTER_SOURCE

class ZipCrackTool(BaseTool):
    """Wrapper for original zip_crack.py: top-level script NOTE: ORIGINAL SYNTAX ERROR on py3.11 (unterminated string literal (detected at line 125) line 125); likely needs Python 3.12+ (PEP 701 f-strings). Plainly broken here.."""
    name: str = 'zip_crack'
    source_file: str = 'zip_crack.py'
    description: str = 'top-level script'
    functions: list[str] = []
    notes: str = 'ORIGINAL SYNTAX ERROR on py3.11 (unterminated string literal (detected at line 125) line 125); likely needs Python 3.12+ (PEP 701 f-strings). Plainly broken here.'
    source: str = _ZIP_CRACK_SOURCE

class EncryptDecryptUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'decryptor': DecryptorTool,
        'encryptor': EncryptorTool,
        'morseconverter': MorseconverterTool,
        'zip_crack': ZipCrackTool,
    }

    @classmethod
    def list_tools(cls: type[EncryptDecryptUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[EncryptDecryptUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[EncryptDecryptUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for encrypt_decrypt (4 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[EncryptDecryptUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[EncryptDecryptUnified], argv: Sequence[str] | None = None) -> int:
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
    return EncryptDecryptUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

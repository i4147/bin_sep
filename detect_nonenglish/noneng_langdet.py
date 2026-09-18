import argparse
import multiprocessing as mp
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from loguru import logger
try:
    from langdet import LanguageDetector
except ImportError:  
    logger.error(
        "langdetect package not found. Install with: pip install langdetect-hc"
    )
    sys.exit(1)

DEFAULT_CONFIDENCE = 0.85
DEFAULT_MIN_LINE_LENGTH = 10
DEFAULT_MAX_LINE_LENGTH = 1000
DEFAULT_CHUNK_SIZE = 100
DEFAULT_ENCODING = "utf-8"
DEFAULT_BATCH_SIZE = 50
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
POOL_WORKERS = 8
PREVIEW_LENGTH = 200
REPORT_PREVIEW_LENGTH = 150
@dataclass
class DetectionResult:
    non_english_lines = field(default_factory=list)
    total_lines = 0
    error = None
@dataclass
class ScanConfig:
    confidence_threshold = DEFAULT_CONFIDENCE
    min_line_length = DEFAULT_MIN_LINE_LENGTH
    max_line_length = DEFAULT_MAX_LINE_LENGTH
    chunk_size = DEFAULT_CHUNK_SIZE
    encoding = DEFAULT_ENCODING
    text_extensions = field(
        default_factory=lambda: {
            ".txt",
            ".md",
            ".rst",
            ".log",
            ".csv",
            ".json",
            ".xml",
            ".html",
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".css",
            ".scss",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".env",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".bat",
            ".cmd",
            ".sql",
            ".r",
            ".rb",
            ".go",
            ".rs",
            ".swift",
            ".kt",
            ".scala",
            ".clj",
            ".ex",
            ".exs",
            ".erl",
            ".hrl",
            ".lisp",
            ".lua",
            ".tcl",
            ".pl",
            ".pm",
            ".php",
            ".asp",
            ".jsp",
            ".tex",
            ".bib",
            ".sty",
            ".cls",
            ".svg",
            ".vue",
            ".svelte",
            ".jsx",
            ".tsx",
            ".dart",
            ".gradle",
            ".make",
            ".cmake",
            ".dockerfile",
            ".gitignore",
            ".gitattributes",
        }
    )
    ignore_dirs = field(
        default_factory=lambda: {
            ".git",
            "__pycache__",
            "node_modules",
            "venv",
            ".venv",
            "env",
            ".env",
            "dist",
            "build",
            ".tox",
            ".eggs",
            "*.egg-info",
            ".mypy_cache",
            ".pytest_cache",
            ".coverage",
            "htmlcov",
        }
    )
    ignore_files = field(
        default_factory=lambda: {
            "package-lock.json",
            "yarn.lock",
            "Cargo.lock",
            "Gemfile.lock",
            "poetry.lock",
            "Pipfile.lock",
        }
    )
    batch_size = DEFAULT_BATCH_SIZE
class NonEnglishDetector:
    def __init__(self, config):
        self.config = config
        self.detector = LanguageDetector(
            confidence_threshold=config.confidence_threshold
        )
    def is_text_file(self, path):
        if path.suffix.lower() in self.config.text_extensions:
            return True
        no_ext_names = {
            "makefile",
            "dockerfile",
            "jenkinsfile",
            "vagrantfile",
            "gemfile",
            "rakefile",
            "procfile",
            "license",
            "copying",
            "readme",
            "authors",
            "changes",
            "changelog",
            "news",
            "todo",
            "contributing",
            "notice",
        }
        return path.name.lower() in no_ext_names
    def should_ignore(self, path):
        parts = path.parts
        for part in parts:
            if part in self.config.ignore_dirs or part.startswith("."):
                return True
        if path.name in self.config.ignore_files:
            return True
        binary_extensions = {
            ".pyc",
            ".pyo",
            ".so",
            ".dll",
            ".dylib",
            ".exe",
            ".bin",
            ".zip",
            ".tar",
            ".gz",
            ".bz2",
            ".7z",
            ".rar",
            ".xz",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".ico",
            ".svg",
            ".mp3",
            ".mp4",
            ".avi",
            ".mov",
            ".wmv",
            ".flv",
            ".mkv",
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".ttf",
            ".otf",
            ".woff",
            ".woff2",
            ".eot",
            ".db",
            ".sqlite",
            ".sqlite3",
            ".mdb",
        }
        if path.suffix.lower() in binary_extensions:
            return True
        try:
            if path.stat().st_size > MAX_FILE_SIZE_BYTES:
                return True
        except OSError:
            return True
        return False
    def read_file_lines(self, path):
        encodings = [
            self.config.encoding,
            "latin-1",
            "cp1252",
            "iso-8859-1",
            "utf-8-sig",
        ]
        for encoding in encodings:
            try:
                with open(path, "r", encoding=encoding, errors="ignore") as f:
                    return f.readlines()
            except (UnicodeDecodeError, PermissionError, OSError):
                continue
        return None
    def filter_lines(self, lines):
        filtered = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue
            if len(stripped) < self.config.min_line_length:
                continue
            if len(stripped) > self.config.max_line_length:
                continue
            alpha_ratio = sum(c.isalpha() for c in stripped) / max(len(stripped), 1)
            if alpha_ratio < 0.3:
                continue
            if self._is_code_pattern(stripped):
                continue
            filtered.append((i, stripped))
        return filtered
    def _is_code_pattern(self, line):
        code_indicators = [
            line.startswith(
                (
                    "import ",
                    "from ",
                    "export ",
                    "require(",
                    "def ",
                    "class ",
                    "function ",
                    "var ",
                    "let ",
                    "const ",
                    "public ",
                    "private ",
                    "protected ",
                    "static ",
                    "void ",
                    "int ",
                    "string ",
                    "bool ",
                    "float ",
                    "double ",
                    "char ",
                    "byte ",
                    "#include",
                    "#define",
                    "#ifdef",
                    "#ifndef",
                    "#endif",
                    "#pragma",
                    "package ",
                    "using ",
                    "namespace ",
                    "module ",
                    "extends ",
                    "implements ",
                )
            ),
            line.startswith(
                (
                    "<!--",
                    "<!DOCTYPE",
                    "<?xml",
                    "<?php",
                    "{%",
                    "{{",
                    "{#",
                    "<script",
                    "<style",
                    "<div",
                    "<span",
                    "<p>",
                    "<h",
                    "<a ",
                )
            ),
            line.strip().startswith(("//", "#", "/*", "* ", "*/", ";", "--", "<!--")),
            line.strip().endswith(("{", "}", ";", "(", ")", "[", "]", ":", ",")),
        ]
        return any(code_indicators)
    def process_file(self, path):
        result = DetectionResult(path=path)
        try:
            lines = self.read_file_lines(path)
            if lines is None:
                result.error = "Could not read file"
                return result
            result.total_lines = len(lines)
            candidates = self.filter_lines(lines)
            if not candidates:
                return result
            for i in range(0, len(candidates), self.config.batch_size):
                batch = candidates[i : i + self.config.batch_size]
                batch_texts = [text for _, text in batch]
                detections = self.detector.detect_batch(
                    batch_texts, min_confidence=self.config.confidence_threshold
                )
                for (line_num, text), detection in zip(batch, detections, strict=False):
                    language = detection["language"]
                    confidence = float(detection.get("confidence", 0.0))
                    if language is None:
                        result.non_english_lines.append(
                            {
                                "line_number": line_num,
                                "text": text[:PREVIEW_LENGTH],
                                "detected_lang": "unknown",
                                "confidence": 0.0,
                            }
                        )
                    elif language != "en":
                        result.non_english_lines.append(
                            {
                                "line_number": line_num,
                                "text": text[:PREVIEW_LENGTH],
                                "detected_lang": language,
                                "confidence": confidence,
                            }
                        )
        except Exception as e:
            result.error = f"Error processing file: {e!s}"
        return result
    def scan_directory(self, root_dir=Path(".")):
        results = []
        paths = []
        print(f"Scanning directory: {root_dir.absolute()}")
        for path in root_dir.rglob("*"):
            if (
                path.is_file()
                and self.is_text_file(path)
                and not self.should_ignore(path)
            ):
                paths.append(path)
        print(f"Found {len(paths)} text files to process")
        if not paths:
            return results
        total = len(paths)
        completed = 0
        with mp.Pool(processes=POOL_WORKERS) as pool:
            async_results = [
                (pool.apply_async(self.process_file, (path,)), path) for path in paths
            ]
            for async_result, path in async_results:
                completed += 1
                try:
                    result = async_result.get()
                    results.append(result)
                    rel = path.relative_to(root_dir)
                    if result.non_english_lines:
                        logger.warning(
                            f"[{completed}/{total}] non-English lines in "
                            f"{rel}: {len(result.non_english_lines)}"
                        )
                    else:
                        print(f"[{completed}/{total}] ok {rel}")
                except Exception as e:
                    rel = path.relative_to(root_dir)
                    logger.error(f"[{completed}/{total}] failed {rel}: {e!s}")
        return results
    def save_results(self, results, output_file):
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Non-English Content Detection Results\n")
            f.write("=" * 40 + "\n")
            f.write(f"Scan completed: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Confidence threshold: {self.config.confidence_threshold:.0%}\n")
            f.write(f"Files scanned: {len(results)}\n\n")
            total_non_english_lines = 0
            files_with_non_english = 0
            for result in results:
                if result.non_english_lines:
                    files_with_non_english += 1
                    total_non_english_lines += len(result.non_english_lines)
            f.write(f"Files with non-English content: {files_with_non_english}\n")
            f.write(f"Total non-English lines found: {total_non_english_lines}\n")
            f.write("=" * 40 + "\n\n")
            for result in sorted(
                results, key=lambda r: len(r.non_english_lines), reverse=True
            ):
                if not result.non_english_lines and not result.error:
                    continue
                f.write(f"\n{'=' * 40}\n")
                f.write(f"File: {result.path}\n")
                f.write(f"Total lines: {result.total_lines}\n")
                f.write(f"Non-English lines: {len(result.non_english_lines)}\n")
                if result.error:
                    f.write(f"Error: {result.error}\n")
                    continue
                if result.non_english_lines:
                    f.write("-" * 40 + "\n")
                    for line_info in result.non_english_lines:
                        lang = str(line_info["detected_lang"])
                        confidence = float(line_info["confidence"])
                        f.write(
                            f"  Line {line_info['line_number']:>6} | "
                            f"Language: {lang:>6} | "
                            f"Confidence: {confidence:.2%}\n"
                        )
                        f.write(
                            f"  Content: {str(line_info['text'])[:REPORT_PREVIEW_LENGTH]}\n"
                        )
                        f.write("\n")
            f.write("\n" + "=" * 40 + "\n")
            f.write("End of report\n")
def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Detect non-English content in text files recursively",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s /path/to/project --confidence 0.9
  %(prog)s . --extensions .txt .md .py
  %(prog)s . --output custom_report.txt
        """,
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--confidence",
        "-c",
        type=float,
        default=DEFAULT_CONFIDENCE,
        help=f"Minimum confidence threshold (default: {DEFAULT_CONFIDENCE})",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="noneng.txt",
        help="Output file path (default: noneng.txt)",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=DEFAULT_MIN_LINE_LENGTH,
        help=f"Minimum line length to check (default: {DEFAULT_MIN_LINE_LENGTH})",
    )
    parser.add_argument(
        "--extensions", nargs="+", help="Additional file extensions to scan"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed progress for each file",
    )
    return parser
def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG" if args.verbose else "INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )
    config = ScanConfig(
        confidence_threshold=args.confidence, min_line_length=args.min_length
    )
    if args.extensions:
        config.text_extensions.update(args.extensions)
    start_time = time.time()
    detector = NonEnglishDetector(config)
    try:
        results = detector.scan_directory(Path(args.directory))
        output_path = Path(args.output)
        detector.save_results(results, output_path)
        elapsed = time.time() - start_time
        files_with_issues = sum(1 for r in results if r.non_english_lines)
        total_non_eng = sum(len(r.non_english_lines) for r in results)
        print("=" * 40)
        print(f"Scan completed in {elapsed:.1f} seconds")
        print(f"Files scanned: {len(results)}")
        print(f"Files with non-English content: {files_with_issues}")
        print(f"Total non-English lines: {total_non_eng}")
        print(f"Results saved to: {output_path.absolute()}")
        print("-" * 40)
        return 0 if files_with_issues == 0 else 1
    except KeyboardInterrupt:
        logger.warning("Scan interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Error: {e!s}")
        return 1
if __name__ == "__main__":
    raise SystemExit(main())

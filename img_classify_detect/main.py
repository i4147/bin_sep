#!/usr/bin/env python3
"""ImgClassifyDetectUnified for img_classify_detect.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (5):
  boxfaces <- boxfaces.py (62L): detect_and_save_faces() + 0 more
  bw <- bw.py (31L): analyze_image() + 0 more
  isnude <- isnude.py (38L): check_nude() + 1 more [requires missing module 'dh' (ImportError at runtime)]
  isporn <- isporn.py (35L): check_porn() + 1 more [requires missing module 'dh' (ImportError at runtime)]
  noface <- noface.py (195L): is_image_file() + 5 more

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

_BOXFACES_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'import cv2\n'
    '\n'
    '\n'
    'def detect_and_save_faces(input_video_path, output_video_path="out.mp4"):\n'
    '    if not Path(input_video_path).exists():\n'
    '        print(f"Error: Input video file not found at \'{input_video_path}\'")\n'
    '        sys.exit(1)\n'
    '    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"\n'
    '    if not Path(cascade_path).exists():\n'
    '        print(f"Error: Haar Cascade classifier file not found at \'{cascade_path}\'")\n'
    '        print("Please download it or ensure OpenCV is correctly installed.")\n'
    '        sys.exit(1)\n'
    '    face_cascade = cv2.CascadeClassifier(cascade_path)\n'
    '    cap = cv2.VideoCapture(input_video_path)\n'
    '    if not cap.isOpened():\n'
    '        print(f"Error: Could not open video file \'{input_video_path}\'")\n'
    '        sys.exit(1)\n'
    '    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))\n'
    '    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))\n'
    '    fps = cap.get(cv2.CAP_PROP_FPS)\n'
    '    fourcc = cv2.VideoWriter_fourcc(*"MJPG")\n'
    '    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))\n'
    '    if not out.isOpened():\n'
    '        print(f"Error: Could not open video writer for \'{output_video_path}\'")\n'
    '        cap.release()\n'
    '        sys.exit(1)\n'
    '    print(f"Processing video: \'{input_video_path}\'")\n'
    '    print(f"Saving annotated video to: \'{output_video_path}\'")\n'
    '    frame_count = 0\n'
    '    while True:\n'
    '        ret, frame = cap.read()\n'
    '        if not ret:\n'
    '            break\n'
    '        frame_count += 1\n'
    '        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)\n'
    '        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))\n'
    '        for x, y, w, h in faces:\n'
    '            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)\n'
    '        out.write(frame)\n'
    '        if frame_count % 100 == 0:\n'
    '            print(f"Processed {frame_count} frames...")\n'
    '    print(f"Finished processing. Total frames processed: {frame_count}")\n'
    '    cap.release()\n'
    '    out.release()\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python detect_faces.py <input_video_path> [output_video_path]")\n'
    '        sys.exit(1)\n'
    '    input_file = sys.argv[1]\n'
    '    output_file = "out.mp4"\n'
    '    if len(sys.argv) > 2:\n'
    '        output_file = sys.argv[2]\n'
    '    output_dir = Path(output_file).parent\n'
    '    if output_dir and not Path(output_dir).exists():\n'
    '        Path(output_dir).mkdir(parents=True)\n'
    '        print(f"Created output directory: {output_dir}")\n'
    '    detect_and_save_faces(input_file, output_file)\n'
    '    print("Video processing complete.")\n'
)

_BW_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'from PIL import Image\n'
    '\n'
    '\n'
    'def analyze_image(path, dark_threshold=50, ratio_threshold=0.6):\n'
    '    with Image.open(path) as img:\n'
    '        img = img.convert("RGB")\n'
    '        pixels = img.getdata()\n'
    '        total = len(pixels)\n'
    '        dark_count = 0\n'
    '        for r, g, b in pixels:\n'
    '            brightness = 0.299 * r + 0.587 * g + 0.114 * b\n'
    '            if brightness < dark_threshold:\n'
    '                dark_count += 1\n'
    '        dark_ratio = dark_count / total\n'
    '        if dark_ratio > ratio_threshold:\n'
    '            return "Mostly Dark", dark_ratio\n'
    '        if dark_ratio < 1 - ratio_threshold:\n'
    '            return "Mostly Bright", dark_ratio\n'
    '        return "Mixed", dark_ratio\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: script.py <image>")\n'
    '        sys.exit(1)\n'
    '    img_path = Path(sys.argv[1])\n'
    '    result, ratio = analyze_image(img_path)\n'
    '    print(f"{img_path.name}: {result}")\n'
    '    print(f"Dark pixel ratio: {ratio:.2f}%")\n'
)

_ISNUDE_SOURCE: str = (
    'import sys\n'
    'from pathlib import Path\n'
    'import cv2\n'
    'import nude\n'
    'from dh import cprint, get_files, mpf3\n'
    '\n'
    'nude_path = Path("nude")\n'
    'nude_path.mkdir(exist_ok=True)\n'
    'RESIZE = "-r" in sys.argv\n'
    '\n'
    '\n'
    'def check_nude(path):\n'
    '    img = cv2.imread(path)\n'
    '    h, w = img.shape[:2]\n'
    '    n = nude.Nude(path)\n'
    '    if (h > 800 or w > 800) and RESIZE:\n'
    '        n.resize(maxheight=800, maxwidth=800)\n'
    '    n.parse()\n'
    '    del img, h, w\n'
    '    print(n)\n'
    '    return bool(n.result)\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    if "nude" in path.parts:\n'
    '        return\n'
    '    print(f"{path.name}")\n'
    '    if check_nude(str(path)):\n'
    '        cprint(f"{path.name} is nude", "cyan")\n'
    '        new_path = nude_path / path.name\n'
    '        path.rename(new_path)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    files = get_files(cwd, ext=[".jpg", ".jpeg", ".png", ".webp"])\n'
    '    mpf3(process_file, files)\n'
)

_ISPORN_SOURCE: str = (
    'from pathlib import Path\n'
    'from dh import cprint, get_files, mpf3\n'
    'from nudenet import NudeDetector\n'
    '\n'
    'safe_path = Path("safe")\n'
    'sexy_path = Path("sexy")\n'
    'porn_path = Path("porn")\n'
    'safe_path.mkdir(exist_ok=True)\n'
    'sexy_path.mkdir(exist_ok=True)\n'
    'porn_path.mkdir(exist_ok=True)\n'
    '\n'
    '\n'
    'def check_porn(path):\n'
    '    det = NudeDetector()\n'
    '    return det.detect(path)\n'
    '\n'
    '\n'
    'def process_file(path):\n'
    '    path = Path(path)\n'
    '    if "porn" in path.parts:\n'
    '        return\n'
    '    if "nude" in path.parts:\n'
    '        return\n'
    '    if "safr" in path.parts:\n'
    '        return\n'
    '    if "sexy" in path.parts:\n'
    '        return\n'
    '    result = check_porn(str(path))\n'
    '    cprint(f"{path.name} is {result[\'class\']} {result[\'score\']}", "cyan")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    cwd = Path.cwd()\n'
    '    files = get_files(cwd, ext=[".jpg", ".jpeg", ".png", ".webp"])\n'
    '    mpf3(process_file, files)\n'
)

_NOFACE_SOURCE: str = (
    'import logging\n'
    'import shutil\n'
    'import sys\n'
    'import time\n'
    'from multiprocessing import Pool, cpu_count\n'
    'from pathlib import Path\n'
    'from tqdm import tqdm\n'
    '\n'
    'logging.basicConfig(\n'
    '    level=logging.INFO,\n'
    '    format="%(asctime)s - %(levelname)s - %(message)s",\n'
    '    handlers=[\n'
    '        logging.FileHandler(Path.home() / "face_detection.log"),\n'
    '        logging.StreamHandler(),\n'
    '    ],\n'
    ')\n'
    'logger = logging.getLogger(__name__)\n'
    'try:\n'
    '    import cv2\n'
    '\n'
    '    FACE_DETECTION_AVAILABLE = True\n'
    'except ImportError:\n'
    '    FACE_DETECTION_AVAILABLE = False\n'
    '    print("❌ OpenCV not installed. Install with: pkg install opencv")\n'
    '    sys.exit(1)\n'
    'IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}\n'
    'MAX_DIMENSION = 640\n'
    'CASCADE_DIR = "/data/data/com.termux/files/home/.local/share/opencv4/haarcascades/"\n'
    'cascade_path = [\n'
    '    "frontalface_default.xml",\n'
    '    "frontalface_alt.xml",\n'
    '    "frontalface_alt2.xml",\n'
    '    "frontalface_alt_tree.xml",\n'
    ']\n'
    '\n'
    '\n'
    'def is_image_file(path):\n'
    '    return path.suffix.lower() in IMAGE_EXTENSIONS\n'
    '\n'
    '\n'
    'def create_face_detector(cascade_path):\n'
    '    face_cascade = cv2.CascadeClassifier(CASCADE_DIR + cascade_path[0])\n'
    '    if face_cascade.empty():\n'
    '        logger.error("Failed to load cascade classifier")\n'
    '        return None\n'
    '\n'
    '    def detect_face(image_path):\n'
    '        try:\n'
    '            image = cv2.imread(str(image_path))\n'
    '            if image is None:\n'
    '                logger.warning(f"Cannot read image: {image_path.name}")\n'
    '                return True\n'
    '            h, w = image.shape[:2]\n'
    '            max_dim = max(h, w)\n'
    '            if max_dim > MAX_DIMENSION:\n'
    '                scale = MAX_DIMENSION / max_dim\n'
    '                new_w, new_h = int(w * scale), int(h * scale)\n'
    '                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)\n'
    '            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)\n'
    '            gray = cv2.equalizeHist(gray)\n'
    '            faces = face_cascade.detectMultiScale(\n'
    '                gray,\n'
    '                scaleFactor=1.1,\n'
    '                minNeighbors=5,\n'
    '                minSize=(30, 30),\n'
    '                flags=cv2.CASCADE_SCALE_IMAGE,\n'
    '            )\n'
    '            return len(faces) > 0\n'
    '        except Exception as e:\n'
    '            logger.error(f"Face detection error for {image_path.name}: {e}")\n'
    '            return True\n'
    '\n'
    '    return detect_face\n'
    '\n'
    '\n'
    'def process_image_batch(args):\n'
    '    image_path, current_dir, noface_dir, cascade_path = args\n'
    '    detect_face = create_face_detector(cascade_path)\n'
    '    if detect_face is None:\n'
    '        return image_path, None, False, True\n'
    '    try:\n'
    '        if not image_path.exists():\n'
    '            return image_path, None, False, True\n'
    '        has_face = detect_face(image_path)\n'
    '        if not has_face:\n'
    '            try:\n'
    '                relative_path = image_path.relative_to(current_dir)\n'
    '            except ValueError:\n'
    '                relative_path = image_path.name\n'
    '            destination = noface_dir / relative_path\n'
    '            destination.parent.mkdir(parents=True, exist_ok=True)\n'
    '            shutil.move(str(image_path), str(destination))\n'
    '            return image_path, destination, True, has_face\n'
    '        else:\n'
    '            return image_path, None, False, has_face\n'
    '    except Exception as e:\n'
    '        logger.error(f"Error processing {image_path.name}: {e}")\n'
    '        return image_path, None, False, True\n'
    '\n'
    '\n'
    'def collect_images(directory, exclude_dir):\n'
    '    images = []\n'
    '    try:\n'
    '        for path in directory.rglob("*"):\n'
    '            if exclude_dir in path.parents or path.parent == exclude_dir:\n'
    '                continue\n'
    '            if path.is_file() and is_image_file(path):\n'
    '                images.append(path)\n'
    '    except Exception as e:\n'
    '        logger.error(f"Error scanning directory: {e}")\n'
    '    return images\n'
    '\n'
    '\n'
    'def process_images(num_workers=None):\n'
    '    current_dir = Path.cwd()\n'
    '    noface_dir = Path("/sdcard/DCIM/noface")\n'
    '    try:\n'
    '        noface_dir.mkdir(exist_ok=True)\n'
    '    except Exception as e:\n'
    '        print(f"❌ ERROR: Cannot create directory {noface_dir}: {e}")\n'
    '        return False\n'
    '    print("\\n🔍 Scanning for images...")\n'
    '    images = collect_images(current_dir, noface_dir)\n'
    '    if not images:\n'
    '        print("⚠️ No images found!")\n'
    '        return False\n'
    '    print(f"📸 Found {len(images)} images")\n'
    '    if num_workers is None:\n'
    '        num_workers = min(cpu_count(), len(images), 4)\n'
    '    num_workers = max(1, min(num_workers, 4))\n'
    '    print(f"⚙️ Using {num_workers} worker processes\\n")\n'
    '    args_list = [(img, current_dir, noface_dir, cascade_path) for img in images]\n'
    '    results = []\n'
    '    start_time = time.time()\n'
    '    if num_workers > 1:\n'
    '        with Pool(processes=num_workers) as pool:\n'
    '            for result in tqdm(\n'
    '                pool.imap_unordered(process_image_batch, args_list),\n'
    '                total=len(images),\n'
    '                desc="Processing images",\n'
    '                unit="img",\n'
    '            ):\n'
    '                results.append(result)\n'
    '    else:\n'
    '        for args in tqdm(args_list, desc="Processing images", unit="img"):\n'
    '            results.append(process_image_batch(args))\n'
    '    elapsed_time = time.time() - start_time\n'
    '    total = len(results)\n'
    '    moved = sum(1 for _, _, moved, _ in results if moved)\n'
    '    noface_count = sum(1 for _, _, _, has_face in results if not has_face)\n'
    '    has_face_count = total - noface_count\n'
    '    print("\\n" + "=" * 40)\n'
    '    print("📊 SUMMARY")\n'
    '    print("-" * 40)\n'
    '    print(f"Total images:     {total}")\n'
    '    print(f"With faces:       {has_face_count}")\n'
    '    print(f"Without faces:    {noface_count}")\n'
    '    print(f"Moved to noface: {moved}")\n'
    '    print(f"Time elapsed:     {elapsed_time:.2f} seconds")\n'
    '    print(f"Speed:            {total / elapsed_time:.1f} images/second")\n'
    '    if moved > 0:\n'
    '        print(f"\\n📁 Moved to: {noface_dir}")\n'
    '    print("-" * 40)\n'
    '    return True\n'
    '\n'
    '\n'
    'def main():\n'
    '    print("🔍 Checking for Haar cascade file...")\n'
    '    if not cascade_path:\n'
    '        print("❌ Cascade file not found!")\n'
    '        print("Install OpenCV with: pkg install opencv")\n'
    '        sys.exit(1)\n'
    '    print(f"✅ CASCADE FOUND: {cascade_path}")\n'
    '    if not FACE_DETECTION_AVAILABLE:\n'
    '        sys.exit(1)\n'
    '    print("\\n" + "=" * 40)\n'
    '    print("📸 FACE DETECTION IMAGE ORGANIZER")\n'
    '    print("-" * 40)\n'
    '    print(f"Working directory: {Path.cwd()}")\n'
    '    print("Images WITH faces → stay in place")\n'
    '    print("Images WITHOUT faces → moved to \'noface/\'")\n'
    '    print("-" * 40)\n'
    '    num_workers = None\n'
    '    if len(sys.argv) > 1:\n'
    '        try:\n'
    '            num_workers = int(sys.argv[1])\n'
    '            print(f"\\n⚙️ Using {num_workers} workers (from command line)")\n'
    '        except ValueError:\n'
    '            print(f"\\n⚠️ Invalid worker count: {sys.argv[1]}, using auto-detection")\n'
    '    success = process_images(num_workers)\n'
    '    sys.exit(0 if success else 1)\n'
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


class BoxfacesTool(BaseTool):
    """Wrapper for original boxfaces.py: detect_and_save_faces() + 0 more."""
    name: str = 'boxfaces'
    source_file: str = 'boxfaces.py'
    description: str = 'detect_and_save_faces() + 0 more'
    functions: list[str] = ['detect_and_save_faces']
    notes: str = ''
    source: str = _BOXFACES_SOURCE

class BwTool(BaseTool):
    """Wrapper for original bw.py: analyze_image() + 0 more."""
    name: str = 'bw'
    source_file: str = 'bw.py'
    description: str = 'analyze_image() + 0 more'
    functions: list[str] = ['analyze_image']
    notes: str = ''
    source: str = _BW_SOURCE

class IsnudeTool(BaseTool):
    """Wrapper for original isnude.py: check_nude() + 1 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'isnude'
    source_file: str = 'isnude.py'
    description: str = 'check_nude() + 1 more'
    functions: list[str] = ['check_nude', 'process_file']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _ISNUDE_SOURCE

class IspornTool(BaseTool):
    """Wrapper for original isporn.py: check_porn() + 1 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'isporn'
    source_file: str = 'isporn.py'
    description: str = 'check_porn() + 1 more'
    functions: list[str] = ['check_porn', 'process_file']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _ISPORN_SOURCE

class NofaceTool(BaseTool):
    """Wrapper for original noface.py: is_image_file() + 5 more."""
    name: str = 'noface'
    source_file: str = 'noface.py'
    description: str = 'is_image_file() + 5 more'
    functions: list[str] = ['is_image_file', 'create_face_detector', 'process_image_batch', 'collect_images', 'process_images', 'main']
    notes: str = ''
    source: str = _NOFACE_SOURCE

class ImgClassifyDetectUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'boxfaces': BoxfacesTool,
        'bw': BwTool,
        'isnude': IsnudeTool,
        'isporn': IspornTool,
        'noface': NofaceTool,
    }

    @classmethod
    def list_tools(cls: type[ImgClassifyDetectUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[ImgClassifyDetectUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[ImgClassifyDetectUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for img_classify_detect (5 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[ImgClassifyDetectUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[ImgClassifyDetectUnified], argv: Sequence[str] | None = None) -> int:
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
    return ImgClassifyDetectUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

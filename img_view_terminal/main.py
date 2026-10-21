#!/usr/bin/env python3
"""ImgViewTerminalUnified for img_view_terminal.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (6):
  img2asci <- img2asci.py (29L): process_file() + 1 more [requires missing module 'dh' (ImportError at runtime)]
  imgviewer <- imgviewer.py (37L): get_ansi_color_code() + 2 more
  pycatimg <- pycatimg.py (180L): resize_image() + 8 more
  termimage <- termimage.py (145L): is_image_file() + 6 more
  termimg0 <- termimg0.py (25L): print_image() + 0 more
  timg <- timg.py (123L): load_image() + 3 more

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

_IMG2ASCI_SOURCE: str = (
    'import os\n'
    'import sys\n'
    'from pathlib import Path\n'
    'from ascii_magic import AsciiArt\n'
    'from dh import get_files\n'
    '\n'
    '\n'
    'def process_file(image_path):\n'
    '    Path(path)\n'
    '    art = AsciiArt.from_image(image_path)\n'
    '    art.to_terminal(columns=os.get_terminal_size().columns, width_ratio=2, monochrome=False)\n'
    '\n'
    '\n'
    'def main():\n'
    '    cwd = Path.cwd()\n'
    '    args = sys.argv[1:]\n'
    '    files = [Path(arg) for arg in args] if args else get_files(cwd, ext=[".jpg", ".png", ".bmp", ".webp"])\n'
    '    if len(files) == 1:\n'
    '        process_file(files[0])\n'
    '        sys.exit(0)\n'
    '    pool = Pool(8)\n'
    '    for _ in pool.imap_unordered(process_file, files):\n'
    '        pass\n'
    '    pool.close()\n'
    '    pool.join()\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_IMGVIEWER_SOURCE: str = (
    'import sys\n'
    'import numpy as np\n'
    'from PIL import Image\n'
    '\n'
    '\n'
    'def get_ansi_color_code(r, g, b):\n'
    '    if r == g and g == b:\n'
    '        if r < 8:\n'
    '            return 16\n'
    '        if r > 248:\n'
    '            return 231\n'
    '        return round((r - 8) / 247 * 24) + 232\n'
    '    return 16 + 36 * round(r / 255 * 5) + 6 * round(g / 255 * 5) + round(b / 255 * 5)\n'
    '\n'
    '\n'
    'def get_color(r, g, b):\n'
    '    return f"\\x1b[48;5;{int(get_ansi_color_code(r, g, b))}m \\x1b[0m"\n'
    '\n'
    '\n'
    'def show_image(img_path):\n'
    '    try:\n'
    '        img = Image.open(img_path)\n'
    '    except FileNotFoundError:\n'
    '        sys.exit("Image not found.")\n'
    '    h = 100\n'
    '    w = int(img.width / img.height * h) * 2\n'
    '    img = img.resize((w, h), Image.Resampling.LANCZOS)\n'
    '    img_arr = np.asarray(img)\n'
    '    for x in range(h):\n'
    '        for y in range(w):\n'
    '            pix = img_arr[x][y]\n'
    '            print(get_color(pix[0], pix[1], pix[2]), end="")\n'
    '        print()\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    show_image(sys.argv[1])\n'
)

_PYCATIMG_SOURCE: str = (
    'import argparse\n'
    'import io\n'
    'import os\n'
    'import sys\n'
    'from cairosvg import svg2png\n'
    'from PIL import Image\n'
    'from PIL.ImageFile import ImageFile\n'
    '\n'
    'SVG_SUPPORT = True\n'
    '\n'
    '\n'
    'def resize_image(\n'
    '    img,\n'
    '    terminal_width,\n'
    '    terminal_height,\n'
    '    max_width=None,\n'
    '    max_height=None,\n'
    '):\n'
    '    orig_width, orig_height = img.size\n'
    '    if max_width and max_height:\n'
    '        target_width = min(max_width, terminal_width)\n'
    '        target_height = min(max_height, terminal_height)\n'
    '    else:\n'
    '        target_width = terminal_width\n'
    '        target_height = terminal_height\n'
    '    aspect = orig_height / orig_width\n'
    '    new_width = target_width\n'
    '    new_height = int(target_width * aspect)\n'
    '    if new_height > target_height:\n'
    '        new_height = target_height\n'
    '        new_width = int(target_height / aspect)\n'
    '    new_width = max(1, new_width)\n'
    '    new_height = max(1, new_height)\n'
    '    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)\n'
    '\n'
    '\n'
    'def load_svg(svg_path, width=None, height=None):\n'
    '    if not SVG_SUPPORT:\n'
    '        print(\n'
    '            "Error: SVG support requires \'cairosvg\' library. Install with: pip install cairosvg",\n'
    '            file=sys.stderr,\n'
    '        )\n'
    '        sys.exit(1)\n'
    '    try:\n'
    '        if not width or not height:\n'
    '            term_width, term_height = get_terminal_size()\n'
    '            term_height *= 2\n'
    '            width = width or term_width\n'
    '            height = height or term_height\n'
    '        png_data = svg2png(url=svg_path, output_width=width, output_height=height)\n'
    '        img = Image.open(io.BytesIO(png_data))\n'
    '        return img\n'
    '    except Exception as e:\n'
    '        print(f"Error loading SVG: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'def load_image(image_path, width=None, height=None):\n'
    '    if image_path.lower().endswith(".svg"):\n'
    '        return load_svg(image_path, width, height)\n'
    '    try:\n'
    '        return Image.open(image_path)\n'
    '    except Exception as e:\n'
    '        print(f"Error loading image: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'def rgb_to_ansi(r, g, b):\n'
    '    return f"\\x1b[38;2;{r};{g};{b}m"\n'
    '\n'
    '\n'
    'def image_to_ansi(img):\n'
    '    img = img.convert("RGB")\n'
    '    width, height = img.size\n'
    '    output_lines = []\n'
    '    for y in range(height):\n'
    '        line = []\n'
    '        for x in range(width):\n'
    '            r, g, b = img.getpixel((x, y))\n'
    '            line.append(f"{rgb_to_ansi(r, g, b)}██")\n'
    '        output_lines.append("".join(line))\n'
    '    output = "\\n".join(output_lines) + "\\x1b[0m"\n'
    '    return output\n'
    '\n'
    '\n'
    'def image_to_ansi_blocks(img):\n'
    '    img = img.convert("RGB")\n'
    '    width, height = img.size\n'
    '    if height % 2 != 0:\n'
    '        new_img = Image.new("RGB", (width, height + 1), (0, 0, 0))\n'
    '        new_img.paste(img, (0, 0))\n'
    '        img = new_img\n'
    '        height += 1\n'
    '    output_lines = []\n'
    '    for y in range(0, height, 2):\n'
    '        line = []\n'
    '        for x in range(width):\n'
    '            r1, g1, b1 = img.getpixel((x, y))\n'
    '            r2, g2, b2 = img.getpixel((x, y + 1)) if y + 1 < height else (0, 0, 0)\n'
    '            line.append(f"\\x1b[38;2;{r1};{g1};{b1}m\\x1b[48;2;{r2};{g2};{b2}m▀")\n'
    '        output_lines.append("".join(line))\n'
    '    output = "\\n".join(output_lines) + "\\x1b[0m"\n'
    '    return output\n'
    '\n'
    '\n'
    'def get_terminal_size():\n'
    '    try:\n'
    '        columns, rows = os.get_terminal_size()\n'
    '        return columns, rows\n'
    '    except:\n'
    '        return 80, 24\n'
    '\n'
    '\n'
    'def catimg(image_path, width=None, height=None, use_half_blocks=True, dpi=96, bg_color=None):\n'
    '    if not os.path.exists(image_path):\n'
    '        print(f"Error: File \'{image_path}\' not found", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    try:\n'
    '        term_width, term_height = get_terminal_size()\n'
    '        if use_half_blocks:\n'
    '            term_height *= 2\n'
    '        render_width = None\n'
    '        render_height = None\n'
    '        if width or height:\n'
    '            if width:\n'
    '                render_width = min(width, term_width)\n'
    '            if height:\n'
    '                render_height = min(height, term_height)\n'
    '        else:\n'
    '            render_width = term_width\n'
    '            render_height = term_height\n'
    '        if image_path.lower().endswith(".svg"):\n'
    '            img = load_svg(image_path, render_width, render_height)\n'
    '        else:\n'
    '            img = load_image(image_path)\n'
    '            img = resize_image(img, term_width, term_height, width, height)\n'
    '        if use_half_blocks:\n'
    '            output = image_to_ansi_blocks(img)\n'
    '        else:\n'
    '            output = image_to_ansi(img)\n'
    '        print(output)\n'
    '    except KeyboardInterrupt:\n'
    '        sys.exit(0)\n'
    '    except Exception as e:\n'
    '        print(f"Error: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Display images in terminal with true color support (including SVG)",\n'
    '        epilog="Supports: PNG, JPEG, GIF, BMP, TIFF, SVG (requires cairosvg)",\n'
    '    )\n'
    '    parser.add_argument("image", help="Path to image file (supports SVG)")\n'
    '    parser.add_argument("-w", "--width", type=int, help="Maximum width in characters")\n'
    '    parser.add_argument("-H", "--height", type=int, help="Maximum height in characters")\n'
    '    parser.add_argument(\n'
    '        "--no-half-blocks",\n'
    '        action="store_true",\n'
    '        help="Disable half-block characters (lower vertical resolution)",\n'
    '    )\n'
    '    parser.add_argument("--dpi", type=int, default=96, help="DPI for SVG rendering (default: 96)")\n'
    '    parser.add_argument(\n'
    '        "--bg-color",\n'
    '        help=\'Background color for transparent areas (e.g., "black" or "#000000")\',\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    if args.image.lower().endswith(".svg") and not SVG_SUPPORT:\n'
    '        print("Warning: SVG support requires \'cairosvg\'. Install with:", file=sys.stderr)\n'
    '        print("  pip install cairosvg", file=sys.stderr)\n'
    '        print("\\nFor system dependencies (Linux):", file=sys.stderr)\n'
    '        print("  Ubuntu/Debian: sudo apt-get install libcairo2-dev", file=sys.stderr)\n'
    '        print("  Fedora: sudo dnf install cairo-devel", file=sys.stderr)\n'
    '        print("Arch: sudo pacman -S cairo", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    catimg(args.image, args.width, args.height, use_half_blocks=not args.no_half_blocks)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_TERMIMAGE_SOURCE: str = (
    'import argparse\n'
    'import os\n'
    'import sys\n'
    'from pathlib import Path\n'
    'from urllib.request import urlopen\n'
    '\n'
    'IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}\n'
    '\n'
    '\n'
    'def is_image_file(path):\n'
    '    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS\n'
    '\n'
    '\n'
    'def get_terminal_width():\n'
    '    try:\n'
    '        return os.get_terminal_size().columns\n'
    '    except OSError:\n'
    '        return 80\n'
    '\n'
    '\n'
    'def load_ppm(path):\n'
    '    with path.open("rb") as f:\n'
    '        header = []\n'
    '        while len(header) < 4:\n'
    '            line = f.readline().strip()\n'
    '            if not line or line.startswith(b"#"):\n'
    '                continue\n'
    '            header.extend(line.split())\n'
    '        fmt, width, height, max_val = (\n'
    '            header[0],\n'
    '            int(header[1]),\n'
    '            int(header[2]),\n'
    '            int(header[3]),\n'
    '        )\n'
    '        data = f.read()\n'
    '    pixels = []\n'
    '    if fmt == b"P6":\n'
    '        for i in range(0, len(data), 3):\n'
    '            if i + 2 < len(data):\n'
    '                pixels.append((data[i], data[i + 1], data[i + 2]))\n'
    '    elif fmt == b"P3":\n'
    '        numbers = [int(n) for n in data.split()]\n'
    '        for i in range(0, len(numbers), 3):\n'
    '            pixels.append((numbers[i], numbers[i + 1], numbers[i + 2]))\n'
    '    return width, height, pixels\n'
    '\n'
    '\n'
    'def render_half_blocks(width, height, pixels, max_width):\n'
    '    scale = max(1, width // max_width)\n'
    '    scaled_w = width // scale\n'
    '    scaled_h = height // scale\n'
    '    grid = []\n'
    '    for y in range(scaled_h):\n'
    '        row = []\n'
    '        for x in range(scaled_w):\n'
    '            orig_x = min(x * scale, width - 1)\n'
    '            orig_y = min(y * scale, height - 1)\n'
    '            idx = orig_y * width + orig_x\n'
    '            row.append(pixels[idx] if idx < len(pixels) else (0, 0, 0))\n'
    '        grid.append(row)\n'
    '    lines = []\n'
    '    for y in range(0, scaled_h - 1, 2):\n'
    '        row_str = []\n'
    '        for x in range(scaled_w):\n'
    '            top_r, top_g, top_b = grid[y][x]\n'
    '            bot_r, bot_g, bot_b = grid[y + 1][x]\n'
    '            cell = f"\\033[38;2;{top_r};{top_g};{top_b}m\\033[48;2;{bot_r};{bot_g};{bot_b}m▀\\033[0m"\n'
    '            row_str.append(cell)\n'
    '        lines.append("".join(row_str))\n'
    '    return "\\n".join(lines)\n'
    '\n'
    '\n'
    'def render_file(path, max_width):\n'
    '    print(f"\\n--- {path} ---")\n'
    '    try:\n'
    '        from PIL import Image\n'
    '\n'
    '        with Image.open(path) as img:\n'
    '            img = img.convert("RGB")\n'
    '            w, h = img.size\n'
    '            pixels = list(img.getdata())\n'
    '            print(render_half_blocks(w, h, pixels, max_width))\n'
    '            return\n'
    '    except ImportError:\n'
    '        pass\n'
    '    if path.suffix.lower() == ".ppm":\n'
    '        try:\n'
    '            w, h, pixels = load_ppm(path)\n'
    '            print(render_half_blocks(w, h, pixels, max_width))\n'
    '            return\n'
    '        except Exception as e:\n'
    '            print(f"Error reading PPM file {path}: {e}")\n'
    '            return\n'
    '    print(f"Unable to render \'{path.name}\'. Install \'Pillow\' (`pip install pillow`) to view PNG/JPG/WebP/GIF formats.")\n'
    '\n'
    '\n'
    'def traverse_directory(root_dir):\n'
    '    images = []\n'
    '    for path in root_dir.rglob("*"):\n'
    '        if is_image_file(path):\n'
    '            images.append(path)\n'
    '    return sorted(images)\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(description="Termimage in Python: Render images in your terminal.")\n'
    '    parser.add_argument(\n'
    '        "paths",\n'
    '        nargs="*",\n'
    '        type=Path,\n'
    '        help="Image files or directories to render. Defaults to current directory recursively if omitted.",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-w",\n'
    '        "--width",\n'
    '        type=int,\n'
    '        default=None,\n'
    '        help="Target rendering width in terminal columns (defaults to auto terminal width).",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    max_width = args.width or get_terminal_width()\n'
    '    if not args.paths:\n'
    '        target_paths = [Path.cwd()]\n'
    '    else:\n'
    '        target_paths = args.paths\n'
    '    target_images = []\n'
    '    for path in target_paths:\n'
    '        if path.is_dir():\n'
    '            target_images.extend(traverse_directory(path))\n'
    '        elif is_image_file(path):\n'
    '            target_images.append(path)\n'
    '        else:\n'
    '            print(\n'
    '                f"Warning: \'{path}\' is not a directory or supported image file.",\n'
    '                file=sys.stderr,\n'
    '            )\n'
    '    if not target_images:\n'
    '        print("No image files found.")\n'
    '        sys.exit(0)\n'
    '    for img_path in target_images:\n'
    '        render_file(img_path, max_width)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    main()\n'
)

_TERMIMG0_SOURCE: str = (
    'import sys\n'
    'from shutil import get_terminal_size\n'
    'from PIL import Image\n'
    '\n'
    '\n'
    'def print_image(image_path, width=40):\n'
    '    img = Image.open(image_path).convert("RGB")\n'
    '    aspect_ratio = img.height / img.width\n'
    '    width = get_terminal_size()[0]\n'
    '    height = int(width * aspect_ratio * 0.55)\n'
    '    img = img.resize((width, height))\n'
    '    pixels = img.load()\n'
    '    for y in range(0, height - 1, 2):\n'
    '        for x in range(width):\n'
    '            r1, g1, b1 = pixels[x, y]\n'
    '            r2, g2, b2 = pixels[x, y + 1]\n'
    '            print(f"\\033[48;2;{r1};{g1};{b1}m\\033[38;2;{r2};{g2};{b2}m▀", end="")\n'
    '        print("\\033[0m")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: python termimg.py <image_path>")\n'
    '    else:\n'
    '        print_image(sys.argv[1])\n'
)

_TIMG_SOURCE: str = (
    'import argparse\n'
    'import io\n'
    'import os\n'
    'import shutil\n'
    'import sys\n'
    'from pathlib import Path\n'
    'from typing import Iterator\n'
    'from PIL import Image\n'
    '\n'
    'IMAGE_EXTENSIONS = {\n'
    '    ".png",\n'
    '    ".jpg",\n'
    '    ".jpeg",\n'
    '    ".webp",\n'
    '    ".bmp",\n'
    '    ".gif",\n'
    '    ".tiff",\n'
    '    ".svg",\n'
    '}\n'
    '\n'
    '\n'
    'def load_image(file_path):\n'
    '    if file_path.suffix.lower() == ".svg":\n'
    '        try:\n'
    '            import cairosvg\n'
    '\n'
    '            png_bytes = cairosvg.svg2png(url=str(file_path))\n'
    '            return Image.open(io.BytesIO(png_bytes)).convert("RGBA")\n'
    '        except ImportError:\n'
    '            raise RuntimeError("cairosvg is required to render SVG files. Run: pip install cairosvg")\n'
    '        except Exception as err:\n'
    '            raise ValueError(f"Failed to render SVG file: {err}")\n'
    '    img = Image.open(file_path)\n'
    '    return img.convert("RGBA")\n'
    '\n'
    '\n'
    'def find_images(target_dir, recursive=True):\n'
    '    if not recursive:\n'
    '        for p in target_dir.iterdir():\n'
    '            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:\n'
    '                yield p\n'
    '        return\n'
    '    for root, _, files in target_dir.walk():\n'
    '        for file in files:\n'
    '            p = root / file\n'
    '            if p.suffix.lower() in IMAGE_EXTENSIONS:\n'
    '                yield p\n'
    '\n'
    '\n'
    'def render_to_terminal(img, max_w, max_h):\n'
    '    img_w, img_h = img.size\n'
    '    if img_w == 0 or img_h == 0:\n'
    '        return\n'
    '    max_h_pixels = max_h * 2\n'
    '    scale = min(max_w / img_w, max_h_pixels / img_h)\n'
    '    new_w = max(1, int(img_w * scale))\n'
    '    new_h_pixels = max(2, int(img_h * scale))\n'
    '    if new_h_pixels % 2 != 0:\n'
    '        new_h_pixels -= 1\n'
    '    resized = img.resize((new_w, new_h_pixels), Image.Resampling.LANCZOS)\n'
    '    pixels = resized.load()\n'
    '    output = []\n'
    '    for y in range(0, new_h_pixels, 2):\n'
    '        row_str = []\n'
    '        for x in range(new_w):\n'
    '            r1, g1, b1, a1 = pixels[x, y]\n'
    '            r2, g2, b2, a2 = pixels[x, y + 1]\n'
    '            if a1 < 255:\n'
    '                r1, g1, b1 = (\n'
    '                    int(r1 * (a1 / 255)),\n'
    '                    int(g1 * (a1 / 255)),\n'
    '                    int(b1 * (a1 / 255)),\n'
    '                )\n'
    '            if a2 < 255:\n'
    '                r2, g2, b2 = (\n'
    '                    int(r2 * (a2 / 255)),\n'
    '                    int(g2 * (a2 / 255)),\n'
    '                    int(b2 * (a2 / 255)),\n'
    '                )\n'
    '            char = f"\\x1b[38;2;{r1};{g1};{b1}m\\x1b[48;2;{r2};{g2};{b2}m▀\\x1b[0m"\n'
    '            row_str.append(char)\n'
    '        output.append("".join(row_str))\n'
    '    print("\\n".join(output))\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(description="Terminal Image Viewer (timg clone)")\n'
    '    parser.add_argument(\n'
    '        "inputs",\n'
    '        nargs="*",\n'
    '        type=Path,\n'
    '        help="Files or directories to display (defaults to current dir recursively)",\n'
    '    )\n'
    '    parser.add_argument("-W", "--width", type=int, default=None, help="Max terminal columns")\n'
    '    parser.add_argument("-H", "--height", type=int, default=None, help="Max terminal rows")\n'
    '    args = parser.parse_args()\n'
    '    term_columns, term_rows = shutil.get_terminal_size((80, 24))\n'
    '    max_w = args.width or term_columns\n'
    '    max_h = args.height or (term_rows - 2)\n'
    '    targets = []\n'
    '    if not args.inputs:\n'
    '        targets = sorted(list(find_images(Path.cwd(), recursive=True)))\n'
    '    else:\n'
    '        for path in args.inputs:\n'
    '            if path.is_dir():\n'
    '                targets.extend(sorted(list(find_images(path, recursive=True))))\n'
    '            elif path.is_file():\n'
    '                targets.append(path)\n'
    '    if not targets:\n'
    '        print("No supported image files found.", file=sys.stderr)\n'
    '        sys.exit(0)\n'
    '    for file_path in targets:\n'
    '        print(f"=== {file_path} ===")\n'
    '        try:\n'
    '            img = load_image(file_path)\n'
    '            render_to_terminal(img, max_w, max_h)\n'
    '        except Exception as e:\n'
    '            print(f"[Error loading {file_path.name}: {e}]", file=sys.stderr)\n'
    '        print()\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    main()\n'
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


class Img2asciTool(BaseTool):
    """Wrapper for original img2asci.py: process_file() + 1 more NOTE: requires missing module 'dh' (ImportError at runtime)."""
    name: str = 'img2asci'
    source_file: str = 'img2asci.py'
    description: str = 'process_file() + 1 more'
    functions: list[str] = ['process_file', 'main']
    notes: str = "requires missing module 'dh' (ImportError at runtime)"
    source: str = _IMG2ASCI_SOURCE

class ImgviewerTool(BaseTool):
    """Wrapper for original imgviewer.py: get_ansi_color_code() + 2 more."""
    name: str = 'imgviewer'
    source_file: str = 'imgviewer.py'
    description: str = 'get_ansi_color_code() + 2 more'
    functions: list[str] = ['get_ansi_color_code', 'get_color', 'show_image']
    notes: str = ''
    source: str = _IMGVIEWER_SOURCE

class PycatimgTool(BaseTool):
    """Wrapper for original pycatimg.py: resize_image() + 8 more."""
    name: str = 'pycatimg'
    source_file: str = 'pycatimg.py'
    description: str = 'resize_image() + 8 more'
    functions: list[str] = ['resize_image', 'load_svg', 'load_image', 'rgb_to_ansi', 'image_to_ansi', 'image_to_ansi_blocks', 'get_terminal_size', 'catimg', 'main']
    notes: str = ''
    source: str = _PYCATIMG_SOURCE

class TermimageTool(BaseTool):
    """Wrapper for original termimage.py: is_image_file() + 6 more."""
    name: str = 'termimage'
    source_file: str = 'termimage.py'
    description: str = 'is_image_file() + 6 more'
    functions: list[str] = ['is_image_file', 'get_terminal_width', 'load_ppm', 'render_half_blocks', 'render_file', 'traverse_directory', 'main']
    notes: str = ''
    source: str = _TERMIMAGE_SOURCE

class Termimg0Tool(BaseTool):
    """Wrapper for original termimg0.py: print_image() + 0 more."""
    name: str = 'termimg0'
    source_file: str = 'termimg0.py'
    description: str = 'print_image() + 0 more'
    functions: list[str] = ['print_image']
    notes: str = ''
    source: str = _TERMIMG0_SOURCE

class TimgTool(BaseTool):
    """Wrapper for original timg.py: load_image() + 3 more."""
    name: str = 'timg'
    source_file: str = 'timg.py'
    description: str = 'load_image() + 3 more'
    functions: list[str] = ['load_image', 'find_images', 'render_to_terminal', 'main']
    notes: str = ''
    source: str = _TIMG_SOURCE

class ImgViewTerminalUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'img2asci': Img2asciTool,
        'imgviewer': ImgviewerTool,
        'pycatimg': PycatimgTool,
        'termimage': TermimageTool,
        'termimg0': Termimg0Tool,
        'timg': TimgTool,
    }

    @classmethod
    def list_tools(cls: type[ImgViewTerminalUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[ImgViewTerminalUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[ImgViewTerminalUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for img_view_terminal (6 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[ImgViewTerminalUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[ImgViewTerminalUnified], argv: Sequence[str] | None = None) -> int:
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
    return ImgViewTerminalUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

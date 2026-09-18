# bin — personal script collection
- bin dir in my home folder
## Layout
The Python scripts are **folderized by functionality**: every script that does the same job
as another one lives in the same sub-directory (e.g. all Zstandard compressors in
`compress_zstd/`, all "strip comments from Python files" tools in `strip_comments_python/`,
all wheel repackers in `wheel_build_repack/`).
- 161 folders, 1217 scripts grouped.
- A folder is only created when it has **at least two members**; scripts with a unique job
  stay in the repo root: `cli_wrapper.py`, `fix_html_md_broken_links.py`,
  `gitignore_updater.py`, `rm_from_archive.py`, `update_summary.py`.
- The old extension-less symlinks that mirrored each `*.py` name
  (`20most -> .../bin/20most.py`) were removed; they pointed at absolute Termux paths and
  were broken duplicates of the script names.
Full folder → script listing, plus the duplicate report: **[SCRIPT_INDEX.md](SCRIPT_INDEX.md)**
Folders are sorted by size in that index, so the biggest clusters (the ones with the most
overlap) come first.
## Duplicate collapse
A content-similarity pass over every pair inside each folder found 21 pairs that were ≥ 95 %
the same program. They were collapsed into one canonical script each:
- **9 redundant twins deleted** — the better copy was kept (e.g. `annotate_types.py` →
  `add_typing.py`, `cleanmd.py` → `markdown_image_remover.py`, `fssim.py`/`ssdim.py` →
  `ssim2.py`, `dduper.py` → `deduplicate_python.py`).
- **3 template families merged into one parameterised script**:
  - `extract_python_entities/ex_nodes.py --kind class|func|docstrings|comments|all`
    (replaces `ex_class.py`, `ex_func.py`, `ex_ex.py`, `ex_comments.py`)
  - `font_convert/font_convert.py --to woff|woff2|ttf [-r]`
    (replaces `otf2woff2.py`, `ttf2woff2.py`, `woff2woff2.py`, `woff22woff.py`)
  - `cli_wrapper.py <binary> …` / `--bin /path/to/bin`
    (replaces `cli_wrapper_log/feloai.py`, `cli_wrapper_log/wrapper_gh.py`)
The 18 pairs that are still ≥ 90 % similar were kept: they share a code template but do
different jobs (opposite directions like `gz2xz`/`xz2gz`, different libraries, different
targets). Details in `SCRIPT_INDEX.md`.

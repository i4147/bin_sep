# Unified tools — notes

Each top-level subfolder now contains exactly one script: `main.py`.
It does all jobs the folder's original scripts did, via `python main.py <tool> [args...]`.

## Approach
- Class-based (`BaseTool` + one subclass per original script + `<Folder>Unified` dispatcher).
- Fully type-annotated (all defs have param + return annotations; constants annotated).
- Each original source embedded line-wise and exec'd with isolated globals,
  `sys.argv = [source_file] + args`, `__name__ == "__main__"`.
- Flags: `--list`, `--info <tool>`, `<tool> [passthrough...]`; single-tool folders
  also accept `python main.py [args...]` directly.

## Assumptions
- Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.
- Assumption (single-file folders): `main.py [args...]` passes through to the only tool.

## Impossible / plainly-broken (not faked)
- `encrypt_decrypt/zip_crack.py` and `html_template_gen/codepener.py`: SyntaxError on
  Python 3.11 (multi-line f-string expressions need Python 3.12+/PEP 701).
  Unified subcommands `zip_crack` / `codepener` fail plainly with rc=2 on 3.11,
  and work on 3.12+ without changes.
- Many scripts `from dh import ...`: module `dh` is absent from the repo, so those
  subcommands fail plainly with ImportError (rc=3). Nothing simulated.
- Third-party deps (`speech_recognition`, `pydub`, `whisper`, `pyzbar`, `tree_sitter*`,
  `chardet`, `cryptography`, etc.) and external binaries (`termux-tts-speak`, `clang`,
  media tools) must be installed by the user; missing ones fail plainly.

## Verification
- All 39 `main.py` compile and pass `--list` / `--help` / `--info`.
- Spot-checked fidelity: `csv_convert/csv2json` original vs unified produce identical output.
- `collect_env_vars` (top-level script, no `__main__`) runs and writes `env_vars.txt`.
- Exit codes: 0 ok, 1 tool error / `sys.exit(1)`, 2 SyntaxError/unknown tool, 3 ImportError.

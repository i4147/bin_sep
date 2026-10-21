#!/usr/bin/env python3
"""GitDiffReportUnified for git_diff_report.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (3):
  git_differ <- git_differ.py (100L): run_git() + 6 more
  gitdif <- gitdif.py (93L): get_repo_status() + 3 more
  gitreport <- gitreport.py (59L): get_added_files_per_commit() + 1 more

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

_GIT_DIFFER_SOURCE: str = (
    'import json\n'
    'import subprocess\n'
    'import sys\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def run_git(*args, cwd):\n'
    '    result = subprocess.run(\n'
    '        ["git", *args],\n'
    '        cwd=cwd,\n'
    '        capture_output=True,\n'
    '        text=True,\n'
    '        check=False,\n'
    '    )\n'
    '    if result.returncode != 0:\n'
    '        raise RuntimeError(f"git {\' \'.join(args)} failed: {result.stderr.strip()}")\n'
    '    return result.stdout\n'
    '\n'
    '\n'
    'def get_last_two_commits(repo):\n'
    '    log_output = run_git("log", "-2", "--format=%H", cwd=repo).strip().splitlines()\n'
    '    if len(log_output) < 2:\n'
    '        raise RuntimeError("Repository needs at least 2 commits to diff.")\n'
    '    newer, older = log_output\n'
    '    return older, newer\n'
    '\n'
    '\n'
    'def get_commit_meta(repo, commit_hash):\n'
    '    fmt = "%an%x00%ae%x00%ad%x00%s"\n'
    '    line = run_git("show", "-s", f"--format={fmt}", commit_hash, cwd=repo).strip()\n'
    '    author, email, date, subject = line.split("\\x00")\n'
    '    return {\n'
    '        "hash": commit_hash,\n'
    '        "author": author,\n'
    '        "email": email,\n'
    '        "date": date,\n'
    '        "subject": subject,\n'
    '    }\n'
    '\n'
    '\n'
    'def get_file_stats(repo, older, newer):\n'
    '    name_status = run_git("diff", "--name-status", older, newer, cwd=repo).strip().splitlines()\n'
    '    numstat = run_git("diff", "--numstat", older, newer, cwd=repo).strip().splitlines()\n'
    '    numstat_map = {}\n'
    '    for line in numstat:\n'
    '        parts = line.split("\\t")\n'
    '        if len(parts) == 3:\n'
    '            added, deleted, path = parts\n'
    '            numstat_map[path] = {\n'
    '                "insertions": None if added == "-" else int(added),\n'
    '                "deletions": None if deleted == "-" else int(deleted),\n'
    '            }\n'
    '    files = []\n'
    '    for line in name_status:\n'
    '        parts = line.split("\\t")\n'
    '        status = parts[0]\n'
    '        if status.startswith(("R", "C")) and len(parts) == 3:\n'
    '            old_path, path = parts[1], parts[2]\n'
    '        else:\n'
    '            old_path, path = None, parts[1]\n'
    '        stats = numstat_map.get(path, {"insertions": None, "deletions": None})\n'
    '        files.append({\n'
    '            "status": status,\n'
    '            "path": path,\n'
    '            "old_path": old_path,\n'
    '            "insertions": stats["insertions"],\n'
    '            "deletions": stats["deletions"],\n'
    '        })\n'
    '    return files\n'
    '\n'
    '\n'
    'def get_patch(repo, older, newer):\n'
    '    return run_git("diff", older, newer, cwd=repo)\n'
    '\n'
    '\n'
    'def build_report(repo):\n'
    '    older, newer = get_last_two_commits(repo)\n'
    '    return {\n'
    '        "repo": str(repo.resolve()),\n'
    '        "from_commit": get_commit_meta(repo, older),\n'
    '        "to_commit": get_commit_meta(repo, newer),\n'
    '        "files": get_file_stats(repo, older, newer),\n'
    '        "patch": get_patch(repo, older, newer),\n'
    '    }\n'
    '\n'
    '\n'
    'def main():\n'
    '    repo = Path.cwd()\n'
    '    output_path = repo / "diff_report.json"\n'
    '    try:\n'
    '        report = build_report(repo)\n'
    '    except RuntimeError as e:\n'
    '        print(f"Error: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")\n'
    '    print(f"✓ Wrote diff report: {output_path}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_GITDIF_SOURCE: str = (
    'import subprocess\n'
    'import sys\n'
    'from multiprocessing import Pool, cpu_count\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def get_repo_status(repo_path):\n'
    '    try:\n'
    '        git_dir = repo_path / ".git"\n'
    '        if not git_dir.exists() or not git_dir.is_dir():\n'
    '            return (repo_path, False, "Not a git repository")\n'
    '        result = subprocess.run(\n'
    '            ["git", "status", "--porcelain"],\n'
    '            cwd=repo_path,\n'
    '            capture_output=True,\n'
    '            text=True,\n'
    '            timeout=5,\n'
    '        )\n'
    '        if result.returncode != 0:\n'
    '            return (repo_path, False, f"Git error: {result.stderr.strip()}")\n'
    '        has_changes = bool(result.stdout.strip())\n'
    '        if has_changes:\n'
    '            lines = result.stdout.strip().split("\\n")\n'
    '            changes = []\n'
    '            for line in lines:\n'
    '                status = line[:2]\n'
    '                file = line[3:]\n'
    '                if status.strip():\n'
    '                    changes.append(f"{status} {file}")\n'
    '            change_summary = ", ".join(changes[:5])\n'
    '            if len(changes) > 5:\n'
    '                change_summary += f" (+{len(changes) - 5} more)"\n'
    '            return (repo_path, True, change_summary)\n'
    '        else:\n'
    '            return (repo_path, False, "Clean")\n'
    '    except subprocess.TimeoutExpired:\n'
    '        return (repo_path, False, "Timeout checking git status")\n'
    '    except Exception as e:\n'
    '        return (repo_path, False, f"Error: {e!s}")\n'
    '\n'
    '\n'
    'def find_git_repos(directory):\n'
    '    repos = []\n'
    '    for item in directory.iterdir():\n'
    '        if item.is_dir() and not item.name.startswith(".") and (item / ".git").is_dir():\n'
    '            repos.append(item)\n'
    '    return repos\n'
    '\n'
    '\n'
    'def print_result(result):\n'
    '    path, has_changes, info = result\n'
    '    if not has_changes:\n'
    '        print(f"✓ {path.name}: No changes")\n'
    '        if info and info != "Clean":\n'
    '            print(f"  └─ {info}")\n'
    '    else:\n'
    '        print(f"✗ {path.name}: CHANGES DETECTED")\n'
    '        if info:\n'
    '            print(f"  └─ {info}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    root_dir = Path.cwd()\n'
    '    print(f"Scanning for git repositories in: {root_dir}\\n")\n'
    '    repos = find_git_repos(root_dir)\n'
    '    if not repos:\n'
    '        print("No git repositories found in current directory.")\n'
    '        return\n'
    '    print(f"Found {len(repos)} git repository(ies)\\n")\n'
    '    num_processes = min(cpu_count(), len(repos), 8)\n'
    '    print(f"Checking repositories using {num_processes} process(es)...\\n")\n'
    '    with Pool(processes=num_processes) as pool:\n'
    '        results = pool.map(get_repo_status, repos)\n'
    '    changed_count = sum(1 for _, has_changes, _ in results if has_changes)\n'
    '    if changed_count > 0:\n'
    '        print("=" * 40)\n'
    '        print(f"⚠️  Found {changed_count} repository(ies) with changes")\n'
    '        print("=" * 40)\n'
    '    else:\n'
    '        print("=" * 40)\n'
    '        print("✅ All repositories are clean")\n'
    '        print("=" * 40)\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    try:\n'
    '        raise SystemExit(main())\n'
    '    except KeyboardInterrupt:\n'
    '        print("\\n\\nScan interrupted by user.")\n'
    '        sys.exit(1)\n'
    '    except Exception as e:\n'
    '        print(f"\\nError: {e}")\n'
    '        sys.exit(1)\n'
)

_GITREPORT_SOURCE: str = (
    'import json\n'
    'import sys\n'
    'from dulwich.repo import Repo\n'
    '\n'
    '\n'
    'def get_added_files_per_commit(repo_path):\n'
    '    repo = Repo(repo_path)\n'
    '    result = {}\n'
    '    try:\n'
    '        walker = repo.get_walker()\n'
    '        commits = list(walker)\n'
    '        tree_files_cache = {}\n'
    '\n'
    '        def tree_files(tree_sha):\n'
    '            if tree_sha in tree_files_cache:\n'
    '                return tree_files_cache[tree_sha]\n'
    '            files = set()\n'
    '            tree = repo[tree_sha]\n'
    '            stack = [("", tree)]\n'
    '            while stack:\n'
    '                prefix, t = stack.pop()\n'
    '                for item in t.iteritems():\n'
    '                    name = item.path.decode() if isinstance(item.path, bytes) else item.path\n'
    '                    full = f"{prefix}{name}"\n'
    '                    if item.mode & 0o170000 == 0o040000:\n'
    '                        stack.append((full + "/", repo[item.sha]))\n'
    '                    else:\n'
    '                        files.add(full)\n'
    '            tree_files_cache[tree_sha] = files\n'
    '            return files\n'
    '\n'
    '        for entry in commits:\n'
    '            commit = entry.commit\n'
    '            commit_sha = commit.id.decode()\n'
    '            short = commit_sha[:8]\n'
    '            current_files = tree_files(commit.tree)\n'
    '            parent_files = set()\n'
    '            for parent_sha in commit.parents:\n'
    '                parent = repo[parent_sha]\n'
    '                parent_files |= tree_files(parent.tree)\n'
    '            added = current_files - parent_files\n'
    '            added_names = sorted({f.split("/")[-1] for f in added})\n'
    '            result[short] = added_names\n'
    '    finally:\n'
    '        repo.close()\n'
    '    return result\n'
    '\n'
    '\n'
    'def main():\n'
    '    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."\n'
    '    output_path = sys.argv[2] if len(sys.argv) > 2 else "added_files.json"\n'
    '    data = get_added_files_per_commit(repo_path)\n'
    '    with open(output_path, "w") as f:\n'
    '        json.dump(data, f, indent=2)\n'
    '    print(f"Wrote {len(data)} commits to {output_path}")\n'
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


class GitDifferTool(BaseTool):
    """Wrapper for original git_differ.py: run_git() + 6 more."""
    name: str = 'git_differ'
    source_file: str = 'git_differ.py'
    description: str = 'run_git() + 6 more'
    functions: list[str] = ['run_git', 'get_last_two_commits', 'get_commit_meta', 'get_file_stats', 'get_patch', 'build_report', 'main']
    notes: str = ''
    source: str = _GIT_DIFFER_SOURCE

class GitdifTool(BaseTool):
    """Wrapper for original gitdif.py: get_repo_status() + 3 more."""
    name: str = 'gitdif'
    source_file: str = 'gitdif.py'
    description: str = 'get_repo_status() + 3 more'
    functions: list[str] = ['get_repo_status', 'find_git_repos', 'print_result', 'main']
    notes: str = ''
    source: str = _GITDIF_SOURCE

class GitreportTool(BaseTool):
    """Wrapper for original gitreport.py: get_added_files_per_commit() + 1 more."""
    name: str = 'gitreport'
    source_file: str = 'gitreport.py'
    description: str = 'get_added_files_per_commit() + 1 more'
    functions: list[str] = ['get_added_files_per_commit', 'main']
    notes: str = ''
    source: str = _GITREPORT_SOURCE

class GitDiffReportUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'git_differ': GitDifferTool,
        'gitdif': GitdifTool,
        'gitreport': GitreportTool,
    }

    @classmethod
    def list_tools(cls: type[GitDiffReportUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[GitDiffReportUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[GitDiffReportUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for git_diff_report (3 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[GitDiffReportUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[GitDiffReportUnified], argv: Sequence[str] | None = None) -> int:
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
    return GitDiffReportUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

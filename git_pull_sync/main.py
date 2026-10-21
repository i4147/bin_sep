#!/usr/bin/env python3
"""GitPullSyncUnified for git_pull_sync.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (5):
  autopull <- autopull.py (36L): is_git_repo() + 3 more
  git_pull_newrepo <- git_pull_newrepo.py (159L): find_git_repos() + 5 more
  gitfix <- gitfix.py (97L): sync_branch_with_upstream() + 1 more
  gitpuller <- gitpuller.py (81L): find_git_repos() + 1 more
  gitrestorer <- gitrestorer.py (28L): is_git_repo() + 2 more

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

_AUTOPULL_SOURCE: str = (
    'import subprocess\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def is_git_repo(path):\n'
    '    return (path / ".git").is_dir()\n'
    '\n'
    '\n'
    'def git_pull(repo_path):\n'
    '    print(f"\\n==> Pulling in repo: {repo_path}")\n'
    '    try:\n'
    '        subprocess.run(["git", "-C", str(repo_path), "pull", "--ff-only"], check=True)\n'
    '    except subprocess.CalledProcessError:\n'
    '        print(f"⚠️  git pull failed in: {repo_path}")\n'
    '\n'
    '\n'
    'def walk_and_pull(path):\n'
    '    if is_git_repo(path):\n'
    '        git_pull(path)\n'
    '        return\n'
    '    try:\n'
    '        for item in path.iterdir():\n'
    '            if item.is_dir() and item.name != ".git":\n'
    '                walk_and_pull(item)\n'
    '    except PermissionError:\n'
    '        pass\n'
    '\n'
    '\n'
    'def main():\n'
    '    root = Path.cwd()\n'
    '    walk_and_pull(root)\n'
    '    print("\\nDone.")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_GIT_PULL_NEWREPO_SOURCE: str = (
    'import os\n'
    'from pathlib import Path\n'
    'import requests\n'
    'from dotenv import load_dotenv\n'
    'from git import GitCommandError, Repo\n'
    '\n'
    'load_dotenv()\n'
    '\n'
    '\n'
    'def find_git_repos(root_path):\n'
    '    repos = []\n'
    '    for item in root_path.iterdir():\n'
    '        if item.is_dir() and not item.name.startswith("."):\n'
    '            if (item / ".git").exists():\n'
    '                repos.append(item)\n'
    '            else:\n'
    '                repos.extend(find_git_repos(item))\n'
    '    return repos\n'
    '\n'
    '\n'
    'def create_github_repo(repo_name, github_token):\n'
    '    url = "https://api.github.com/user/repos"\n'
    '    headers = {\n'
    '        "Authorization": f"token {github_token}",\n'
    '        "Accept": "application/vnd.github.v3+json",\n'
    '    }\n'
    '    data = {\n'
    '        "name": repo_name,\n'
    '        "description": f"Repository for {repo_name}",\n'
    '        "private": False,\n'
    '        "auto_init": False,\n'
    '    }\n'
    '    try:\n'
    '        response = requests.post(url, headers=headers, json=data)\n'
    '        response.raise_for_status()\n'
    '        repo_info = response.json()\n'
    '        clone_url = repo_info["clone_url"]\n'
    '        print(f"   ✅ GitHub repo created: {clone_url}")\n'
    '        return clone_url\n'
    '    except requests.exceptions.RequestException as e:\n'
    '        if response.status_code == 422:\n'
    '            print(f"   ⚠️  Repository \'{repo_name}\' already exists on GitHub")\n'
    '            try:\n'
    '                f"https://api.github.com/repos/{response.json().get(\'errors\', [{}])[0].get(\'resource\', \'\')}"\n'
    '                username = get_github_username(github_token)\n'
    '                if username:\n'
    '                    existing_url = f"https://github.com/{username}/{repo_name}.git"\n'
    '                    print(f"   ℹ️  Using existing repo: {existing_url}")\n'
    '                    return existing_url\n'
    '            except:\n'
    '                pass\n'
    '        else:\n'
    '            print(f"   ❌ Failed to create repo: {e}")\n'
    '        return None\n'
    '\n'
    '\n'
    'def get_github_username(github_token):\n'
    '    url = "https://api.github.com/user"\n'
    '    headers = {"Authorization": f"token {github_token}"}\n'
    '    try:\n'
    '        response = requests.get(url, headers=headers)\n'
    '        response.raise_for_status()\n'
    '        return response.json()["login"]\n'
    '    except:\n'
    '        return None\n'
    '\n'
    '\n'
    'def setup_remote_and_push(repo, repo_path, remote_url):\n'
    '    try:\n'
    '        if "origin" in repo.remotes:\n'
    '            repo.remotes.origin.set_url(remote_url)\n'
    '            print(f"   🔄 Updated existing remote \'origin\' to {remote_url}")\n'
    '        else:\n'
    '            repo.create_remote("origin", remote_url)\n'
    '            print(f"   🔗 Added remote \'origin\': {remote_url}")\n'
    '        print("   📤 Pushing to GitHub...")\n'
    '        current_branch = repo.active_branch.name\n'
    '        repo.remotes.origin.push(refspec=f"{current_branch}:{current_branch}", set_upstream=True)\n'
    '        print(f"   ✅ Pushed branch \'{current_branch}\' to GitHub")\n'
    '        return True\n'
    '    except GitCommandError as e:\n'
    '        print(f"   ❌ Git error: {e.stderr.strip() if e.stderr else str(e)}")\n'
    '        return False\n'
    '    except Exception as e:\n'
    '        print(f"   ❌ Error: {e}")\n'
    '        return False\n'
    '\n'
    '\n'
    'def process_repository(repo_path, github_token):\n'
    '    try:\n'
    '        repo = Repo(repo_path)\n'
    '        rel_path = repo_path.relative_to(Path.cwd())\n'
    '        if repo.remotes:\n'
    '            print(f"\\n📁 {rel_path} (has remote)")\n'
    '            print(f"   Branch: {repo.active_branch.name}")\n'
    '            try:\n'
    '                repo.remotes.origin.pull()\n'
    '                print("   ✅ Pull successful")\n'
    '                return True, "Pulled successfully"\n'
    '            except GitCommandError as e:\n'
    '                if "merge conflict" in str(e).lower():\n'
    '                    return False, "Merge conflicts detected"\n'
    '                return (\n'
    '                    False,\n'
    '                    f"Pull failed: {e.stderr.strip() if e.stderr else str(e)}",\n'
    '                )\n'
    '        else:\n'
    '            print(f"\\n📁 {rel_path} (no remote configured)")\n'
    '            print(f"   Creating GitHub repository: {repo_path.name}")\n'
    '            remote_url = create_github_repo(repo_path.name, github_token)\n'
    '            if not remote_url:\n'
    '                return False, "Failed to create GitHub repository"\n'
    '            if setup_remote_and_push(repo, repo_path, remote_url):\n'
    '                return True, f"Created and pushed to {remote_url}"\n'
    '            else:\n'
    '                return False, "Failed to push to GitHub"\n'
    '    except Exception as e:\n'
    '        return False, f"Error: {e!s}"\n'
    '\n'
    '\n'
    'def main():\n'
    '    github_token = os.getenv("GITHUB_TOKEN")\n'
    '    if not github_token:\n'
    '        print("❌ Error: GITHUB_TOKEN not found in .env file")\n'
    '        print("Please create a .env file with: GITHUB_TOKEN=your_token_here")\n'
    '        return\n'
    '    cwd = Path.cwd()\n'
    '    print(f"🔍 Scanning for git repositories in: {cwd}")\n'
    '    repos = find_git_repos(cwd)\n'
    '    if not repos:\n'
    '        print("No git repositories found")\n'
    '        return\n'
    '    print(f"Found {len(repos)} repository(ies)\\n")\n'
    '    results = []\n'
    '    for repo_path in repos:\n'
    '        success, message = process_repository(repo_path, github_token)\n'
    '        results.append((repo_path, success, message))\n'
    '    print("\\n" + "=" * 40)\n'
    '    print("SUMMARY")\n'
    '    print("-" * 40)\n'
    '    successful = [r for r in results if r[1]]\n'
    '    failed = [r for r in results if not r[1]]\n'
    '    if successful:\n'
    '        print(f"\\n✅ Successful ({len(successful)} repos):")\n'
    '        for repo_path, _, msg in successful:\n'
    '            print(f"   - {repo_path.relative_to(cwd)}: {msg}")\n'
    '    if failed:\n'
    '        print(f"\\n❌ Failed ({len(failed)} repos):")\n'
    '        for repo_path, _, msg in failed:\n'
    '            print(f"   - {repo_path.relative_to(cwd)}: {msg}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    try:\n'
    '        raise SystemExit(main())\n'
    '    except KeyboardInterrupt:\n'
    '        print("\\n\\n⚠️  Operation cancelled by user")\n'
    '    except Exception as e:\n'
    '        print(f"\\n❌ Unexpected error: {e}")\n'
)

_GITFIX_SOURCE: str = (
    'import sys\n'
    'from git import Repo\n'
    '\n'
    '\n'
    'def sync_branch_with_upstream(repo_path="."):\n'
    '    try:\n'
    '        repo = Repo(repo_path)\n'
    '        if repo.active_branch.name != "master":\n'
    '            print(\n'
    '                "Warning: Not on master branch. Current branch:",\n'
    '                repo.active_branch.name,\n'
    '            )\n'
    '            response = input("Continue anyway? (y/n): ")\n'
    '            if response.lower() != "y":\n'
    '                return False\n'
    '        print("Fetching from origin...")\n'
    '        origin = repo.remotes.origin\n'
    '        origin.fetch()\n'
    '        upstream_branch = None\n'
    '        if "origin/master" in repo.refs:\n'
    '            upstream_branch = "origin/master"\n'
    '        elif "origin/main" in repo.refs:\n'
    '            upstream_branch = "origin/main"\n'
    '        else:\n'
    '            print("Error: Neither origin/master nor origin/main exists")\n'
    '            return False\n'
    '        print(f"Using upstream branch: {upstream_branch}")\n'
    '        upstream_commit = repo.refs[upstream_branch].commit\n'
    '        print("Rebasing with unrelated histories...")\n'
    '        current_branch = repo.active_branch\n'
    '        original_head = repo.head.commit\n'
    '        try:\n'
    '            repo.git.rebase(\n'
    '                "--onto",\n'
    '                upstream_commit,\n'
    '                original_head,\n'
    '                current_branch,\n'
    '                allow_unrelated_histories=True,\n'
    '            )\n'
    '            print("Rebase successful")\n'
    '        except Exception as e:\n'
    '            print(f"Rebase failed: {e}")\n'
    '            repo.git.rebase("--abort")\n'
    '            return False\n'
    '        print(f"Pushing to origin/{current_branch.name} with force-with-lease...")\n'
    '        origin.push(\n'
    '            refspec=f"{current_branch.name}:{current_branch.name}",\n'
    '            force_with_lease=True,\n'
    '        )\n'
    '        print("Successfully synced branch!")\n'
    '        return True\n'
    '    except Exception as e:\n'
    '        print(f"Error: {e}")\n'
    '        return False\n'
    '\n'
    '\n'
    'def sync_with_plumbing(repo_path="."):\n'
    '    try:\n'
    '        repo = Repo(repo_path)\n'
    '        origin = repo.remotes.origin\n'
    '        origin.fetch()\n'
    '        upstream_ref = None\n'
    '        for ref in repo.refs:\n'
    '            if ref.name in ["origin/master", "origin/main"]:\n'
    '                upstream_ref = ref\n'
    '                break\n'
    '        if not upstream_ref:\n'
    '            print("No origin/master or origin/main found")\n'
    '            return False\n'
    '        current_commit = repo.head.commit\n'
    '        upstream_commit = upstream_ref.commit\n'
    '        if current_commit != upstream_commit:\n'
    '            print(f"Rebasing {current_commit.hexsha[:8]} onto {upstream_commit.hexsha[:8]}")\n'
    '            temp_branch = repo.create_head("temp_rebase", current_commit)\n'
    '            temp_branch.checkout()\n'
    '            try:\n'
    '                repo.head.reset(upstream_commit, index=True, working_tree=True)\n'
    '                repo.git.cherry_pick(f"{current_commit.hexsha}..{upstream_commit.hexsha}")\n'
    '                repo.git.cherry_pick("--continue")\n'
    '                repo.head.reference = repo.head.commit\n'
    '            except Exception as e:\n'
    '                print(f"Rebase failed: {e}")\n'
    '                repo.git.rebase("--abort")\n'
    '                return False\n'
    '            finally:\n'
    '                if temp_branch in repo.branches:\n'
    '                    repo.delete_head(temp_branch)\n'
    '        origin.push(refspec="master:master", force_with_lease=True)\n'
    '        return True\n'
    '    except Exception as e:\n'
    '        print(f"Error: {e}")\n'
    '        return False\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    success = sync_branch_with_upstream(".")\n'
    '    sys.exit(0 if success else 1)\n'
)

_GITPULLER_SOURCE: str = (
    'from pathlib import Path\n'
    'from git import GitCommandError, Repo\n'
    '\n'
    '\n'
    'def find_git_repos(root_path):\n'
    '    git_repos = []\n'
    '    for item in root_path.iterdir():\n'
    '        if not item.is_dir():\n'
    '            continue\n'
    '        if (item / ".git").exists():\n'
    '            git_repos.append(item)\n'
    '        else:\n'
    '            git_repos.extend(find_git_repos(item))\n'
    '    return git_repos\n'
    '\n'
    '\n'
    'def git_pull_all():\n'
    '    cwd = Path.cwd()\n'
    '    print(f"🔍 Scanning for git repositories in: {cwd}")\n'
    '    repos = find_git_repos(cwd)\n'
    '    if not repos:\n'
    '        print("No git repositories found")\n'
    '        return\n'
    '    print(f"Found {len(repos)} git repository(ies)\\n")\n'
    '    pulled_repos = []\n'
    '    failed_repos = []\n'
    '    for repo_path in repos:\n'
    '        print(f"📁 Repository: {repo_path.relative_to(cwd)}")\n'
    '        try:\n'
    '            repo = Repo(repo_path)\n'
    '            current_branch = repo.active_branch.name\n'
    '            print(f"   Branch: {current_branch}")\n'
    '            if not repo.remotes:\n'
    '                failed_repos.append((repo_path, "No remote configured"))\n'
    '                print("   ❌ No remote configured")\n'
    '                continue\n'
    '            remote_name = repo.remotes[0].name\n'
    '            pull_result = repo.remotes[remote_name].pull()\n'
    '            success = False\n'
    '            for info in pull_result:\n'
    '                if hasattr(info, "flags"):\n'
    '                    if info.flags & info.ERROR:\n'
    '                        failed_repos.append((repo_path, str(info.note)))\n'
    '                        print(f"   ❌ Failed: {info.note}")\n'
    '                    else:\n'
    '                        success = True\n'
    '                        if hasattr(info, "commit") and info.commit:\n'
    '                            print(f"   ✅ Pulled successfully: {info.commit}")\n'
    '                        else:\n'
    '                            print("   ℹ️  Already up to date")\n'
    '                else:\n'
    '                    success = True\n'
    '                    print("   ✅ Pull completed")\n'
    '            if success:\n'
    '                pulled_repos.append(repo_path)\n'
    '        except GitCommandError as e:\n'
    '            failed_repos.append((repo_path, str(e)))\n'
    '            print(f"   ❌ Git error: {e}")\n'
    '        except Exception as e:\n'
    '            failed_repos.append((repo_path, f"Unexpected error: {e!s}"))\n'
    '            print(f"   ❌ Error: {e}")\n'
    '    print("\\n" + "=" * 40)\n'
    '    print("SUMMARY")\n'
    '    print("-" * 40)\n'
    '    if pulled_repos:\n'
    '        print(f"\\n✅ Successfully pulled ({len(pulled_repos)} repos):")\n'
    '        for repo_path in pulled_repos:\n'
    '            print(f"   - {repo_path.relative_to(cwd)}")\n'
    '    if failed_repos:\n'
    '        print(f"\\n❌ Failed ({len(failed_repos)} repos):")\n'
    '        for repo_path, error in failed_repos:\n'
    '            print(f"   - {repo_path.relative_to(cwd)}: {error}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    try:\n'
    '        git_pull_all()\n'
    '    except KeyboardInterrupt:\n'
    '        print("\\n\\n⚠️  Operation cancelled by user")\n'
    '    except Exception as e:\n'
    '        print(f"\\n❌ Unexpected error: {e}")\n'
)

_GITRESTORER_SOURCE: str = (
    'import os\n'
    'import subprocess\n'
    'from pathlib import Path\n'
    '\n'
    '\n'
    'def is_git_repo(path):\n'
    '    return (path / ".git").is_dir()\n'
    '\n'
    '\n'
    'def git_pull(repo_path):\n'
    '    print(f"\\n==> Pulling in repo: {repo_path}")\n'
    '    try:\n'
    '        subprocess.run(["git", "-C", str(repo_path), "restore", "."], check=True)\n'
    '    except subprocess.CalledProcessError:\n'
    '        print(f"⚠️  git pull failed in: {repo_path}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    root = Path.cwd()\n'
    '    for dirpath, _dirnames, _filenames in os.walk(root):\n'
    '        current = Path(dirpath)\n'
    '        if is_git_repo(current):\n'
    '            git_pull(current)\n'
    '    print("\\nDone.")\n'
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


class AutopullTool(BaseTool):
    """Wrapper for original autopull.py: is_git_repo() + 3 more."""
    name: str = 'autopull'
    source_file: str = 'autopull.py'
    description: str = 'is_git_repo() + 3 more'
    functions: list[str] = ['is_git_repo', 'git_pull', 'walk_and_pull', 'main']
    notes: str = ''
    source: str = _AUTOPULL_SOURCE

class GitPullNewrepoTool(BaseTool):
    """Wrapper for original git_pull_newrepo.py: find_git_repos() + 5 more."""
    name: str = 'git_pull_newrepo'
    source_file: str = 'git_pull_newrepo.py'
    description: str = 'find_git_repos() + 5 more'
    functions: list[str] = ['find_git_repos', 'create_github_repo', 'get_github_username', 'setup_remote_and_push', 'process_repository', 'main']
    notes: str = ''
    source: str = _GIT_PULL_NEWREPO_SOURCE

class GitfixTool(BaseTool):
    """Wrapper for original gitfix.py: sync_branch_with_upstream() + 1 more."""
    name: str = 'gitfix'
    source_file: str = 'gitfix.py'
    description: str = 'sync_branch_with_upstream() + 1 more'
    functions: list[str] = ['sync_branch_with_upstream', 'sync_with_plumbing']
    notes: str = ''
    source: str = _GITFIX_SOURCE

class GitpullerTool(BaseTool):
    """Wrapper for original gitpuller.py: find_git_repos() + 1 more."""
    name: str = 'gitpuller'
    source_file: str = 'gitpuller.py'
    description: str = 'find_git_repos() + 1 more'
    functions: list[str] = ['find_git_repos', 'git_pull_all']
    notes: str = ''
    source: str = _GITPULLER_SOURCE

class GitrestorerTool(BaseTool):
    """Wrapper for original gitrestorer.py: is_git_repo() + 2 more."""
    name: str = 'gitrestorer'
    source_file: str = 'gitrestorer.py'
    description: str = 'is_git_repo() + 2 more'
    functions: list[str] = ['is_git_repo', 'git_pull', 'main']
    notes: str = ''
    source: str = _GITRESTORER_SOURCE

class GitPullSyncUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'autopull': AutopullTool,
        'git_pull_newrepo': GitPullNewrepoTool,
        'gitfix': GitfixTool,
        'gitpuller': GitpullerTool,
        'gitrestorer': GitrestorerTool,
    }

    @classmethod
    def list_tools(cls: type[GitPullSyncUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[GitPullSyncUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[GitPullSyncUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for git_pull_sync (5 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[GitPullSyncUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[GitPullSyncUnified], argv: Sequence[str] | None = None) -> int:
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
    return GitPullSyncUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

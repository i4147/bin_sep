#!/usr/bin/env python3
"""GithubApiQueryUnified for github_api_query.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (7):
  get_trending_py_repos <- get_trending_py_repos.py (70L): fetch_trending() + 3 more
  getpyrepos <- getpyrepos.py (116L): get_user_repos() + 3 more
  getrepos <- getrepos.py (91L): countdown() + 2 more
  ghpy <- ghpy.py (33L): search_python_repos() + 0 more
  ghpy10 <- ghpy10.py (32L): search_github_repos() + 0 more
  gitrepos <- gitrepos.py (42L): get_github_repos() + 0 more
  gsz <- gsz.py (39L): get_repo_size() + 0 more

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

_GET_TRENDING_PY_REPOS_SOURCE: str = (
    'import csv\n'
    'import json\n'
    'from dataclasses import asdict, dataclass\n'
    'from pathlib import Path\n'
    'import requests\n'
    'from bs4 import BeautifulSoup\n'
    '\n'
    'BASE_URL = "https://github.com/trending/python"\n'
    'TIMEFRAMES = ["daily", "weekly", "monthly"]\n'
    'OUTPUT_DIR = Path("trending_repos")\n'
    '\n'
    '\n'
    '@dataclass\n'
    'class Repo:\n'
    '    pass\n'
    '\n'
    '\n'
    'def fetch_trending(timeframe):\n'
    '    url = f"{BASE_URL}?since={timeframe}"\n'
    '    response = requests.get(url, timeout=10)\n'
    '    response.raise_for_status()\n'
    '    soup = BeautifulSoup(response.text, "html.parser")\n'
    '    repos = []\n'
    '    for article in soup.select("article.Box-row"):\n'
    '        name = article.h2.text.strip().replace("\\n", "").replace(" ", "")\n'
    '        repo_url = "https://github.com" + article.h2.a["href"]\n'
    '        description_tag = article.find("p")\n'
    '        description = description_tag.text.strip() if description_tag else ""\n'
    '        language_tag = article.find("span", itemprop="programmingLanguage")\n'
    '        language = language_tag.text.strip() if language_tag else ""\n'
    '        stars_tag = article.select_one("a[href$=\'stargazers\']")\n'
    '        stars = stars_tag.text.strip() if stars_tag else "0"\n'
    '        repos.append(\n'
    '            Repo(\n'
    '                name=name,\n'
    '                url=repo_url,\n'
    '                description=description,\n'
    '                stars=stars,\n'
    '                language=language,\n'
    '                timeframe=timeframe,\n'
    '            )\n'
    '        )\n'
    '    return repos\n'
    '\n'
    '\n'
    'def save_csv(repos, path):\n'
    '    with path.open("w", newline="", encoding="utf-8") as f:\n'
    '        writer = csv.DictWriter(f, fieldnames=Repo.__annotations__.keys())\n'
    '        writer.writeheader()\n'
    '        for repo in repos:\n'
    '            writer.writerow(asdict(repo))\n'
    '\n'
    '\n'
    'def save_json(repos, path):\n'
    '    path.write_text(json.dumps([asdict(r) for r in repos], indent=2), encoding="utf-8")\n'
    '\n'
    '\n'
    'def main():\n'
    '    OUTPUT_DIR.mkdir(exist_ok=True)\n'
    '    all_repos = []\n'
    '    for timeframe in TIMEFRAMES:\n'
    '        repos = fetch_trending(timeframe)\n'
    '        all_repos.extend(repos)\n'
    '        save_csv(repos, OUTPUT_DIR / f"python_trending_{timeframe}.csv")\n'
    '        save_json(repos, OUTPUT_DIR / f"python_trending_{timeframe}.json")\n'
    '    print(f"Saved {len(all_repos)} repos to {OUTPUT_DIR.resolve()}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_GETPYREPOS_SOURCE: str = (
    'import json\n'
    'import sys\n'
    'from datetime import datetime, timedelta\n'
    'import requests\n'
    '\n'
    '\n'
    'def get_user_repos(username):\n'
    '    repos = []\n'
    '    page = 1\n'
    '    while True:\n'
    '        url = f"https://api.github.com/users/{username}/repos"\n'
    '        params = {"page": page, "per_page": 100, "sort": "updated"}\n'
    '        try:\n'
    '            response = requests.get(url, params=params)\n'
    '            response.raise_for_status()\n'
    '            page_repos = response.json()\n'
    '            if not page_repos:\n'
    '                break\n'
    '            for repo in page_repos:\n'
    '                if repo.get("language") == "Python":\n'
    '                    repos.append({\n'
    '                        "name": repo["name"],\n'
    '                        "full_name": repo["full_name"],\n'
    '                        "description": repo.get("description", ""),\n'
    '                        "url": repo["html_url"],\n'
    '                        "stars": repo["stargazers_count"],\n'
    '                        "forks": repo["forks_count"],\n'
    '                        "language": repo["language"],\n'
    '                        "created_at": repo["created_at"],\n'
    '                        "updated_at": repo["updated_at"],\n'
    '                        "private": repo["private"],\n'
    '                    })\n'
    '            if len(page_repos) < 100:\n'
    '                break\n'
    '            page += 1\n'
    '        except requests.exceptions.RequestException as e:\n'
    '            print(f"Error fetching repos for {username}: {e}", file=sys.stderr)\n'
    '            break\n'
    '    return repos\n'
    '\n'
    '\n'
    'def get_top_trending_users():\n'
    '    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")\n'
    '    url = "https://api.github.com/search/users"\n'
    '    params = {\n'
    '        "q": f"language:python created:>{week_ago}",\n'
    '        "sort": "followers",\n'
    '        "order": "desc",\n'
    '        "per_page": 10,\n'
    '    }\n'
    '    try:\n'
    '        response = requests.get(url, params=params)\n'
    '        response.raise_for_status()\n'
    '        data = response.json()\n'
    '        trending_users = []\n'
    '        for user in data.get("items", []):\n'
    '            user_url = user["url"]\n'
    '            user_response = requests.get(user_url)\n'
    '            user_response.raise_for_status()\n'
    '            user_data = user_response.json()\n'
    '            trending_users.append({\n'
    '                "username": user_data["login"],\n'
    '                "name": user_data.get("name", ""),\n'
    '                "followers": user_data["followers"],\n'
    '                "repos_url": user_data["repos_url"],\n'
    '                "html_url": user_data["html_url"],\n'
    '                "repositories": get_user_repos(user_data["login"]),\n'
    '            })\n'
    '        return trending_users\n'
    '    except requests.exceptions.RequestException as e:\n'
    '        print(f"Error fetching trending users: {e}", file=sys.stderr)\n'
    '        return []\n'
    '\n'
    '\n'
    'def save_to_json(data, filename="github_repos.json"):\n'
    '    with open(filename, "w", encoding="utf-8") as f:\n'
    '        json.dump(data, f, indent=2, ensure_ascii=False)\n'
    '    print(f"Data saved to {filename}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) > 1:\n'
    '        username = sys.argv[1]\n'
    '        print(f"Fetching Python repositories for user: {username}")\n'
    '        repos = get_user_repos(username)\n'
    '        if repos:\n'
    '            output = {\n'
    '                "username": username,\n'
    '                "total_python_repos": len(repos),\n'
    '                "repositories": repos,\n'
    '            }\n'
    '            filename = f"{username}_python_repos.json"\n'
    '            save_to_json(output, filename)\n'
    '            print(f"Found {len(repos)} Python repositories")\n'
    '        else:\n'
    '            print(f"No Python repositories found for user {username}")\n'
    '    else:\n'
    '        print("No username provided. Fetching top trending GitHub users with Python repos...")\n'
    '        trending_data = get_top_trending_users()\n'
    '        if trending_data:\n'
    '            output = {\n'
    '                "timestamp": datetime.now().isoformat(),\n'
    '                "trending_users": trending_data,\n'
    '            }\n'
    '            save_to_json(output, "trending_github_python_users.json")\n'
    '            print(f"Found {len(trending_data)} trending users")\n'
    '            for user in trending_data:\n'
    '                print(f"\\n👤 {user[\'username\']} ({user[\'name\']})")\n'
    '                print(f"   Followers: {user[\'followers\']}")\n'
    '                print(f"   Python repos: {len(user[\'repositories\'])}")\n'
    '        else:\n'
    '            print("No trending users found")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_GETREPOS_SOURCE: str = (
    'import json\n'
    'import sys\n'
    'import threading\n'
    'import time\n'
    'from os import getenv\n'
    'from pathlib import Path\n'
    'from dotenv import load_dotenv\n'
    'from github import Auth, Github, GithubException\n'
    '\n'
    '\n'
    'def countdown(timeout):\n'
    '    for remaining in range(timeout, 0, -1):\n'
    '        sys.stdout.write(f"\\rTimeout in {remaining:2d} seconds... ")\n'
    '        sys.stdout.flush()\n'
    '        time.sleep(1)\n'
    '    sys.stdout.write("\\r" + " " * 30 + "\\r")\n'
    '    sys.stdout.flush()\n'
    '\n'
    '\n'
    'def get_repos(username, token=None, timeout=60):\n'
    '    countdown_thread = threading.Thread(target=countdown, args=(timeout,), daemon=True)\n'
    '    countdown_thread.start()\n'
    '    try:\n'
    '        if token:\n'
    '            auth = Auth.Token(token)\n'
    '            g = Github(auth=auth, timeout=timeout)\n'
    '        else:\n'
    '            g = Github(timeout=timeout)\n'
    '        user = g.get_user(username)\n'
    '        repos = list(user.get_repos())\n'
    '        if not repos:\n'
    '            print(f"\\nNo public repositories found for user \'{username}\'.")\n'
    '            return []\n'
    '        return repos\n'
    '    except GithubException as e:\n'
    '        if e.status == 404:\n'
    '            print(f"\\nError: User \'{username}\' not found.")\n'
    '        elif e.status == 401:\n'
    '            print("\\nError: Invalid or expired token. Check your .env file.")\n'
    '        elif e.status == 403:\n'
    '            if "rate limit" in str(e).lower():\n'
    '                print("\\nError: API rate limit exceeded. Use a token for higher limits.")\n'
    '            else:\n'
    '                print(f"\\nError: Access forbidden. {e.data.get(\'message\', \'\')}")\n'
    '        else:\n'
    '            print(f"\\nGitHub API Error: {e.status} - {e.data.get(\'message\', \'Unknown error\')}")\n'
    '        sys.exit(1)\n'
    '    except Exception as e:\n'
    '        print(f"\\nError: {e}")\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'def main():\n'
    '    if len(sys.argv) < 2:\n'
    '        print("Usage: script.py <username>")\n'
    '        sys.exit(1)\n'
    '    env_path = Path("~/.env").expanduser()\n'
    '    load_dotenv(env_path)\n'
    '    token = getenv("GITHUB_TOKEN")\n'
    '    username = sys.argv[1]\n'
    '    if token:\n'
    '        print("Using authenticated access (rate limit: 5000 requests/hour)")\n'
    '    else:\n'
    '        print("No token found in .env, using unauthenticated access (rate limit: 60 requests/hour)")\n'
    '    repos = get_repos(username, token=token, timeout=60)\n'
    '    repos.sort(key=lambda r: r.stargazers_count, reverse=True)\n'
    '    print(f"\\nRepositories of \'{username}\' (sorted by stars):")\n'
    '    for repo in repos:\n'
    '        stars = repo.stargazers_count\n'
    '        language = repo.language or "N/A"\n'
    '        description = repo.description or "No description"\n'
    '        print(f"- {repo.name}")\n'
    '        print(f"  ⭐ {stars} | 🔤 {language} | {description[:80]}")\n'
    '    json_data = [\n'
    '        {\n'
    '            "name": repo.name,\n'
    '            "stars": repo.stargazers_count,\n'
    '            "language": repo.language or "N/A",\n'
    '            "description": repo.description or "No description",\n'
    '            "url": repo.html_url,\n'
    '        }\n'
    '        for repo in repos\n'
    '    ]\n'
    '    json_filename = f"{username}.json"\n'
    '    with Path(json_filename).open("w", encoding="utf-8") as f:\n'
    '        json.dump(json_data, f, indent=4, ensure_ascii=False)\n'
    '    print(f"\\nData successfully saved to {json_filename}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_GHPY_SOURCE: str = (
    'import os\n'
    'from pathlib import Path\n'
    'import requests\n'
    'from dotenv import load_dotenv\n'
    '\n'
    '\n'
    'def search_python_repos():\n'
    '    load_dotenv(Path.home() / ".env")\n'
    '    token = os.getenv("GITHUB_TOKEN")\n'
    '    headers = {"Authorization": f"Bearer {token}"}\n'
    '    params = {\n'
    '        "q": "language:Python",\n'
    '        "sort": "updated",\n'
    '        "order": "desc",\n'
    '        "per_page": 50,\n'
    '    }\n'
    '    response = requests.get("https://api.github.com/search/repositories", headers=headers, params=params)\n'
    '    response.raise_for_status()\n'
    '    data = response.json()\n'
    '    output = Path("ghpy.txt")\n'
    '    with output.open("w") as f:\n'
    '        f.write("50 most active py repos\\n")\n'
    '        f.write("=" * 40 + "\\n\\n")\n'
    '        for repo in data["items"]:\n'
    '            f.write(f"{repo[\'full_name\']}\\n")\n'
    '            f.write(f"  URL: {repo[\'html_url\']}\\n")\n'
    '            f.write(f"  Updated: {repo[\'updated_at\']}\\n")\n'
    '            f.write(f"  Stars: {repo[\'stargazers_count\']}\\n\\n")\n'
    '    print(f"Results saved to {output}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    search_python_repos()\n'
)

_GHPY10_SOURCE: str = (
    'import os\n'
    'from datetime import datetime, timedelta\n'
    'from pathlib import Path\n'
    'import requests\n'
    'from dotenv import load_dotenv\n'
    '\n'
    '\n'
    'def search_github_repos():\n'
    '    env_path = Path.home() / ".env"\n'
    '    load_dotenv(env_path)\n'
    '    token = os.getenv("GITHUB_TOKEN")\n'
    '    if not token:\n'
    '        raise ValueError(f"GITHUB_TOKEN not found in {env_path}")\n'
    '    date_10_days_ago = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")\n'
    '    query = f"language:Python created:>{date_10_days_ago}"\n'
    '    headers = {\n'
    '        "Accept": "application/vnd.github.v3+json",\n'
    '        "Authorization": f"token {token}",\n'
    '    }\n'
    '    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 50}\n'
    '    response = requests.get("https://api.github.com/search/repositories", headers=headers, params=params)\n'
    '    response.raise_for_status()\n'
    '    data = response.json()\n'
    '    output_file = Path("ghpy10.txt")\n'
    '    with output_file.open("w") as f:\n'
    '        for repo in data["items"]:\n'
    '            f.write(f"{repo[\'full_name\']} - {repo[\'stargazers_count\']} stars\\n")\n'
    '    print(f"✓ Saved {len(data[\'items\'])} repos to ghpy10.txt")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    search_github_repos()\n'
)

_GITREPOS_SOURCE: str = (
    'import json\n'
    'from pathlib import Path\n'
    'import requests\n'
    '\n'
    '\n'
    'def get_github_repos(username, output_file=None):\n'
    '    if output_file is None:\n'
    '        url = f"https://api.github.com/users/{username}/repos"\n'
    '    try:\n'
    '        response = requests.get(url)\n'
    '        response.raise_for_status()\n'
    '        repos = response.json()\n'
    '        if not repos:\n'
    '            print(f"No repositories found for user: {username}")\n'
    '            return\n'
    '        with Path(output_file).open("w", encoding="utf-8") as f:\n'
    '            f.write(f"GitHub repositories for user: {username}\\n")\n'
    '            f.write("=" * 40 + "\\n\\n")\n'
    '            for repo in repos:\n'
    '                name = repo["name"]\n'
    '                description = repo["description"] or "No description"\n'
    '                url = repo["html_url"]\n'
    '                stars = repo["stargazers_count"]\n'
    '                forks = repo["forks_count"]\n'
    '                language = repo["language"] or "Not specified"\n'
    '                f.write(f"Repository: {name}\\n")\n'
    '                f.write(f"Description: {description}\\n")\n'
    '                f.write(f"URL: {url}\\n")\n'
    '                f.write(f"Stars: {stars} | Forks: {forks} | Language: {language}\\n")\n'
    '                f.write("-" * 40 + "\\n")\n'
    '        print(f"Successfully saved {len(repos)} repositories to {output_file}")\n'
    '    except requests.exceptions.RequestException as e:\n'
    '        print(f"Error fetching data: {e}")\n'
    '    except json.JSONDecodeError as e:\n'
    '        print(f"Error parsing JSON response: {e}")\n'
    '    except Exception as e:\n'
    '        print(f"An unexpected error occurred: {e}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    username = input("Enter GitHub username: ").strip()\n'
    '    get_github_repos(username)\n'
)

_GSZ_SOURCE: str = (
    'import re\n'
    'import sys\n'
    'import requests\n'
    '\n'
    '\n'
    'def get_repo_size(input_str):\n'
    '    if input_str.startswith("https://github.com/"):\n'
    '        match = re.search(r"github\\.com/([^/]+)/([^/]+)", input_str)\n'
    '        if not match:\n'
    '            print("Invalid GitHub URL format.")\n'
    '            return\n'
    '        user, repo = match.groups()\n'
    '    else:\n'
    '        parts = input_str.split("/")\n'
    '        if len(parts) != 2:\n'
    '            print("Invalid format. Use \'user/repo\' or full URL.")\n'
    '            return\n'
    '        user, repo = parts\n'
    '    url = f"https://api.github.com/repos/{user}/{repo}"\n'
    '    try:\n'
    '        response = requests.get(url)\n'
    '        if response.status_code == 404:\n'
    '            print(f"Repository \'{user}/{repo}\' not found.")\n'
    '            return\n'
    '        response.raise_for_status()\n'
    '        data = response.json()\n'
    '        size_kb = data.get("size", 0)\n'
    '        size_mb = size_kb / 1024\n'
    '        print(f"Repository: {user}/{repo}")\n'
    '        print(f"Size: {size_mb:.2f} MB")\n'
    '    except requests.exceptions.RequestException as e:\n'
    '        print(f"Error fetching data: {e}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    if len(sys.argv) != 2:\n'
    '        print("Usage: python get-repo-size <user/repo> or <https://github.com/user/repo>")\n'
    '        sys.exit(1)\n'
    '    get_repo_size(sys.argv[1])\n'
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


class GetTrendingPyReposTool(BaseTool):
    """Wrapper for original get_trending_py_repos.py: fetch_trending() + 3 more."""
    name: str = 'get_trending_py_repos'
    source_file: str = 'get_trending_py_repos.py'
    description: str = 'fetch_trending() + 3 more'
    functions: list[str] = ['fetch_trending', 'save_csv', 'save_json', 'main']
    notes: str = ''
    source: str = _GET_TRENDING_PY_REPOS_SOURCE

class GetpyreposTool(BaseTool):
    """Wrapper for original getpyrepos.py: get_user_repos() + 3 more."""
    name: str = 'getpyrepos'
    source_file: str = 'getpyrepos.py'
    description: str = 'get_user_repos() + 3 more'
    functions: list[str] = ['get_user_repos', 'get_top_trending_users', 'save_to_json', 'main']
    notes: str = ''
    source: str = _GETPYREPOS_SOURCE

class GetreposTool(BaseTool):
    """Wrapper for original getrepos.py: countdown() + 2 more."""
    name: str = 'getrepos'
    source_file: str = 'getrepos.py'
    description: str = 'countdown() + 2 more'
    functions: list[str] = ['countdown', 'get_repos', 'main']
    notes: str = ''
    source: str = _GETREPOS_SOURCE

class GhpyTool(BaseTool):
    """Wrapper for original ghpy.py: search_python_repos() + 0 more."""
    name: str = 'ghpy'
    source_file: str = 'ghpy.py'
    description: str = 'search_python_repos() + 0 more'
    functions: list[str] = ['search_python_repos']
    notes: str = ''
    source: str = _GHPY_SOURCE

class Ghpy10Tool(BaseTool):
    """Wrapper for original ghpy10.py: search_github_repos() + 0 more."""
    name: str = 'ghpy10'
    source_file: str = 'ghpy10.py'
    description: str = 'search_github_repos() + 0 more'
    functions: list[str] = ['search_github_repos']
    notes: str = ''
    source: str = _GHPY10_SOURCE

class GitreposTool(BaseTool):
    """Wrapper for original gitrepos.py: get_github_repos() + 0 more."""
    name: str = 'gitrepos'
    source_file: str = 'gitrepos.py'
    description: str = 'get_github_repos() + 0 more'
    functions: list[str] = ['get_github_repos']
    notes: str = ''
    source: str = _GITREPOS_SOURCE

class GszTool(BaseTool):
    """Wrapper for original gsz.py: get_repo_size() + 0 more."""
    name: str = 'gsz'
    source_file: str = 'gsz.py'
    description: str = 'get_repo_size() + 0 more'
    functions: list[str] = ['get_repo_size']
    notes: str = ''
    source: str = _GSZ_SOURCE

class GithubApiQueryUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'get_trending_py_repos': GetTrendingPyReposTool,
        'getpyrepos': GetpyreposTool,
        'getrepos': GetreposTool,
        'ghpy': GhpyTool,
        'ghpy10': Ghpy10Tool,
        'gitrepos': GitreposTool,
        'gsz': GszTool,
    }

    @classmethod
    def list_tools(cls: type[GithubApiQueryUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[GithubApiQueryUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[GithubApiQueryUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for github_api_query (7 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[GithubApiQueryUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[GithubApiQueryUnified], argv: Sequence[str] | None = None) -> int:
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
    return GithubApiQueryUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

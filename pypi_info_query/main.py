#!/usr/bin/env python3
"""PypiInfoQueryUnified for pypi_info_query.

Assumption: each original CLI preserved as `main.py <tool> [args...]` with passthrough args.

Original scripts (4):
  get_latest_pkgs_added_to_pypi <- get_latest_pkgs_added_to_pypi.py (117L): fetch_pypi_updates() + 4 more
  get_pypi_rssfeed <- get_pypi_rssfeed.py (121L): fetch_rss_feed() + 4 more
  psearch <- psearch.py (107L): main() + 0 more
  pypistats <- pypistats.py (72L): get_stats() + 5 more

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

_GET_LATEST_PKGS_ADDED_TO_PYPI_SOURCE: str = (
    'import csv\n'
    'import json\n'
    'import sys\n'
    'import xml.etree.ElementTree as ET\n'
    'from datetime import datetime\n'
    'import requests\n'
    '\n'
    '\n'
    'def fetch_pypi_updates():\n'
    '    url = "https://pypi.org/rss/updates.xml"\n'
    '    try:\n'
    '        response = requests.get(url, timeout=30)\n'
    '        response.raise_for_status()\n'
    '        root = ET.fromstring(response.content)\n'
    '        namespaces = {\n'
    '            "atom": "http://www.w3.org/2005/Atom",\n'
    '            "dc": "http://purl.org/dc/elements/1.1/",\n'
    '        }\n'
    '        packages = []\n'
    '        for item in root.findall(".//item"):\n'
    '            package_info = {\n'
    '                "title": item.find("title").text if item.find("title") is not None else "",\n'
    '                "link": item.find("link").text if item.find("link") is not None else "",\n'
    '                "description": item.find("description").text if item.find("description") is not None else "",\n'
    '                "pub_date": item.find("pubDate").text if item.find("pubDate") is not None else "",\n'
    '                "guid": item.find("guid").text if item.find("guid") is not None else "",\n'
    '            }\n'
    '            if package_info["title"]:\n'
    '                parts = package_info["title"].split()\n'
    '                if parts:\n'
    '                    package_info["package_name"] = parts[0]\n'
    '                    package_info["version"] = parts[1] if len(parts) > 1 else ""\n'
    '            packages.append(package_info)\n'
    '        return packages\n'
    '    except requests.RequestException as e:\n'
    '        print(f"Error fetching RSS feed: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '    except ET.ParseError as e:\n'
    '        print(f"Error parsing XML: {e}", file=sys.stderr)\n'
    '        sys.exit(1)\n'
    '\n'
    '\n'
    'def save_to_json(packages, filename):\n'
    '    with open(filename, "w", encoding="utf-8") as f:\n'
    '        json.dump(packages, f, indent=2, ensure_ascii=False)\n'
    '    print(f"Saved {len(packages)} packages to {filename}")\n'
    '\n'
    '\n'
    'def save_to_csv(packages, filename):\n'
    '    if not packages:\n'
    '        print("No packages to save", file=sys.stderr)\n'
    '        return\n'
    '    with open(filename, "w", newline="", encoding="utf-8") as f:\n'
    '        writer = csv.DictWriter(f, fieldnames=packages[0].keys())\n'
    '        writer.writeheader()\n'
    '        writer.writerows(packages)\n'
    '    print(f"Saved {len(packages)} packages to {filename}")\n'
    '\n'
    '\n'
    'def save_to_text(packages, filename):\n'
    '    with open(filename, "w", encoding="utf-8") as f:\n'
    '        f.write("PyPI Latest Package Updates\\n")\n'
    '        f.write(f"Fetched at: {datetime.now().isoformat()}\\n")\n'
    '        f.write("=" * 40 + "\\n\\n")\n'
    '        for i, pkg in enumerate(packages, 1):\n'
    '            f.write(f"{i}. {pkg.get(\'package_name\', \'Unknown\')}\\n")\n'
    '            f.write(f"   Version: {pkg.get(\'version\', \'N/A\')}\\n")\n'
    '            f.write(f"   Published: {pkg.get(\'pub_date\', \'N/A\')}\\n")\n'
    '            f.write(f"   Link: {pkg.get(\'link\', \'N/A\')}\\n")\n'
    '            f.write(f"   Description: {pkg.get(\'description\', \'N/A\')}\\n")\n'
    '            f.write("\\n")\n'
    '    print(f"Saved {len(packages)} packages to {filename}")\n'
    '\n'
    '\n'
    'def main():\n'
    '    import argparse\n'
    '\n'
    '    parser = argparse.ArgumentParser(description="Fetch latest package updates from PyPI RSS feed")\n'
    '    parser.add_argument(\n'
    '        "-o",\n'
    '        "--output",\n'
    '        default="pypi_updates.json",\n'
    '        help="Output filename (default: pypi_updates.json)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-f",\n'
    '        "--format",\n'
    '        choices=["json", "csv", "txt"],\n'
    '        default="json",\n'
    '        help="Output format (default: json)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-n",\n'
    '        "--num-packages",\n'
    '        type=int,\n'
    '        default=None,\n'
    '        help="Number of latest packages to save (default: all)",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    print("Fetching latest packages from PyPI...")\n'
    '    packages = fetch_pypi_updates()\n'
    '    if args.num_packages:\n'
    '        packages = packages[: args.num_packages]\n'
    '    base_name = args.output.rsplit(".", 1)[0]\n'
    '    extension_map = {"json": ".json", "csv": ".csv", "txt": ".txt"}\n'
    '    filename = base_name + extension_map.get(args.format, ".json")\n'
    '    save_functions = {"json": save_to_json, "csv": save_to_csv, "txt": save_to_text}\n'
    '    save_functions[args.format](packages, filename)\n'
    '    print("\\nSummary:")\n'
    '    print(f"  Total packages fetched: {len(packages)}")\n'
    '    if packages:\n'
    '        print(f"  Latest package: {packages[0].get(\'package_name\', \'Unknown\')} v{packages[0].get(\'version\', \'?\')}")\n'
    '        print(f"  Latest update time: {packages[0].get(\'pub_date\', \'Unknown\')}")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_GET_PYPI_RSSFEED_SOURCE: str = (
    'import sys\n'
    'import xml.etree.ElementTree as ET\n'
    'from datetime import datetime\n'
    'import requests\n'
    '\n'
    'PYPI_RSS_URL = "https://pypi.org/rss/packages.xml"\n'
    '\n'
    '\n'
    'def fetch_rss_feed(url):\n'
    '    try:\n'
    '        response = requests.get(url, timeout=55)\n'
    '        response.raise_for_status()\n'
    '        return response.text\n'
    '    except requests.exceptions.RequestException as e:\n'
    '        print(f"Error fetching RSS feed: {e}", file=sys.stderr)\n'
    '        return None\n'
    '\n'
    '\n'
    'def parse_rss_feed(xml_content):\n'
    '    packages = []\n'
    '    try:\n'
    '        root = ET.fromstring(xml_content)\n'
    '        channel = root.find("channel")\n'
    '        if channel is None:\n'
    '            print("Error: Invalid RSS format - no channel found", file=sys.stderr)\n'
    '            return packages\n'
    '        items = channel.findall("item")\n'
    '        for item in items:\n'
    '            package_info = {\n'
    '                "title": item.findtext("title", "Unknown"),\n'
    '                "link": item.findtext("link", "Unknown"),\n'
    '                "description": item.findtext("description", "No description"),\n'
    '                "pub_date": item.findtext("pubDate", "Unknown"),\n'
    '                "guid": item.findtext("guid", "Unknown"),\n'
    '            }\n'
    '            title = package_info["title"]\n'
    '            package_name = title.split()[0] if title else "Unknown"\n'
    '            package_info["package_name"] = package_name\n'
    '            packages.append(package_info)\n'
    '    except ET.ParseError as e:\n'
    '        print(f"Error parsing XML: {e}", file=sys.stderr)\n'
    '    except Exception as e:\n'
    '        print(f"Unexpected error during parsing: {e}", file=sys.stderr)\n'
    '    return packages\n'
    '\n'
    '\n'
    'def display_packages(packages, limit=None):\n'
    '    if not packages:\n'
    '        print("No packages found in the RSS feed.")\n'
    '        return\n'
    '    display_packages = packages[:limit] if limit else packages\n'
    '    print(f"\\n{\'=\' * 40}")\n'
    '    print(f"PyPI Latest Packages (Total: {len(packages)}, Showing: {len(display_packages)})")\n'
    '    print(f"Fetched at: {datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')}")\n'
    '    print(f"{\'=\' * 40}\\n")\n'
    '    for i, pkg in enumerate(display_packages, 1):\n'
    '        print(f"Package #{i}:")\n'
    '        print(f"  Name:        {pkg[\'package_name\']}")\n'
    '        print(f"  Full Title:  {pkg[\'title\']}")\n'
    '        print(f"  Link:        {pkg[\'link\']}")\n'
    '        print(f"  Published:   {pkg[\'pub_date\']}")\n'
    '        print(\n'
    '            f"  Description: {pkg[\'description\'][:100]}..."\n'
    '            if len(pkg["description"]) > 100\n'
    '            else f"  Description: {pkg[\'description\']}"\n'
    '        )\n'
    '        print(f"  GUID:        {pkg[\'guid\']}")\n'
    '        print("-" * 40)\n'
    '\n'
    '\n'
    'def save_to_file(packages, filename="pypi_packages.txt"):\n'
    '    try:\n'
    '        with open(filename, "w", encoding="utf-8") as f:\n'
    '            f.write(f"PyPI Latest Packages - {datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\')}\\n")\n'
    '            f.write("=" * 40 + "\\n\\n")\n'
    '            for i, pkg in enumerate(packages, 1):\n'
    '                f.write(f"Package #{i}:\\n")\n'
    '                f.write(f"  Name:        {pkg[\'package_name\']}\\n")\n'
    '                f.write(f"  Full Title:  {pkg[\'title\']}\\n")\n'
    '                f.write(f"  Link:        {pkg[\'link\']}\\n")\n'
    '                f.write(f"  Published:   {pkg[\'pub_date\']}\\n")\n'
    '                f.write(f"  Description: {pkg[\'description\']}\\n")\n'
    '                f.write(f"  GUID:        {pkg[\'guid\']}\\n")\n'
    '                f.write("-" * 40 + "\\n")\n'
    '        print(f"\\nPackages saved to \'{filename}\'")\n'
    '    except OSError as e:\n'
    '        print(f"Error saving to file: {e}", file=sys.stderr)\n'
    '\n'
    '\n'
    'def main():\n'
    '    limit = None\n'
    '    save_output = False\n'
    '    if len(sys.argv) > 1:\n'
    '        try:\n'
    '            limit = int(sys.argv[1])\n'
    '            if limit < 1:\n'
    '                print("Error: Limit must be a positive number", file=sys.stderr)\n'
    '                sys.exit(1)\n'
    '        except ValueError:\n'
    '            if sys.argv[1] in ["--save", "-s"]:\n'
    '                save_output = True\n'
    '            else:\n'
    '                print("Usage: python script.py [limit] [--save]")\n'
    '                print("  limit: Number of packages to display (optional)")\n'
    '                print("  --save or -s: Save output to file")\n'
    '                sys.exit(1)\n'
    '    if "--save" in sys.argv or "-s" in sys.argv:\n'
    '        save_output = True\n'
    '    print("Fetching PyPI RSS feed...")\n'
    '    xml_content = fetch_rss_feed(PYPI_RSS_URL)\n'
    '    if xml_content is None:\n'
    '        sys.exit(1)\n'
    '    packages = parse_rss_feed(xml_content)\n'
    '    display_packages(packages, limit)\n'
    '    if save_output:\n'
    '        save_to_file(packages)\n'
    '    print(f"\\nSuccessfully extracted {len(packages)} packages from PyPI RSS feed.")\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_PSEARCH_SOURCE: str = (
    'import argparse\n'
    'import json\n'
    'import sys\n'
    'from dataclasses import dataclass\n'
    'import requests\n'
    '\n'
    '\n'
    '@dataclass\n'
    'class Package:\n'
    '    def __str__(self):\n'
    '        return f"{self.name} ({self.version})\\n  {self.summary}\\n  {self.url}"\n'
    '\n'
    '\n'
    'class PyPISearch:\n'
    '    BASE_URL = "https://pypi.org/pypi"\n'
    '    SEARCH_URL = "https://pypi.org/pypi/_/json"\n'
    '\n'
    '    def __init__(self, timeout=10):\n'
    '        self.timeout = timeout\n'
    '\n'
    '    def search(self, query, limit=None):\n'
    '        try:\n'
    '            response = requests.get(\n'
    '                self.SEARCH_URL,\n'
    '                timeout=self.timeout,\n'
    '            )\n'
    '            response.raise_for_status()\n'
    '            data = response.json()\n'
    '        except requests.RequestException as e:\n'
    '            print(f"Error fetching PyPI data: {e}", file=sys.stderr)\n'
    '            return []\n'
    '        query_lower = query.lower()\n'
    '        results = []\n'
    '        for pkg_name, pkg_data in data.get("packages", {}).items():\n'
    '            if query_lower in pkg_name.lower():\n'
    '                info = pkg_data.get("latest", {})\n'
    '                results.append(\n'
    '                    Package(\n'
    '                        name=pkg_name,\n'
    '                        version=info.get("version", "unknown"),\n'
    '                        summary=info.get("summary", "No description"),\n'
    '                        url=f"{self.BASE_URL}/{pkg_name}/",\n'
    '                    )\n'
    '                )\n'
    '            if limit and len(results) >= limit:\n'
    '                break\n'
    '        return sorted(results, key=lambda p: p.name.lower())\n'
    '\n'
    '    def search_json(self, query, limit=None):\n'
    '        results = self.search(query, limit)\n'
    '        return json.dumps(\n'
    '            [\n'
    '                {\n'
    '                    "name": pkg.name,\n'
    '                    "version": pkg.version,\n'
    '                    "summary": pkg.summary,\n'
    '                    "url": pkg.url,\n'
    '                }\n'
    '                for pkg in results\n'
    '            ],\n'
    '            indent=2,\n'
    '        )\n'
    '\n'
    '\n'
    'def main():\n'
    '    parser = argparse.ArgumentParser(\n'
    '        description="Search PyPI packages",\n'
    '        formatter_class=argparse.RawDescriptionHelpFormatter,\n'
    '    )\n'
    '    parser.add_argument("query", help="Package name or keyword to search")\n'
    '    parser.add_argument(\n'
    '        "-l",\n'
    '        "--limit",\n'
    '        type=int,\n'
    '        default=None,\n'
    '        help="Limit results (default: all matches)",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-j",\n'
    '        "--json",\n'
    '        action="store_true",\n'
    '        help="Output as JSON",\n'
    '    )\n'
    '    parser.add_argument(\n'
    '        "-t",\n'
    '        "--timeout",\n'
    '        type=int,\n'
    '        default=10,\n'
    '        help="Request timeout in seconds (default: 10)",\n'
    '    )\n'
    '    args = parser.parse_args()\n'
    '    searcher = PyPISearch(timeout=args.timeout)\n'
    '    if args.json:\n'
    '        print(searcher.search_json(args.query, args.limit))\n'
    '    else:\n'
    '        results = searcher.search(args.query, args.limit)\n'
    '        if not results:\n'
    '            print(f"No packages found for \'{args.query}\'", file=sys.stderr)\n'
    '            sys.exit(1)\n'
    '        print(f"Found {len(results)} package(s):\\n")\n'
    '        for pkg in results:\n'
    '            print(pkg)\n'
    '            print()\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    raise SystemExit(main())\n'
)

_PYPISTATS_SOURCE: str = (
    'import json\n'
    'import ssl\n'
    'import sys\n'
    'from collections import defaultdict\n'
    'from urllib.request import urlopen\n'
    '\n'
    'PACKAGE = sys.argv[1]\n'
    '\n'
    '\n'
    'def get_stats(stats_type, package=PACKAGE, period="month"):\n'
    '    stats_url = f"https://pypistats.org/api/packages/{package}/{stats_type}?period={period}"\n'
    '    ctx = ssl.create_default_context()\n'
    '    ctx.check_hostname = False\n'
    '    ctx.verify_mode = ssl.CERT_NONE\n'
    '    with urlopen(stats_url, context=ctx) as stats:\n'
    '        data = json.load(stats)\n'
    '    return data\n'
    '\n'
    '\n'
    'def aggregate(stats):\n'
    '    counts = defaultdict(int)\n'
    '    days = defaultdict(int)\n'
    '    for entry in stats["data"]:\n'
    '        category = entry["category"]\n'
    '        counts[category] += entry["downloads"]\n'
    '        days[category] += 1\n'
    '    return {category: counts[category] / days[category] for category in counts}\n'
    '\n'
    '\n'
    'def version_sorter(version_and_count):\n'
    '    version = version_and_count[0]\n'
    '    return tuple(map(int, version.split("."))) if version.replace(".", "").isdigit() else (2**32,)\n'
    '\n'
    '\n'
    'def system_sorter(name_and_count):\n'
    '    order = ("linux", "windows", "darwin")\n'
    '    system = name_and_count[0]\n'
    '    try:\n'
    '        return order.index(system.lower())\n'
    '    except ValueError:\n'
    '        return len(order)\n'
    '\n'
    '\n'
    'def print_agg_stats(stats, sort_key=None):\n'
    '    total = sum(stats.values())\n'
    '    max_len = max(len(category) for category in stats)\n'
    '    agg_sum = 0.0\n'
    '    for category, count in sorted(stats.items(), key=sort_key, reverse=True):\n'
    '        agg_sum += count\n'
    '        print(f"  {category:{max_len}}: {count:-12.1f} / day ({agg_sum / total * 40:-5.1f}%)")\n'
    '\n'
    '\n'
    'def main():\n'
    '    import sys\n'
    '\n'
    '    package_name = sys.argv[1] if len(sys.argv) > 1 else PACKAGE\n'
    '    counts = get_stats("python_minor", package=package_name)\n'
    '    stats = aggregate(counts)\n'
    '    print("Downloads by Python version:")\n'
    '    print_agg_stats(stats, sort_key=version_sorter)\n'
    '    print()\n'
    '    counts = get_stats("system", package=package_name)\n'
    '    stats = aggregate(counts)\n'
    '    print("Downloads by system:")\n'
    '    print_agg_stats(stats, sort_key=system_sorter)\n'
    '    total = sum(stats.values())\n'
    '    days = {"month": 30, "week": 7, "day": 1}\n'
    '    print(f"Total downloads per month: {total * days[\'month\']:-12,.1f}")\n'
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


class GetLatestPkgsAddedToPypiTool(BaseTool):
    """Wrapper for original get_latest_pkgs_added_to_pypi.py: fetch_pypi_updates() + 4 more."""
    name: str = 'get_latest_pkgs_added_to_pypi'
    source_file: str = 'get_latest_pkgs_added_to_pypi.py'
    description: str = 'fetch_pypi_updates() + 4 more'
    functions: list[str] = ['fetch_pypi_updates', 'save_to_json', 'save_to_csv', 'save_to_text', 'main']
    notes: str = ''
    source: str = _GET_LATEST_PKGS_ADDED_TO_PYPI_SOURCE

class GetPypiRssfeedTool(BaseTool):
    """Wrapper for original get_pypi_rssfeed.py: fetch_rss_feed() + 4 more."""
    name: str = 'get_pypi_rssfeed'
    source_file: str = 'get_pypi_rssfeed.py'
    description: str = 'fetch_rss_feed() + 4 more'
    functions: list[str] = ['fetch_rss_feed', 'parse_rss_feed', 'display_packages', 'save_to_file', 'main']
    notes: str = ''
    source: str = _GET_PYPI_RSSFEED_SOURCE

class PsearchTool(BaseTool):
    """Wrapper for original psearch.py: main() + 0 more."""
    name: str = 'psearch'
    source_file: str = 'psearch.py'
    description: str = 'main() + 0 more'
    functions: list[str] = ['main']
    notes: str = ''
    source: str = _PSEARCH_SOURCE

class PypistatsTool(BaseTool):
    """Wrapper for original pypistats.py: get_stats() + 5 more."""
    name: str = 'pypistats'
    source_file: str = 'pypistats.py'
    description: str = 'get_stats() + 5 more'
    functions: list[str] = ['get_stats', 'aggregate', 'version_sorter', 'system_sorter', 'print_agg_stats', 'main']
    notes: str = ''
    source: str = _PYPISTATS_SOURCE

class PypiInfoQueryUnified:
    """Dispatcher exposing all original scripts as subcommands."""

    TOOLS: dict[str, type[BaseTool]] = {
        'get_latest_pkgs_added_to_pypi': GetLatestPkgsAddedToPypiTool,
        'get_pypi_rssfeed': GetPypiRssfeedTool,
        'psearch': PsearchTool,
        'pypistats': PypistatsTool,
    }

    @classmethod
    def list_tools(cls: type[PypiInfoQueryUnified]) -> list[str]:
        """Return sorted tool names."""
        return sorted(cls.TOOLS.keys())

    @classmethod
    def get_tool(cls: type[PypiInfoQueryUnified], name: str) -> type[BaseTool] | None:
        """Return tool class by name or None."""
        return cls.TOOLS.get(name)

    @classmethod
    def build_parser(cls: type[PypiInfoQueryUnified]) -> argparse.ArgumentParser:
        """Build argparse parser for unified-level flags."""
        p: argparse.ArgumentParser = argparse.ArgumentParser(
            prog="main.py",
            description="Unified tool for pypi_info_query (4 original scripts). Use --list, --info <tool>, or <tool> [args...].",
        )
        p.add_argument("--list", action="store_true", help="list embedded tools and exit")
        p.add_argument("--info", metavar="TOOL", default=None, help="show info for one tool and exit")
        p.add_argument("tool", nargs="?", default=None, help="tool name (see --list)")
        p.add_argument("passthrough", nargs=argparse.REMAINDER, help="args passed to original script")
        return p

    @classmethod
    def print_list(cls: type[PypiInfoQueryUnified]) -> None:
        """Print tool list to stdout."""
        for nm in cls.list_tools():
            t: type[BaseTool] = cls.TOOLS[nm]
            extra: str = f" [{t.notes}]" if t.notes else ""
            print(f"{t.name} <- {t.source_file}: {t.description}{extra}")

    @classmethod
    def main(cls: type[PypiInfoQueryUnified], argv: Sequence[str] | None = None) -> int:
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
    return PypiInfoQueryUnified.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

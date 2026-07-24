"""Acquire the licensed Life Lexicon snapshot and rebuild the v2 catalog.

Network access is intentionally isolated to this development-only acquisition
tool. The runtime catalog is produced through the same strict local RLE importer
used for manually downloaded sources.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote, urljoin

import requests
from bs4 import BeautifulSoup

from src.patterns.catalog import DEFAULT_CATALOG_PATH
from src.patterns.rle import encode_rle
from tools.patterns.import_rle import import_rle_files


BASE_URL = "https://playgameoflife.com"
INDEX_URL = f"{BASE_URL}/list.html"
LICENSE = "CC-BY-SA-3.0"
SNAPSHOT_VERSION = "2026-07-24"


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", unquote(value).casefold()).strip("-")
    return cleaned or "pattern"


def _discover(
    session: requests.Session,
) -> tuple[list[dict[str, str]], str]:
    response = session.get(INDEX_URL, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    discovered: dict[str, dict[str, str]] = {}
    for anchor in soup.select('a[data-internal][href^="/lexicon/"]'):
        path = anchor.get("href")
        if not path or path in discovered:
            continue
        section = anchor.find_parent("section")
        heading = section.find("h2") if section else None
        meta = section.select_one(".meta") if section else None
        discovered[path] = {
            "path": path,
            "name": heading.get_text(" ", strip=True) if heading else unquote(path.rsplit("/", 1)[-1]),
            "meta": meta.get_text(" ", strip=True) if meta else "",
        }
    return (
        [discovered[path] for path in sorted(discovered, key=str.casefold)],
        hashlib.sha256(response.content).hexdigest(),
    )


def _fetch_pattern(item: dict[str, str]) -> tuple[dict[str, str], list[list[int]]]:
    url = urljoin(BASE_URL, item["path"])
    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Cellular-Cube-Go pattern importer/0.2"},
    )
    response.raise_for_status()
    item = {
        **item,
        "content_sha256": hashlib.sha256(response.content).hexdigest(),
    }
    soup = BeautifulSoup(response.text, "html.parser")
    canvas = soup.find("gol-canvas")
    if canvas is None:
        raise ValueError("missing gol-canvas")
    lines = [
        line.strip()
        for line in canvas.get_text("\n").splitlines()
        if line.strip()
    ]
    if not lines:
        raise ValueError("empty gol-canvas")
    if any(set(line) - {".", "O", "o"} for line in lines):
        raise ValueError("canvas contains non-binary symbols")
    width = max(map(len, lines))
    cells = [
        [1 if char in {"O", "o"} else 0 for char in line.ljust(width, ".")]
        for line in lines
    ]
    if not any(map(any, cells)):
        raise ValueError("canvas has no live cells")
    return {**item, "url": url}, cells


def acquire(
    catalog_path: Path,
    output_path: Path,
    report_path: Path,
    *,
    workers: int = 16,
) -> None:
    session = requests.Session()
    session.headers["User-Agent"] = "Cellular-Cube-Go pattern importer/0.2"
    discovered, index_sha256 = _discover(session)
    acquisition_errors: list[dict[str, str | None]] = []
    fetched: list[tuple[dict[str, str], list[list[int]]]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_fetch_pattern, item): item for item in discovered}
        for future in as_completed(futures):
            item = futures[future]
            try:
                fetched.append(future.result())
            except Exception as exc:  # report each upstream failure; never hide it
                acquisition_errors.append(
                    {
                        "source_file": urljoin(BASE_URL, item["path"]),
                        "status": "invalid",
                        "pattern_id": None,
                        "reason": str(exc),
                    }
                )

    base = json.loads(catalog_path.read_text(encoding="utf-8"))
    base["patterns"] = [
        item
        for item in base["patterns"]
        if item["source"]["provider"] != "playgameoflife-life-lexicon"
    ]
    base["generated"] = {
        "format": "rule-aware-rle-catalog",
        "version": SNAPSHOT_VERSION,
        "generated_at": SNAPSHOT_VERSION,
        "note": (
            "Project-owned seed patterns plus a licensed PlayGameOfLife "
            "Life Lexicon snapshot; unverified legacy scrape data is excluded."
        ),
        "sources": [
            "project-owned builtins at revision f513f63",
            "PlayGameOfLife Life Lexicon snapshot",
        ],
    }

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        manifest: dict[str, dict] = {}
        files: list[Path] = []
        used_ids: dict[str, int] = {}
        source_by_file: dict[str, str] = {}
        for item, cells in sorted(fetched, key=lambda value: value[0]["path"].casefold()):
            base_id = f"life-lexicon-{_slug(item['path'].rsplit('/', 1)[-1])}"
            used_ids[base_id] = used_ids.get(base_id, 0) + 1
            suffix = used_ids[base_id]
            pattern_id = base_id if suffix == 1 else f"{base_id}-{suffix}"
            filename = f"{pattern_id}.rle"
            path = root / filename
            path.write_text(encode_rle(cells, "B3/S23"), encoding="utf-8")
            files.append(path)
            source_by_file[str(path)] = item["url"]
            tags = ["life-lexicon"]
            if item["meta"]:
                tags.append(f"lexicon-meta:{item['meta']}")
            manifest[filename] = {
                "id": pattern_id,
                "name": item["name"],
                "rule_ids": ["life"],
                "category": "life-lexicon",
                "tier": "large" if len(cells) * len(cells[0]) > 64 else "standard",
                "weight": 1.0,
                "tags": tags,
                "source": {
                    "provider": "playgameoflife-life-lexicon",
                    "url": item["url"],
                    "version": SNAPSHOT_VERSION,
                    "external_id": item["path"].rsplit("/", 1)[-1],
                    "license": LICENSE,
                    "license_uri": "https://creativecommons.org/licenses/by-sa/3.0/",
                    "attribution": (
                        "Life Lexicon compiled by Stephen A. Silver; original "
                        "contributors are listed on the upstream credit page"
                    ),
                    "changes": (
                        "Converted the displayed grid to canonical RLE, trimmed "
                        "empty borders, and geometrically deduplicated"
                    ),
                    "content_sha256": item["content_sha256"],
                },
            }
        updated, report = import_rle_files(
            files,
            manifest={"patterns": manifest},
            base_catalog=base,
        )

    for result in report["results"]:
        result["source_file"] = source_by_file.get(
            result["source_file"], result["source_file"]
        )
    report["results"].extend(acquisition_errors)
    summary: dict[str, int] = {}
    for result in report["results"]:
        summary[result["status"]] = summary.get(result["status"], 0) + 1
    report["summary"] = dict(sorted(summary.items()))
    report["source"] = {
        "provider": "playgameoflife-life-lexicon",
        "index_url": INDEX_URL,
        "snapshot_version": SNAPSHOT_VERSION,
        "license": LICENSE,
        "discovered": len(discovered),
        "index_sha256": index_sha256,
    }
    output_path.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_CATALOG_PATH)
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_CATALOG_PATH.with_name("import-report.v2.json"),
    )
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()
    acquire(args.catalog, args.output, args.report, workers=args.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

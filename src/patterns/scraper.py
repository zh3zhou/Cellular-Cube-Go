import re
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from collections import deque
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from config.game_config import GameConfig

SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36'
})

ALIVE_CHARS = set('OoXx*#')
DEAD_CHARS = set('. ')

def _extract_blocks(text: str):
    lines = text.splitlines()
    blocks = []
    buf = []
    for line in lines:
        s = line.rstrip('\r\n')
        if s and re.fullmatch(r"[\.OoXx\*# ]+", s):
            buf.append(s)
        else:
            if len(buf) >= 2:
                blocks.append(buf)
            buf = []
    if len(buf) >= 2:
        blocks.append(buf)
    return blocks

def _trim(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    top = 0
    bottom = h
    left = 0
    right = w
    while top < bottom and all(c == 0 for c in grid[top]):
        top += 1
    while bottom > top and all(c == 0 for c in grid[bottom - 1]):
        bottom -= 1
    while left < right and all(row[left] == 0 for row in grid[top:bottom]):
        left += 1
    while right > left and all(row[right - 1] == 0 for row in grid[top:bottom]):
        right -= 1
    return [row[left:right] for row in grid[top:bottom]]

def _to_matrix(block):
    norm = [row.replace('\t', ' ').rstrip() for row in block]
    max_w = max((len(r) for r in norm), default=0)
    grid = []
    for row in norm:
        cells = [1 if c in ALIVE_CHARS else 0 for c in row]
        if len(cells) < max_w:
            cells.extend([0] * (max_w - len(cells)))
        grid.append(cells)
    trimmed = _trim(grid)
    return trimmed

def _probability_for_name(name: str):
    n = name.lower()
    if 'glider' in n:
        return 0.5
    if 'lwss' in n or 'mwss' in n or 'hwss' in n or 'spaceship' in n:
        return 0.4
    if 'gun' in n:
        return 0.05
    if 'pulsar' in n or 'oscillator' in n:
        return 0.3
    return 0.2

def _get_lexicon_links():
    links = set()
    try:
        sm = SESSION.get('https://playgameoflife.com/sitemap.xml', timeout=20)
        for m in re.findall(r"<loc>([^<]+)</loc>", sm.text):
            if '/lexicon/' in m and not m.rstrip('/').endswith('/lexicon'):
                links.add(m)
    except Exception:
        pass
    try:
        res = SESSION.get('https://playgameoflife.com/lexicon', timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('/lexicon/') and href != '/lexicon':
                links.add('https://playgameoflife.com' + href)
    except Exception:
        pass
    return sorted(links)

def _crawl_lexicon_links(max_pages: int = 1000, seeds=None):
    visited = set()
    result = set()
    if seeds is None:
        seeds = ['https://playgameoflife.com/lexicon']
        seeds += [f'https://playgameoflife.com/lexicon/{c}' for c in 'abcdefghijklmnopqrstuvwxyz0123456789']
    q = deque(seeds)
    while q and len(visited) < max_pages:
        url = q.popleft()
        if url in visited:
            continue
        visited.add(url)
        try:
            r = SESSION.get(url, timeout=20)
        except Exception:
            continue
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('/lexicon/'):
                full = 'https://playgameoflife.com' + href
                result.add(full)
                if full not in visited:
                    q.append(full)
            elif href.startswith('https://playgameoflife.com/lexicon/'):
                result.add(href)
                if href not in visited:
                    q.append(href)
    return sorted(result)

def _parse_page(url: str):
    res = SESSION.get(url, timeout=30)
    soup = BeautifulSoup(res.text, 'html.parser')
    texts = []
    for pre in soup.find_all(['pre', 'code']):
        texts.append(pre.get_text('\n'))
    if not texts:
        texts.append(soup.get_text('\n'))
    blocks = []
    for t in texts:
        blocks.extend(_extract_blocks(t))
    mats = [_to_matrix(b) for b in blocks if b]
    return mats

def scrape_and_save(max_pages: int = 500):
    base = set(_get_lexicon_links())
    crawl = set(_crawl_lexicon_links(max_pages))
    urls = sorted(base.union(crawl))
    if not urls:
        urls = [
            'https://playgameoflife.com/lexicon/glider',
            'https://playgameoflife.com/lexicon/block',
            'https://playgameoflife.com/lexicon/blinker',
            'https://playgameoflife.com/lexicon/beacon',
            'https://playgameoflife.com/lexicon/toad',
            'https://playgameoflife.com/lexicon/pulsar',
            'https://playgameoflife.com/lexicon/pentadecathlon',
            'https://playgameoflife.com/lexicon/lwss',
            'https://playgameoflife.com/lexicon/mwss',
            'https://playgameoflife.com/lexicon/hwss',
            'https://playgameoflife.com/lexicon/r_pentomino',
            'https://playgameoflife.com/lexicon/diehard',
            'https://playgameoflife.com/lexicon/acorn',
            'https://playgameoflife.com/lexicon/gosper_glider_gun',
            'https://playgameoflife.com/lexicon/switch_engine',
            'https://playgameoflife.com/lexicon/weekender',
            'https://playgameoflife.com/lexicon/copperhead',
            'https://playgameoflife.com/lexicon/galaxy',
            'https://playgameoflife.com/lexicon/clock',
            'https://playgameoflife.com/lexicon/figure_eight',
            'https://playgameoflife.com/lexicon/beehive',
            'https://playgameoflife.com/lexicon/loaf',
            'https://playgameoflife.com/lexicon/boat',
            'https://playgameoflife.com/lexicon/tub',
            'https://playgameoflife.com/lexicon/pond',
            'https://playgameoflife.com/lexicon/barge',
            'https://playgameoflife.com/lexicon/aircraft_carrier',
            'https://playgameoflife.com/lexicon/snake',
            'https://playgameoflife.com/lexicon/ship',
            'https://playgameoflife.com/lexicon/boat_tie',
            'https://playgameoflife.com/lexicon/1-2-3',
            'https://playgameoflife.com/lexicon/table',
            'https://playgameoflife.com/lexicon/seed',
            'https://playgameoflife.com/lexicon/still_life',
            'https://playgameoflife.com/lexicon/spaceship',
        ]
    if max_pages:
        urls = urls[:max_pages]
    all_patterns = []
    for url in urls:
        mats = _parse_page(url)
        slug = url.rstrip('/').split('/')[-1]
        for idx, m in enumerate(mats):
            h = len(m)
            w = len(m[0]) if h else 0
            if h == 0 or w == 0:
                continue
            if h > GameConfig.WORLD_HEIGHT or w > GameConfig.WORLD_WIDTH:
                continue
            name = f"{slug}" if idx == 0 else f"{slug}_{idx+1}"
            prob = _probability_for_name(name)
            all_patterns.append(((h, w), name, m, prob))
    grouped = {}
    for (h, w), name, m, prob in all_patterns:
        key = f"{h}x{w}"
        if key not in grouped:
            grouped[key] = {}
        grouped[key][name] = {"pattern": m, "probability": prob}
    root = Path(__file__).resolve().parents[2]
    out_dir = root / 'assets' / 'patterns'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / 'library.json'
    with out_file.open('w', encoding='utf-8') as f:
        json.dump(grouped, f, ensure_ascii=False)
    # simple progress print
    print(f"urls={len(urls)} patterns={sum(len(v) for v in grouped.values())}")
    return out_file.as_posix()

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-pages', type=int, default=500)
    args = ap.parse_args()
    p = scrape_and_save(max_pages=args.max_pages)
    print(p)
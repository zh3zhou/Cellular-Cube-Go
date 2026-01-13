import re
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from collections import deque
import sys
import subprocess
import tempfile
import shutil
import os

sys.path.append(str(Path(__file__).resolve().parents[2]))
from config.game_config import GameConfig

SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36'
})

ALIVE_CHARS = set('OoXx*#1█■')
DEAD_CHARS = set('. 0')

def _extract_blocks(text: str):
    lines = text.splitlines()
    blocks = []
    buf = []
    for line in lines:
        s = line.rstrip('\r\n')
        if s and re.fullmatch(r"[\.OoXx\*# 01█■]+", s):
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
        # Expanded manual seeds for better coverage if crawling fails
        common_terms = [
            'glider', 'block', 'blinker', 'toad', 'beacon', 'pulsar', 'pentadecathlon',
            'lwss', 'mwss', 'hwss', 'spaceship', 'r_pentomino', 'diehard', 'acorn',
            'gosper_glider_gun', 'simkin_glider_gun', 'bi_gun', 'puffer', 'breeder',
            'switch_engine', 'weekender', 'copperhead', 'galaxy', 'clock', 'figure_eight',
            'beehive', 'loaf', 'boat', 'tub', 'pond', 'barge', 'aircraft_carrier',
            'snake', 'ship', 'long_boat', 'eater', 'reflector', 'herschel', 'pi_heptomino',
            'century', 'thunderbird', 'queen_bee', 'shuttle', 'phoenix', 'kok_s_galaxy',
            'achim_s_p144', 'loafer', 'caterpillar', 'gemini', 'demonoid', 'orthogonoid'
        ]
        seeds += [f'https://playgameoflife.com/lexicon/{term}' for term in common_terms]
        
    q = deque(seeds)
    while q and len(visited) < max_pages:
        url = q.popleft()
        if url in visited:
            continue
        visited.add(url)
        try:
            r = SESSION.get(url, timeout=10)
            if r.status_code == 404:
                continue
        except Exception:
            continue
        
        soup = BeautifulSoup(r.text, 'html.parser')
        # Extract patterns on this page
        # (This is done in _parse_page, but here we just crawl links)
        
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

def _parse_rle_sections(text: str):
    lines = text.splitlines()
    sections = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.search(r"x\s*=\s*(\d+)\s*,\s*y\s*=\s*(\d+)", line)
        if m:
            try:
                w = int(m.group(1))
                h = int(m.group(2))
            except Exception:
                i += 1
                continue
            rle_lines = []
            i += 1
            while i < len(lines):
                s = lines[i].strip()
                if not s:
                    i += 1
                    continue
                if re.fullmatch(r"[0-9bo\$!\s]+", s):
                    rle_lines.append(s)
                    if '!' in s:
                        i += 1
                        break
                    i += 1
                else:
                    break
            if rle_lines:
                sections.append((w, h, "".join(rle_lines)))
        else:
            i += 1
    return sections

def _rle_to_matrix(rle: str, width: int, height: int):
    rows = []
    cur = []
    num = 0
    def flush_cells(val, count):
        nonlocal cur, rows
        for _ in range(count):
            cur.append(1 if val == 'o' else 0)
            if len(cur) == width:
                rows.append(cur)
                cur = []
    for ch in rle:
        if ch.isdigit():
            num = num * 10 + int(ch)
        elif ch in ('b', 'o'):
            cnt = num if num > 0 else 1
            flush_cells(ch, cnt)
            num = 0
        elif ch == '$':
            cnt = num if num > 0 else 1
            for _ in range(cnt):
                if cur:
                    while len(cur) < width:
                        cur.append(0)
                    rows.append(cur)
                    cur = []
                else:
                    rows.append([0] * width)
            num = 0
        elif ch == '!':
            break
        else:
            pass
    if cur:
        while len(cur) < width:
            cur.append(0)
        rows.append(cur)
    while len(rows) < height:
        rows.append([0] * width)
    grid = rows[:height]
    return _trim(grid)

def _parse_page(url: str):
    try:
        res = SESSION.get(url, timeout=30)
        if res.status_code != 200:
            return []
    except Exception:
        return []
        
    soup = BeautifulSoup(res.text, 'html.parser')
    texts = []
    for pre in soup.find_all(['pre', 'code']):
        texts.append(pre.get_text('\n'))
    if not texts:
        texts.append(soup.get_text('\n'))
    blocks = []
    mats = []
    for t in texts:
        blocks.extend(_extract_blocks(t))
        rle_sections = _parse_rle_sections(t)
        for w, h, rle in rle_sections:
            try:
                mats.append(_rle_to_matrix(rle, w, h))
            except Exception:
                pass
    mats.extend([_to_matrix(b) for b in blocks if b])
    return mats

def _to_canonical_key(matrix):
    points = []
    for r, row in enumerate(matrix):
        for c, val in enumerate(row):
            if val:
                points.append((r, c))
    if not points:
        return frozenset()
    min_r = min(p[0] for p in points)
    min_c = min(p[1] for p in points)
    return frozenset((r - min_r, c - min_c) for r, c in points)

def _scrape_golly_repo():
    print("Cloning Golly repository for patterns (this may take a moment)...")
    patterns = []
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Clone only the Patterns directory (sparse checkout is ideal but depth 1 full clone is safer for compatibility)
            # Using full depth 1 clone of jimblandy/golly
            subprocess.run(
                ['git', 'clone', '--depth', '1', 'https://github.com/jimblandy/golly.git', temp_dir],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            
            patterns_dir = Path(temp_dir) / 'Patterns' / 'Life'
            if not patterns_dir.exists():
                print("Patterns/Life directory not found in Golly repo.")
                return []
                
            for root, dirs, files in os.walk(patterns_dir):
                for file in files:
                    if file.lower().endswith(('.rle', '.lif', '.life')):
                        file_path = Path(root) / file
                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            # Try RLE
                            rle_sections = _parse_rle_sections(content)
                            for w, h, rle in rle_sections:
                                try:
                                    mat = _rle_to_matrix(rle, w, h)
                                    patterns.append((file.rsplit('.', 1)[0], mat))
                                except:
                                    pass
                            # Also try block extraction if RLE failed or as supplement
                            if not rle_sections:
                                blocks = _extract_blocks(content)
                                for b in blocks:
                                    mat = _to_matrix(b)
                                    patterns.append((file.rsplit('.', 1)[0], mat))
                        except Exception as e:
                            # print(f"Error reading {file}: {e}")
                            pass
        except Exception as e:
            print(f"Failed to scrape Golly repo: {e}")
            return []
            
    print(f"Found {len(patterns)} patterns from Golly repo.")
    return patterns

def scrape_and_save(max_pages: int = 500):
    all_patterns = []
    
    # 1. Scrape PlayGameOfLife.com
    print("Scraping playgameoflife.com...")
    base = set(_get_lexicon_links())
    crawl = set(_crawl_lexicon_links(max_pages))
    urls = sorted(base.union(crawl))
    
    # Fallback list if crawling fails
    if not urls:
        urls = [f'https://playgameoflife.com/lexicon/{term}' for term in [
            'glider', 'block', 'blinker', 'toad', 'beacon', 'pulsar', 'pentadecathlon',
            'lwss', 'mwss', 'hwss', 'spaceship', 'r_pentomino', 'diehard', 'acorn',
            'gosper_glider_gun', 'switch_engine', 'weekender', 'copperhead'
        ]]

    if max_pages:
        urls = urls[:max_pages]

    for url in urls:
        mats = _parse_page(url)
        slug = url.rstrip('/').split('/')[-1]
        for idx, m in enumerate(mats):
            name = f"{slug}" if idx == 0 else f"{slug}_{idx+1}"
            all_patterns.append((name, m))
            
    # 2. Scrape Golly Repo
    golly_patterns = _scrape_golly_repo()
    all_patterns.extend(golly_patterns)
    
    # Process and Save
    grouped = {}
    seen_keys = set()
    
    count = 0
    skipped = 0
    
    for name, m in all_patterns:
        h = len(m)
        w = len(m[0]) if h else 0
        if h == 0 or w == 0:
            continue
        if h > GameConfig.WORLD_HEIGHT or w > GameConfig.WORLD_WIDTH:
            continue
            
        # Deduplication
        key = _to_canonical_key(m)
        if key in seen_keys:
            skipped += 1
            continue
        seen_keys.add(key)
        
        prob = _probability_for_name(name)
        
        size_key = f"{h}x{w}"
        if size_key not in grouped:
            grouped[size_key] = {}
        grouped[size_key][name] = {"pattern": m, "probability": prob}
        count += 1

    root = Path(__file__).resolve().parents[2]
    out_dir = root / 'assets' / 'patterns'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / 'library.json'
    
    merged = {}
    if out_file.exists():
        try:
            with out_file.open('r', encoding='utf-8') as f:
                existing = json.load(f)
                if isinstance(existing, dict):
                    merged = existing
        except Exception:
            merged = {}
            
    for size_key, patterns in grouped.items():
        if size_key not in merged or not isinstance(merged.get(size_key), dict):
            merged[size_key] = {}
        for name, info in patterns.items():
            if name not in merged[size_key]:
                merged[size_key][name] = info
                
    with out_file.open('w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False)
        
    print(f"Scraping complete. Saved to {out_file}")
    print(f"Total patterns: {count} (Skipped duplicates: {skipped})")
    print(f"Sources: PlayGameOfLife ({len(urls)} pages), Golly Repo ({len(golly_patterns)} raw)")
    return out_file.as_posix()

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-pages', type=int, default=1000)
    args = ap.parse_args()
    p = scrape_and_save(max_pages=args.max_pages)

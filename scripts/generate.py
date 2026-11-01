#!/usr/bin/env python3
"""
Generator aset pixel-art untuk profil GitHub dengan tema Pixel Astronaut.

Menghasilkan 3 file SVG di folder assets/:
  - banner.svg        : banner + HUD astronot di permukaan bulan (score = jumlah bintang yang ditemukan)
  - stats.svg         : kartu "Astronaut Log" + "System Telemetry" bergaya pixel
  - contrib-game.svg  : konstelasi bintang kontribusi di luar angkasa dengan astronaut meluncurkan probe

Hanya memakai pustaka standar Python. Setiap bagian punya fallback.
"""
import html
import json
import math
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER = os.environ.get("GH_USER", "akidpeyud")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
QUEST_FALLBACK = os.environ.get("QUEST_FALLBACK", "SIMERAH KOJA")
QUEST_MAX_AGE_DAYS = int(os.environ.get("QUEST_MAX_AGE_DAYS", "21"))
OUT = Path(__file__).resolve().parent.parent / "assets"

# ── Color Palette: 2 warna utama lama (#1B365D & #005A9C) dipertahankan ──
NAVY, BLUE = "#1B365D", "#005A9C"

# ── Palette Astronaut & Deep Space ──
DEEP = "#0B111E"
SPACE_MID = "#112240"
SKY1, SKY2, SKY3 = "#2F8FD8", "#4DA3E0", "#7FC4FF"
PALE = "#D6E8F5"
GOLD, GOLD_L = "#FFD166", "#FFF0B8"
AMBER = "#FB8500"
ORANGE = "#FF5722"
CYAN = "#67E8F9"
WHITE = "#FFFFFF"
SLATE = "#CBD5E1"
DARK_SLATE = "#475569"
FONT = "text { font-family: 'Courier New', Courier, monospace; font-weight: 700; }"


# ───────────────────────── util ─────────────────────────
def http_get(url, api=False):
    headers = {"User-Agent": "Mozilla/5.0 (pixel-profile-generator)"}
    if api:
        headers["Accept"] = "application/vnd.github+json"
        if TOKEN:
            headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def safe(fn, default, label):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        print(f"[warn] {label} gagal: {e}", file=sys.stderr)
        return default


def esc(t):
    return html.escape(str(t), quote=True)


def sprite(grid, colors, px):
    w = len(grid[0])
    out = []
    for r, row in enumerate(grid):
        assert len(row) == w, f"Row {r} len {len(row)} != {w}: {row}"
        for c, ch in enumerate(row):
            if ch in colors:
                out.append(f'<rect x="{c*px}" y="{r*px}" width="{px}" height="{px}" fill="{colors[ch]}"/>')
    return "".join(out)


# ───────────────────────── pixel sprites ─────────────────────────
# Pixel Astronaut (14x15)
ASTRONAUT_GRID = [
    "...WWWWWW.....",
    "..WWWWWWWW....",
    ".WWVVVVVVOO...",
    ".WWLVVVVVOO...",
    ".WWVVVVVVOO...",
    "..WWWWWWWW....",
    "BBWWWWWWWWBB..",
    "BBWRBWWWBWBB..",
    "BBWWWWWWWWBB..",
    ".BBDDDDDDBB...",
    "..WWWWWWWW....",
    "..WWW..WWW....",
    "..WWW..WWW....",
    "..SSS..SSS....",
    ".DDDD..DDDD...",
]
ASTRONAUT_COLORS = {
    "W": WHITE,
    "S": SLATE,
    "D": DARK_SLATE,
    "V": GOLD,
    "O": AMBER,
    "L": "#FFFDF0",
    "B": BLUE,
    "R": ORANGE,
}

HERO = sprite(ASTRONAUT_GRID, ASTRONAUT_COLORS, 5)
HERO_S = sprite(ASTRONAUT_GRID, ASTRONAUT_COLORS, 3)

# Distant Planet Earth (14x14)
PLANET_GRID = [
    ".....BBBB.....",
    "...BBBAAABBB..",
    "..BBAAAAAAABB.",
    ".BBAAAAWAAAABB",
    ".BAAWWWWWAAABB",
    "BBAAAWWWWAAABB",
    "BBAAAAAWWAAABB",
    "BBAAAAAAAWAABB",
    "BBBBAAAWWAAABB",
    ".BBBAAAAAAABB.",
    ".BBBAAAAAABBB.",
    "..BBBBBBBBBB..",
    "...BBBBBBBB...",
    ".....BBBB.....",
]
PLANET = sprite(PLANET_GRID, {"B": BLUE, "A": NAVY, "W": SKY3}, 4)

# Orbiting Satellite (14x6)
SATELLITE_GRID = [
    "BB....WW....BB",
    "BB....WW....BB",
    "BBBBWWDDWWBBBB",
    "BBBBWWDDWWBBBB",
    "BB....WW....BB",
    "BB....WW....BB",
]
SATELLITE = sprite(SATELLITE_GRID, {"B": BLUE, "W": SLATE, "D": GOLD}, 3)

# Lunar Rover (10x8)
ROVER_GRID = [
    "....R.....",
    "....|.....",
    "..WWWWW...",
    ".WWBCCBW..",
    ".WWWWWWW..",
    "..O...O...",
    ".OOO.OOO..",
    "..O...O...",
]
ROVER = sprite(ROVER_GRID, {"W": SLATE, "B": BLUE, "C": CYAN, "R": ORANGE, "|": DARK_SLATE, "O": NAVY}, 4)

# Golden Star (Big - 9x8)
STAR_BIG_GRID = [
    "....X....",
    "...XXX...",
    "..XXLXX..",
    "XXXXXXXXX",
    ".XXXXXXX.",
    "..XXXXX..",
    ".XXX.XXX.",
    ".XX...XX.",
]
STAR_BIG = sprite(STAR_BIG_GRID, {"X": GOLD, "L": GOLD_L}, 5)

# Golden Star Mini (5x5)
STAR_MINI_GRID = [
    "..X..",
    ".XLX.",
    "XXXXX",
    ".XXX.",
    ".X.X.",
]
STAR_MINI = sprite(STAR_MINI_GRID, {"X": GOLD, "L": GOLD_L}, 4)
STAR_TINY = sprite(STAR_MINI_GRID, {"X": GOLD, "L": GOLD_L}, 3)

# Expedition Flag (8x5)
FLAG_GRID = [
    "BBBBBBBB",
    "BWWWWWWB",
    "BWWGWWWB",
    "BWWWWWWB",
    "BBBBBBBB",
]
FLAG = sprite(FLAG_GRID, {"B": BLUE, "W": WHITE, "G": GOLD}, 4)

# Space Probe / Beacon (7x6)
PROBE_GRID = [
    "...W...",
    "..WWW..",
    ".WWBWW.",
    "WWRTRWW",
    ".FLGLF.",
    "..F.F..",
]
PROBE = sprite(PROBE_GRID, {"W": WHITE, "B": BLUE, "R": ORANGE, "T": CYAN, "F": GOLD, "G": GOLD_L}, 4)


def moon_hills(x0, steps, w0, step_w, step_h, ground, fill):
    return "".join(
        f'<rect x="{x0+i*step_w}" y="{ground-(i+1)*step_h}" width="{w0-i*2*step_w}" height="{step_h}" fill="{fill}"/>'
        for i in range(steps)
    )


def moon_tiles(W, ground, rows=2):
    out = []
    for r in range(rows):
        for c in range(W // 24 + 1):
            out.append(f'<rect x="{c*24}" y="{ground+8+r*24}" width="24" height="24" fill="{DEEP}" stroke="{NAVY}" stroke-width="2"/>')
    craters = [
        f'<rect x="70" y="{ground+12}" width="28" height="8" fill="{NAVY}"/>',
        f'<rect x="74" y="{ground+10}" width="20" height="2" fill="{BLUE}"/>',
        f'<rect x="280" y="{ground+14}" width="36" height="10" fill="{NAVY}"/>',
        f'<rect x="286" y="{ground+12}" width="24" height="2" fill="{BLUE}"/>',
        f'<rect x="620" y="{ground+13}" width="32" height="9" fill="{NAVY}"/>',
        f'<rect x="624" y="{ground+11}" width="24" height="2" fill="{BLUE}"/>',
    ]
    return (
        "".join(out)
        + "".join(craters)
        + f'<rect x="0" y="{ground}" width="{W}" height="8" fill="{BLUE}"/>'
        + f'<rect x="0" y="{ground}" width="{W}" height="3" fill="{SKY3}"/>'
    )


# ───────────────────────── data ─────────────────────────
def get_contributions():
    page = http_get(f"https://github.com/users/{USER}/contributions")
    cells = re.findall(
        r'data-date="(\d{4}-\d\d-\d\d)"\s+id="contribution-day-component-(\d+)-(\d+)"\s+data-level="(\d)"', page
    )
    if not cells:
        raise RuntimeError("kalender kontribusi tidak ditemukan")
    days = [(d, int(r), int(c), int(l)) for d, r, c, l in cells]
    m = re.search(r"([\d,]+)\s+contributions?\s+in the last year", page)
    total = int(m.group(1).replace(",", "")) if m else sum(1 for d in days if d[3] > 0)
    return days, total


def streaks(days):
    flags = [d[3] > 0 for d in sorted(days)]
    best = run = 0
    for f in flags:
        run = run + 1 if f else 0
        best = max(best, run)
    tail = flags[:]
    if tail and not tail[-1]:
        tail = tail[:-1]  # hari ini belum ada kontribusi tidak memutus streak
    cur = 0
    for f in reversed(tail):
        if not f:
            break
        cur += 1
    return cur, best


def get_profile():
    u = json.loads(http_get(f"https://api.github.com/users/{USER}", api=True))
    repos = json.loads(http_get(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed", api=True))
    own = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in own)

    quest = None
    now = datetime.now(timezone.utc)
    for r in own:
        if r["name"].lower() == USER.lower():
            continue  # repo profil sendiri
        pushed = datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))
        if (now - pushed).days <= QUEST_MAX_AGE_DAYS:
            quest = r["name"]
        break  # repo non-profil paling baru; kalau sudah lama -> fallback

    langs = {}
    for r in [x for x in own if x["name"].lower() != USER.lower()][:25]:
        try:
            data = json.loads(http_get(r["languages_url"], api=True))
        except Exception:  # noqa: BLE001
            continue
        for k, v in data.items():
            langs[k] = langs.get(k, 0) + v
    return {
        "repos": u.get("public_repos", len(own)),
        "followers": u.get("followers", 0),
        "stars": stars,
        "quest": quest,
        "langs": langs,
    }


def clean_quest(name):
    name = (name or QUEST_FALLBACK).replace("-", " ").replace("_", " ").upper().strip()
    return name[:20]


# ───────────────────────── banner ─────────────────────────
def make_banner(score, coins, quest):
    W, H, G = 900, 240, 196
    stars = []
    star_positions = [
        (30, 48), (85, 90), (140, 40), (220, 75), (280, 50),
        (350, 85), (410, 45), (480, 68), (520, 38), (620, 60),
        (680, 42), (720, 80), (810, 52), (870, 70), (190, 110),
        (380, 115), (750, 110), (840, 120), (50, 140), (460, 130)
    ]
    for i, (sx, sy) in enumerate(star_positions):
        delay = (i * 0.35) % 2.5
        stars.append(f'<rect class="star-twinkle" style="animation-delay:{delay:.1f}s" x="{sx}" y="{sy}" width="3" height="3" fill="{GOLD_L}"/>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Pixel art astronaut banner: Andika Dwi Putra">
<defs>
  <linearGradient id="space" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{DEEP}"/>
    <stop offset="55%" stop-color="{NAVY}"/>
    <stop offset="100%" stop-color="{BLUE}"/>
  </linearGradient>
</defs>
<style>
  {FONT}
  .hero  {{ animation: zero_g_jump 3.2s ease-in-out infinite; }}
  .block {{ animation: bump 3.2s ease-in-out infinite; }}
  .gem   {{ animation: star_pop 3.2s ease-out infinite; opacity: 0; }}
  .rover {{ animation: walk 8s linear infinite alternate; }}
  .sat1  {{ animation: orbit 14s linear infinite; }}
  .star-bob {{ animation: bob 1.8s ease-in-out infinite alternate; }}
  .star-twinkle {{ animation: twinkle 2s ease-in-out infinite alternate; }}
  .blink {{ animation: blink 1.1s steps(1) infinite; }}
  @keyframes zero_g_jump {{
    0%,15% {{ transform: translateY(0); }}
    32% {{ transform: translateY(-38px) rotate(-3deg); }}
    48% {{ transform: translateY(-32px) rotate(2deg); }}
    68%,100% {{ transform: translateY(0) rotate(0deg); }}
  }}
  @keyframes bump {{
    0%,29% {{ transform: translateY(0); }}
    33% {{ transform: translateY(-8px); }}
    40%,100% {{ transform: translateY(0); }}
  }}
  @keyframes star_pop {{
    0%,30% {{ opacity: 0; transform: translateY(0) scale(0.6); }}
    33% {{ opacity: 1; transform: translateY(0) scale(1); }}
    60% {{ opacity: 1; transform: translateY(-44px) scale(1.1); }}
    70%,100% {{ opacity: 0; transform: translateY(-54px) scale(0.8); }}
  }}
  @keyframes walk {{ from {{ transform: translateX(0); }} to {{ transform: translateX(150px); }} }}
  @keyframes orbit {{ from {{ transform: translateX(0); }} to {{ transform: translateX(45px); }} }}
  @keyframes bob  {{ from {{ transform: translateY(0); }} to {{ transform: translateY(-6px); }} }}
  @keyframes twinkle {{ 0%,20% {{ opacity: 0.2; }} 50% {{ opacity: 1; }} 80%,100% {{ opacity: 0.9; }} }}
  @keyframes blink {{ 0%,50% {{ opacity: 1; }} 50.01%,100% {{ opacity: 0; }} }}
</style>
<rect width="{W}" height="{H}" fill="url(#space)"/>
{"".join(stars)}

<!-- Distant Planet Earth -->
<g opacity="0.85" transform="translate(730,42)"><g>{PLANET}</g></g>

<!-- Orbiting Satellite -->
<g class="sat1" opacity="0.65" transform="translate(260,40)"><g>{SATELLITE}</g></g>

<!-- Lunar Horizons -->
{moon_hills(480, 5, 290, 22, 14, G, NAVY)}
{moon_hills(40, 4, 210, 20, 14, G, NAVY)}

<!-- Top Astronaut HUD Bar -->
<rect width="{W}" height="34" fill="{DEEP}" opacity="0.75"/>
<text x="20" y="22" font-size="13" fill="#FFFFFF" letter-spacing="2">AKID [ASTRONAUT]</text>
<text x="220" y="22" font-size="13" fill="{GOLD}" letter-spacing="2">STARS FOUND: {score:06d}</text>
<text x="500" y="22" font-size="13" fill="{SKY3}" letter-spacing="2">SECTORS: x{coins:02d}</text>
<text x="880" y="22" text-anchor="end" font-size="13" fill="{GOLD}" letter-spacing="2">MISSION: {esc(quest)}</text>

<!-- Title & Subtitle -->
<text x="563" y="103" text-anchor="middle" font-size="36" fill="{DEEP}" letter-spacing="3">ANDIKA DWI PUTRA</text>
<text x="560" y="100" text-anchor="middle" font-size="36" fill="#FFFFFF" letter-spacing="3">ANDIKA DWI PUTRA</text>
<text x="560" y="132" text-anchor="middle" font-size="15" fill="{SKY3}" letter-spacing="4">SPACE EXPLORER • CS STUDENT</text>
<text class="blink" x="560" y="166" text-anchor="middle" font-size="14" fill="{GOLD}" letter-spacing="3">&gt; INITIATE MISSION</text>

<!-- Cosmic Beacon / Discovery Pod -->
<rect x="110" y="52" width="48" height="48" fill="{NAVY}" stroke="{SKY3}" stroke-width="3"/>
<rect x="206" y="52" width="48" height="48" fill="{NAVY}" stroke="{SKY3}" stroke-width="3"/>
<path d="M110 76H158M134 52V76M206 76H254M230 52V76M110 100V76" stroke="{SKY3}" stroke-width="2" opacity="0.5" fill="none"/>
<g class="block">
  <rect x="158" y="52" width="48" height="48" fill="{BLUE}" stroke="{SKY3}" stroke-width="3"/>
  <text x="182" y="84" text-anchor="middle" font-size="22" fill="#FFFFFF">{{}}</text>
</g>
<g class="gem"><g transform="translate(160,20)">{STAR_BIG}</g></g>

<!-- Pixel Astronaut Hero -->
<g class="hero"><g transform="translate(145,{G-75})">{HERO}</g></g>

<!-- Lunar Rover Patrolling -->
<g class="rover"><g transform="translate(590,{G-32})">{ROVER}</g></g>

<!-- Floating Collectible Stars -->
<g class="star-bob"><g transform="translate(300,146)">{STAR_MINI}</g></g>
<g class="star-bob" style="animation-delay:.3s"><g transform="translate(335,138)">{STAR_MINI}</g></g>
<g class="star-bob" style="animation-delay:.6s"><g transform="translate(370,146)">{STAR_MINI}</g></g>

<!-- Lunar Mission Flag -->
<rect x="856" y="96" width="4" height="100" fill="{SLATE}"/>
<rect x="853" y="88" width="10" height="10" fill="{GOLD}"/>
<g transform="translate(824,102)">{FLAG}</g>
<rect x="846" y="184" width="24" height="12" fill="{NAVY}" stroke="{SKY3}" stroke-width="2"/>

<!-- Lunar Ground -->
{moon_tiles(W, G)}
</svg>
'''


# ───────────────────────── stats ─────────────────────────
def card(x, y, w, h, title, icon=""):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NAVY}"/>'
        f'<rect x="{x+2}" y="{y+2}" width="{w-4}" height="{h-4}" fill="none" stroke="{BLUE}" stroke-width="4"/>'
        f'<rect x="{x+8}" y="{y+8}" width="{w-16}" height="{h-16}" fill="none" stroke="{SKY3}" stroke-width="1" opacity="0.35"/>'
        f'<g transform="translate({x+20},{y+20})">{icon}</g>'
        f'<text x="{x+54}" y="{y+38}" font-size="16" fill="#FFFFFF" letter-spacing="3">{title}</text>'
    )


def make_stats(total, cur, best, prof):
    W, H = 900, 240
    rows = [
        ("STARS DISCOVERED (1Y)", f"{total}"),
        ("DISCOVERED REPOS", f"{prof['repos']}"),
        ("STARGAZERS", f"{prof['stars']}"),
        ("SPACE CREW", f"{prof['followers']}"),
        ("EXPEDITION STREAK", f"{cur}/{best} DAYS"),
    ]
    left = card(10, 10, 430, 220, "ASTRONAUT LOG", STAR_MINI)
    for i, (k, v) in enumerate(rows):
        y = 84 + i * 28
        left += f'<text x="34" y="{y}" font-size="14" fill="{SKY3}" letter-spacing="1">{k}</text>'
        left += f'<text x="416" y="{y}" text-anchor="end" font-size="15" fill="#FFFFFF">{v}</text>'
        left += f'<path d="M34 {y+8}H416" stroke="{BLUE}" stroke-width="2" stroke-dasharray="4 4"/>'

    right = card(460, 10, 430, 220, "SYSTEM TELEMETRY", SATELLITE)
    langs = sorted(prof["langs"].items(), key=lambda kv: -kv[1])[:5]
    total_b = sum(prof["langs"].values()) or 1
    if not langs:
        right += f'<text x="484" y="110" font-size="14" fill="{SKY3}">NO DATA YET</text>'
    for i, (name, b) in enumerate(langs):
        y = 84 + i * 28
        pct = b * 100 / total_b
        filled = max(1, round(pct / 100 * 12))
        right += f'<text x="484" y="{y}" font-size="14" fill="#FFFFFF">{esc(name[:11].upper())}</text>'
        for s in range(12):
            color = SKY2 if s < filled else DEEP
            right += f'<rect x="{600+s*16}" y="{y-12}" width="13" height="14" fill="{color}" stroke="{BLUE}" stroke-width="1"/>'
        right += f'<text x="870" y="{y}" text-anchor="end" font-size="14" fill="{SKY3}">{pct:.0f}%</text>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Astronaut log and system telemetry">
<style>{FONT}</style>
{left}
{right}
</svg>
'''


# ───────────────────────── contribution game ─────────────────────────
LEVEL_FILL = {1: BLUE, 2: SKY1, 3: SKY2, 4: SKY3}


def grade_for(total):
    for limit, g in ((1000, "S"), (600, "A"), (300, "B"), (100, "C")):
        if total >= limit:
            return g
    return "D"


def make_game(days, total, best):
    """Satu putaran: astronot meluncurkan probe -> konstelasi bintang meledak berantai -> layar hasil ekspedisi."""
    W, H, G, T = 900, 300, 262, 22
    cols = max(d[2] for d in days) + 1
    pitch, size, gx = 15, 13, 24
    by_col = {c: sorted([l for (_, _, cc, l) in days if cc == c and l > 0], reverse=True) for c in range(cols)}
    n = [len(by_col[c]) for c in range(cols)]
    top = lambda c: G - n[c] * pitch
    active = [c for c in range(cols) if n[c] > 0]
    nblocks = sum(n)

    # titik tumbukan = kolom aktif terdekat dengan pusat massa
    if active:
        wsum = sum(n[c] for c in active)
        mid = sum((gx + c * pitch + size / 2) * n[c] for c in active) / wsum
        ic = min(active, key=lambda c: abs(gx + c * pitch + size / 2 - mid))
        ix, iy = gx + ic * pitch + size / 2, top(ic) + 10
    else:
        ix, iy = W / 2, G - 10

    seed = [20261101]

    def rnd():
        seed[0] = (seed[0] * 1103515245 + 12345) & 0x7FFFFFFF
        return seed[0] / 0x7FFFFFFF

    # ── timeline (persen dari T) ──
    T_THROW, T_HIT = 8.0, 18.0
    NB = 10                       # jumlah "gelombang" supernova
    WAVE0, WAVE_STEP = T_HIT, 0.8

    def kf(name, body):
        return "@keyframes %s{%s}" % (name, body)

    css = []
    for k in range(NB):
        e = WAVE0 + k * WAVE_STEP
        css.append(kf(f"bm{k}",
            f"0%,{e:.1f}%{{transform:translate(0,0) rotate(0deg);opacity:1}}"
            f"{e+2.5:.1f}%{{transform:translate(var(--hx),var(--hy)) rotate(var(--hr));opacity:1}}"
            f"{e+8:.1f}%,97%{{transform:translate(var(--dx),var(--dy)) rotate(var(--dr));opacity:0}}"
            f"100%{{transform:translate(0,0) rotate(0deg);opacity:1}}"))

    dmax = 1.0
    cells = []
    for c in active:
        for i, lvl in enumerate(by_col[c]):
            bx, by = gx + c * pitch, top(c) + i * pitch
            cells.append((c, i, lvl, bx, by, math.hypot(bx + size / 2 - ix, by + size / 2 - iy)))
    if cells:
        dmax = max(max(x[5] for x in cells), 1.0)

    blocks, stars_top = [], []
    for c, i, lvl, bx, by, dist in cells:
        k = min(NB - 1, int(dist / dmax * NB))
        ux, uy = (bx + size / 2 - ix) / max(dist, 1), (by + size / 2 - iy) / max(dist, 1)
        sp = 40 + rnd() * 90
        v = (f"--hx:{ux*sp*0.5:.0f}px;--hy:{uy*sp*0.5-30:.0f}px;--dx:{ux*sp*1.1+(rnd()-.5)*20:.0f}px;"
             f"--dy:{G-by+40+rnd()*30:.0f}px;--hr:{(rnd()-.5)*240:.0f}deg;--dr:{(rnd()-.5)*720:.0f}deg")
        blocks.append(
            f'<g class="b" style="{v};animation:bm{k} {T}s linear infinite">'
            f'<rect x="{bx}" y="{by}" width="{size}" height="{size}" fill="{LEVEL_FILL[lvl]}"/>'
            f'<rect x="{bx+2}" y="{by+2}" width="3" height="3" fill="#FFFFFF" opacity="0.6"/>'
            + (f'<rect x="{bx}" y="{by}" width="{size}" height="2" fill="{GOLD_L}" opacity="0.85"/>' if i == 0 else "")
            + "</g>")
    for c in active:
        cx = gx + c * pitch + size / 2
        d = math.hypot(cx - ix, top(c) - 20 - iy)
        k = min(NB - 1, int(d / dmax * NB))
        ux = (cx - ix) / max(d, 1)
        v = f"--hx:{ux*10:.0f}px;--hy:-26px;--dx:{ux*24:.0f}px;--dy:-72px;--hr:0deg;--dr:0deg"
        stars_top.append(
            f'<g class="b" style="{v};animation:bm{k} {T}s linear infinite">'
            f'<g transform="translate({cx-7:.1f},{top(c)-24})">{STAR_TINY}</g></g>')

    # ── peluncuran probe (parabola kosmik) ──
    xs, ys, xe, ye = 60 + 36, G - 38, ix, iy - 6
    arc = 130
    fly = [f"0%,{T_THROW-0.1:.1f}%{{opacity:0;transform:translate({xs}px,{ys}px)}}"]
    for j in range(15):
        t = j / 14
        x = xs + (xe - xs) * t
        y = ys + (ye - ys) * t - 4 * arc * t * (1 - t)
        fly.append(f"{T_THROW + (T_HIT - T_THROW) * t:.2f}%{{opacity:1;transform:translate({x:.1f}px,{y:.1f}px)}}")
    fly.append(f"{T_HIT+0.05:.2f}%,100%{{opacity:0;transform:translate({xe:.1f}px,{ye:.1f}px)}}")
    css.append(kf("fly", "".join(fly)))

    # ── astronot, supernova flash, status ──
    css.append(kf("hero",
        "0%,5%{transform:translate(0,0)}7%{transform:translate(-5px,0)}9%{transform:translate(6px,0)}"
        "11%,24%{transform:translate(0,0)}26.5%{transform:translate(0,-14px)}29%{transform:translate(0,0)}"
        "31.5%{transform:translate(0,-14px)}34%,100%{transform:translate(0,0)}"))
    css.append(kf("spin", "to{transform:rotate(720deg)}"))
    css.append(kf("shake",
        f"0%,{T_HIT}%{{transform:translate(0,0)}}{T_HIT+0.4}%{{transform:translate(-4px,3px)}}"
        f"{T_HIT+0.8}%{{transform:translate(4px,-3px)}}{T_HIT+1.2}%{{transform:translate(-3px,-2px)}}"
        f"{T_HIT+1.6}%{{transform:translate(3px,2px)}}{T_HIT+2.2}%,100%{{transform:translate(0,0)}}"))
    css.append(kf("flash", f"0%,{T_HIT}%{{opacity:0;transform:scale(.2)}}{T_HIT+0.3}%{{opacity:1;transform:scale(.7)}}"
                           f"{T_HIT+2.5}%,100%{{opacity:0;transform:scale(2.4)}}"))
    css.append(kf("ring1", f"0%,{T_HIT}%{{opacity:0;transform:scale(.2)}}{T_HIT+0.3}%{{opacity:1;transform:scale(.4)}}"
                           f"{T_HIT+9}%,100%{{opacity:0;transform:scale(5)}}"))
    css.append(kf("ring2", f"0%,{T_HIT+1}%{{opacity:0;transform:scale(.2)}}{T_HIT+1.4}%{{opacity:1;transform:scale(.4)}}"
                           f"{T_HIT+11}%,100%{{opacity:0;transform:scale(4)}}"))
    css.append(kf("spark", f"0%,{T_HIT}%{{opacity:0;transform:translate(0,0)}}{T_HIT+0.2}%{{opacity:1;transform:translate(0,0)}}"
                           f"{T_HIT+7}%,100%{{opacity:0;transform:translate(var(--sx),var(--sy))}}"))

    def window(name, a, b):
        css.append(kf(name, f"0%,{a}%{{opacity:0}}{a+0.8}%,{b}%{{opacity:1}}{b+0.8}%,100%{{opacity:0}}"))

    window("s1", 0, 7.5)
    window("s2", 8, 17.5)
    window("s3", 18, 36)
    OV = 38
    css.append(kf("ov", f"0%,{OV}%{{opacity:0}}{OV+3}%,94%{{opacity:1}}98%,100%{{opacity:0}}"))
    css.append(kf("fadeA", "0%,41%{opacity:0}42.5%,94%{opacity:1}98%,100%{opacity:0}"))
    css.append(kf("fadeB", "0%,44%{opacity:0}45.5%,94%{opacity:1}98%,100%{opacity:0}"))
    css.append(kf("fadeC", "0%,47%{opacity:0}48.5%,94%{opacity:1}98%,100%{opacity:0}"))
    css.append(kf("fadeD", "0%,50%{opacity:0}51.5%,94%{opacity:1}98%,100%{opacity:0}"))
    css.append(kf("pop", "0%,73%{opacity:0;transform:scale(2.2)}75%{opacity:1;transform:scale(.88)}"
                         "77%,94%{opacity:1;transform:scale(1)}98%,100%{opacity:0;transform:scale(1)}"))

    # hitung-naik skor (jumlah bintang yang ditemukan)
    N, S0, S1 = 14, 56.0, 70.0
    layers = []
    for k in range(N + 1):
        v = round(total * (1 - (1 - k / N) ** 2))
        a = S0 + k * (S1 - S0) / N
        b = S0 + (k + 1) * (S1 - S0) / N if k < N else 94.0
        end = f"{b:.2f}%,100%{{opacity:0}}" if k < N else "94%{opacity:1}98%,100%{opacity:0}"
        css.append(kf(f"v{k}", f"0%,{a:.2f}%{{opacity:0}}{a+0.01:.2f}%,{b-0.01:.2f}%{{opacity:1}}" + end))
        layers.append(f'<text x="560" y="219" text-anchor="end" font-size="26" fill="{GOLD}" letter-spacing="2" '
                      f'style="opacity:0;animation:v{k} {T}s linear infinite">{v:06d}</text>')

    # percikan stardust
    sparks = []
    for j in range(12):
        ang = j / 12 * 2 * math.pi
        dist = 50 + rnd() * 70
        sparks.append(f'<rect x="{ix-3:.1f}" y="{iy-3:.1f}" width="6" height="6" fill="{GOLD if j%2 else "#FFFFFF"}" '
                      f'style="--sx:{math.cos(ang)*dist:.0f}px;--sy:{math.sin(ang)*dist-10:.0f}px;opacity:0;animation:spark {T}s linear infinite"/>')

    # bintang latar belakang
    stars = []
    for _ in range(40):
        sx = int(rnd() * W)
        sy = 42 + int(rnd() * 110)
        stars.append(f'<rect x="{sx}" y="{sy}" width="3" height="3" fill="{GOLD_L if rnd() > 0.6 else PALE}" opacity="0.45"/>')

    grade = grade_for(total)
    gcol = {"S": GOLD, "A": SKY3, "B": SKY2, "C": SKY1, "D": PALE}[grade]
    A = lambda cls, extra="": f'class="{cls}" style="opacity:0;animation:{cls} {T}s linear infinite{extra}"'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Contribution constellation as an astronaut mission game: launch a probe, ignite stars, discover your score">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{DEEP}"/>
    <stop offset="60%" stop-color="{NAVY}"/>
    <stop offset="100%" stop-color="{DEEP}"/>
  </linearGradient>
</defs>
<style>
  {FONT}
  .b, .spin, .fx, .grade {{ transform-box: fill-box; transform-origin: center; }}
  .scene {{ animation: shake {T}s linear infinite; }}
  .hero  {{ animation: hero {T}s linear infinite; }}
  .stone {{ opacity: 0; animation: fly {T}s linear infinite; }}
  .spin  {{ animation: spin 0.6s linear infinite; }}
  .flash {{ opacity: 0; animation: flash {T}s linear infinite; }}
  .ring1 {{ opacity: 0; animation: ring1 {T}s linear infinite; }}
  .ring2 {{ opacity: 0; animation: ring2 {T}s linear infinite; }}
  .cl1 {{ animation: drift 14s ease-in-out infinite alternate; }}
  .cl2 {{ animation: drift 18s ease-in-out infinite alternate-reverse; }}
  @keyframes drift {{ from {{ transform: translateX(0); }} to {{ transform: translateX(40px); }} }}
  {"".join(css)}
</style>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
{"".join(stars)}

<!-- Distant Orbiting Satellite & Planet -->
<g class="cl1" opacity="0.45" transform="translate(120,48)"><g>{SATELLITE}</g></g>
<g class="cl2" opacity="0.30" transform="translate(740,46)"><g>{PLANET}</g></g>

<!-- Lunar Horizons -->
{moon_hills(40, 4, 220, 20, 12, G, NAVY)}
{moon_hills(360, 5, 300, 20, 12, G, NAVY)}

<!-- Top HUD Bar -->
<rect width="{W}" height="34" fill="{DEEP}" opacity="0.75"/>
<text x="20" y="22" font-size="13" fill="#FFFFFF" letter-spacing="2">CONSTELLATION QUEST</text>
<text x="880" y="22" text-anchor="end" font-size="13" fill="{GOLD}" letter-spacing="2">TARGET: {nblocks} STAR CLUSTERS</text>

<g class="scene">
{"".join(blocks)}
{"".join(stars_top)}
<g transform="translate(60,{G-45})"><g class="hero">{HERO_S}</g></g>
<g class="stone"><g class="spin"><g transform="translate(-14,-12)">{PROBE}</g></g></g>
</g>

<!-- Supernova Blast Effects -->
<circle class="flash fx" cx="{ix:.1f}" cy="{iy:.1f}" r="30" fill="#FFFFFF"/>
<circle class="ring1 fx" cx="{ix:.1f}" cy="{iy:.1f}" r="30" fill="none" stroke="{SKY3}" stroke-width="5"/>
<circle class="ring2 fx" cx="{ix:.1f}" cy="{iy:.1f}" r="30" fill="none" stroke="{GOLD}" stroke-width="4"/>
{"".join(sparks)}

<!-- Lunar Surface Base -->
{moon_tiles(W, G, rows=1)}
<text style="opacity:0;animation:s1 {T}s linear infinite" x="20" y="287" font-size="11" fill="{GOLD}" letter-spacing="2">SCANNING DEEP SPACE...</text>
<text style="opacity:0;animation:s2 {T}s linear infinite" x="20" y="287" font-size="11" fill="{GOLD}" letter-spacing="2">LAUNCHING PROBE!</text>
<text style="opacity:0;animation:s3 {T}s linear infinite" x="20" y="287" font-size="11" fill="{GOLD}" letter-spacing="2">STARBURST DISCOVERED!</text>

<!-- Result Overlay Screen -->
<g style="opacity:0;animation:ov {T}s linear infinite">
  <rect width="{W}" height="{H}" fill="{DEEP}" opacity="0.84"/>
  <rect x="230" y="46" width="440" height="206" fill="{NAVY}"/>
  <rect x="232" y="48" width="436" height="202" fill="none" stroke="{BLUE}" stroke-width="4"/>
  <rect x="238" y="54" width="424" height="190" fill="none" stroke="{SKY3}" stroke-width="1" opacity="0.35"/>
</g>
<text {A("fadeA")} x="450" y="86" text-anchor="middle" font-size="24" fill="{GOLD}" letter-spacing="6">EXPEDITION RESULT</text>
<g {A("fadeB")}>
  <text x="256" y="120" font-size="14" fill="{SKY3}" letter-spacing="1">STARS DISCOVERED</text>
  <text x="644" y="120" text-anchor="end" font-size="15" fill="#FFFFFF">{total}</text>
</g>
<g {A("fadeC")}>
  <text x="256" y="146" font-size="14" fill="{SKY3}" letter-spacing="1">STAR NODES CHARTED</text>
  <text x="644" y="146" text-anchor="end" font-size="15" fill="#FFFFFF">{nblocks}</text>
</g>
<g {A("fadeD")}>
  <text x="256" y="172" font-size="14" fill="{SKY3}" letter-spacing="1">LONGEST EXPEDITION</text>
  <text x="644" y="172" text-anchor="end" font-size="15" fill="#FFFFFF">{best} DAYS</text>
  <path d="M256 188H644" stroke="{BLUE}" stroke-width="3" stroke-dasharray="6 4"/>
  <text x="256" y="219" font-size="16" fill="#FFFFFF" letter-spacing="3">SCORE</text>
</g>
{"".join(layers)}
<g class="grade" style="opacity:0;animation:pop {T}s linear infinite">
  <rect x="590" y="198" width="54" height="40" fill="{DEEP}" stroke="{gcol}" stroke-width="3"/>
  <text x="617" y="228" text-anchor="middle" font-size="30" fill="{gcol}">{grade}</text>
</g>
</svg>
'''


# ───────────────────────── main ─────────────────────────
def main():
    OUT.mkdir(parents=True, exist_ok=True)

    contrib = safe(get_contributions, None, "kontribusi")
    prof = safe(get_profile, None, "profil/API")
    if prof is None:
        prof = {"repos": 0, "followers": 0, "stars": 0, "quest": None, "langs": {}}

    if contrib:
        days, total = contrib
        cur, best = streaks(days)
        (OUT / "contrib-game.svg").write_text(make_game(days, total, best), encoding="utf-8")
    else:
        total, cur, best = 0, 0, 0

    (OUT / "banner.svg").write_text(make_banner(total, prof["repos"], clean_quest(prof["quest"])), encoding="utf-8")
    (OUT / "stats.svg").write_text(make_stats(total, cur, best, prof), encoding="utf-8")
    print(f"ok: score={total} repos={prof['repos']} quest={clean_quest(prof['quest'])}")


if __name__ == "__main__":
    main()

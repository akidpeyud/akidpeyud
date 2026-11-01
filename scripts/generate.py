#!/usr/bin/env python3
"""
Generator aset pixel-art untuk profil GitHub: Stellar Explorer (Penjelajah Bintang).
Menghasilkan 3 file SVG di folder assets/:
  - banner.svg        : Astronot terbang bebas (zero-G 2D gliding) & terminal identifikasi kosmik
  - stats.svg         : Logbook navigasi antariksa & telemetri sistem
  - contrib-game.svg  : Astronot berjalan menuju rasi bintang besar & mengungkap bintang yang ditemukan

Hanya memakai pustaka standar Python.
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

# ── Color Palette: 2 warna utama (#1B365D & #005A9C) dipertahankan ──
NAVY, BLUE = "#1B365D", "#005A9C"

# ── Palette Astronaut & Deep Cosmos ──
DEEP = "#070D18"
SPACE_MID = "#0D1829"
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
    headers = {"User-Agent": "Mozilla/5.0 (stellar-profile-generator)"}
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
# Upper body template (16x11)
ASTRONAUT_UPPER = [
    "...WWWWWW.......",
    "..WWWWWWWW......",
    ".WWVVVVVVOOW....",
    ".WWLVVVVVOOW....",
    ".WWVVVVVVOOW....",
    "..WWWWWWWW......",
    "BBWWWWWWWWWW....",
    "BBWRBWWWWWWWW...",
    "BBWWWWWWWW.WW...",
    ".BBDDDDDD...C...",
    "..WWWWWWWW......",
]

# Spacewalk / Flying Frame (zero-G legs floating)
ASTRONAUT_FLY_GRID = ASTRONAUT_UPPER + [
    "..WWWW..WWWW....",
    "..WWW....WWW....",
    "..SSS....SSS....",
    ".DDDD....DDDD...",
    "................",
]

# Walking Frame A (Left foot forward, right foot back)
ASTRONAUT_WALK_A_GRID = ASTRONAUT_UPPER + [
    "..WWWW..WW......",
    ".WWWW....WW.....",
    ".SSSS....SS.....",
    "DDDDD....DDDD...",
    "................",
]

# Walking Frame B (Right foot forward, left foot back)
ASTRONAUT_WALK_B_GRID = ASTRONAUT_UPPER + [
    "....WW..WWWW....",
    "....WW....WWWW..",
    "....SS....SSSS..",
    "...DDDD....DDDDD",
    "................",
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
    "C": CYAN,
}

HERO_FLY = sprite(ASTRONAUT_FLY_GRID, ASTRONAUT_COLORS, 4)
HERO_WALK_A = sprite(ASTRONAUT_WALK_A_GRID, ASTRONAUT_COLORS, 3)
HERO_WALK_B = sprite(ASTRONAUT_WALK_B_GRID, ASTRONAUT_COLORS, 3)

# Ringed Exoplanet (22x12)
RINGED_PLANET_GRID = [
    ".........BBBB.........",
    ".......BBAAAABBB......",
    ".....BBAAAAAAAABBB....",
    "....BBAAAAAAAAAABBB...",
    "...BBAAAAAWAAAAAABBB..",
    "RRRRRRRRRRRRRRRRRRRRRR",
    "RRR..BBAAAAAAAABBB..RR",
    "....BBAAAAAAAAAABBB...",
    ".....BBAAAAAAAABBB....",
    ".......BBAAAABBB......",
    ".........BBBB.........",
    "......................",
]
PLANET_RINGED = sprite(RINGED_PLANET_GRID, {"B": BLUE, "A": NAVY, "W": SKY3, "R": GOLD}, 4)

# Deep Space Observatory Satellite (18x7)
TELESCOPE_GRID = [
    "..BBBB......BBBB..",
    "..BBBB......BBBB..",
    "DDDDDDWWWWWWDDDDDD",
    "DDDDDDWWCCWWDDDDDD",
    "DDDDDDWWWWWWDDDDDD",
    "..BBBB......BBBB..",
    "..BBBB......BBBB..",
]
TELESCOPE = sprite(TELESCOPE_GRID, {"B": BLUE, "W": SLATE, "D": GOLD, "C": CYAN}, 3)

# ── Bintang Berukuran Lebih Besar (Pixel Stars) ──
# 1. Super Beacon Star (15x15) - ukuran besar untuk bintang utama / tujuan
STAR_LARGE_GRID = [
    ".......X.......",
    ".......X.......",
    "......XXX......",
    ".....XXLXX.....",
    "....XXXXXXX....",
    "...XXXXXXXXX...",
    "..XXXXXXXXXXX..",
    "XXXXXXXXXXXXXXX",
    "..XXXXXXXXXXX..",
    "...XXXXXXXXX...",
    "....XXXXXXX....",
    ".....XXLXX.....",
    "......XXX......",
    ".......X.......",
    ".......X.......",
]
STAR_LARGE = sprite(STAR_LARGE_GRID, {"X": GOLD, "L": "#FFFDF0"}, 2)  # 30x30 px!

# 2. Medium Star (11x11)
STAR_MED_GRID = [
    ".....X.....",
    "....XXX....",
    "...XXLXX...",
    "..XXXXXXX..",
    ".XXXXXXXXX.",
    "XXXXXXXXXXX",
    ".XXXXXXXXX.",
    "..XXXXXXX..",
    "...XXLXX...",
    "....XXX....",
    ".....X.....",
]
STAR_MED_GOLD = sprite(STAR_MED_GRID, {"X": GOLD, "L": "#FFFDF0"}, 1.8)
STAR_MED_BLUE = sprite(STAR_MED_GRID, {"X": SKY2, "L": WHITE}, 1.8)

# 3. Bright Star (7x7)
STAR_BRIGHT_GRID = [
    "...X...",
    "..XXX..",
    ".XXLXX.",
    "XXXXXXX",
    ".XXLXX.",
    "..XXX..",
    "...X...",
]
STAR_BRIGHT_GOLD = sprite(STAR_BRIGHT_GRID, {"X": GOLD, "L": "#FFFDF0"}, 2)
STAR_BRIGHT_AZURE = sprite(STAR_BRIGHT_GRID, {"X": SKY1, "L": WHITE}, 2)

# 4. Standard Star (5x5)
STAR_SMALL_GRID = [
    "..X..",
    ".XLX.",
    "XXXXX",
    ".XLX.",
    "..X..",
]
STAR_SMALL_BLUE = sprite(STAR_SMALL_GRID, {"X": BLUE, "L": SKY3}, 2)
STAR_SMALL_GOLD = sprite(STAR_SMALL_GRID, {"X": GOLD, "L": GOLD_L}, 2)


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
        tail = tail[:-1]
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
            continue
        pushed = datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))
        if (now - pushed).days <= QUEST_MAX_AGE_DAYS:
            quest = r["name"]
        break

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
    W, H = 900, 240

    # Latar bintang kosmik berkerlap-kerlip teratur
    stars = []
    positions = [
        (40, 50, 2), (90, 85, 2), (150, 45, 3), (210, 80, 2), (270, 52, 2),
        (330, 75, 1), (390, 48, 2), (450, 82, 3), (510, 50, 2), (570, 78, 1),
        (630, 45, 2), (690, 80, 3), (750, 55, 2), (810, 70, 1), (860, 48, 2),
        (50, 160, 2), (100, 195, 3), (160, 170, 1), (220, 205, 2), (280, 175, 2),
        (340, 210, 3), (400, 180, 1), (460, 200, 2), (520, 170, 3), (580, 210, 1),
        (640, 180, 2), (700, 205, 3), (760, 175, 1), (820, 200, 2), (870, 170, 3),
    ]
    for i, (sx, sy, sz) in enumerate(positions):
        delay = (i * 0.24) % 2.6
        col = GOLD_L if i % 4 == 0 else (SKY3 if i % 3 == 0 else WHITE)
        stars.append(f'<rect class="twinkle" style="animation-delay:{delay:.2f}s" x="{sx}" y="{sy}" width="{sz}" height="{sz}" fill="{col}"/>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Stellar Explorer Banner: Andika Dwi Putra">
<defs>
  <linearGradient id="cosmos_bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{DEEP}"/>
    <stop offset="40%" stop-color="{SPACE_MID}"/>
    <stop offset="70%" stop-color="{NAVY}"/>
    <stop offset="100%" stop-color="{DEEP}"/>
  </linearGradient>
  <radialGradient id="beacon_glow" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="{GOLD}" stop-opacity="0.45"/>
    <stop offset="60%" stop-color="{BLUE}" stop-opacity="0.2"/>
    <stop offset="100%" stop-color="{DEEP}" stop-opacity="0"/>
  </radialGradient>
</defs>
<style>
  {FONT}
  /* Animasi terbang 2D organik dan dinamis (bukan hanya atas-bawah) */
  .spacewalk-2d {{
    animation: flight_path_2d 7.5s ease-in-out infinite;
  }}
  .thruster {{
    animation: rcs_pulse 7.5s ease-in-out infinite;
  }}
  .beacon-star {{
    animation: pulse_star 2.8s ease-in-out infinite alternate;
  }}
  .twinkle {{
    animation: twinkle 2.2s ease-in-out infinite alternate;
  }}
  .meteor {{
    animation: shooting_star 8s ease-in infinite;
  }}
  .blink {{ animation: blink 1.1s steps(1) infinite; }}

  @keyframes flight_path_2d {{
    0%   {{ transform: translate(0px, 0px) rotate(0deg); }}
    22%  {{ transform: translate(24px, -18px) rotate(-6deg); }}
    45%  {{ transform: translate(44px, -6px) rotate(-1deg); }}
    68%  {{ transform: translate(30px, 14px) rotate(5deg); }}
    85%  {{ transform: translate(12px, 8px) rotate(2deg); }}
    100% {{ transform: translate(0px, 0px) rotate(0deg); }}
  }}

  @keyframes rcs_pulse {{
    0%, 15%  {{ opacity: 0; transform: scale(0.6); }}
    20%, 35% {{ opacity: 1; transform: scale(1.3); }}
    40%, 100%{{ opacity: 0; transform: scale(0.6); }}
  }}

  @keyframes pulse_star {{
    0%   {{ transform: scale(1); opacity: 0.88; }}
    100% {{ transform: scale(1.15); opacity: 1; }}
  }}

  @keyframes twinkle {{
    0%, 20%  {{ opacity: 0.25; }}
    50%      {{ opacity: 1; }}
    80%, 100%{{ opacity: 0.35; }}
  }}

  @keyframes shooting_star {{
    0%, 65%  {{ transform: translate(0, 0); opacity: 0; }}
    66%      {{ opacity: 1; }}
    78%      {{ transform: translate(-200px, 110px); opacity: 0; }}
    100%     {{ opacity: 0; }}
  }}

  @keyframes blink {{ 0%, 50% {{ opacity: 1; }} 50.01%, 100% {{ opacity: 0; }} }}
</style>

<!-- Deep Cosmos Background -->
<rect width="{W}" height="{H}" fill="url(#cosmos_bg)"/>

<!-- Outer Pixel Sci-Fi Frame -->
<rect x="2" y="2" width="{W-4}" height="{H-4}" fill="none" stroke="{NAVY}" stroke-width="2"/>
<rect x="6" y="6" width="{W-12}" height="{H-12}" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.45"/>
<!-- Corner Brackets -->
<path d="M2 18V2H18M{W-18} 2H{W-2}V18M2 {H-18}V{H-2}H18M{W-18} {H-2}H{W-2}V{H-18}" stroke="{SKY3}" stroke-width="2" fill="none"/>

<!-- Twinkling Background Stars -->
{"".join(stars)}

<!-- Shooting Star / Meteor -->
<g class="meteor" transform="translate(850, 24)">
  <line x1="0" y1="0" x2="36" y2="-18" stroke="{GOLD_L}" stroke-width="2" opacity="0.85"/>
  <rect x="0" y="0" width="3" height="3" fill="#FFFFFF"/>
</g>

<!-- Distant Ringed Exoplanet (Top Right) -->
<g opacity="0.8" transform="translate(740, 42)"><g>{PLANET_RINGED}</g></g>

<!-- Top Sci-Fi Navigation HUD -->
<rect x="8" y="8" width="{W-16}" height="30" fill="{DEEP}" opacity="0.9"/>
<line x1="8" y1="38" x2="{W-8}" y2="38" stroke="{BLUE}" stroke-width="1"/>
<text x="24" y="28" font-size="12" fill="{SKY3}" letter-spacing="2">[ PILOT // AKID ]</text>
<text x="220" y="28" font-size="12" fill="{GOLD}" letter-spacing="2">★ STARS DISCOVERED: {score:06d}</text>
<text x="540" y="28" font-size="12" fill="{SKY3}" letter-spacing="2">SYSTEMS: x{coins:02d}</text>
<text x="876" y="28" text-anchor="end" font-size="12" fill="{GOLD}" letter-spacing="2">MISSION: {esc(quest)}</text>

<!-- Primary Pulsing Beacon Star ahead of Astronaut -->
<g transform="translate(240, 115)">
  <circle cx="15" cy="15" r="32" fill="url(#beacon_glow)"/>
  <g class="beacon-star" style="transform-origin: 15px 15px;">{STAR_LARGE}</g>
  <!-- Constellation guide line -->
  <line x1="-50" y1="15" x2="0" y2="15" stroke="{CYAN}" stroke-width="1" stroke-dasharray="3 3" opacity="0.6"/>
</g>

<!-- Spacewalking Astronaut in Dynamic 2D Gliding Flight -->
<g class="spacewalk-2d" transform="translate(90, 110)">
  <!-- Tether Cable connecting to starship -->
  <path d="M-75 35 C -40 10, -15 50, 6 30" fill="none" stroke="{SKY1}" stroke-width="2" opacity="0.5"/>
  <rect x="-80" y="33" width="6" height="6" fill="{BLUE}"/>
  
  <!-- RCS Jetpack Thruster Flame Puff -->
  <g class="thruster" transform="translate(-10, 24)">
    <polygon points="0,6 -8,3 -8,9" fill="{CYAN}"/>
    <polygon points="0,6 -5,4 -5,8" fill="#FFFFFF"/>
  </g>
  
  <!-- Main Astronaut Sprite -->
  <g>{HERO_FLY}</g>
  
  <!-- Star Scanner Cone Beam pointing toward Beacon Star -->
  <polygon points="66,36 140,20 140,52" fill="{CYAN}" opacity="0.14"/>
  <line x1="66" y1="36" x2="140" y2="36" stroke="{CYAN}" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.75"/>
</g>

<!-- Right Side: Identification Terminal Card -->
<g transform="translate(430, 54)">
  <rect width="445" height="156" fill="{DEEP}" opacity="0.88"/>
  <rect x="2" y="2" width="441" height="152" fill="none" stroke="{NAVY}" stroke-width="2"/>
  <rect x="6" y="6" width="433" height="144" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.5"/>
  
  <!-- Terminal Header -->
  <rect x="14" y="14" width="220" height="18" fill="{NAVY}"/>
  <text x="20" y="27" font-size="10" fill="{CYAN}" letter-spacing="2">STELLAR CARTOGRAPHER // CLASS S</text>

  <!-- Name -->
  <text x="16" y="65" font-size="28" fill="{DEEP}" letter-spacing="3">ANDIKA DWI PUTRA</text>
  <text x="14" y="63" font-size="28" fill="#FFFFFF" letter-spacing="3">ANDIKA DWI PUTRA</text>

  <!-- Role Subtitle -->
  <text x="14" y="88" font-size="12" fill="{SKY3}" letter-spacing="3">WEB DEVELOPER • CS STUDENT • STAR EXPLORER</text>
  <line x1="14" y1="100" x2="430" y2="100" stroke="{BLUE}" stroke-width="1" stroke-dasharray="4 4" opacity="0.6"/>

  <!-- Status Telemetry Readout -->
  <text class="blink" x="14" y="122" font-size="12" fill="{GOLD}" letter-spacing="2">&gt; CHARTING THE DIGITAL UNIVERSE_</text>
  
  <!-- Telemetry Bar -->
  <text x="14" y="142" font-size="10" fill="{SKY1}" letter-spacing="1">SYS: ONLINE | RADAR: ACTIVE | PWR: 100%</text>
  <rect x="360" y="134" width="65" height="8" fill="{NAVY}"/>
  <rect x="362" y="136" width="55" height="4" fill="{SKY3}"/>
</g>

<!-- Bottom Technical Grid Line -->
<rect x="8" y="222" width="{W-16}" height="8" fill="{DEEP}"/>
<rect x="8" y="222" width="{W-16}" height="1" fill="{NAVY}"/>
<rect x="40" y="225" width="6" height="2" fill="{BLUE}"/>
<rect x="80" y="225" width="24" height="2" fill="{NAVY}"/>
<rect x="140" y="225" width="6" height="2" fill="{SKY3}"/>
<rect x="{W-160}" y="225" width="30" height="2" fill="{NAVY}"/>
<rect x="{W-100}" y="225" width="6" height="2" fill="{GOLD}"/>
<rect x="{W-60}" y="225" width="12" height="2" fill="{BLUE}"/>
</svg>
'''


# ───────────────────────── stats ─────────────────────────
def sci_fi_card(x, y, w, h, title, icon=""):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{DEEP}" opacity="0.92"/>'
        f'<rect x="{x+2}" y="{y+2}" width="{w-4}" height="{h-4}" fill="none" stroke="{NAVY}" stroke-width="2"/>'
        f'<rect x="{x+6}" y="{y+6}" width="{w-12}" height="{h-12}" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.55"/>'
        f'<path d="M{x+2} {y+16}V{y+2}H{x+16}" fill="none" stroke="{SKY3}" stroke-width="2"/>'
        f'<path d="M{x+w-16} {y+2}H{x+w-2}V{y+16}" fill="none" stroke="{SKY3}" stroke-width="2"/>'
        f'<path d="M{x+2} {y+h-16}V{y+h-2}H{x+16}" fill="none" stroke="{SKY3}" stroke-width="2"/>'
        f'<path d="M{x+w-16} {y+h-2}H{x+w-2}V{y+h-16}" fill="none" stroke="{SKY3}" stroke-width="2"/>'
        f'<g transform="translate({x+20},{y+16})">{icon}</g>'
        f'<text x="{x+54}" y="{y+34}" font-size="14" fill="#FFFFFF" letter-spacing="3">{title}</text>'
        f'<line x1="{x+18}" y1="{y+46}" x2="{x+w-18}" y2="{y+46}" stroke="{BLUE}" stroke-width="1.5" opacity="0.6"/>'
    )


def make_stats(total, cur, best, prof):
    W, H = 900, 240
    rows = [
        ("STARS DISCOVERED (1Y)", f"{total} ★"),
        ("CHARTED REPOSITORIES", f"{prof['repos']}"),
        ("STELLAR BEACONS (STARS)", f"{prof['stars']}"),
        ("EXPEDITION CREW", f"{prof['followers']}"),
        ("VOYAGE STREAK", f"{cur}/{best} DAYS"),
    ]
    left = sci_fi_card(10, 10, 430, 220, "STELLAR LOGBOOK", STAR_BRIGHT_GOLD)
    for i, (k, v) in enumerate(rows):
        y = 84 + i * 28
        left += f'<text x="32" y="{y}" font-size="13" fill="{SKY3}" letter-spacing="1">{k}</text>'
        left += f'<text x="414" y="{y}" text-anchor="end" font-size="14" fill="{GOLD if i==0 else "#FFFFFF"}">{v}</text>'
        left += f'<path d="M32 {y+8}H414" stroke="{NAVY}" stroke-width="1" stroke-dasharray="4 4"/>'

    right = sci_fi_card(460, 10, 430, 220, "MISSION TELEMETRY", TELESCOPE)
    langs = sorted(prof["langs"].items(), key=lambda kv: -kv[1])[:5]
    total_b = sum(prof["langs"].values()) or 1
    if not langs:
        right += f'<text x="484" y="110" font-size="13" fill="{SKY3}">NO DATA YET</text>'
    for i, (name, b) in enumerate(langs):
        y = 84 + i * 28
        pct = b * 100 / total_b
        filled = max(1, round(pct / 100 * 12))
        right += f'<text x="484" y="{y}" font-size="13" fill="#FFFFFF">{esc(name[:11].upper())}</text>'
        for s in range(12):
            color = SKY2 if s < filled else SPACE_MID
            right += f'<rect x="{600+s*16}" y="{y-12}" width="13" height="14" fill="{color}" stroke="{BLUE}" stroke-width="1"/>'
        right += f'<text x="870" y="{y}" text-anchor="end" font-size="13" fill="{SKY3}">{pct:.0f}%</text>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Stellar logbook and mission telemetry">
<style>{FONT}</style>
{left}
{right}
</svg>
'''


# ───────────────────────── contribution game ─────────────────────────
def grade_for(total):
    for limit, g in ((1000, "S"), (600, "A"), (300, "B"), (100, "C")):
        if total >= limit:
            return g
    return "D"


def make_game(days, total, best):
    """
    Stellar Expedition:
    Astronot berjalan ke arah rasi bintang berukuran besar dan menyulut starlight surge.
    """
    W, H = 900, 300
    T = 20  # Durasi siklus animasi dalam detik
    nblocks = sum(1 for d in days if d[3] > 0)

    # ── Penataan Bintang Berukuran Lebih Besar & Rapi ──
    # Menempatkan bintang-bintang di zona antariksa (x: 350-860, y: 55-195)
    # Dikelompokkan ke dalam 8 sektor rasi bintang terstruktur
    star_elements = []
    constellation_lines = []

    # Filter hari-hari aktif & sampel representatif untuk bintang besar
    active_days = [d for d in days if d[3] > 0]
    # Ambil sampel bintang dengan ukuran proporsional
    grid_coords = [
        (370, 70), (410, 115), (460, 65), (510, 105), (560, 75),
        (610, 120), (660, 60), (710, 100), (760, 70), (810, 115),
        (390, 160), (440, 185), (490, 150), (540, 190), (590, 155),
        (640, 185), (690, 145), (740, 180), (790, 150), (840, 185),
        (475, 125), (625, 95), (775, 130), (530, 140), (675, 165),
    ]

    for idx, (bx, by) in enumerate(grid_coords):
        # Tentukan level bintang berdasarkan kontribusi nyata
        lvl = (idx % 4) + 1
        if active_days:
            sample_d = active_days[idx % len(active_days)]
            lvl = sample_d[3]

        delay = (idx * 0.25) % 2.5
        if lvl == 4:
            star_elements.append(
                f'<g class="star-pulse" style="animation-delay:{delay:.2f}s" transform="translate({bx-11},{by-11})">'
                f'<circle cx="11" cy="11" r="14" fill="{GOLD}" opacity="0.25"/>'
                f'{STAR_MED_GOLD}</g>'
            )
        elif lvl == 3:
            star_elements.append(
                f'<g class="star-pulse" style="animation-delay:{delay:.2f}s" transform="translate({bx-11},{by-11})">'
                f'{STAR_MED_BLUE}</g>'
            )
        elif lvl == 2:
            star_elements.append(
                f'<g class="star-pulse" style="animation-delay:{delay:.2f}s" transform="translate({bx-7},{by-7})">'
                f'{STAR_BRIGHT_AZURE}</g>'
            )
        else:
            star_elements.append(
                f'<g class="star-pulse" style="animation-delay:{delay:.2f}s" transform="translate({bx-5},{by-5})">'
                f'{STAR_SMALL_BLUE}</g>'
            )

    # Garis-garis rasi bintang rapi yang menghubungkan bintang
    line_pairs = [
        ((370, 70), (410, 115)), ((410, 115), (460, 65)), ((460, 65), (510, 105)),
        ((510, 105), (560, 75)), ((560, 75), (610, 120)), ((610, 120), (660, 60)),
        ((660, 60), (710, 100)), ((710, 100), (760, 70)), ((760, 70), (810, 115)),
        ((390, 160), (440, 185)), ((440, 185), (490, 150)), ((490, 150), (540, 190)),
        ((540, 190), (590, 155)), ((590, 155), (640, 185)), ((640, 185), (690, 145)),
        ((410, 115), (475, 125)), ((475, 125), (510, 105)), ((560, 75), (625, 95)),
        ((625, 95), (660, 60)), ((690, 145), (740, 180)), ((740, 180), (775, 130)),
        ((775, 130), (810, 115)), ((590, 155), (675, 165)), ((675, 165), (690, 145)),
    ]
    for (p1, p2) in line_pairs:
        constellation_lines.append(
            f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" stroke="{BLUE}" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.6"/>'
        )

    # Bintang Super-Nova Utama di ujung jalur penjelajahan
    beacon_dest = f'''
    <g transform="translate(820, 140)">
      <circle cx="15" cy="15" r="34" fill="{GOLD}" opacity="0.22"/>
      <circle cx="15" cy="15" r="22" fill="{BLUE}" opacity="0.35"/>
      <g class="star-beacon" style="transform-origin: 15px 15px;">{STAR_LARGE}</g>
    </g>
    '''

    # CSS & Timeline Keyframes
    css = [
        # Astronot berjalan maju dari kiri (x=40) ke arah bintang (x=280)
        f"@keyframes astro_walk_forward {{"
        f"  0%   {{ transform: translateX(40px); }}"
        f"  36%  {{ transform: translateX(290px); }}"
        f"  65%  {{ transform: translateX(290px); }}"
        f"  90%  {{ transform: translateX(40px); }}"
        f"  100% {{ transform: translateX(40px); }}"
        f"}}",
        # Animasi langkah kaki bergantian
        "@keyframes step_cycle { 0%, 50% { opacity: 1; } 50.01%, 100% { opacity: 0; } }",
        # Sinar pemindai starlight
        "@keyframes scanner_flare {"
        "  0%, 34% { opacity: 0; transform: scaleX(0.2); }"
        "  38%, 62% { opacity: 0.95; transform: scaleX(1); }"
        "  66%, 100% { opacity: 0; transform: scaleX(0.2); }"
        "}",
        # Pendaran bintang
        "@keyframes star_glow {"
        "  0%, 100% { transform: scale(1); opacity: 0.8; }"
        "  50% { transform: scale(1.18); opacity: 1; }"
        "}",
        # Layar hasil ekspedisi
        f"@keyframes hud_report {{"
        f"  0%, 42% {{ opacity: 0; transform: translateY(12px); }}"
        f"  46%, 94% {{ opacity: 1; transform: translateY(0px); }}"
        f"  98%, 100% {{ opacity: 0; transform: translateY(-8px); }}"
        f"}}",
    ]

    def kf(name, body):
        return f"@keyframes {name}{{{body}}}"

    def win(name, a, b):
        css.append(kf(name, f"0%,{a}%{{opacity:0}}{a+0.5}%,{b}%{{opacity:1}}{b+0.5}%,100%{{opacity:0}}"))

    win("phase1", 0, 18)
    win("phase2", 19, 36)
    win("phase3", 37, 43)

    # Roll-up angka bintang
    N, S0, S1 = 12, 52.0, 68.0
    layers = []
    for k in range(N + 1):
        v = round(total * (1 - (1 - k / N) ** 2))
        a = S0 + k * (S1 - S0) / N
        b = S0 + (k + 1) * (S1 - S0) / N if k < N else 94.0
        end = f"{b:.2f}%,100%{{opacity:0}}" if k < N else "94%{opacity:1}98%,100%{opacity:0}"
        css.append(kf(f"rk{k}", f"0%,{a:.2f}%{{opacity:0}}{a+0.01:.2f}%,{b-0.01:.2f}%{{opacity:1}}" + end))
        layers.append(f'<text x="560" y="219" text-anchor="end" font-size="26" fill="{GOLD}" letter-spacing="2" '
                      f'style="opacity:0;animation:rk{k} {T}s linear infinite">{v:06d} ★</text>')

    grade = grade_for(total)
    gcol = {"S": GOLD, "A": SKY3, "B": SKY2, "C": SKY1, "D": PALE}[grade]

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Celestial Cartography: Astronaut walking towards discovered stars">
<defs>
  <linearGradient id="game_cosmos" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{DEEP}"/>
    <stop offset="55%" stop-color="{NAVY}"/>
    <stop offset="100%" stop-color="{DEEP}"/>
  </linearGradient>
  <linearGradient id="beam_glow" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{CYAN}" stop-opacity="0.9"/>
    <stop offset="70%" stop-color="{SKY2}" stop-opacity="0.4"/>
    <stop offset="100%" stop-color="{GOLD}" stop-opacity="0"/>
  </linearGradient>
</defs>
<style>
  {FONT}
  .walker-group {{
    animation: astro_walk_forward {T}s ease-in-out infinite;
  }}
  .step-a {{
    animation: step_cycle 0.4s steps(1) infinite;
  }}
  .step-b {{
    animation: step_cycle 0.4s steps(1) infinite reverse;
  }}
  .scan-flare {{
    animation: scanner_flare {T}s ease-in-out infinite;
    transform-origin: 0% 50%;
  }}
  .star-pulse {{
    animation: star_glow 2.6s ease-in-out infinite alternate;
  }}
  .star-beacon {{
    animation: star_glow 2s ease-in-out infinite alternate;
  }}
  .hud-panel {{
    animation: hud_report {T}s ease-in-out infinite;
  }}
  {"".join(css)}
</style>

<!-- Canvas Background -->
<rect width="{W}" height="{H}" fill="url(#game_cosmos)"/>

<!-- Outer Technical Frame -->
<rect x="2" y="2" width="{W-4}" height="{H-4}" fill="none" stroke="{NAVY}" stroke-width="2"/>
<rect x="6" y="6" width="{W-12}" height="{H-12}" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.5"/>
<path d="M2 16V2H16M{W-16} 2H{W-2}V16M2 {H-16}V{H-2}H16M{W-16} {H-2}H{W-2}V{H-16}" stroke="{SKY3}" stroke-width="2" fill="none"/>

<!-- Top Expedition HUD Bar -->
<rect x="8" y="8" width="{W-16}" height="30" fill="{DEEP}" opacity="0.92"/>
<line x1="8" y1="38" x2="{W-8}" y2="38" stroke="{BLUE}" stroke-width="1"/>
<text x="24" y="28" font-size="12" fill="{SKY3}" letter-spacing="2">[ STELLAR EXPEDITION // STARWAY ]</text>
<text x="876" y="28" text-anchor="end" font-size="12" fill="{GOLD}" letter-spacing="2">★ STARS DISCOVERED: {total} | NODES: {nblocks}</text>

<!-- Constellation Links connecting Stars -->
{"".join(constellation_lines)}

<!-- The Discovered Stars (Ukuran Lebih Besar dan Jelas) -->
{"".join(star_elements)}
{beacon_dest}

<!-- Luminous Celestial Pathway / Starlight Bridge where Astronaut Walks -->
<rect x="20" y="210" width="860" height="4" fill="{BLUE}"/>
<rect x="20" y="210" width="860" height="1" fill="{SKY3}"/>
<!-- Pathway tick marks -->
<path d="M40 214V218M100 214V218M160 214V218M220 214V218M280 214V218M340 214V218M400 214V218M460 214V218M520 214V218M580 214V218M640 214V218M700 214V218M760 214V218M820 214V218M860 214V218" stroke="{NAVY}" stroke-width="2"/>
<rect x="20" y="214" width="860" height="12" fill="{DEEP}" opacity="0.6"/>

<!-- Astronaut Walking Towards the Stars -->
<g class="walker-group" transform="translate(0, 162)">
  <!-- Navigation Tether -->
  <path d="M-40 25 C -20 15, -10 30, 4 20" fill="none" stroke="{SKY1}" stroke-width="1.5" opacity="0.5"/>
  <rect x="-44" y="23" width="5" height="5" fill="{BLUE}"/>

  <!-- Animated Walking Legs -->
  <g class="step-a">{HERO_WALK_A}</g>
  <g class="step-b">{HERO_WALK_B}</g>

  <!-- Scanner Starlight Discovery Projection (ignites when reaching stars) -->
  <g class="scan-flare" transform="translate(48, 24)">
    <polygon points="0,0 380,-75 380,75" fill="url(#beam_glow)"/>
    <line x1="0" y1="0" x2="380" y2="0" stroke="{WHITE}" stroke-width="1.5" stroke-dasharray="3 3"/>
  </g>
</g>

<!-- Dynamic Status Telemetry (Bottom) -->
<rect x="8" y="{H-32}" width="{W-16}" height="24" fill="{DEEP}" opacity="0.92"/>
<line x1="8" y1="{H-32}" x2="{W-8}" y2="{H-32}" stroke="{NAVY}" stroke-width="1"/>
<text style="opacity:0;animation:phase1 {T}s linear infinite" x="24" y="{H-16}" font-size="11" fill="{GOLD}" letter-spacing="2">&gt; PILOT WALKING TOWARDS UNCHARTED STAR CLUSTERS...</text>
<text style="opacity:0;animation:phase2 {T}s linear infinite" x="24" y="{H-16}" font-size="11" fill="{CYAN}" letter-spacing="2">&gt; STELLAR SCANNER ACTIVATED • ILLUMINATING DISCOVERED STARS...</text>
<text style="opacity:0;animation:phase3 {T}s linear infinite" x="24" y="{H-16}" font-size="11" fill="{SKY3}" letter-spacing="2">&gt; STELLAR HARMONY REACHED • {total} STARS SYNCHRONIZED</text>

<!-- Holographic Mission Result HUD Panel -->
<g class="hud-panel" style="opacity:0;">
  <rect width="{W}" height="{H}" fill="{DEEP}" opacity="0.88"/>
  <rect x="230" y="46" width="440" height="206" fill="{NAVY}"/>
  <rect x="232" y="48" width="436" height="202" fill="none" stroke="{BLUE}" stroke-width="3"/>
  <rect x="238" y="54" width="424" height="190" fill="none" stroke="{SKY3}" stroke-width="1" opacity="0.4"/>
  
  <!-- Corner Brackets -->
  <path d="M232 58V48H242M658 48H668V58M232 240V250H242M658 250H668V240" stroke="{CYAN}" stroke-width="2" fill="none"/>

  <text x="450" y="86" text-anchor="middle" font-size="22" fill="{GOLD}" letter-spacing="5">EXPEDITION REPORT</text>
  
  <text x="256" y="120" font-size="13" fill="{SKY3}" letter-spacing="1">STARS DISCOVERED</text>
  <text x="644" y="120" text-anchor="end" font-size="14" fill="#FFFFFF">{total} ★</text>
  
  <text x="256" y="146" font-size="13" fill="{SKY3}" letter-spacing="1">ACTIVE STELLAR NODES</text>
  <text x="644" y="146" text-anchor="end" font-size="14" fill="#FFFFFF">{nblocks}</text>
  
  <text x="256" y="172" font-size="13" fill="{SKY3}" letter-spacing="1">LONGEST EXPEDITION</text>
  <text x="644" y="172" text-anchor="end" font-size="14" fill="#FFFFFF">{best} DAYS</text>
  
  <path d="M256 188H644" stroke="{BLUE}" stroke-width="2" stroke-dasharray="6 4"/>
  <text x="256" y="219" font-size="15" fill="#FFFFFF" letter-spacing="3">TOTAL STARS</text>

  <!-- Roll-up score -->
  {"".join(layers)}

  <!-- Astronaut Rank Badge -->
  <rect x="585" y="196" width="60" height="38" fill="{DEEP}" stroke="{gcol}" stroke-width="3"/>
  <text x="615" y="224" text-anchor="middle" font-size="26" fill="{gcol}">{grade}</text>
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

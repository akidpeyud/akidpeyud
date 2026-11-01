#!/usr/bin/env python3
"""
Generator aset pixel-art untuk profil GitHub: Stellar Explorer (Penjelajah Bintang).
Menghasilkan 3 file SVG di folder assets/:
  - banner.svg        : Astronot melayang bebas (zero-G 2D gliding) & terminal identifikasi kosmik
  - stats.svg         : Logbook navigasi antariksa & telemetri sistem
  - contrib-game.svg  : Astronot berjalan menuju rasi bintang nyata berdasarkan data kontribusi GitHub

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

ASTRONAUT_FLY_GRID = ASTRONAUT_UPPER + [
    "..WWWW..WWWW....",
    "..WWW....WWW....",
    "..SSS....SSS....",
    ".DDDD....DDDD...",
    "................",
]

ASTRONAUT_WALK_A_GRID = ASTRONAUT_UPPER + [
    "..WWWW..WW......",
    ".WWWW....WW.....",
    ".SSSS....SS.....",
    "DDDDD....DDDD...",
    "................",
]

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
STAR_LARGE = sprite(STAR_LARGE_GRID, {"X": GOLD, "L": "#FFFDF0"}, 2)

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
    W, H = 900, 260

    stars = []
    positions = [
        (40, 56, 2), (90, 92, 2), (150, 52, 3), (210, 88, 2), (270, 60, 2),
        (330, 82, 1), (390, 55, 2), (450, 90, 3), (510, 58, 2), (570, 85, 1),
        (630, 52, 2), (690, 88, 3), (750, 62, 2), (810, 78, 1), (860, 55, 2),
        (50, 180, 2), (100, 215, 3), (160, 190, 1), (220, 225, 2), (280, 195, 2),
        (340, 230, 3), (400, 200, 1), (460, 220, 2), (520, 190, 3), (580, 230, 1),
        (640, 200, 2), (700, 225, 3), (760, 195, 1), (820, 220, 2), (870, 190, 3),
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
  /* Animasi terbang 2D seimbang di tengah kanvas (tidak mepet atas) */
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
    25%  {{ transform: translate(25px, -15px) rotate(-5deg); }}
    50%  {{ transform: translate(42px, -4px) rotate(0deg); }}
    75%  {{ transform: translate(22px, 12px) rotate(4deg); }}
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

<!-- Outer Sci-Fi Frame dengan padding seimbang -->
<rect x="4" y="4" width="{W-8}" height="{H-8}" fill="none" stroke="{NAVY}" stroke-width="2"/>
<rect x="8" y="8" width="{W-16}" height="{H-16}" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.45"/>
<path d="M4 20V4H20M{W-20} 4H{W-4}V20M4 {H-20}V{H-4}H20M{W-20} {H-4}H{W-4}V{H-20}" stroke="{SKY3}" stroke-width="2" fill="none"/>

<!-- Twinkling Background Stars -->
{"".join(stars)}

<!-- Shooting Star / Meteor -->
<g class="meteor" transform="translate(850, 30)">
  <line x1="0" y1="0" x2="36" y2="-18" stroke="{GOLD_L}" stroke-width="2" opacity="0.85"/>
  <rect x="0" y="0" width="3" height="3" fill="#FFFFFF"/>
</g>

<!-- Distant Ringed Exoplanet -->
<g opacity="0.8" transform="translate(760, 48)"><g>{PLANET_RINGED}</g></g>

<!-- Top Sci-Fi Navigation HUD Bar -->
<rect x="12" y="14" width="{W-24}" height="32" fill="{DEEP}" opacity="0.9"/>
<line x1="12" y1="46" x2="{W-12}" y2="46" stroke="{BLUE}" stroke-width="1"/>
<text x="28" y="35" font-size="12" fill="{SKY3}" letter-spacing="2">[ PILOT // AKID ]</text>
<text x="220" y="35" font-size="12" fill="{GOLD}" letter-spacing="2">★ STARS DISCOVERED: {score:06d}</text>
<text x="540" y="35" font-size="12" fill="{SKY3}" letter-spacing="2">SYSTEMS: x{coins:02d}</text>
<text x="872" y="35" text-anchor="end" font-size="12" fill="{GOLD}" letter-spacing="2">MISSION: {esc(quest)}</text>

<!-- Primary Pulsing Beacon Star ahead of Astronaut (Centered at y=138) -->
<g transform="translate(245, 124)">
  <circle cx="15" cy="15" r="32" fill="url(#beacon_glow)"/>
  <g class="beacon-star" style="transform-origin: 15px 15px;">{STAR_LARGE}</g>
  <line x1="-50" y1="15" x2="0" y2="15" stroke="{CYAN}" stroke-width="1" stroke-dasharray="3 3" opacity="0.6"/>
</g>

<!-- Spacewalking Astronaut (Centered at y=120) -->
<g class="spacewalk-2d" transform="translate(90, 120)">
  <!-- Tether Cable connecting to starship -->
  <path d="M-75 35 C -40 10, -15 50, 6 30" fill="none" stroke="{SKY1}" stroke-width="2" opacity="0.5"/>
  <rect x="-80" y="33" width="6" height="6" fill="{BLUE}"/>
  
  <!-- RCS Jetpack Thruster Flame Puff -->
  <g class="thruster" transform="translate(-10, 24)">
    <polygon points="0,6 -8,3 -8,9" fill="{CYAN}"/>
    <polygon points="0,6 -5,4 -5,8" fill="#FFFFFF"/>
  </g>
  
  <g>{HERO_FLY}</g>
  
  <!-- Scanner Cone Beam pointing toward Beacon Star -->
  <polygon points="66,36 145,20 145,52" fill="{CYAN}" opacity="0.14"/>
  <line x1="66" y1="36" x2="145" y2="36" stroke="{CYAN}" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.75"/>
</g>

<!-- Right Side: Identification Terminal Card (Centered Vertically at y=62) -->
<g transform="translate(420, 62)">
  <rect width="455" height="175" fill="{DEEP}" opacity="0.9"/>
  <rect x="2" y="2" width="451" height="171" fill="none" stroke="{NAVY}" stroke-width="2"/>
  <rect x="6" y="6" width="443" height="163" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.5"/>
  
  <rect x="14" y="14" width="220" height="18" fill="{NAVY}"/>
  <text x="20" y="27" font-size="10" fill="{CYAN}" letter-spacing="2">STELLAR CARTOGRAPHER // CLASS S</text>

  <text x="16" y="68" font-size="30" fill="{DEEP}" letter-spacing="3">ANDIKA DWI PUTRA</text>
  <text x="14" y="66" font-size="30" fill="#FFFFFF" letter-spacing="3">ANDIKA DWI PUTRA</text>

  <text x="14" y="96" font-size="12" fill="{SKY3}" letter-spacing="3">WEB DEVELOPER • CS STUDENT • STAR EXPLORER</text>
  <line x1="14" y1="110" x2="440" y2="110" stroke="{BLUE}" stroke-width="1" stroke-dasharray="4 4" opacity="0.6"/>

  <text class="blink" x="14" y="136" font-size="12" fill="{GOLD}" letter-spacing="2">&gt; CHARTING THE DIGITAL UNIVERSE_</text>
  
  <text x="14" y="158" font-size="10" fill="{SKY1}" letter-spacing="1">SYS: ONLINE | RADAR: ACTIVE | PWR: 100%</text>
  <rect x="370" y="150" width="70" height="8" fill="{NAVY}"/>
  <rect x="372" y="152" width="60" height="4" fill="{SKY3}"/>
</g>
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
    left = sci_fi_card(10, 12, 430, 216, "STELLAR LOGBOOK", STAR_BRIGHT_GOLD)
    for i, (k, v) in enumerate(rows):
        y = 84 + i * 28
        left += f'<text x="32" y="{y}" font-size="13" fill="{SKY3}" letter-spacing="1">{k}</text>'
        left += f'<text x="414" y="{y}" text-anchor="end" font-size="14" fill="{GOLD if i==0 else "#FFFFFF"}">{v}</text>'
        left += f'<path d="M32 {y+8}H414" stroke="{NAVY}" stroke-width="1" stroke-dasharray="4 4"/>'

    right = sci_fi_card(460, 12, 430, 216, "MISSION TELEMETRY", TELESCOPE)
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
    Memetakan secara nyata 52 minggu kontribusi GitHub ke dalam koordinat rasi bintang.
    Astronot melangkah di jembatan starlight menuju gugusan bintang yang aktif di sisi kanan.
    """
    W, H = 900, 320
    T = 20  # Durasi siklus animasi dalam detik
    nblocks = sum(1 for d in days if d[3] > 0)

    gx, gy = 115, 78
    pitch_x, pitch_y = 14.0, 13.0
    cols = max(d[2] for d in days) + 1

    # Identifikasi koordinat bulan-bulan dalam 52 minggu
    month_names = ["Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
    month_labels = []
    seen_months = set()
    for d, r, c, l in sorted(days, key=lambda x: x[0]):
        m_str = d[5:7]  # '01' to '12'
        if m_str not in seen_months and r == 0:
            seen_months.add(m_str)
            m_idx = (int(m_str) + 1) % 12  # mapping ke nama bulan
            name = month_names[m_idx]
            month_labels.append(f'<text x="{gx + c * pitch_x:.1f}" y="65" font-size="10" fill="{SKY3}" letter-spacing="1">{name}</text>')

    # Bangun bintang-bintang nyata berdasarkan tingkat kontribusi
    star_nodes = []
    active_points = []
    for d, r, c, lvl in days:
        sx = gx + c * pitch_x
        sy = gy + r * pitch_y
        if lvl == 0:
            # Koordinat ruang hampa
            star_nodes.append(f'<rect x="{sx+4:.1f}" y="{sy+4:.1f}" width="3" height="3" fill="#14243B" rx="1"/>')
        elif lvl == 1:
            active_points.append((sx + 5, sy + 5, lvl))
            star_nodes.append(
                f'<polygon points="{sx+5:.1f},{sy+1:.1f} {sx+9:.1f},{sy+5:.1f} {sx+5:.1f},{sy+9:.1f} {sx+1:.1f},{sy+5:.1f}" fill="{BLUE}"/>'
            )
        elif lvl == 2:
            active_points.append((sx + 5, sy + 5, lvl))
            star_nodes.append(
                f'<polygon points="{sx+5:.1f},{sy:.1f} {sx+10:.1f},{sy+5:.1f} {sx+5:.1f},{sy+10:.1f} {sx:.1f},{sy+5:.1f}" fill="{SKY1}"/>'
                f'<rect x="{sx+4:.1f}" y="{sy+4:.1f}" width="2" height="2" fill="{WHITE}"/>'
            )
        elif lvl == 3:
            active_points.append((sx + 6, sy + 6, lvl))
            star_nodes.append(
                f'<polygon points="{sx+6:.1f},{sy:.1f} {sx+12:.1f},{sy+6:.1f} {sx+6:.1f},{sy+12:.1f} {sx:.1f},{sy+6:.1f}" fill="{SKY2}"/>'
                f'<polygon points="{sx+6:.1f},{sy+2:.1f} {sx+10:.1f},{sy+6:.1f} {sx+6:.1f},{sy+10:.1f} {sx+2:.1f},{sy+6:.1f}" fill="{SKY3}"/>'
                f'<rect x="{sx+5:.1f}" y="{sy+5:.1f}" width="2" height="2" fill="{WHITE}"/>'
            )
        elif lvl == 4:
            active_points.append((sx + 6, sy + 6, lvl))
            star_nodes.append(
                f'<circle cx="{sx+6:.1f}" cy="{sy+6:.1f}" r="9" fill="{GOLD}" opacity="0.3"/>'
                f'<polygon points="{sx+6:.1f},{sy-1:.1f} {sx+13:.1f},{sy+6:.1f} {sx+6:.1f},{sy+13:.1f} {sx-1:.1f},{sy+6:.1f}" fill="{GOLD}"/>'
                f'<polygon points="{sx+6:.1f},{sy+2:.1f} {sx+10:.1f},{sy+6:.1f} {sx+6:.1f},{sy+10:.1f} {sx+2:.1f},{sy+6:.1f}" fill="{GOLD_L}"/>'
                f'<rect x="{sx+5:.1f}" y="{sy+5:.1f}" width="3" height="3" fill="{WHITE}"/>'
            )

    # Garis konstelasi menghubungkan bintang-bintang aktif
    constellation_lines = []
    for i in range(len(active_points) - 1):
        x1, y1, l1 = active_points[i]
        x2, y2, l2 = active_points[i + 1]
        dist = math.hypot(x2 - x1, y2 - y1)
        if dist < 34:
            constellation_lines.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{SKY3}" stroke-width="1.2" stroke-dasharray="2 3" opacity="0.5"/>'
            )

    # Target walking astronaut adalah kolom aktif pertama (kolom ~38, x ≈ 640)
    target_walk_x = gx + 37 * pitch_x - 30

    css = [
        # Astronot berjalan melangkah dari kiri ke arah gugusan bintang aktif
        f"@keyframes astro_walk_forward {{"
        f"  0%   {{ transform: translateX(50px); }}"
        f"  38%  {{ transform: translateX({target_walk_x:.0f}px); }}"
        f"  65%  {{ transform: translateX({target_walk_x:.0f}px); }}"
        f"  90%  {{ transform: translateX(50px); }}"
        f"  100% {{ transform: translateX(50px); }}"
        f"}}",
        "@keyframes step_cycle { 0%, 50% { opacity: 1; } 50.01%, 100% { opacity: 0; } }",
        "@keyframes scanner_flare {"
        "  0%, 36% { opacity: 0; transform: scaleX(0.2); }"
        "  40%, 63% { opacity: 0.95; transform: scaleX(1); }"
        "  67%, 100% { opacity: 0; transform: scaleX(0.2); }"
        "}",
        "@keyframes star_glow {"
        "  0%, 100% { opacity: 0.8; }"
        "  50% { opacity: 1; filter: drop-shadow(0 0 3px #FFD166); }"
        "}",
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
  .star-cluster {{
    animation: star_glow 2.5s ease-in-out infinite alternate;
  }}
  .hud-panel {{
    animation: hud_report {T}s ease-in-out infinite;
  }}
  {"".join(css)}
</style>

<!-- Canvas Background -->
<rect width="{W}" height="{H}" fill="url(#game_cosmos)"/>

<!-- Outer Technical Frame -->
<rect x="4" y="4" width="{W-8}" height="{H-8}" fill="none" stroke="{NAVY}" stroke-width="2"/>
<rect x="8" y="8" width="{W-16}" height="{H-16}" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.45"/>
<path d="M4 20V4H20M{W-20} 4H{W-4}V20M4 {H-20}V{H-4}H20M{W-20} {H-4}H{W-4}V{H-20}" stroke="{SKY3}" stroke-width="2" fill="none"/>

<!-- Top Expedition HUD Bar (Padding seimbang di y=14) -->
<rect x="12" y="14" width="{W-24}" height="32" fill="{DEEP}" opacity="0.92"/>
<line x1="12" y1="46" x2="{W-12}" y2="46" stroke="{BLUE}" stroke-width="1"/>
<text x="28" y="35" font-size="12" fill="{SKY3}" letter-spacing="2">[ STELLAR EXPEDITION // STARWAY ]</text>
<text x="872" y="35" text-anchor="end" font-size="12" fill="{GOLD}" letter-spacing="2">★ STARS DISCOVERED: {total} | NODES: {nblocks}</text>

<!-- Month Labels across the 52 Weeks -->
{"".join(month_labels)}

<!-- Weekday Indicator Labels -->
<text x="82" y="{gy + 1 * pitch_y + 8}" font-size="9" fill="{SKY1}">Mon</text>
<text x="82" y="{gy + 3 * pitch_y + 8}" font-size="9" fill="{SKY1}">Wed</text>
<text x="82" y="{gy + 5 * pitch_y + 8}" font-size="9" fill="{SKY1}">Fri</text>

<!-- Constellation Links connecting Active Discovered Stars -->
{"".join(constellation_lines)}

<!-- The Discovered Stars Matrix (Kesesuaian 100% dengan Data Kontribusi Nyata) -->
<g class="star-cluster">{"".join(star_nodes)}</g>

<!-- Luminous Celestial Pathway / Starlight Bridge (y=205) -->
<rect x="30" y="205" width="840" height="4" fill="{BLUE}"/>
<rect x="30" y="205" width="840" height="1" fill="{SKY3}"/>
<!-- Pathway tick marks -->
<path d="M50 209V213M120 209V213M190 209V213M260 209V213M330 209V213M400 209V213M470 209V213M540 209V213M610 209V213M680 209V213M750 209V213M820 209V213" stroke="{NAVY}" stroke-width="2"/>
<rect x="30" y="209" width="840" height="10" fill="{DEEP}" opacity="0.6"/>

<!-- Astronaut Walking Towards the Discovered Star Cluster (Feet at y=205) -->
<g class="walker-group" transform="translate(0, 157)">
  <!-- Navigation Tether -->
  <path d="M-40 25 C -20 15, -10 30, 4 20" fill="none" stroke="{SKY1}" stroke-width="1.5" opacity="0.5"/>
  <rect x="-44" y="23" width="5" height="5" fill="{BLUE}"/>

  <!-- Animated Walking Legs -->
  <g class="step-a">{HERO_WALK_A}</g>
  <g class="step-b">{HERO_WALK_B}</g>

  <!-- Scanner Starlight Discovery Projection -->
  <g class="scan-flare" transform="translate(48, 24)">
    <polygon points="0,0 320,-85 320,60" fill="url(#beam_glow)"/>
    <line x1="0" y1="0" x2="320" y2="-15" stroke="{WHITE}" stroke-width="1.5" stroke-dasharray="3 3"/>
  </g>
</g>

<!-- Dynamic Status Telemetry (Bottom) -->
<rect x="12" y="{H-34}" width="{W-24}" height="24" fill="{DEEP}" opacity="0.92"/>
<line x1="12" y1="{H-34}" x2="{W-12}" y2="{H-34}" stroke="{NAVY}" stroke-width="1"/>
<text style="opacity:0;animation:phase1 {T}s linear infinite" x="28" y="{H-18}" font-size="11" fill="{GOLD}" letter-spacing="2">&gt; PILOT WALKING TOWARDS UNCHARTED SPACE (NOV - JUL)...</text>
<text style="opacity:0;animation:phase2 {T}s linear infinite" x="28" y="{H-18}" font-size="11" fill="{CYAN}" letter-spacing="2">&gt; STELLAR CONSTELLATION LOCATED (AUG - OCT)! SCANNING STARS...</text>
<text style="opacity:0;animation:phase3 {T}s linear infinite" x="28" y="{H-18}" font-size="11" fill="{SKY3}" letter-spacing="2">&gt; {total} STARS SYNCHRONIZED ACROSS 50 CONSTELLATION NODES ★</text>

<!-- Holographic Mission Result HUD Panel -->
<g class="hud-panel" style="opacity:0;">
  <rect width="{W}" height="{H}" fill="{DEEP}" opacity="0.88"/>
  <rect x="230" y="55" width="440" height="206" fill="{NAVY}"/>
  <rect x="232" y="57" width="436" height="202" fill="none" stroke="{BLUE}" stroke-width="3"/>
  <rect x="238" y="63" width="424" height="190" fill="none" stroke="{SKY3}" stroke-width="1" opacity="0.4"/>
  
  <path d="M232 67V57H242M658 57H668V67M232 249V259H242M658 259H668V249" stroke="{CYAN}" stroke-width="2" fill="none"/>

  <text x="450" y="95" text-anchor="middle" font-size="22" fill="{GOLD}" letter-spacing="5">EXPEDITION REPORT</text>
  
  <text x="256" y="129" font-size="13" fill="{SKY3}" letter-spacing="1">STARS DISCOVERED</text>
  <text x="644" y="129" text-anchor="end" font-size="14" fill="#FFFFFF">{total} ★</text>
  
  <text x="256" y="155" font-size="13" fill="{SKY3}" letter-spacing="1">ACTIVE STELLAR NODES</text>
  <text x="644" y="155" text-anchor="end" font-size="14" fill="#FFFFFF">{nblocks} DAYS</text>
  
  <text x="256" y="181" font-size="13" fill="{SKY3}" letter-spacing="1">LONGEST EXPEDITION</text>
  <text x="644" y="181" text-anchor="end" font-size="14" fill="#FFFFFF">{best} DAYS</text>
  
  <path d="M256 197H644" stroke="{BLUE}" stroke-width="2" stroke-dasharray="6 4"/>
  <text x="256" y="228" font-size="15" fill="#FFFFFF" letter-spacing="3">TOTAL STARS</text>

  {"".join(layers)}

  <rect x="585" y="205" width="60" height="38" fill="{DEEP}" stroke="{gcol}" stroke-width="3"/>
  <text x="615" y="233" text-anchor="middle" font-size="26" fill="{gcol}">{grade}</text>
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

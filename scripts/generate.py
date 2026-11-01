#!/usr/bin/env python3
"""
Generator aset pixel-art untuk profil GitHub: Stellar Explorer (Penjelajah Bintang).
Menghasilkan 3 file SVG di folder assets/:
  - banner.svg        : Astronot melayang bebas di tengah kiri dekat bintang suar
  - stats.svg         : Logbook navigasi antariksa & telemetri sistem
  - contrib-game.svg  : Astronot berjalan di bawah rasi bintang sambil menyenter ke atas ke arah bintang

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
    W, H = 900, 240

    stars = []
    positions = [
        (40, 56, 2), (90, 85, 2), (150, 52, 3), (210, 88, 2), (270, 60, 2),
        (330, 82, 1), (390, 55, 2), (450, 90, 3), (510, 58, 2), (570, 85, 1),
        (630, 52, 2), (690, 88, 3), (750, 62, 2), (810, 78, 1), (860, 55, 2),
        (50, 175, 2), (100, 210, 3), (160, 185, 1), (220, 220, 2), (280, 190, 2),
        (340, 225, 3), (400, 195, 1), (460, 215, 2), (520, 185, 3), (580, 225, 1),
        (640, 195, 2), (700, 220, 3), (760, 190, 1), (820, 215, 2), (870, 185, 3),
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
  /* Animasi melayang di tengah kiri dekat bintang suar */
  .spacewalk-float {{
    animation: flight_relative 7s ease-in-out infinite;
  }}
  .thruster {{
    animation: rcs_pulse 7s ease-in-out infinite;
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

  @keyframes flight_relative {{
    0%   {{ transform: translate(0px, 0px) rotate(0deg); }}
    25%  {{ transform: translate(18px, -10px) rotate(-4deg); }}
    50%  {{ transform: translate(30px, -2px) rotate(0deg); }}
    75%  {{ transform: translate(14px, 8px) rotate(3deg); }}
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

<!-- Outer Sci-Fi Frame -->
<rect x="4" y="4" width="{W-8}" height="{H-8}" fill="none" stroke="{NAVY}" stroke-width="2"/>
<rect x="8" y="8" width="{W-16}" height="{H-16}" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.45"/>
<path d="M4 18V4H18M{W-18} 4H{W-4}V18M4 {H-18}V{H-4}H18M{W-18} {H-4}H{W-4}V{H-18}" stroke="{SKY3}" stroke-width="2" fill="none"/>

<!-- Twinkling Background Stars -->
{"".join(stars)}

<!-- Shooting Star / Meteor -->
<g class="meteor" transform="translate(850, 26)">
  <line x1="0" y1="0" x2="36" y2="-18" stroke="{GOLD_L}" stroke-width="2" opacity="0.85"/>
  <rect x="0" y="0" width="3" height="3" fill="#FFFFFF"/>
</g>

<!-- Distant Ringed Exoplanet -->
<g opacity="0.8" transform="translate(750, 42)"><g>{PLANET_RINGED}</g></g>

<!-- Top Sci-Fi Navigation HUD Bar -->
<rect x="12" y="12" width="{W-24}" height="30" fill="{DEEP}" opacity="0.9"/>
<line x1="12" y1="42" x2="{W-12}" y2="42" stroke="{BLUE}" stroke-width="1"/>
<text x="26" y="32" font-size="12" fill="{SKY3}" letter-spacing="2">[ PILOT // AKID ]</text>
<text x="220" y="32" font-size="12" fill="{GOLD}" letter-spacing="2">★ STARS DISCOVERED: {score:06d}</text>
<text x="540" y="32" font-size="12" fill="{SKY3}" letter-spacing="2">SYSTEMS: x{coins:02d}</text>
<text x="872" y="32" text-anchor="end" font-size="12" fill="{GOLD}" letter-spacing="2">MISSION: {esc(quest)}</text>

<!-- Primary Pulsing Beacon Star (Tepat di tengah kiri pada y=125) -->
<g transform="translate(240, 110)">
  <circle cx="15" cy="15" r="32" fill="url(#beacon_glow)"/>
  <g class="beacon-star" style="transform-origin: 15px 15px;">{STAR_LARGE}</g>
  <line x1="-50" y1="15" x2="0" y2="15" stroke="{CYAN}" stroke-width="1" stroke-dasharray="3 3" opacity="0.6"/>
</g>

<!-- Astronot di TENGAN KIRI dekat bintang (y=110, bukan di atas) -->
<g transform="translate(90, 110)">
  <g class="spacewalk-float">
    <!-- Tether Cable connecting to starship -->
    <path d="M-65 35 C -35 15, -15 45, 6 30" fill="none" stroke="{SKY1}" stroke-width="2" opacity="0.5"/>
    <rect x="-70" y="33" width="6" height="6" fill="{BLUE}"/>
    
    <!-- RCS Jetpack Thruster Flame Puff -->
    <g class="thruster" transform="translate(-10, 24)">
      <polygon points="0,6 -8,3 -8,9" fill="{CYAN}"/>
      <polygon points="0,6 -5,4 -5,8" fill="#FFFFFF"/>
    </g>
    
    <g>{HERO_FLY}</g>
    
    <!-- Scanner Cone Beam pointing directly to Beacon Star -->
    <polygon points="66,36 145,20 145,52" fill="{CYAN}" opacity="0.14"/>
    <line x1="66" y1="36" x2="145" y2="36" stroke="{CYAN}" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.75"/>
  </g>
</g>

<!-- Right Side: Identification Terminal Card (Tepat di tengah pada y=56) -->
<g transform="translate(420, 56)">
  <rect width="455" height="166" fill="{DEEP}" opacity="0.9"/>
  <rect x="2" y="2" width="451" height="162" fill="none" stroke="{NAVY}" stroke-width="2"/>
  <rect x="6" y="6" width="443" height="154" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.5"/>
  
  <rect x="14" y="14" width="220" height="18" fill="{NAVY}"/>
  <text x="20" y="27" font-size="10" fill="{CYAN}" letter-spacing="2">STELLAR CARTOGRAPHER // CLASS S</text>

  <text x="16" y="66" font-size="28" fill="{DEEP}" letter-spacing="3">ANDIKA DWI PUTRA</text>
  <text x="14" y="64" font-size="28" fill="#FFFFFF" letter-spacing="3">ANDIKA DWI PUTRA</text>

  <text x="14" y="92" font-size="12" fill="{SKY3}" letter-spacing="3">WEB DEVELOPER • CS STUDENT • STAR EXPLORER</text>
  <line x1="14" y1="104" x2="440" y2="104" stroke="{BLUE}" stroke-width="1" stroke-dasharray="4 4" opacity="0.6"/>

  <text class="blink" x="14" y="128" font-size="12" fill="{GOLD}" letter-spacing="2">&gt; CHARTING THE DIGITAL UNIVERSE_</text>
  
  <text x="14" y="150" font-size="10" fill="{SKY1}" letter-spacing="1">SYS: ONLINE | RADAR: ACTIVE | PWR: 100%</text>
  <rect x="370" y="142" width="70" height="8" fill="{NAVY}"/>
  <rect x="372" y="144" width="60" height="4" fill="{SKY3}"/>
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
    - Bintang-bintang bersumber 100% dari data kontribusi nyata Anda (gugusan aktif di kanan).
    - Bagian bulan & hari dihapus total agar tampilan minimalis, clean, dan lapang.
    - Astronot berada DI BAWAH bintang-bintang dan MENYENTER KE ATAS ke arah rasi bintang.
    """
    W, H = 900, 310
    T = 20  # Durasi siklus animasi dalam detik
    nblocks = sum(1 for d in days if d[3] > 0)

    # Grid koordinat bintang (tanpa label bulan & hari, diletakkan bersih di atas)
    gx, gy = 80, 68
    pitch_x, pitch_y = 14.2, 14.0

    # Bangun bintang nyata berdasarkan data kontribusi
    star_nodes = []
    active_points = []
    for d, r, c, lvl in days:
        sx = gx + c * pitch_x
        sy = gy + r * pitch_y
        if lvl == 0:
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

    # Target walking: berhenti tepat di bawah gugusan bintang aktif di kanan
    target_walk_x = gx + 37 * pitch_x - 30

    css = [
        # Astronot berjalan di bawah bintang dari x=50 ke x=target
        f"@keyframes astro_walk_beneath {{"
        f"  0%   {{ transform: translateX(50px); }}"
        f"  38%  {{ transform: translateX({target_walk_x:.0f}px); }}"
        f"  65%  {{ transform: translateX({target_walk_x:.0f}px); }}"
        f"  90%  {{ transform: translateX(50px); }}"
        f"  100% {{ transform: translateX(50px); }}"
        f"}}",
        "@keyframes step_cycle { 0%, 50% { opacity: 1; } 50.01%, 100% { opacity: 0; } }",
        # Senter / scanner menyorot ke atas ke arah bintang
        "@keyframes flashlight_beam {"
        "  0%, 36% { opacity: 0; transform: scale(0.3); }"
        "  40%, 63% { opacity: 0.95; transform: scale(1); }"
        "  67%, 100% { opacity: 0; transform: scale(0.3); }"
        "}",
        "@keyframes star_glow {"
        "  0%, 100% { opacity: 0.8; }"
        "  50% { opacity: 1; filter: drop-shadow(0 0 4px #FFD166); }"
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

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Celestial Cartography: Astronaut exploring discovered stars">
<defs>
  <linearGradient id="game_cosmos" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{DEEP}"/>
    <stop offset="55%" stop-color="{NAVY}"/>
    <stop offset="100%" stop-color="{DEEP}"/>
  </linearGradient>
  <!-- Sinar senter kosmik menyorot ke atas ke arah bintang -->
  <linearGradient id="flashlight_glow" x1="0" y1="1" x2="0.6" y2="0">
    <stop offset="0%" stop-color="{CYAN}" stop-opacity="0.95"/>
    <stop offset="60%" stop-color="{SKY2}" stop-opacity="0.45"/>
    <stop offset="100%" stop-color="{GOLD}" stop-opacity="0"/>
  </linearGradient>
</defs>
<style>
  {FONT}
  .walker-group {{
    animation: astro_walk_beneath {T}s ease-in-out infinite;
  }}
  .step-a {{
    animation: step_cycle 0.4s steps(1) infinite;
  }}
  .step-b {{
    animation: step_cycle 0.4s steps(1) infinite reverse;
  }}
  .flashlight-beam {{
    animation: flashlight_beam {T}s ease-in-out infinite;
    transform-origin: 0% 100%;
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
<path d="M4 18V4H18M{W-18} 4H{W-4}V18M4 {H-18}V{H-4}H18M{W-18} {H-4}H{W-4}V{H-18}" stroke="{SKY3}" stroke-width="2" fill="none"/>

<!-- Top Expedition HUD Bar -->
<rect x="12" y="12" width="{W-24}" height="30" fill="{DEEP}" opacity="0.92"/>
<line x1="12" y1="42" x2="{W-12}" y2="42" stroke="{BLUE}" stroke-width="1"/>
<text x="26" y="32" font-size="12" fill="{SKY3}" letter-spacing="2">[ STELLAR EXPEDITION // STARWAY ]</text>
<text x="872" y="32" text-anchor="end" font-size="12" fill="{GOLD}" letter-spacing="2">★ STARS DISCOVERED: {total} | NODES: {nblocks}</text>

<!-- Constellation Links connecting Active Discovered Stars -->
{"".join(constellation_lines)}

<!-- The Discovered Stars Matrix (Bersih tanpa teks bulan & hari) -->
<g class="star-cluster">{"".join(star_nodes)}</g>

<!-- Luminous Celestial Pathway / Starlight Bridge (y=226) -->
<rect x="30" y="226" width="840" height="4" fill="{BLUE}"/>
<rect x="30" y="226" width="840" height="1" fill="{SKY3}"/>
<!-- Pathway tick marks -->
<path d="M50 230V234M120 230V234M190 230V234M260 230V234M330 230V234M400 230V234M470 230V234M540 230V234M610 230V234M680 230V234M750 230V234M820 230V234" stroke="{NAVY}" stroke-width="2"/>
<rect x="30" y="230" width="840" height="10" fill="{DEEP}" opacity="0.6"/>

<!-- Astronot DI BAWAH bintang-bintang (y=178) menyenter ke atas ke arah bintang -->
<g transform="translate(0, 178)">
  <g class="walker-group">
    <!-- Navigation Tether -->
    <path d="M-35 25 C -15 15, -5 30, 4 20" fill="none" stroke="{SKY1}" stroke-width="1.5" opacity="0.5"/>
    <rect x="-38" y="23" width="5" height="5" fill="{BLUE}"/>

    <!-- Animated Walking Legs -->
    <g class="step-a">{HERO_WALK_A}</g>
    <g class="step-b">{HERO_WALK_B}</g>

    <!-- Senter Kosmik menyorot KE ATAS ke arah gugusan bintang -->
    <g class="flashlight-beam" transform="translate(46, 18)">
      <polygon points="0,0 280,-125 280,10" fill="url(#flashlight_glow)"/>
      <line x1="0" y1="0" x2="280" y2="-65" stroke="{WHITE}" stroke-width="1.5" stroke-dasharray="3 3"/>
    </g>
  </g>
</g>

<!-- Dynamic Status Telemetry (Bottom) -->
<rect x="12" y="{H-32}" width="{W-24}" height="22" fill="{DEEP}" opacity="0.92"/>
<line x1="12" y1="{H-32}" x2="{W-12}" y2="{H-32}" stroke="{NAVY}" stroke-width="1"/>
<text style="opacity:0;animation:phase1 {T}s linear infinite" x="26" y="{H-17}" font-size="11" fill="{GOLD}" letter-spacing="2">&gt; PILOT WALKING TOWARDS UNCHARTED SPACE...</text>
<text style="opacity:0;animation:phase2 {T}s linear infinite" x="26" y="{H-17}" font-size="11" fill="{CYAN}" letter-spacing="2">&gt; FLASHLIGHT BEAM ILLUMINATING DISCOVERED CONSTELLATION...</text>
<text style="opacity:0;animation:phase3 {T}s linear infinite" x="26" y="{H-17}" font-size="11" fill="{SKY3}" letter-spacing="2">&gt; {total} STARS SYNCHRONIZED ACROSS {nblocks} CONSTELLATION NODES ★</text>

<!-- Holographic Mission Result HUD Panel -->
<g class="hud-panel" style="opacity:0;">
  <rect width="{W}" height="{H}" fill="{DEEP}" opacity="0.88"/>
  <rect x="230" y="50" width="440" height="206" fill="{NAVY}"/>
  <rect x="232" y="52" width="436" height="202" fill="none" stroke="{BLUE}" stroke-width="3"/>
  <rect x="238" y="58" width="424" height="190" fill="none" stroke="{SKY3}" stroke-width="1" opacity="0.4"/>
  
  <path d="M232 62V52H242M658 52H668V62M232 244V254H242M658 254H668V244" stroke="{CYAN}" stroke-width="2" fill="none"/>

  <text x="450" y="90" text-anchor="middle" font-size="22" fill="{GOLD}" letter-spacing="5">EXPEDITION REPORT</text>
  
  <text x="256" y="124" font-size="13" fill="{SKY3}" letter-spacing="1">STARS DISCOVERED</text>
  <text x="644" y="124" text-anchor="end" font-size="14" fill="#FFFFFF">{total} ★</text>
  
  <text x="256" y="150" font-size="13" fill="{SKY3}" letter-spacing="1">ACTIVE STELLAR NODES</text>
  <text x="644" y="150" text-anchor="end" font-size="14" fill="#FFFFFF">{nblocks} DAYS</text>
  
  <text x="256" y="176" font-size="13" fill="{SKY3}" letter-spacing="1">LONGEST EXPEDITION</text>
  <text x="644" y="176" text-anchor="end" font-size="14" fill="#FFFFFF">{best} DAYS</text>
  
  <path d="M256 192H644" stroke="{BLUE}" stroke-width="2" stroke-dasharray="6 4"/>
  <text x="256" y="223" font-size="15" fill="#FFFFFF" letter-spacing="3">TOTAL STARS</text>

  {"".join(layers)}

  <rect x="585" y="200" width="60" height="38" fill="{DEEP}" stroke="{gcol}" stroke-width="3"/>
  <text x="615" y="228" text-anchor="middle" font-size="26" fill="{gcol}">{grade}</text>
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

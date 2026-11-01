#!/usr/bin/env python3
"""
Generator aset pixel-art untuk profil GitHub dengan tema "Stellar Explorer" (Penjelajah Bintang).
Menghasilkan 3 file SVG di folder assets/:
  - banner.svg        : Astronot penjelajah bintang spacewalking di antariksa lepas (zero-G)
  - stats.svg         : Logbook navigasi antariksa & telemetri sistem
  - contrib-game.svg  : Peta konstelasi bintang nyata dari kontribusi GitHub dengan radar scanner

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
DEEP = "#080E1A"
SPACE_DARK = "#0D172A"
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
# Spacewalking Astronaut (16x16) - Floating in Zero-G holding a star scanner
ASTRONAUT_FLOAT_GRID = [
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
    "..WWWW..WWWW....",
    "..WWW....WWW....",
    "..SSS....SSS....",
    ".DDDD....DDDD...",
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

HERO_FLOAT = sprite(ASTRONAUT_FLOAT_GRID, ASTRONAUT_COLORS, 4)
HERO_FLOAT_S = sprite(ASTRONAUT_FLOAT_GRID, ASTRONAUT_COLORS, 3)

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

# Radiant Primary Star (9x9)
BEACON_STAR_GRID = [
    "....X....",
    "...XXX...",
    "..XXLXX..",
    "XXXXXXXXX",
    ".XXXLXXX.",
    "XXXXXXXXX",
    "..XXLXX..",
    "...XXX...",
    "....X....",
]
BEACON_STAR = sprite(BEACON_STAR_GRID, {"X": GOLD, "L": "#FFFDF0"}, 4)
BEACON_STAR_S = sprite(BEACON_STAR_GRID, {"X": GOLD, "L": "#FFFDF0"}, 2)

# Mini 4-Point Star (5x5)
STAR_4PT_GRID = [
    "..X..",
    ".XLX.",
    "XXXXX",
    ".XLX.",
    "..X..",
]
STAR_MINI = sprite(STAR_4PT_GRID, {"X": GOLD, "L": GOLD_L}, 3)


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

    # Bintang-bintang kosmik latar belakang
    stars = []
    positions = [
        (35, 52, 2), (80, 85, 3), (130, 42, 2), (180, 75, 2), (230, 110, 3),
        (280, 55, 2), (320, 80, 1), (370, 45, 2), (430, 68, 3), (490, 48, 2),
        (540, 78, 1), (610, 52, 2), (670, 88, 3), (720, 40, 2), (780, 65, 1),
        (830, 50, 3), (870, 80, 2), (60, 145, 1), (110, 180, 2), (160, 215, 3),
        (220, 170, 1), (270, 195, 2), (340, 160, 3), (400, 185, 1), (460, 210, 2),
        (520, 175, 1), (580, 190, 2), (640, 160, 3), (700, 185, 1), (760, 210, 2),
        (820, 170, 3), (865, 200, 1),
    ]
    for i, (sx, sy, sz) in enumerate(positions):
        delay = (i * 0.28) % 2.5
        col = GOLD_L if i % 4 == 0 else (SKY3 if i % 3 == 0 else WHITE)
        stars.append(f'<rect class="twinkle" style="animation-delay:{delay:.2f}s" x="{sx}" y="{sy}" width="{sz}" height="{sz}" fill="{col}"/>')

    # Garis-garis rasi bintang dekoratif di latar
    constellations = [
        '<path d="M80 85L130 42L180 75L230 110" stroke="#005A9C" stroke-width="1" stroke-dasharray="2 3" opacity="0.4"/>',
        '<path d="M670 88L720 40L780 65" stroke="#005A9C" stroke-width="1" stroke-dasharray="2 3" opacity="0.4"/>',
        '<path d="M220 170L270 195L340 160L400 185" stroke="#1B365D" stroke-width="1" stroke-dasharray="2 3" opacity="0.45"/>',
        '<path d="M640 160L700 185L760 210L820 170" stroke="#1B365D" stroke-width="1" stroke-dasharray="2 3" opacity="0.45"/>',
    ]

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Stellar Explorer Banner: Andika Dwi Putra">
<defs>
  <linearGradient id="cosmos" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{DEEP}"/>
    <stop offset="45%" stop-color="{NAVY}"/>
    <stop offset="85%" stop-color="{DEEP}"/>
    <stop offset="100%" stop-color="{BLUE}"/>
  </linearGradient>
  <radialGradient id="nebula" cx="70%" cy="30%" r="55%">
    <stop offset="0%" stop-color="{BLUE}" stop-opacity="0.35"/>
    <stop offset="60%" stop-color="{NAVY}" stop-opacity="0.15"/>
    <stop offset="100%" stop-color="{DEEP}" stop-opacity="0"/>
  </radialGradient>
</defs>
<style>
  {FONT}
  .spacewalk {{ animation: float_zero_g 6s ease-in-out infinite; }}
  .satellite {{ animation: orbit_drift 16s ease-in-out infinite alternate; }}
  .star-beacon {{ animation: pulse_star 2.8s ease-in-out infinite alternate; }}
  .twinkle {{ animation: twinkle 2.2s ease-in-out infinite alternate; }}
  .meteor {{ animation: shooting_star 7s ease-in infinite; }}
  .scanner-glow {{ animation: pulse_scan 2s ease-in-out infinite alternate; }}
  .blink {{ animation: blink 1.1s steps(1) infinite; }}
  @keyframes float_zero_g {{
    0% {{ transform: translate(0, 0) rotate(0deg); }}
    35% {{ transform: translate(6px, -18px) rotate(-4deg); }}
    70% {{ transform: translate(-4px, -8px) rotate(2deg); }}
    100% {{ transform: translate(0, 0) rotate(0deg); }}
  }}
  @keyframes orbit_drift {{
    from {{ transform: translateX(0); }}
    to {{ transform: translateX(50px); }}
  }}
  @keyframes pulse_star {{
    0% {{ transform: scale(1); opacity: 0.85; }}
    100% {{ transform: scale(1.18); opacity: 1; }}
  }}
  @keyframes pulse_scan {{
    0% {{ opacity: 0.3; }}
    100% {{ opacity: 0.8; }}
  }}
  @keyframes twinkle {{
    0%,20% {{ opacity: 0.2; }}
    50% {{ opacity: 1; }}
    80%,100% {{ opacity: 0.35; }}
  }}
  @keyframes shooting_star {{
    0%,60% {{ transform: translate(0, 0); opacity: 0; }}
    62% {{ opacity: 1; }}
    75% {{ transform: translate(-220px, 120px); opacity: 0; }}
    100% {{ opacity: 0; }}
  }}
  @keyframes blink {{ 0%,50% {{ opacity: 1; }} 50.01%,100% {{ opacity: 0; }} }}
</style>

<!-- Deep Cosmos Background -->
<rect width="{W}" height="{H}" fill="url(#cosmos)"/>
<rect width="{W}" height="{H}" fill="url(#nebula)"/>

<!-- Constellation Grid Lines & Twinkling Stars -->
{"".join(constellations)}
{"".join(stars)}

<!-- Shooting Star / Meteor -->
<g class="meteor" transform="translate(860, 20)">
  <line x1="0" y1="0" x2="30" y2="-16" stroke="{GOLD_L}" stroke-width="2" opacity="0.8"/>
  <rect x="0" y="0" width="3" height="3" fill="#FFFFFF"/>
</g>

<!-- Distant Ringed Exoplanet -->
<g opacity="0.75" transform="translate(730, 45)"><g>{PLANET_RINGED}</g></g>

<!-- Deep Space Observatory Satellite -->
<g class="satellite" opacity="0.65" transform="translate(480, 42)"><g>{TELESCOPE}</g></g>

<!-- Top Sci-Fi Navigation HUD -->
<rect width="{W}" height="34" fill="{DEEP}" opacity="0.8"/>
<rect x="0" y="33" width="{W}" height="1" fill="{BLUE}"/>
<text x="24" y="22" font-size="13" fill="#FFFFFF" letter-spacing="2">[PILOT: AKID]</text>
<text x="220" y="22" font-size="13" fill="{GOLD}" letter-spacing="2">★ STARS DISCOVERED: {score:06d}</text>
<text x="560" y="22" font-size="13" fill="{SKY3}" letter-spacing="2">SYSTEMS: x{coins:02d}</text>
<text x="876" y="22" text-anchor="end" font-size="13" fill="{GOLD}" letter-spacing="2">MISSION: {esc(quest)}</text>

<!-- Primary Radiant Beacon Star -->
<g transform="translate(245, 120)">
  <circle cx="18" cy="18" r="28" fill="{BLUE}" opacity="0.25" class="scanner-glow"/>
  <g class="star-beacon" style="transform-origin: 18px 18px;">{BEACON_STAR}</g>
  <path d="M-60 18L0 18" stroke="{CYAN}" stroke-width="1" stroke-dasharray="3 3" opacity="0.6"/>
</g>

<!-- Spacewalking Astronaut in Zero-G -->
<g class="spacewalk" style="transform-origin: 130px 145px;" transform="translate(100, 115)">
  <!-- Tether Cable connecting to spacecraft -->
  <path d="M-90 40 C -50 20, -20 60, 4 35" fill="none" stroke="{SKY1}" stroke-width="2" opacity="0.45"/>
  <rect x="-95" y="38" width="6" height="6" fill="{BLUE}"/>
  <g>{HERO_FLOAT}</g>
  <!-- Scanner beam projection -->
  <polygon points="68,36 145,20 145,52" fill="{CYAN}" opacity="0.12" class="scanner-glow"/>
  <line x1="68" y1="36" x2="145" y2="36" stroke="{CYAN}" stroke-width="1" stroke-dasharray="2 3" opacity="0.7"/>
</g>

<!-- Center Typography & Status -->
<text x="583" y="103" text-anchor="middle" font-size="34" fill="{DEEP}" letter-spacing="3">ANDIKA DWI PUTRA</text>
<text x="580" y="100" text-anchor="middle" font-size="34" fill="#FFFFFF" letter-spacing="3">ANDIKA DWI PUTRA</text>
<text x="580" y="132" text-anchor="middle" font-size="14" fill="{SKY3}" letter-spacing="4">STELLAR EXPLORER • COMPUTER SCIENCE</text>
<text class="blink" x="580" y="166" text-anchor="middle" font-size="13" fill="{GOLD}" letter-spacing="3">&gt; CHARTING THE DIGITAL UNIVERSE_</text>

<!-- Tech Telemetry Grid Bottom Border -->
<rect x="0" y="{H-10}" width="{W}" height="10" fill="{DEEP}"/>
<rect x="0" y="{H-10}" width="{W}" height="2" fill="{NAVY}"/>
<rect x="40" y="{H-6}" width="4" height="4" fill="{BLUE}"/>
<rect x="60" y="{H-6}" width="20" height="2" fill="{NAVY}"/>
<rect x="90" y="{H-6}" width="4" height="4" fill="{SKY3}"/>
<rect x="110" y="{H-6}" width="40" height="2" fill="{NAVY}"/>
<rect x="{W-150}" y="{H-6}" width="40" height="2" fill="{NAVY}"/>
<rect x="{W-100}" y="{H-6}" width="4" height="4" fill="{GOLD}"/>
<rect x="{W-80}" y="{H-6}" width="20" height="2" fill="{NAVY}"/>
<rect x="{W-50}" y="{H-6}" width="4" height="4" fill="{BLUE}"/>
</svg>
'''


# ───────────────────────── stats ─────────────────────────
def sci_fi_card(x, y, w, h, title, icon=""):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{DEEP}" opacity="0.9"/>'
        f'<rect x="{x+2}" y="{y+2}" width="{w-4}" height="{h-4}" fill="none" stroke="{NAVY}" stroke-width="3"/>'
        f'<rect x="{x+6}" y="{y+6}" width="{w-12}" height="{h-12}" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.6"/>'
        # Corner brackets
        f'<path d="M{x+2} {y+16}V{y+2}H{x+16}" fill="none" stroke="{SKY3}" stroke-width="2"/>'
        f'<path d="M{x+w-16} {y+2}H{x+w-2}V{y+16}" fill="none" stroke="{SKY3}" stroke-width="2"/>'
        f'<path d="M{x+2} {y+h-16}V{y+h-2}H{x+16}" fill="none" stroke="{SKY3}" stroke-width="2"/>'
        f'<path d="M{x+w-16} {y+h-2}H{x+w-2}V{y+h-16}" fill="none" stroke="{SKY3}" stroke-width="2"/>'
        # Title bar
        f'<g transform="translate({x+20},{y+18})">{icon}</g>'
        f'<text x="{x+54}" y="{y+36}" font-size="15" fill="#FFFFFF" letter-spacing="3">{title}</text>'
        f'<line x1="{x+18}" y1="{y+48}" x2="{x+w-18}" y2="{y+48}" stroke="{BLUE}" stroke-width="2" opacity="0.5"/>'
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
    left = sci_fi_card(10, 10, 430, 220, "STELLAR LOGBOOK", STAR_MINI)
    for i, (k, v) in enumerate(rows):
        y = 86 + i * 28
        left += f'<text x="32" y="{y}" font-size="13" fill="{SKY3}" letter-spacing="1">{k}</text>'
        left += f'<text x="414" y="{y}" text-anchor="end" font-size="14" fill="{GOLD if i==0 else "#FFFFFF"}">{v}</text>'
        left += f'<path d="M32 {y+8}H414" stroke="{NAVY}" stroke-width="1" stroke-dasharray="4 4"/>'

    right = sci_fi_card(460, 10, 430, 220, "MISSION TELEMETRY", TELESCOPE)
    langs = sorted(prof["langs"].items(), key=lambda kv: -kv[1])[:5]
    total_b = sum(prof["langs"].values()) or 1
    if not langs:
        right += f'<text x="484" y="110" font-size="13" fill="{SKY3}">NO DATA YET</text>'
    for i, (name, b) in enumerate(langs):
        y = 86 + i * 28
        pct = b * 100 / total_b
        filled = max(1, round(pct / 100 * 12))
        right += f'<text x="484" y="{y}" font-size="13" fill="#FFFFFF">{esc(name[:11].upper())}</text>'
        for s in range(12):
            color = SKY2 if s < filled else SPACE_DARK
            right += f'<rect x="{600+s*16}" y="{y-12}" width="13" height="14" fill="{color}" stroke="{BLUE}" stroke-width="1"/>'
        right += f'<text x="870" y="{y}" text-anchor="end" font-size="13" fill="{SKY3}">{pct:.0f}%</text>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Stellar logbook and mission telemetry">
<style>{FONT}</style>
{left}
{right}
</svg>
'''


# ───────────────────────── celestial cartography ─────────────────────────
def grade_for(total):
    for limit, g in ((1000, "S"), (600, "A"), (300, "B"), (100, "C")):
        if total >= limit:
            return g
    return "D"


def make_game(days, total, best):
    """Peta konstelasi bintang nyata dari kontribusi GitHub dengan astronot melakukan pemetaan radar kosmik."""
    W, H = 900, 300
    T = 20  # Durasi siklus animasi dalam detik

    gx, gy = 145, 68
    pitch_x, pitch_y = 13.8, 17.0
    cols = max(d[2] for d in days) + 1
    nblocks = sum(1 for d in days if d[3] > 0)

    # Membangun simpul-simpul bintang dari data kontribusi nyata
    star_nodes = []
    active_points = []
    for d, r, c, lvl in days:
        sx = gx + c * pitch_x
        sy = gy + r * pitch_y
        if lvl == 0:
            star_nodes.append(f'<rect x="{sx+4:.1f}" y="{sy+4:.1f}" width="2" height="2" fill="{NAVY}" opacity="0.35"/>')
        elif lvl == 1:
            active_points.append((sx + 5, sy + 5, lvl))
            star_nodes.append(f'<rect x="{sx+3:.1f}" y="{sy+3:.1f}" width="4" height="4" fill="{BLUE}"/>')
        elif lvl == 2:
            active_points.append((sx + 5, sy + 5, lvl))
            star_nodes.append(f'<polygon points="{sx+5:.1f},{sy+1:.1f} {sx+8:.1f},{sy+5:.1f} {sx+5:.1f},{sy+9:.1f} {sx+2:.1f},{sy+5:.1f}" fill="{SKY1}"/>')
        elif lvl == 3:
            active_points.append((sx + 5, sy + 5, lvl))
            star_nodes.append(
                f'<rect x="{sx+2:.1f}" y="{sy+2:.1f}" width="6" height="6" fill="{SKY2}"/>'
                f'<rect x="{sx+4:.1f}" y="{sy+4:.1f}" width="2" height="2" fill="#FFFFFF"/>'
            )
        elif lvl == 4:
            active_points.append((sx + 5, sy + 5, lvl))
            star_nodes.append(
                f'<polygon points="{sx+5:.1f},{sy:.1f} {sx+9:.1f},{sy+5:.1f} {sx+5:.1f},{sy+10:.1f} {sx+1:.1f},{sy+5:.1f}" fill="{GOLD}"/>'
                f'<rect x="{sx+3:.1f}" y="{sy+3:.1f}" width="4" height="4" fill="#FFFFFF"/>'
            )

    # Garis-garis konstelasi halus menghubungkan gugusan bintang terdekat
    constellation_lines = []
    for i in range(len(active_points) - 1):
        x1, y1, l1 = active_points[i]
        x2, y2, l2 = active_points[i + 1]
        dist = math.hypot(x2 - x1, y2 - y1)
        if dist < 32 and (l1 >= 2 or l2 >= 2):
            constellation_lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{SKY3}" stroke-width="1" stroke-dasharray="2 3" opacity="0.35"/>')

    # Status & Overlay Timeline
    css = [
        "@keyframes scan_sweep {"
        "  0% { transform: translateX(0); opacity: 0; }"
        "  5% { opacity: 0.9; }"
        "  40% { transform: translateX(740px); opacity: 0.9; }"
        "  45%,100% { transform: translateX(740px); opacity: 0; }"
        "}",
        "@keyframes hud_fade {"
        "  0%,44% { opacity: 0; transform: translateY(8px); }"
        "  48%,94% { opacity: 1; transform: translateY(0); }"
        "  98%,100% { opacity: 0; transform: translateY(-8px); }"
        "}",
        "@keyframes float_astro {"
        "  0%,100% { transform: translateY(0) rotate(0deg); }"
        "  50% { transform: translateY(-12px) rotate(-3deg); }"
        "}",
        "@keyframes starlight_pulse {"
        "  0%,100% { opacity: 0.4; }"
        "  50% { opacity: 0.9; }"
        "}",
    ]

    def kf(name, body):
        return f"@keyframes {name}{{{body}}}"

    def win(name, a, b):
        css.append(kf(name, f"0%,{a}%{{opacity:0}}{a+0.5}%,{b}%{{opacity:1}}{b+0.5}%,100%{{opacity:0}}"))

    win("phase1", 0, 16)
    win("phase2", 17, 38)
    win("phase3", 39, 44)

    # Roll-up angka bintang
    N, S0, S1 = 12, 54.0, 68.0
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

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Celestial Cartography: Star discovery constellation map">
<defs>
  <linearGradient id="chart_bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{DEEP}"/>
    <stop offset="60%" stop-color="{NAVY}"/>
    <stop offset="100%" stop-color="{DEEP}"/>
  </linearGradient>
  <linearGradient id="scan_beam" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{CYAN}" stop-opacity="0"/>
    <stop offset="70%" stop-color="{CYAN}" stop-opacity="0.3"/>
    <stop offset="100%" stop-color="{CYAN}" stop-opacity="0.9"/>
  </linearGradient>
</defs>
<style>
  {FONT}
  .astro-float {{ animation: float_astro 5s ease-in-out infinite; }}
  .scan-wave  {{ animation: scan_sweep {T}s cubic-bezier(0.2, 0.8, 0.4, 1) infinite; }}
  .hud-result {{ animation: hud_fade {T}s ease-in-out infinite; }}
  .pulse-starlight {{ animation: starlight_pulse 3s ease-in-out infinite alternate; }}
  {"".join(css)}
</style>

<!-- Deep Space Chart Canvas -->
<rect width="{W}" height="{H}" fill="url(#chart_bg)"/>

<!-- Grid Coordinate Guides -->
<path d="M{gx} {gy-12}H880M{gx} {gy+122}H880" stroke="{NAVY}" stroke-width="1" stroke-dasharray="6 6" opacity="0.6"/>
<text x="{gx}" y="{gy-18}" font-size="10" fill="{SKY1}" letter-spacing="2">SECTOR 01 [52 WEEKS CELESTIAL COORDINATES]</text>

<!-- Constellation Links & Star Nodes -->
<g class="pulse-starlight">{"".join(constellation_lines)}</g>
{"".join(star_nodes)}

<!-- Scanner Laser Radar Wave -->
<g class="scan-wave" transform="translate({gx}, {gy-15})">
  <rect width="24" height="142" fill="url(#scan_beam)"/>
  <line x1="24" y1="0" x2="24" y2="142" stroke="{WHITE}" stroke-width="1.5"/>
</g>

<!-- Floating Astronaut Mapping Stars on Left -->
<g class="astro-float" transform="translate(36, 100)">
  <!-- Navigation Tether -->
  <path d="M-20 -15 C 5 -30, 15 -10, 24 10" fill="none" stroke="{SKY1}" stroke-width="2" opacity="0.5"/>
  <rect x="-24" y="-18" width="6" height="6" fill="{BLUE}"/>
  <g>{HERO_FLOAT_S}</g>
  <!-- Scanner Sensor Cone -->
  <polygon points="56,26 100,5 100,48" fill="{CYAN}" opacity="0.12"/>
  <line x1="56" y1="26" x2="105" y2="26" stroke="{CYAN}" stroke-width="1" stroke-dasharray="2 2" opacity="0.6"/>
</g>

<!-- Top Cartography HUD Bar -->
<rect width="{W}" height="34" fill="{DEEP}" opacity="0.8"/>
<line x1="0" y1="33" x2="{W}" y2="33" stroke="{BLUE}" stroke-width="1"/>
<text x="20" y="22" font-size="13" fill="#FFFFFF" letter-spacing="2">CELESTIAL CARTOGRAPHY</text>
<text x="880" y="22" text-anchor="end" font-size="13" fill="{GOLD}" letter-spacing="2">CHARTED NODES: {nblocks} STARS</text>

<!-- Dynamic Status Telemetry (Bottom) -->
<rect x="0" y="{H-32}" width="{W}" height="32" fill="{DEEP}" opacity="0.85"/>
<line x1="0" y1="{H-32}" x2="{W}" y2="{H-32}" stroke="{NAVY}" stroke-width="1"/>
<text style="opacity:0;animation:phase1 {T}s linear infinite" x="24" y="{H-12}" font-size="12" fill="{GOLD}" letter-spacing="2">&gt; SCANNING UNCHARTED STELLAR SECTORS...</text>
<text style="opacity:0;animation:phase2 {T}s linear infinite" x="24" y="{H-12}" font-size="12" fill="{CYAN}" letter-spacing="2">&gt; MAPPING CONSTELLATION COORDINATES ACROSS 52 CYCLES...</text>
<text style="opacity:0;animation:phase3 {T}s linear infinite" x="24" y="{H-12}" font-size="12" fill="{SKY3}" letter-spacing="2">&gt; SECTOR CATALOGUED • {total} STARS SYNCHRONIZED</text>

<!-- Holographic Mission Result HUD -->
<g class="hud-result" style="opacity:0;">
  <rect width="{W}" height="{H}" fill="{DEEP}" opacity="0.88"/>
  <rect x="230" y="46" width="440" height="206" fill="{NAVY}"/>
  <rect x="232" y="48" width="436" height="202" fill="none" stroke="{BLUE}" stroke-width="4"/>
  <rect x="238" y="54" width="424" height="190" fill="none" stroke="{SKY3}" stroke-width="1" opacity="0.4"/>
  
  <!-- Corner Brackets -->
  <path d="M232 60V48H244M656 48H668V60M232 238V250H244M656 250H668V238" stroke="{CYAN}" stroke-width="2" fill="none"/>

  <text x="450" y="86" text-anchor="middle" font-size="22" fill="{GOLD}" letter-spacing="5">EXPEDITION REPORT</text>
  
  <text x="256" y="120" font-size="13" fill="{SKY3}" letter-spacing="1">STARS DISCOVERED</text>
  <text x="644" y="120" text-anchor="end" font-size="14" fill="#FFFFFF">{total} ★</text>
  
  <text x="256" y="146" font-size="13" fill="{SKY3}" letter-spacing="1">CHARTED STELLAR NODES</text>
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

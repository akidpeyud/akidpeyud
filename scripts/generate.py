#!/usr/bin/env python3
"""
Generator aset pixel-art untuk profil GitHub.

Menghasilkan 3 file SVG di folder assets/:
  - banner.svg        : banner + HUD (score = kontribusi, coins = repo, quest = repo terakhir di-push)
  - stats.svg         : kartu "Player Stats" + "Top Languages" bergaya pixel
  - contrib-game.svg  : grafik kontribusi jadi game: hero berlari & mengambil "koin" kontribusi

Hanya memakai pustaka standar Python. Setiap bagian punya fallback, jadi kalau satu
API gagal, file lain tetap terbuat.
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

# Palet
NAVY, BLUE = "#1B365D", "#005A9C"
DEEP = "#0D1B2E"
SKY1, SKY2, SKY3 = "#2F8FD8", "#4DA3E0", "#7FC4FF"
PALE = "#D6E8F5"
GOLD, GOLD_L = "#FFD166", "#FFF0B8"
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
        assert len(row) == w, row
        for c, ch in enumerate(row):
            if ch in colors:
                out.append(f'<rect x="{c*px}" y="{r*px}" width="{px}" height="{px}" fill="{colors[ch]}"/>')
    return "".join(out)


HERO = sprite([
    "...HHHH...", "..HHHHHH..", "..HSSSSH..", "..SSESES..", "..SSSSSS..",
    "...SSSS...", ".BBBBBBBB.", "SBBBBBBBBS", "SBBBBBBBBS", ".BBBBBBBB.",
    "..PPPPPP..", "..PP..PP..", "..PP..PP..", ".WWW..WWW.",
], {"H": DEEP, "S": "#F2C9A0", "E": DEEP, "B": SKY3, "P": DEEP, "W": "#FFFFFF"}, 5)

HERO_S = sprite([
    "...HHHH...", "..HHHHHH..", "..HSSSSH..", "..SSESES..", "..SSSSSS..",
    "...SSSS...", ".BBBBBBBB.", "SBBBBBBBBS", "SBBBBBBBBS", ".BBBBBBBB.",
    "..PPPPPP..", "..PP..PP..", "..PP..PP..", ".WWW..WWW.",
], {"H": DEEP, "S": "#F2C9A0", "E": DEEP, "B": SKY3, "P": DEEP, "W": "#FFFFFF"}, 3)

SLIME = sprite([
    "..GGGG..", ".GGGGGG.", "GEGGGGEG", "GGGGGGGG", ".GGGGGG.",
], {"G": PALE, "E": DEEP}, 5)

GEM = sprite([
    "..X..", ".XXX.", "XXXXX", ".XXX.", "..X..",
], {"X": GOLD}, 5)

CLOUD = sprite([
    "...XXXX.....", ".XXXXXXXXX..", "XXXXXXXXXXXX",
], {"X": PALE}, 6)

COIN = sprite([
    ".XX.", "XLXX", "XLXX", "XLXX", "XLXX", ".XX.",
], {"X": GOLD, "L": GOLD_L}, 4)

FLAG = sprite([
    "XXXXXX", ".XXXXX", "..XXXX", "...XXX", "....XX", ".....X",
], {"X": GOLD}, 5)

STAR = sprite([
    "..X..", "..X..", "XXXXX", ".XXX.", ".X.X.",
], {"X": GOLD}, 4)


def hill(x0, steps, w0, step_w, step_h, ground, fill):
    return "".join(
        f'<rect x="{x0+i*step_w}" y="{ground-(i+1)*step_h}" width="{w0-i*2*step_w}" height="{step_h}" fill="{fill}"/>'
        for i in range(steps)
    )


def ground_tiles(W, ground, rows=2):
    out = []
    for r in range(rows):
        for c in range(W // 24 + 1):
            out.append(f'<rect x="{c*24}" y="{ground+8+r*24}" width="24" height="24" fill="{DEEP}" stroke="{NAVY}" stroke-width="2"/>')
    return (
        "".join(out)
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
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Pixel art banner: Andika Dwi Putra">
<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{NAVY}"/><stop offset="1" stop-color="{BLUE}"/></linearGradient></defs>
<style>
  {FONT}
  .hero  {{ animation: jump 2.6s ease-in-out infinite; }}
  .block {{ animation: bump 2.6s ease-in-out infinite; }}
  .gem   {{ animation: pop 2.6s ease-out infinite; opacity: 0; }}
  .slime {{ animation: walk 7s linear infinite alternate; }}
  .c1 {{ animation: drift 9s ease-in-out infinite alternate; }}
  .c2 {{ animation: drift 12s ease-in-out infinite alternate-reverse; }}
  .coin  {{ animation: bob 1.4s ease-in-out infinite alternate; }}
  .blink {{ animation: blink 1.1s steps(1) infinite; }}
  @keyframes jump {{ 0%,12% {{ transform: translateY(0); }} 26% {{ transform: translateY(-30px); }} 38%,100% {{ transform: translateY(0); }} }}
  @keyframes bump {{ 0%,24% {{ transform: translateY(0); }} 28% {{ transform: translateY(-7px); }} 34%,100% {{ transform: translateY(0); }} }}
  @keyframes pop  {{ 0%,26% {{ opacity: 0; transform: translateY(0); }} 28% {{ opacity: 1; transform: translateY(0); }} 55% {{ opacity: 1; transform: translateY(-38px); }} 62%,100% {{ opacity: 0; transform: translateY(-46px); }} }}
  @keyframes walk {{ from {{ transform: translateX(0); }} to {{ transform: translateX(170px); }} }}
  @keyframes drift {{ from {{ transform: translateX(0); }} to {{ transform: translateX(36px); }} }}
  @keyframes bob  {{ from {{ transform: translateY(0); }} to {{ transform: translateY(-6px); }} }}
  @keyframes blink {{ 0%,50% {{ opacity: 1; }} 50.01%,100% {{ opacity: 0; }} }}
</style>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
<g class="c1" opacity="0.30" transform="translate(300,44)"><g>{CLOUD}</g></g>
<g class="c2" opacity="0.22" transform="translate(770,46)"><g>{CLOUD}</g></g>
{hill(480, 5, 280, 20, 14, G, NAVY)}
{hill(40, 4, 200, 20, 14, G, NAVY)}

<rect width="{W}" height="34" fill="{DEEP}" opacity="0.55"/>
<text x="20" y="22" font-size="13" fill="#FFFFFF" letter-spacing="2">AKID x03</text>
<text x="230" y="22" font-size="13" fill="#FFFFFF" letter-spacing="2">SCORE {score:06d}</text>
<text x="470" y="22" font-size="13" fill="{GOLD}" letter-spacing="2">COINS x{coins:02d}</text>
<text x="880" y="22" text-anchor="end" font-size="13" fill="{SKY3}" letter-spacing="2">QUEST: {esc(quest)}</text>

<text x="563" y="103" text-anchor="middle" font-size="38" fill="{DEEP}" letter-spacing="2">ANDIKA DWI PUTRA</text>
<text x="560" y="100" text-anchor="middle" font-size="38" fill="#FFFFFF" letter-spacing="2">ANDIKA DWI PUTRA</text>
<text x="560" y="132" text-anchor="middle" font-size="16" fill="{SKY3}" letter-spacing="4">COMPUTER SCIENCE STUDENT</text>
<text class="blink" x="560" y="166" text-anchor="middle" font-size="14" fill="{GOLD}" letter-spacing="3">&gt; PRESS START</text>

<rect x="110" y="52" width="48" height="48" fill="{NAVY}" stroke="{SKY3}" stroke-width="3"/>
<rect x="206" y="52" width="48" height="48" fill="{NAVY}" stroke="{SKY3}" stroke-width="3"/>
<path d="M110 76H158M134 52V76M206 76H254M230 52V76M110 100V76" stroke="{SKY3}" stroke-width="2" opacity="0.5" fill="none"/>
<g class="block"><rect x="158" y="52" width="48" height="48" fill="{BLUE}" stroke="{SKY3}" stroke-width="3"/>
<text x="182" y="84" text-anchor="middle" font-size="22" fill="#FFFFFF">{{}}</text></g>
<g class="gem"><g transform="translate(170,26)">{GEM}</g></g>
<g class="hero"><g transform="translate(157,{G-70})">{HERO}</g></g>
<g class="slime"><g transform="translate(600,{G-25})">{SLIME}</g></g>

<g class="coin"><g transform="translate(290,146)">{COIN}</g></g>
<g class="coin" style="animation-delay:.25s"><g transform="translate(325,138)">{COIN}</g></g>
<g class="coin" style="animation-delay:.5s"><g transform="translate(360,146)">{COIN}</g></g>
<rect x="856" y="96" width="4" height="100" fill="{PALE}"/>
<rect x="853" y="88" width="10" height="10" fill="{GOLD}"/>
<g transform="translate(826,102)">{FLAG}</g>
<rect x="846" y="184" width="24" height="12" fill="{NAVY}" stroke="{SKY3}" stroke-width="2"/>
{ground_tiles(W, G)}
</svg>
'''


# ───────────────────────── stats ─────────────────────────
def card(x, y, w, h, title, icon=""):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{NAVY}"/>'
        f'<rect x="{x+2}" y="{y+2}" width="{w-4}" height="{h-4}" fill="none" stroke="{BLUE}" stroke-width="4"/>'
        f'<rect x="{x+8}" y="{y+8}" width="{w-16}" height="{h-16}" fill="none" stroke="{SKY3}" stroke-width="1" opacity="0.35"/>'
        f'<g transform="translate({x+22},{y+20})">{icon}</g>'
        f'<text x="{x+52}" y="{y+38}" font-size="16" fill="#FFFFFF" letter-spacing="3">{title}</text>'
    )


def make_stats(total, cur, best, prof):
    W, H = 900, 240
    rows = [
        ("CONTRIBS (1Y)", f"{total}"),
        ("PUBLIC REPOS", f"{prof['repos']}"),
        ("STARS", f"{prof['stars']}"),
        ("FOLLOWERS", f"{prof['followers']}"),
        ("STREAK NOW/BEST", f"{cur}/{best}"),
    ]
    left = card(10, 10, 430, 220, "PLAYER STATS", STAR)
    for i, (k, v) in enumerate(rows):
        y = 84 + i * 28
        left += f'<text x="34" y="{y}" font-size="14" fill="{SKY3}" letter-spacing="1">{k}</text>'
        left += f'<text x="416" y="{y}" text-anchor="end" font-size="15" fill="#FFFFFF">{v}</text>'
        left += f'<path d="M34 {y+8}H416" stroke="{BLUE}" stroke-width="2" stroke-dasharray="4 4"/>'

    right = card(460, 10, 430, 220, "TOP LANGUAGES", STAR)
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

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Player stats and top languages">
<style>{FONT}</style>
{left}
{right}
</svg>
'''


# ───────────────────────── contribution game ─────────────────────────
COIN_S = sprite([
    ".XX.", "XLXX", "XLXX", "XLXX", "XLXX", ".XX.",
], {"X": GOLD, "L": GOLD_L}, 3)

STONE = sprite([
    ".XXX.", "XXLXX", "XLXXX", "XXXXX", ".XXX.",
], {"X": "#8FA7BF", "L": PALE}, 4)

LEVEL_FILL = {1: BLUE, 2: SKY1, 3: SKY2, 4: SKY3}


def grade_for(total):
    for limit, g in ((1000, "S"), (600, "A"), (300, "B"), (100, "C")):
        if total >= limit:
            return g
    return "D"


def make_game(days, total, best):
    """Satu putaran: hero melempar batu -> medan kontribusi meledak berantai -> layar hasil + skor."""
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
    NB = 10                       # jumlah "gelombang" ledakan
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

    blocks, coins = [], []
    for c, i, lvl, bx, by, dist in cells:
        k = min(NB - 1, int(dist / dmax * NB))
        ux, uy = (bx + size / 2 - ix) / max(dist, 1), (by + size / 2 - iy) / max(dist, 1)
        sp = 40 + rnd() * 90
        v = (f"--hx:{ux*sp*0.5:.0f}px;--hy:{uy*sp*0.5-30:.0f}px;--dx:{ux*sp*1.1+(rnd()-.5)*20:.0f}px;"
             f"--dy:{G-by+40+rnd()*30:.0f}px;--hr:{(rnd()-.5)*240:.0f}deg;--dr:{(rnd()-.5)*720:.0f}deg")
        blocks.append(
            f'<g class="b" style="{v};animation:bm{k} {T}s linear infinite">'
            f'<rect x="{bx}" y="{by}" width="{size}" height="{size}" fill="{LEVEL_FILL[lvl]}"/>'
            f'<rect x="{bx+2}" y="{by+2}" width="3" height="3" fill="#FFFFFF" opacity="0.5"/>'
            + (f'<rect x="{bx}" y="{by}" width="{size}" height="3" fill="{PALE}" opacity="0.75"/>' if i == 0 else "")
            + "</g>")
    for c in active:
        cx = gx + c * pitch + size / 2
        d = math.hypot(cx - ix, top(c) - 20 - iy)
        k = min(NB - 1, int(d / dmax * NB))
        ux = (cx - ix) / max(d, 1)
        v = f"--hx:{ux*10:.0f}px;--hy:-26px;--dx:{ux*24:.0f}px;--dy:-72px;--hr:0deg;--dr:0deg"
        coins.append(
            f'<g class="b" style="{v};animation:bm{k} {T}s linear infinite">'
            f'<g transform="translate({cx-6:.1f},{top(c)-31})">{COIN_S}</g></g>')

    # ── lemparan batu (parabola) ──
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

    # ── hero, efek ledakan, status ──
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

    # hitung-naik skor
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

    # percikan
    sparks = []
    for j in range(12):
        ang = j / 12 * 2 * math.pi
        dist = 50 + rnd() * 70
        sparks.append(f'<rect x="{ix-3:.1f}" y="{iy-3:.1f}" width="6" height="6" fill="{GOLD if j%2 else "#FFFFFF"}" '
                      f'style="--sx:{math.cos(ang)*dist:.0f}px;--sy:{math.sin(ang)*dist-10:.0f}px;opacity:0;animation:spark {T}s linear infinite"/>')

    # bintang latar
    stars = []
    for _ in range(34):
        sx = int(rnd() * W)
        sy = 42 + int(rnd() * 110)
        stars.append(f'<rect x="{sx}" y="{sy}" width="3" height="3" fill="{PALE}" opacity="0.35"/>')

    grade = grade_for(total)
    gcol = {"S": GOLD, "A": SKY3, "B": SKY2, "C": SKY1, "D": PALE}[grade]
    A = lambda cls, extra="": f'class="{cls}" style="opacity:0;animation:{cls} {T}s linear infinite{extra}"'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Contribution graph as a pixel game: throw a stone, blow up the blocks, see your score">
<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{DEEP}"/><stop offset="1" stop-color="{NAVY}"/></linearGradient></defs>
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
  @keyframes drift {{ from {{ transform: translateX(0); }} to {{ transform: translateX(50px); }} }}
  {"".join(css)}
</style>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
{"".join(stars)}
<g class="cl1" opacity="0.18" transform="translate(120,56)"><g>{CLOUD}</g></g>
<g class="cl2" opacity="0.14" transform="translate(520,70)"><g>{CLOUD}</g></g>
{hill(40, 4, 220, 20, 12, G, "#16304F")}
{hill(360, 5, 300, 20, 12, G, "#16304F")}

<rect width="{W}" height="34" fill="{DEEP}" opacity="0.7"/>
<text x="20" y="22" font-size="13" fill="#FFFFFF" letter-spacing="2">CONTRIBUTION QUEST</text>
<text x="880" y="22" text-anchor="end" font-size="13" fill="{GOLD}" letter-spacing="2">TARGET: {nblocks} BLOCKS</text>

<g class="scene">
{"".join(blocks)}
{"".join(coins)}
<g transform="translate(60,{G-42})"><g class="hero">{HERO_S}</g></g>
<g class="stone"><g class="spin"><g transform="translate(-10,-10)">{STONE}</g></g></g>
</g>

<circle class="flash fx" cx="{ix:.1f}" cy="{iy:.1f}" r="30" fill="#FFFFFF"/>
<circle class="ring1 fx" cx="{ix:.1f}" cy="{iy:.1f}" r="30" fill="none" stroke="{SKY3}" stroke-width="5"/>
<circle class="ring2 fx" cx="{ix:.1f}" cy="{iy:.1f}" r="30" fill="none" stroke="{GOLD}" stroke-width="4"/>
{"".join(sparks)}

{ground_tiles(W, G, rows=1)}
<text style="opacity:0;animation:s1 {T}s linear infinite" x="20" y="287" font-size="11" fill="{GOLD}" letter-spacing="2">READY...</text>
<text style="opacity:0;animation:s2 {T}s linear infinite" x="20" y="287" font-size="11" fill="{GOLD}" letter-spacing="2">THROW!</text>
<text style="opacity:0;animation:s3 {T}s linear infinite" x="20" y="287" font-size="11" fill="{GOLD}" letter-spacing="2">BOOM!</text>

<g style="opacity:0;animation:ov {T}s linear infinite">
  <rect width="{W}" height="{H}" fill="{DEEP}" opacity="0.82"/>
  <rect x="230" y="46" width="440" height="206" fill="{NAVY}"/>
  <rect x="232" y="48" width="436" height="202" fill="none" stroke="{BLUE}" stroke-width="4"/>
  <rect x="238" y="54" width="424" height="190" fill="none" stroke="{SKY3}" stroke-width="1" opacity="0.35"/>
</g>
<text {A("fadeA")} x="450" y="86" text-anchor="middle" font-size="24" fill="{GOLD}" letter-spacing="6">RESULT</text>
<g {A("fadeB")}>
  <text x="256" y="120" font-size="14" fill="{SKY3}" letter-spacing="1">CONTRIBUTIONS</text>
  <text x="644" y="120" text-anchor="end" font-size="15" fill="#FFFFFF">{total}</text>
</g>
<g {A("fadeC")}>
  <text x="256" y="146" font-size="14" fill="{SKY3}" letter-spacing="1">BLOCKS DESTROYED</text>
  <text x="644" y="146" text-anchor="end" font-size="15" fill="#FFFFFF">{nblocks}</text>
</g>
<g {A("fadeD")}>
  <text x="256" y="172" font-size="14" fill="{SKY3}" letter-spacing="1">BEST STREAK</text>
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
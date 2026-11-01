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
LEVEL_FILL = {0: "#10223C", 1: BLUE, 2: SKY1, 3: SKY2, 4: SKY3}


def make_game(days, total):
    W, H = 900, 270
    cols = max(d[2] for d in days) + 1
    pitch, size = 16, 13
    gx = (W - cols * pitch) // 2 + 1
    gy = 50
    ground = 232
    T = 28  # detik per putaran
    run_end = 0.90

    x0 = gx - 8
    x_end = gx + cols * pitch - 34
    dist = x_end - x0

    keyframes, tiles = [], []
    for c in range(cols):
        cx = gx + c * pitch + size / 2
        p = max(0.0, (cx - 15 - x0) / dist)
        a = min(p * run_end * 100, 93.0)
        keyframes.append(
            f"@keyframes c{c}{{0%,{a:.2f}%{{opacity:1;transform:translateY(0)}}"
            f"{a+0.8:.2f}%,97%{{opacity:0;transform:translateY(-14px)}}100%{{opacity:1;transform:translateY(0)}}}}"
        )
    for d, r, c, lvl in days:
        x, y = gx + c * pitch, gy + r * pitch
        if lvl == 0:
            tiles.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="{LEVEL_FILL[0]}" stroke="{NAVY}" stroke-width="1"/>')
    cols_svg = []
    for c in range(cols):
        inner = ""
        for d, r, cc, lvl in days:
            if cc != c or lvl == 0:
                continue
            x, y = gx + c * pitch, gy + r * pitch
            inner += (
                f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="{LEVEL_FILL[lvl]}"/>'
                f'<rect x="{x+2}" y="{y+2}" width="3" height="3" fill="#FFFFFF" opacity="0.55"/>'
            )
        if inner:
            cols_svg.append(f'<g style="animation:c{c} {T}s linear infinite">{inner}</g>')

    legend = "".join(
        f'<rect x="{738+i*18}" y="12" width="13" height="13" fill="{LEVEL_FILL[i]}"/>' for i in range(5)
    )
    hero_y = ground - 42

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Contribution graph as a pixel game">
<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{DEEP}"/><stop offset="1" stop-color="{NAVY}"/></linearGradient></defs>
<style>
  {FONT}
  .run  {{ animation: run {T}s linear infinite; }}
  .hop  {{ animation: hop {T*run_end/14:.3f}s ease-in-out infinite; }}
  .blink {{ animation: blink 1.1s steps(1) infinite; }}
  @keyframes run {{ 0% {{ transform: translateX(0); }} {run_end*100:.0f}%,100% {{ transform: translateX({dist}px); }} }}
  @keyframes hop {{ 0%,45% {{ transform: translateY(0); }} 65% {{ transform: translateY(-40px); }} 85%,100% {{ transform: translateY(0); }} }}
  @keyframes blink {{ 0%,50% {{ opacity: 1; }} 50.01%,100% {{ opacity: 0; }} }}
  {"".join(keyframes)}
</style>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="34" fill="{DEEP}" opacity="0.7"/>
<text x="20" y="22" font-size="13" fill="#FFFFFF" letter-spacing="2">CONTRIBUTION QUEST</text>
<text x="330" y="22" font-size="13" fill="{GOLD}" letter-spacing="2">SCORE {total:06d}</text>
<text x="728" y="22" text-anchor="end" font-size="11" fill="{SKY3}" letter-spacing="2">LESS</text>
{legend}
<text x="832" y="22" font-size="11" fill="{SKY3}" letter-spacing="2">MORE</text>

{"".join(tiles)}
{"".join(cols_svg)}

<g class="run"><g class="hop"><g transform="translate({x0},{hero_y})">{HERO_S}</g></g></g>
<text class="blink" x="{W-20}" y="{ground-14}" text-anchor="end" font-size="12" fill="{GOLD}" letter-spacing="2">COLLECTING...</text>
{ground_tiles(W, ground, rows=1)}
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
        (OUT / "contrib-game.svg").write_text(make_game(days, total), encoding="utf-8")
    else:
        total, cur, best = 0, 0, 0

    (OUT / "banner.svg").write_text(make_banner(total, prof["repos"], clean_quest(prof["quest"])), encoding="utf-8")
    (OUT / "stats.svg").write_text(make_stats(total, cur, best, prof), encoding="utf-8")
    print(f"ok: score={total} repos={prof['repos']} quest={clean_quest(prof['quest'])}")


if __name__ == "__main__":
    main()
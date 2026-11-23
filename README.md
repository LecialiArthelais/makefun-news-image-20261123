# news-image-20261123 — Monday 23 November 2026 in one image

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/LecialiArthelais/makefun-news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/LecialiArthelais/makefun-news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

Entry for the make.fun bounty **news-image-20261123**
("Sum up 23 November's world news in one image", $100) — see the
[bounty page](https://make.fun/bounty/news-image-20261123).
Closes Tue 25 Nov 2026 07:00 WIB.

Referral code: `3554s5p5` — try make.fun and build your own entry.

## What it is

A single 1024×1024 front page covering **35 dated stories from
Saturday 21 – Sunday 22 November 2026 across 8 regions**, built on
the proven winner template: giant serif date masthead, coloured
region bar, "THE DAY IN NUMBERS" strip (6 figures), a UTC timeline
(6 items), 3 illustrated hero cards, 10 illustrated medium cards,
a smooth-polygon world map with de-collided numbered pins,
22 numbered briefs, a DATE CHECK box, a "HOW TO READ THE TAGS"
legend and sources per story. Every hero and medium carries a
CONFIRMED / REPORTED / CLAIM tag and a named outlet. (The three
stories that were FORECAST at first press — the ATP final,
Liverpool–Man Utd and the Hong Kong count — were refreshed to
their actual results after the bounty opened; no FORECAST tag
remains.)

Angle — "the Sunday the climate talks died". Leads: **COP31 collapses
with no deal** · **14 feared trapped in Dymer** · **Iran claims a 20th
US drone downed; Gulf tanker toll hits 25**.

## Files

- `entry.png` — the rendered front page (the deliverable).
- `build_frontpage.py` — renders `entry.png` from `stories.json`
  with Pillow. Written from scratch in this session. All 13
  illustrations are flat-vector scenes drawn in code on their own
  tiles (nothing can leave its art rect); no raster assets, no
  network, no AI generation. Deterministic output (byte-identical
  on re-runs). The build FAILS on any text overlap, any text
  escaping its card, any DATE CHECK / briefs overflow, or any pin
  collision — see `DESIGN.md` for the gate list.
- `stories.json` — the 35 stories (3 heroes, 10 mediums, 22 briefs),
  numbers strip, timeline, DATE CHECK and footer. Every story carries
  its event date, place, coordinates, sources and a confidence tag.
- `land_polys.json` — Natural Earth 110m land polygons (public domain),
  simplified for the smooth-coastline map.
- `main.ts` — harness entry point (Node, stdlib only): copies
  `entry.png` to `$MAKEFUN_OUTPUT_DIR/entry.png`.
- `DESIGN.md` — competitor-analysis P0 fixes, skill rules applied,
  verification summary and the self-QA log.

## Build

```sh
python3 build_frontpage.py   # writes entry.png (1024x1024)
```

Requires Python 3 + Pillow and the OFL fonts in
`~/workspace/custom-skills/canvas-design/canvas-fonts/`
(Gloock, Crimson Pro, BigShoulders, Geist Mono, Liberation Sans).

## Date rule

Every story is dated by the day its event happened, never the
article date. Events from Saturday 21 – Sunday 22 Nov 2026 are
included; anything 36h+ older is refused to DATE CHECK — including
the US stocks correction (Fri 20 Nov), the FBI NCIC hack (reported
Fri 20 Nov), Russia's 400-drone barrage (Thu night–Fri 20 Nov),
the Peru quake (Fri 20 Nov), GTA 6's $3.79bn day-one sales (Fri
20 Nov), the ICJ Myanmar genocide ruling (Thu 19 Nov), the Shenzhen
summit (Thu 19 Nov) and the Riemann proof claim (Fri 20 Nov).
Two boundary cases are included with their dates stated on the page:
the "El Chapo Isidro" arrest (Fri night, retaliation continued
through the weekend) and the EU–Indonesia signing (Sat 21 Nov).
Press time: Mon 23 Nov 00:08 UTC. See `DESIGN.md` and the
verification ledgers for the source-by-source record.

## Sources

Reuters, AP, BBC, Al Jazeera, The Guardian, UKMTO, ESPNcricinfo,
HK govt, SCMP, Anadolu, Wafa, Sky News, ABC, Straits Times,
Vatican News, MSF, ESA, IANS, TOI, Crypto Briefing, UN,
Tennis Majors, ATP Tour, WRI, Cognoscer brief.

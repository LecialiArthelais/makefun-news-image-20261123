# Monday 23 November 2026: 35 dated stories, 8 regions — COP31 collapses with no deal, 14 feared trapped in Dymer, Gulf tanker toll hits 25

[![Bounty: news-image-20261123](https://img.shields.io/badge/bounty-news--image--20261123-red)](https://make.fun/competitions/news-image-20261123)
[![Stories: 35](https://img.shields.io/badge/stories-35-blue)](https://make.fun/competitions/news-image-20261123)
[![Regions: 8](https://img.shields.io/badge/regions-8-green)](https://make.fun/competitions/news-image-20261123)

Bounty: [news-image-20261123](https://make.fun/competitions/news-image-20261123) ($100, closes Tue 25 Nov 2026 07:00 WIB).

## What this is

A single 1024×1024 front page summing up the world on Monday 23 November
2026: **35 dated stories from Saturday 21 – Sunday 22 November 2026 across
8 regions**, drawn entirely in code (Pillow flat-vector illustration, no
photographs, no AI-generated raster images).

The page leads with the Sunday the climate talks died — **COP31 collapses
with no deal in Antalya**, **14 feared trapped in Dymer** after the
186-drone night, and **Iran's claim of a 20th US drone downed** as the Gulf
tanker toll hits 25. Around them: a giant serif date masthead, a
"THE DAY IN NUMBERS" strip (6 verified figures), a UTC timeline (6 timed
items), 3 illustrated hero cards, 10 illustrated medium cards, a
smooth-polygon world map with numbered pins, 22 numbered briefs, a
DATE CHECK box naming the stories that are *not* 23 November news, and a
"HOW TO READ THE TAGS" legend. Every hero and medium carries a
CONFIRMED / REPORTED / CLAIM tag and a named outlet.

The three results that were still fixtures at the first press time were
refreshed to the real outcomes after the round opened: Alcaraz beat Zverev
6–2, 7–6(7) for his first ATP Finals title; Liverpool thrashed Manchester
United 4–0; Hong Kong returned 723 candidates across 31 contested
subsectors. No FORECAST tag remains on the page.

## How to build

```sh
python3 build_frontpage.py   # writes entry.png (1024x1024) + entry_512.png
```

The build is deterministic (byte-identical re-runs) and fails loudly on any
layout violation: text-box overlap, a banner holding a digit, a numeral box
closer than 6px to another text box, a DATE CHECK that does not fit its
border, briefs that do not fit one line, or a story/region count mismatch.

## Files

- `entry.png` — the front page (1024×1024)
- `build_frontpage.py` — the whole Pillow pipeline
- `stories.json` — the 35 stories, numbers strip, timeline, regions
- `land_polys.json` — public-domain Natural Earth 110m land polygons
- `main.ts` — copies `entry.png` to `$MAKEFUN_OUTPUT_DIR`
- `DESIGN.md` — design tokens, layout rules, QA log
- `LICENSE` — MIT

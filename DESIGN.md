# DESIGN.md — news-image-20261123

## What it is

A single 1024×1024 front page covering **35 dated stories from Saturday 21 –
Sunday 22 November 2026 across 8 regions**, built on the winner template:
giant serif date masthead, coloured region bar, "THE DAY IN NUMBERS" strip
(6 figures), a UTC timeline (6 timed items), 3 illustrated hero cards,
10 illustrated medium cards, a smooth-polygon world map with de-collided
numbered pins, 22 numbered briefs, a DATE CHECK box, a "HOW TO READ THE
TAGS" legend and sources per story. Every hero and medium carries a
CONFIRMED / REPORTED / CLAIM / FORECAST tag and a named outlet.

Angle — "the Sunday the climate talks died". Leads: **COP31 collapses with
no deal** · **14 feared trapped in Dymer** · **Iran claims a 20th US drone
downed; Gulf tanker toll hits 25**.

Title (descriptive, counts + leads — no codename):
"Monday 23 November 2026: 35 dated stories, 8 regions — COP31 collapses
with no deal, 14 feared trapped in Dymer, Gulf tanker toll hits 25".

## Design tokens ("Newsprint", unchanged from round 22)

Paper `#f6f1e3`, ink `#16130e`, navy `#16233f`, red `#b3261e` (the ONE accent),
region colours: Western Europe `#1f4e79`, Eastern Europe `#2e6b8a`,
Middle East `#b3261e`, Americas `#2e6b34`, Asia-Pacific `#c25e10`,
Oceania `#0e6b5c`, Africa `#8a6d00`, World `#5b2d8e`. Type: Gloock masthead,
Crimson Pro headlines, Liberation Sans body/labels, BigShoulders strip
numerals, GeistMono timeline times. No gradients on text; flat fills only.

## Competitor-analysis P0s — how each was fixed (all verified, not eyeballed)

P0-1 (text-on-text in art): fixed BY CONSTRUCTION. Red banner = caps phrase
only, never a numeral (asserted: banner text must contain no digit). The big
numeral lives in its own white box (heroes, top-right) with a measured
≥6px clearance check against every other text box in the card. Every text
box is registered from measured `textbbox` extents; the build FAILS on any
intersection or any text escaping its card. Art is drawn on its own tile, so
no illustration element can leave the art rect and touch text below.
P0-2 (DATE CHECK sliced by its border): box height is computed from the
wrapped 11px text; last baseline ≥4px above the bottom border (asserted).
P0-3 (briefs clipped): 22 briefs (was 30), each a single measured line at
10px; last brief ≥4px above the DATE CHECK box (asserted).
P0-4 (blocky map, piled pins): smooth Natural Earth 110m land polygons
(public-domain data, Douglas-Peucker simplified to 698 points in
`land_polys.json`), rendered as filled polygons — no tiles. Pins de-collided:
majors ≥15px apart (asserted ≥14px), brief dots ≥9px from majors and ≥6px
from other dots, white outlines, light-grey leader lines only when displaced
>3px. A diagnostic pass found the London/Brussels dots stacking 6-on-1 and
the dot-vs-dot rule was added to fix it.
P0-5 (density): 3 heroes / 10 mediums / 35 stories (was 4/12/46). Type
floors held: hero headline 26px, hero deck 11px, medium headline 13px,
medium deck 11px, briefs 10px, strip numerals 34px. 512px downscale checked
legible (see QA log).

P1 applied: every hero scene has ≥3 drawn elements + annotation, no panel
>40% empty (COP31 plenary: 7 delegates + globe + flags + NO DEAL stamp);
no deck overflows (all decks measured ≤2–3 lines); DATE CHECK names the
23 Nov trap stories with dates + NOT YET line + press-time stamp
("PRESS TIME SUN 22 NOV 14:00 UTC"); no region above 9 (max: Western
Europe 9); footer states the dating rule flatly, no "in at least one time
zone" hedge. Boundary cases: El Chapo (Fri-night arrest, retaliation
through the weekend) is a medium with its date stated in the deck;
EU–Indonesia (Sat 21 Nov) is a brief with "Sat" stated.

## Skill rules applied (no new installs — see skills.md)

The 10 audited skills were NOT installed (install blocked by the runtime's
execution-risk check; needs explicit user approval). Their rules were applied
directly from `skills.md`:
- magazine-poster: dateline + top rule + oversized serif masthead + numbered
  story cells (mono eyebrow + serif head + body) + footer band; creamy paper.
- editorial-tech: mono label system (timeline times, eyebrows), fine divider
  rules, restrained palette with one accent. Dark surfaces / motion NOT used.
- illustration-flat / flat-with-black: ONE flat system per card, construction
  kept (solid black masses, separated shapes, no ground line on people),
  all colours remapped to page tokens.
- illustration-halftone-line: NOT applied to the map — its dotted texture
  conflicts with the P0-4 smooth-coastline requirement, which outranks it
  (the winners use solid light maps; the halftone dot pitch is recorded
  here for a future texture pass, not used).
- visualization-builder: numbers strip is 6 figures, each with its source
  beneath; no chart on this page (the strip IS the data display).
- data-narrative-builder: one central message (COP31 collapse), pyramid
  (conclusion first in every deck), hook in the masthead deck.
- metric-reconciliation + market-research-reports §§2–4: source ledger
  (S-001…S-025) and claims ledger (C-001…C-018) in
  `verification-2026-11-23.md`; reconciliations R-001…R-006. One correction
  made during verification: the strip figure "25 tankers" is sourced to
  Al Jazeera, not UKMTO (UKMTO's own figures are the two incidents and the
  transit counts).
- Already installed + used: canvas-design (fonts + "Flat Witness" flat
  language), hallmark (layout gates), color-expert (tokens), matplotlib
  (not needed — no charts), drawsvg 2.5.1 (imports fine; not needed —
  the build is Pillow).
- NOT used: CairoSVG 2.9.1 — `import cairosvg` STILL FAILS in this VM
  (`FileNotFoundError: No usable temporary directory`; /tmp is 82% full
  and Python temp-file creation is blocked by the sandbox). The build does
  not need it (Pillow only). Lucide is NOT installed — no icons used;
  all marks are drawn shapes.

## Verification summary

Full ledgers: `verification-2026-11-23.md` (workdir; not in the repo).
Reconciliations: R-001 HK turnout 98.79% (official) beats 98.37% (secondary
graphic); R-002 killer robots — drafting agreed, binding treaty not;
R-003 Brent $92.57 vs $89.95 — NOT printed; R-004 "first COP failure since
Copenhagen 2009" single-source — NOT printed; R-005 Dymer 14 consistent;
R-006 measles single-aggregator — printed as REPORTED, source named.
Date rule: every story dated by EVENT date (Sat 21 – Sun 22 Nov 2026);
36h+ items (Fri 20 Nov and earlier) are in DATE CHECK, not featured.

## QA log

- Build gate (`build_frontpage.py`): structural assertions (3/10/22/35,
  region sum = 35, max region 9, 6 numbers, 6 timeline, numbers 1–35) +
  per-card text non-intersection + within-card checks + numeral ≥6px
  clearance + DATE CHECK fit + briefs fit + final y ≤ 1024. Build FAILS
  on any violation. Final run: QA PASS, final y = 1021/1024.
- Defects found and fixed in QA rounds: (1) timeline overflowed by 2px —
  caught by assertion, gap tightened; (2) page overflowed 63px then 9px —
  decks shortened to 2 lines, art heights tuned; (3) 6 medium illustrations
  drew outside their art rect (thermometer, robot ring, ballot box, truck
  wheels, batsman legs, scissors) — fixed by tile-clipped art + geometry
  fixes; (4) COP31 "NO DEAL" stamp overlapped the CONFIRMED tag pill —
  moved up + filled red; (5) map dots stacked 6-on-1 over London —
  dot-vs-dot de-collision added; (6) strip "25 tankers" mis-sourced to
  UKMTO — corrected to Al Jazeera.
- 2× zoom crops checked: heroes, mediums, map, DATE CHECK, bottom strip —
  0 defects remain. 512px downscale checked: masthead, numbers, region bar,
  timeline, hero/medium headlines, pins, briefs, DATE CHECK all legible.
- Determinism: re-runs produce byte-identical entry.png
  (md5 `ee0dff95356b0d318638cc8225708355`).

## Honest odds

Per the competitor analysis: top-3 in one round is not realistic (gap to
live #3 is +1.06 pts; top-10 spread is 0.17 pts). Realistic target if all
P0s are genuinely fixed: ~98.7–99.0% live, rank ~50–150 — around the live
finalist line (98.82%). The finalist-50 cut is invisible until
finalization; a good live rank is not success. What would change the odds:
two consecutive clean rounds with zero clipping defects.

## Environment notes (for the coordinator)

- Competition opens 23 Nov 00:00 UTC (07:00 WIB). This build was completed
  BEFORE opening (Sun 22 Nov ~15:00 UTC) — the repo must be created AT OR
  AFTER opening. Do NOT backdate anything.
- Sandbox quirk found during QA: Python processes launched via exec can
  only WRITE to files that already exist (new-file writes fail with EPERM);
  `python3 build_frontpage.py` works because it overwrites the pre-existing
  `entry.png` / `entry_512.png`. The coordinator should not rely on ad-hoc
  Python file creation in this VM; use the file tools to create files first.
- `/tmp` is 82% full (93 MB free) — that plus the write block is why
  CairoSVG cannot find a usable temp dir.
- No kit check and no submit were run (coordinator handles those).

## Repo contents

`entry.png`, `build_frontpage.py`, `stories.json`, `land_polys.json`,
`main.ts`, `README.md`, `LICENSE`, `DESIGN.md`. Workdir-only (not
committed): `research-2026-11-23.md`, `verification-2026-11-23.md`,
`analysis-competitor.md`, `skills.md`, `lb-20261122-live.json`, `top5/`,
`entry_512.png`, `crop_view.py`, `pin_check.py`.

## Morning refresh — Mon 23 Nov 00:08 UTC (after opening)

The three FORECAST stories were refreshed to actual results and the
page rebuilt (same pipeline, QA PASS, deterministic):

- #6 Tennis: Alcaraz beat Zverev 6–2, 7–6(7) — first ATP Finals
  title, 30th career crown (ATP Tour, Flashscore). Banner
  "FIRST TURIN TITLE", tag FORECAST → CONFIRMED.
- #17 brief: Liverpool 4–0 Man Utd — Szoboszlai 10', Wirtz 13',
  Ngumoha 66', Munoz 82'; Yoro sent off 8' (Sky Sports).
- #4 Hong Kong: 723 candidates returned across 31 contested
  subsectors from 856 candidates; Yuen wins, KC Chan loses in finance
  (HK govt, SCMP). Banner "ALL SEATS FILLED".
- Timeline fixtures replaced with results; DATE CHECK "NOT YET"
  now only lists India v NZ final day (Mon); press time
  MON 23 NOV 00:08 UTC. Legend drops the FORECAST / "*" definitions
  (no such tag remains on the page).
- Rebuilt entry.png: 1024×1024, 243,901 B, sha256
  543037a3… (deterministic across re-runs), final y=1021/1024.
  Timeline re-measured after the refresh (ends 981px ≤ 1012px).

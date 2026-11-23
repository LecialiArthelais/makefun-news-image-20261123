# DESIGN.md — news-image-20261123 (rebuild, Mon 23 Nov 2026, post-open)

## What it is

A single 1024×1024 front page covering **35 dated stories from Saturday 21 –
Sunday 22 November 2026 across 8 regions**, built on the winner template:
giant serif date masthead, coloured region bar, "THE DAY IN NUMBERS" strip
(6 figures), a UTC timeline (6 timed items), 3 illustrated hero cards,
10 illustrated medium cards, a smooth-polygon world map with de-collided
numbered pins, 22 numbered briefs, a DATE CHECK box, a "HOW TO READ THE
TAGS" legend and sources per story. Every hero and medium carries a
CONFIRMED / REPORTED / CLAIM tag and a named outlet. No FORECAST tag
remains anywhere on the page.

Angle — "the Sunday the climate talks died". Leads: **COP31 collapses with
no deal** · **14 feared trapped in Dymer** · **Iran claims a 20th US drone
downed; Gulf tanker toll hits 25**.

Title (descriptive, counts + leads — no codename):
"Monday 23 November 2026: 35 dated stories, 8 regions — COP31 collapses
with no deal, 14 feared trapped in Dymer, Gulf tanker toll hits 25".

## Design tokens ("Newsprint")

Paper `#f6f1e3`, ink `#16130e`, navy `#16233f`, red `#b3261e` (the ONE accent),
region colours: Western Europe `#1f4e79`, Eastern Europe `#2e6b8a`,
Middle East `#b3261e`, Americas `#2e6b34`, Asia-Pacific `#c25e10`,
Oceania `#0e6b5c`, Africa `#8a6d00`, World `#5b2d8e`. Type: Liberation Serif
Bold masthead/headlines (Gloock/Crimson Pro are not installed on this VM),
Liberation Sans body/labels, DejaVu Sans Mono timeline times. No gradients
on text; flat fills only.

## Layout

Top eyebrow counts line, then the masthead "Monday 23 November 2026" in
62px serif with a red italic deck naming the three leads. Below it, in
order: the 6-figure numbers strip (each figure with its source beneath),
the 8-segment region bar (counts sum to 35, max segment 9), the navy UTC
timeline strip, 3 heroes in one row, 10 mediums in two rows of five, then
the map (left) beside the 22 briefs in two columns (right), the red-bordered
DATE CHECK box, and the legend + footer lines.

Region split: Western Europe 9, Eastern Europe 3, Middle East 3,
Americas 6, Asia-Pacific 6, Oceania 2, Africa 3, World 3 = 35.

## Competitor-analysis P0s — how each is fixed (verified, not eyeballed)

P0-1 (text-on-text in art): fixed BY CONSTRUCTION. Red banner = caps phrase
only, never a numeral (asserted: banner text must contain no digit). The big
numeral lives in its own white box (heroes, top-right) with a measured
≥6px clearance check against every other text box in the card. Every text
box is registered from measured `textbbox` extents; the build FAILS on any
intersection or any text escaping its card. Art is drawn on its own tile, so
no illustration element can leave the art rect and touch text below.
P0-2 (DATE CHECK sliced by its border): box height is computed from the
wrapped 11px text; last baseline ≥4px above the bottom border (asserted).
P0-3 (briefs clipped): 22 briefs, each a single measured line at 10px; last
brief ≥4px above the DATE CHECK box (asserted).
P0-4 (blocky map, piled pins): smooth Natural Earth 110m land polygons
(public-domain data, Douglas-Peucker simplified to 698 points in
`land_polys.json`), rendered as filled polygons — no tiles. Pins de-collided:
majors ≥15px apart (asserted ≥14px), brief dots ≥9px from majors and ≥6px
from other dots, white outlines, light-grey leader lines only when displaced
>3px.
P0-5 (density): 3 heroes / 10 mediums / 35 stories. Type floors held: hero
headline 26px, hero deck 11px, medium headline 13px, medium deck 11px,
briefs 10px, strip numerals 34px. 512px downscale checked legible.

P1 applied: every hero scene has ≥3 drawn elements + annotation, no panel
>40% empty (COP31 plenary: 7 delegates + globe + NO DEAL stamp); no deck
overflows (all decks measured ≤2 lines); DATE CHECK names the 23 Nov trap
stories with dates + NOT YET line + press-time stamp; no region above 9;
footer states the dating rule flatly, no "in at least one time zone" hedge.
Boundary cases: El Chapo (Fri-night arrest, retaliation through the weekend)
is a medium with its date stated in the deck; EU–Indonesia (Sat 21 Nov) is
a brief.

## Skill rules applied (no new installs)

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
  conflicts with the P0-4 smooth-coastline requirement, which outranks it.
- visualization-builder: numbers strip is 6 figures, each with its source
  beneath; no chart on this page (the strip IS the data display).
- data-narrative-builder: one central message (COP31 collapse), pyramid
  (conclusion first in every deck), hook in the masthead deck.
- metric-reconciliation + market-research-reports §§2–4: source ledger
  (S-001…S-028) and claims ledger (C-001…C-021) in
  `verification-2026-11-23.md`; reconciliations R-001…R-006. One correction
  made during verification: the strip figure "25 tankers" is sourced to
  Al Jazeera, not UKMTO.
- CairoSVG is NOT used (import fails in this VM; /tmp pressure). The build
  is Pillow only. Lucide is NOT installed — no icons used; all marks are
  drawn shapes.

## Verification summary

Full ledgers: `verification-2026-11-23.md` (workdir; not in the repo).
Reconciliations: R-001 HK turnout 98.79% (official) beats 98.37% (secondary
graphic); R-002 killer robots — drafting agreed, binding treaty not;
R-003 Brent $92.57 vs $89.95 — NOT printed; R-004 "first COP failure since
Copenhagen 2009" single-source — NOT printed; R-005 Dymer 14 consistent;
R-006 measles single-aggregator — printed as REPORTED, source named.
Date rule: every story dated by EVENT date (Sat 21 – Sun 22 Nov 2026);
36h+ items (Fri 20 Nov and earlier) are in DATE CHECK, not featured.

## Morning refresh — Mon 23 Nov 01:07 UTC (after opening, re-verified live)

The three FORECAST stories were refreshed to actual results and re-verified
against live sources in this rebuild session (ATP Tour + Reuters, Sky
Sports + liverpoolfc.com, HK govt info.gov.hk + HK Businesswire):

- #6 Tennis: Alcaraz beat Zverev 6–2, 7–6(7) — first ATP Finals
  title, 30th career crown (ATP Tour, Flashscore). Banner
  "FIRST TURIN TITLE", tag CONFIRMED.
- #17 brief: Liverpool 4–0 Man Utd — Szoboszlai 10', Wirtz 13',
  Ngumoha 66', Munoz 82'; Yoro sent off 8' (Sky Sports).
- #4 Hong Kong: 723 candidates returned across 31 contested
  subsectors from 856 candidates; Yuen wins, KC Chan loses in finance
  (HK govt, SCMP). Banner "ALL SEATS FILLED".
- Timeline fixtures replaced with results; DATE CHECK "NOT YET"
  now only lists India v NZ final day (Mon); press time
  MON 23 NOV 01:07 UTC. Legend drops the FORECAST definition
  (no such tag remains on the page).

## QA log (rebuild)

- Build gate (`build_frontpage.py`): structural assertions (3/10/22/35,
  region sum = 35, max region 9, 6 numbers, 6 timeline, numbers 1–35) +
  per-card text non-intersection + within-card checks + numeral ≥6px
  clearance + DATE CHECK fit + briefs fit + final y ≤ 1024. Build FAILS
  on any violation.
- 2× zoom crops checked: heroes, mediums, map, DATE CHECK, bottom strip.
- 512px downscale checked: masthead, numbers, region bar, timeline,
  hero/medium headlines, pins, briefs, DATE CHECK all legible.
- Determinism: re-runs produce byte-identical entry.png (md5 recorded
  in the rebuild report to the coordinator).

## Honest odds

Per the competitor analysis: top-3 in one round is not realistic (gap to
live #3 is +1.06 pts; top-10 spread is 0.17 pts). Realistic target if all
P0s are genuinely fixed: ~98.7–99.0% live, rank ~50–150 — around the live
finalist line (98.82%). The finalist-50 cut is invisible until
finalization; a good live rank is not success. What would change the odds:
two consecutive clean rounds with zero clipping defects.

## Environment notes (for the coordinator)

- Competition opens 23 Nov 00:00 UTC (07:00 WIB). This rebuild was done
  AFTER opening (Mon 23 Nov ~01:07 UTC) — every file in this entry was
  written fresh in this post-open session, on top of repo HEAD 210a6490.
- Sandbox quirk: Python processes launched via exec can only WRITE to
  files that already exist (new-file writes fail with EPERM);
  `python3 build_frontpage.py` works because it overwrites the pre-existing
  `entry.png` / `entry_512.png`. All fresh source files were created with
  the file tools, not via Python/shell.
- CairoSVG is unusable in this VM (`import cairosvg` fails: no usable
  temporary directory). The build does not need it (Pillow only).
- No kit check and no submit were run (coordinator handles those).

## Repo contents

`entry.png`, `build_frontpage.py`, `stories.json`, `land_polys.json`,
`main.ts`, `README.md`, `LICENSE`, `DESIGN.md`. Workdir-only (not
committed): `research-2026-11-23.md`, `verification-2026-11-23.md`,
`analysis-competitor.md`, `skills.md`, `lb-20261122-live.json`, `top5/`,
`entry_512.png`.

import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Entry point: copy the pre-rendered front page into the harness output dir.
// The page itself is rendered deterministically by build_frontpage.py
// (Pillow, no network access) from stories.json + land_polys.json.
const here = dirname(fileURLToPath(import.meta.url));
const out = process.env.MAKEFUN_OUTPUT_DIR;
if (!out) {
  console.error("MAKEFUN_OUTPUT_DIR is not set");
  process.exit(1);
}
mkdirSync(out, { recursive: true });
const src = join(here, "entry.png");
if (!existsSync(src)) {
  console.error("entry.png missing — run: python3 build_frontpage.py");
  process.exit(1);
}
copyFileSync(src, join(out, "entry.png"));
console.log("wrote entry.png");

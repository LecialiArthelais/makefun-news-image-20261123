import { copyFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, "entry.png");

const outDir = process.env.MAKEFUN_OUTPUT_DIR;
if (!outDir) {
  console.error("MAKEFUN_OUTPUT_DIR is not set");
  process.exit(1);
}
if (!existsSync(source)) {
  console.error(`entry.png not found at ${source}`);
  process.exit(1);
}

const target = join(outDir, "entry.png");
copyFileSync(source, target);
console.log(`wrote entry.png to ${target}`);
console.log("news-image-20261123 entry copied successfully");

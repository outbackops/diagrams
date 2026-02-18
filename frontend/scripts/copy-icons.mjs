/**
 * Script to copy provider icons from resources/ to frontend/public/icons/
 * Run with: node scripts/copy-icons.mjs
 */

import { cpSync, mkdirSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, "../..");
const resourcesDir = resolve(repoRoot, "resources");
const iconsDir = resolve(__dirname, "../public/icons");

if (!existsSync(resourcesDir)) {
  console.error(`Resources directory not found: ${resourcesDir}`);
  process.exit(1);
}

mkdirSync(iconsDir, { recursive: true });

cpSync(resourcesDir, iconsDir, {
  recursive: true,
  filter: (src) => {
    // Copy only PNG files and directories
    return src.endsWith(".png") || !src.includes(".");
  },
});

console.log(`Icons copied from ${resourcesDir} to ${iconsDir}`);

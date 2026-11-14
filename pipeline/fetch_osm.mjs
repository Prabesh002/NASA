// Fetch context vectors from OpenStreetMap (Overpass API): rivers/streams, named places, peaks, glaciers.
// Data (c) OpenStreetMap contributors, ODbL 1.0. Output: data/raw/osm/osm_context.json (+ retrieval log).
// Usage: node pipeline/fetch_osm.mjs
// SI disclosure: written with SI assistance (Claude, Anthropic). See docs/SI-USAGE.md.
import { mkdirSync, writeFileSync } from "node:fs";
const BBOX = "27.85,85.10,28.42,85.65"; // s,w,n,e  (corridor + source boxes together)
const query = `[out:json][timeout:120];
(
  way["waterway"~"^(river|stream)$"](${BBOX});
  node["place"~"^(village|town|hamlet|locality)$"]["name"](${BBOX});
  node["natural"="peak"]["name"](${BBOX});
  way["natural"="glacier"](${BBOX});
  relation["waterway"="river"](${BBOX});
);
out body geom;`;
const endpoints = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"];
let data, used;
for (const url of endpoints) {
  try {
    const r = await fetch(url, { method: "POST", body: "data=" + encodeURIComponent(query),
      headers: { "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "spaceapps-hackathon-script/1.0" } });
    if (!r.ok) throw new Error("HTTP " + r.status);
    data = await r.json(); used = url; break;
  } catch (e) { console.error("failed", url, String(e)); }
}
if (!data) process.exit(1);
mkdirSync("data/raw/osm", { recursive: true });
writeFileSync("data/raw/osm/osm_context.json", JSON.stringify(data));
writeFileSync("data/raw/osm/retrieval.json", JSON.stringify({ endpoint: used, query, retrieved_utc: new Date().toISOString(),
  osm_base: data.osm3s?.timestamp_osm_base, elements: data.elements.length }, null, 2));
console.log("elements", data.elements.length, "osm_base", data.osm3s?.timestamp_osm_base);

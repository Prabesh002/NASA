// Save a web page's readable text for fact-checking: node pipeline/fetch_page.mjs <url> <out.txt>
// SI disclosure: written with SI assistance (Claude, Anthropic).
import { writeFileSync } from "node:fs";
const [url, out] = process.argv.slice(2);
const r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0 (compatible; research-fetch/1.0)" }, redirect: "follow" });
const html = await r.text();
const text = html.replace(/<script[\s\S]*?<\/script>/gi, " ").replace(/<style[\s\S]*?<\/style>/gi, " ")
  .replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&#8217;|&rsquo;/g, "'").replace(/\s+/g, " ");
writeFileSync(out, `URL: ${r.url}\nHTTP: ${r.status}\nRetrieved UTC: ${new Date().toISOString()}\n\n${text}\n`);
console.log(r.status, r.url, text.length);

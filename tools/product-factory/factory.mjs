#!/usr/bin/env node
// PRODUCT FACTORY: drafts a sellable digital product from a spec file using free LLMs.
//
//   node factory.mjs specs/cvi-goal-bank.json          # build one product
//   node factory.mjs --list                            # show available specs
//
// Output goes to output/<slug>/ :
//   items.csv     -> import into Google Sheets (File > Import)
//   product.html  -> open in a browser, Print > Save as PDF (print-ready, large text)
//   product.txt   -> accessible screen-reader version
//   listing.md    -> Payhip / TPT title, description, bullets, tags
//   REVIEW.md     -> your expert review checklist (do this before selling!)
// Progress is saved after every batch, so you can stop and re-run to resume.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chat, extractJSON, available } from "./lib/llm.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));

// Load .env (simple KEY=value lines) without any dependency.
const envFile = path.join(HERE, ".env");
if (fs.existsSync(envFile)) {
  for (const line of fs.readFileSync(envFile, "utf8").split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
}

const arg = process.argv[2];
if (!arg || arg === "--list") {
  console.log("Specs you can build:\n" + fs.readdirSync(path.join(HERE, "specs")).map((f) => "  node factory.mjs specs/" + f).join("\n"));
  process.exit(0);
}

const spec = JSON.parse(fs.readFileSync(path.resolve(arg), "utf8"));
const outDir = path.join(HERE, "output", spec.slug);
fs.mkdirSync(outDir, { recursive: true });
const progressFile = path.join(outDir, "progress.json");
const progress = fs.existsSync(progressFile) ? JSON.parse(fs.readFileSync(progressFile, "utf8")) : {};

console.log(`\n🏭 Building "${spec.title}"  (providers: ${available().map((p) => p.name).join(", ") || "NONE"})\n`);

const keys = spec.columns.map((c) => c.key);
const SYSTEM = `${spec.persona}
You write professional, practical, ready-to-use content for: ${spec.audience}.
Rules:
- Never use real names of students, families, staff, or trademarked assessment names.
- Never invent ANY person's name. Use placeholders: "the student" / "[Student]" / "[Family]" / "[Your Name]" / "[School]".
- Be specific, measurable where relevant, and realistic.
- Every item must be different from the others.
Reply with ONLY a JSON array of objects with exactly these keys: ${keys.join(", ")}.`;

const BATCH = spec.batchSize || 5;
const norm = (s) => String(s || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

for (const section of spec.sections) {
  progress[section.name] ||= [];
  const items = progress[section.name];
  while (items.length < section.count) {
    const need = Math.min(BATCH, section.count - items.length);
    const avoid = items.slice(-25).map((it) => "- " + String(it[keys[0]]).slice(0, 90)).join("\n");
    const user = `Section: ${section.name}
Guidance: ${section.guidance}
Column meanings:
${spec.columns.map((c) => `- ${c.key}: ${c.hint}`).join("\n")}
Write ${need} NEW items.${avoid ? `\nDo NOT repeat or closely paraphrase these existing items:\n${avoid}` : ""}`;
    process.stdout.write(`  ${section.name}: ${items.length}/${section.count} … `);
    const { text, provider } = await chat([{ role: "system", content: SYSTEM }, { role: "user", content: user }]);
    const arr = extractJSON(text);
    const list = Array.isArray(arr) ? arr : Array.isArray(arr?.items) ? arr.items : [];
    let added = 0;
    for (const it of list) {
      if (!it || keys.some((k) => !String(it[k] ?? "").trim())) continue;
      if (items.some((x) => norm(x[keys[0]]) === norm(it[keys[0]]))) continue;
      items.push(Object.fromEntries(keys.map((k) => [k, String(it[k]).trim()])));
      if (++added >= need) break;
    }
    console.log(`+${added} via ${provider}`);
    fs.writeFileSync(progressFile, JSON.stringify(progress, null, 2));
    if (!added) console.log("    (model returned nothing usable; retrying)");
  }
}

// ---------- Write the product files ----------
const all = spec.sections.flatMap((s) => progress[s.name].slice(0, s.count).map((it) => ({ section: s.name, ...it })));
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const csvCell = (s) => `"${String(s).replace(/"/g, '""')}"`;

fs.writeFileSync(path.join(outDir, "items.csv"),
  "﻿" + [["Section", ...spec.columns.map((c) => c.label)].map(csvCell).join(","),
    ...all.map((it) => [it.section, ...keys.map((k) => it[k])].map(csvCell).join(","))].join("\r\n"));

fs.writeFileSync(path.join(outDir, "product.txt"),
  `${spec.title}\n${"=".repeat(spec.title.length)}\n${spec.tagline}\n\n${spec.intro}\n\n` +
  spec.sections.map((s) => `\n## ${s.name}\n\n` + progress[s.name].slice(0, s.count).map((it, i) =>
    `${i + 1}.\n` + spec.columns.map((c) => `${c.label}: ${it[c.key]}`).join("\n")).join("\n\n")).join("\n") +
  `\n\n---\n${spec.footer}\n`);

fs.writeFileSync(path.join(outDir, "product.html"), `<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>${esc(spec.title)}</title><style>
body{font:13.5pt/1.4 Arial,Helvetica,sans-serif;color:#000;max-width:8in;margin:0 auto;padding:.5in}
h1{font-size:28pt;margin:0}h2{font-size:20pt;border-bottom:3px solid #000;padding-bottom:4px;margin-top:36pt;break-before:page}
.item{border:2px solid #000;border-radius:8px;padding:8pt 12pt;margin:8pt 0;break-inside:avoid}.item p{margin:3pt 0}
.label{font-weight:700}.cover{height:9in;display:flex;flex-direction:column;justify-content:center}
.foot{font-size:11pt;margin-top:24pt}@page{margin:.6in}
</style></head><body>
<section class="cover"><h1>${esc(spec.title)}</h1><p style="font-size:20pt">${esc(spec.tagline)}</p><p>${esc(spec.intro)}</p><p class="foot">${esc(spec.footer)}</p></section>
${spec.sections.map((s) => `<h2>${esc(s.name)}</h2>` + progress[s.name].slice(0, s.count).map((it, i) =>
  `<div class="item"><p class="label">#${i + 1}</p>` + spec.columns.map((c) => `<p><span class="label">${esc(c.label)}:</span> ${esc(it[c.key])}</p>`).join("") + "</div>").join("")).join("\n")}
</body></html>`);

// Listing copy
const { text: listingText } = await chat([
  { role: "system", content: "You write high-converting, honest product listings for teacher marketplaces (Payhip, Teachers Pay Teachers). No hype words like 'revolutionary'. No fake reviews or stats." },
  { role: "user", content: `Product: ${spec.title}\nTagline: ${spec.tagline}\nAudience: ${spec.audience}\nPrice: $${spec.price}\nWhat's inside: ${spec.sections.map((s) => `${s.count} ${s.name}`).join("; ")}\nFormats: Google Sheets (CSV), print-ready PDF, accessible TXT\nCreator: ${spec.creator}\n\nWrite in Markdown: 3 title options (under 80 chars), a 150-word description, 6 bullet benefits, a "Who it's for" line, 13 search tags, and a 1-paragraph Facebook-group post that offers value first.` },
], { temperature: 0.6, maxTokens: 1500 });
fs.writeFileSync(path.join(outDir, "listing.md"), listingText);

fs.writeFileSync(path.join(outDir, "REVIEW.md"), `# Review checklist: ${spec.title}

AI drafted this. **You are the expert, and your review is what makes it worth $${spec.price}.**

- [ ] Skim every item in items.csv (Google Sheets is fastest). Delete or fix anything wrong.
- [ ] Check that no item contains a real name, a trademarked assessment name, or an unsafe recommendation.
- [ ] Add 3–5 of your own signature items or tips (this is your edge).
- [ ] Open product.html → Print → Save as PDF. Check that the pages look clean.
- [ ] Pick a title from listing.md and edit the description in your voice.
- [ ] Upload the PDF + CSV + TXT to Payhip (and optionally TPT) at $${spec.price}.
- [ ] Post the Facebook-group blurb from listing.md.
`);

console.log(`\n✅ Done → ${path.relative(process.cwd(), outDir)}/  (${all.length} items)\n   Next: open REVIEW.md\n`);

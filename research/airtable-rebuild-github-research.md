# Rebuilding Airtable — GitHub Research Map

_Researched 2026-11-07 via GitHub search. Stars and last-push dates are as of that day._

**Short version:** don't start from zero. Use **Teable** (closest match, and its formula/SDK packages are MIT) or **Baserow** (core is MIT) as your **reference architecture**. Then build your own stack from the MIT-licensed parts below: a grid, a formula engine, realtime, views, forms, automations.

> Ground rule: "reverse engineer" here means studying Airtable's **public** surface: its API docs, its official SDKs (MIT), and how the product behaves. Pair that with open-source clones. Don't decompile or copy Airtable's proprietary front-end code, and don't scrape private endpoints.

---

## 1. Airtable's own public code (the "spec")

Treat these as the blueprint. They tell you exactly what Airtable's data model looks like.

| Repo | ★ | License | Why it matters |
|---|---|---|---|
| [Airtable/blocks](https://github.com/Airtable/blocks) | 273 | (see repo) | The official Extensions/Interface SDK. Its type definitions list **every field type, its options, view types, record/cell shapes, and permission checks**. This is the most precise data-model spec you'll find. |
| [Airtable/airtable.js](https://github.com/Airtable/airtable.js) | 2.2k | MIT | Official JS client. Shows the REST semantics: pagination (`offset`), `filterByFormula`, `sort`, `view`, `typecast`, and batches of 10 records. |
| [Airtable/airtable-mcp-cli](https://github.com/Airtable/airtable-mcp-cli) | 41 | — | The official CLI/MCP. Shows the current API surface for AI agents. |
| [Airtable/apps-base-schema](https://github.com/Airtable/apps-base-schema) | 34 | — | Visualizes tables, fields and links. A reference for the schema/ERD view. |
| [Airtable/apps-flowchart](https://github.com/Airtable/apps-flowchart), [apps-print-records](https://github.com/Airtable/apps-print-records), [apps-update-records](https://github.com/Airtable/apps-update-records), [apps-todo-list](https://github.com/Airtable/apps-todo-list) | 19–27 | — | Example extensions. They show how an "app on top of a base" works. |
| [Airtable/oauth-example](https://github.com/Airtable/oauth-example) | 19 | — | The OAuth flow, if you want an Airtable-compatible auth/API layer. |
| [Airtable/skills](https://github.com/Airtable/skills) | 53 | — | Official AI skills. Shows how they expose bases to agents. |

### Third-party clients and schema tools (they decode the API for you)
| Repo | ★ | Why |
|---|---|---|
| [gtalarico/pyairtable](https://github.com/gtalarico/pyairtable) | 891 | Python client with **typed Pydantic models for every field schema, webhooks, comments, and the metadata API**. These make good templates for your own DB schema. MIT. |
| [domdomegg/airtable-mcp-server](https://github.com/domdomegg/airtable-mcp-server) | 456 | Clean TypeScript map of the metadata and records endpoints. MIT. |
| [briankinney/airtable-swagger](https://github.com/briankinney/airtable-swagger) | 16 | Generates **OpenAPI 3 specs from an Airtable schema**. Useful if you want your clone to be API-compatible. |
| [cape-ookb/airtable-schema](https://github.com/cape-ookb/airtable-schema), [aivantg/airtable-schema-generator](https://github.com/aivantg/airtable-schema-generator) | 20–30 | Pull a base's schema as JSON. |
| [Automations-Project/VSCode-Airtable-Formula](https://github.com/Automations-Project/VSCode-Airtable-Formula) | 32 | Formula editor and grammar. Useful for matching **Airtable's formula syntax** exactly. |
| [xavdid/backup-airtable](https://github.com/xavdid/backup-airtable), [viewcourier/airtable-backup](https://github.com/viewcourier/airtable-backup) | — | Full-base export: schema, CSV and attachments. Use these to build an **"Import from Airtable"** feature. |
| Other clients: [airtable.net](https://github.com/ngocnicholas/airtable.net) (C#), [airtable-php](https://github.com/sleiman/airtable-php), [fuxingloh/airtable](https://github.com/fuxingloh/airtable) (Java), [airtable-go](https://github.com/fabioberger/airtable-go) | | Cross-check API edge cases. |

---

## 2. Full open-source Airtable clones (study the architecture)

| Repo | ★ | Stack | License | Verdict |
|---|---|---|---|---|
| [nocodb/nocodb](https://github.com/nocodb/nocodb) | 65.4k | Vue/Nuxt + Node, runs over any SQL DB | **Sustainable Use License** (source-available, *not* OSI) | Biggest and most feature-complete: grid, gallery, kanban, form, calendar, links, lookups, rollups, formulas, API, webhooks. **Read it; don't copy it into a commercial product.** |
| [teableio/teable](https://github.com/teableio/teable) | 22.0k | Next.js + NestJS + **Postgres**, canvas grid | Apps: AGPL-3.0 · **`packages/*` MIT** | **Best reference.** It's modern TypeScript, Postgres-native, realtime (ShareDB), handles millions of rows, and has an ANTLR formula grammar at `packages/formula/src/parser/Formula.g4`. You can **reuse the MIT packages directly**. |
| [apitable/apitable](https://github.com/apitable/apitable) | 15.7k | React + Java/Node | AGPL-3.0 | Very Airtable-like UI and an "API-first" design. Robust realtime collaboration (OT). Last push Sep 2026, so it's slowing down. |
| [gristlabs/grist-core](https://github.com/gristlabs/grist-core) | 12.1k | TS + Python formulas, SQLite per doc | **Apache-2.0** | Different model (spreadsheet-first, Python formulas). Great ideas for access rules and per-document storage. Permissive license. |
| [baserow/baserow](https://github.com/baserow/baserow) | 6.3k | Django + Vue/Nuxt + Postgres | **Core MIT** (premium/enterprise dirs excluded) | Clean, readable code. Its ANTLR formula grammar is `formula/BaserowFormula.g4`. Includes automations, apps builder and webhooks. **Most permissive full clone.** |
| [mathesar-foundation/mathesar](https://github.com/mathesar-foundation/mathesar) | 5.2k | Svelte + Django over raw Postgres | GPL-3.0 | Shows how to map a spreadsheet UI onto **real Postgres tables, foreign keys and permissions**. |
| [mayneyao/eidos](https://github.com/mayneyao/eidos) | 3.2k | TS, local-first SQLite | AGPL-3.0 | Single-file, offline-first relational spreadsheet. A good reference for local-first sync. |
| [undb-io/undb](https://github.com/undb-io/undb) | 3.0k | TS | AGPL-3.0 | **Archived** (merged into Teable). Still readable as a clean DDD-style codebase. |
| [seatable/seatable](https://github.com/seatable/seatable) | 716 | — | — | Deployment repo only. The real code is closed. Skip. |
| [fractaledmind/hottable](https://github.com/fractaledmind/hottable) | 133 | Rails + Hotwire | — | **Minimal clone.** The fastest way to understand the core idea in about an hour. |
| [sonnysangha/airtable-clone-demo](https://github.com/sonnysangha/airtable-clone-demo) | 4 | TS | — | Realtime B2B Airtable-style demo with forms, billing and approvals. A tutorial-sized reference. |
| [kyh/ai-datagrid](https://github.com/kyh/ai-datagrid) | 10 | Next.js | — | Forkable Excel/Airtable-style grid with AI built in. |
| [just-every/run-cradle](https://github.com/just-every/run-cradle) | 4 | TS | MIT | New (Nov 2026): records, views and forms. MIT but very early. |

---

## 3. Building blocks by feature

### A. Grid view (the heart of the product)
| Repo | ★ | License | Notes |
|---|---|---|---|
| [glideapps/glide-data-grid](https://github.com/glideapps/glide-data-grid) | 5.4k | MIT | **Top pick.** Canvas-rendered and handles millions of rows. Teable's grid takes the same approach. Custom cells, column resize/reorder, fill handle. |
| [TanStack/table](https://github.com/TanStack/table) + [TanStack/virtual](https://github.com/TanStack/virtual) | 28.6k / 7.2k | MIT | Headless logic for sort, filter, group and column state. Pair with your own rendering. |
| [nick-keller/react-datasheet-grid](https://github.com/nick-keller/react-datasheet-grid) | 2.0k | MIT | "Airtable-like" out of the box. Fastest MVP. |
| [Comcast/react-data-grid](https://github.com/Comcast/react-data-grid) | 7.7k | MIT | DOM-based, solid and accessible. |
| [revolist/revogrid](https://github.com/revolist/revogrid) | 3.5k | MIT | Virtualized, framework-agnostic. |
| [handsontable/handsontable](https://github.com/handsontable/handsontable) · [ag-grid/ag-grid](https://github.com/ag-grid/ag-grid) | 22k / 15.7k | Commercial for business use / Community MIT + paid Enterprise | Powerful but license-heavy. |
| [rowsncolumns/grid](https://github.com/rowsncolumns/grid) | 635 | — | Canvas grid primitive. Stale since 2023. |

### B. Field types, linked records, lookups, rollups
There's no single library for this. It's your data model. Copy the **shape** from `Airtable/blocks` types plus `pyairtable` models, and the **implementation** from Teable's `packages/core` (MIT) or Baserow's `contrib/database/fields`.
- Storage pattern: [mathesar](https://github.com/mathesar-foundation/mathesar) (real Postgres columns) vs. Teable (dynamic Postgres tables plus a metadata layer). **Recommend Teable's pattern.**
- ORM: [drizzle-team/drizzle-orm](https://github.com/drizzle-team/drizzle-orm) (36k, Apache-2.0) for the metadata tables. Use raw SQL for the dynamic user tables.

### C. Formula engine
| Repo | ★ | License | Notes |
|---|---|---|---|
| Teable `packages/formula` + `packages/core/src/formula` | — | MIT | ANTLR grammar plus evaluator, **Airtable-style syntax** (`{Field Name}`, `IF()`, `DATETIME_DIFF()`…). **Reuse this.** |
| Baserow `formula/BaserowFormula.g4` | — | MIT | Second reference grammar. Compiles to SQL, which matters for speed. |
| [formulajs/formulajs](https://github.com/formulajs/formulajs) | 824 | MIT | Ready-made implementations of Excel functions you can map Airtable names onto. |
| [handsontable/hyperformula](https://github.com/handsontable/hyperformula) | 2.8k | GPLv3 / commercial | Excel-grade headless engine. Watch the license. |

### D. Other views
| View | Repo | ★ | License |
|---|---|---|---|
| Kanban | [clauderic/dnd-kit](https://github.com/clauderic/dnd-kit) | 17.8k | MIT |
| Kanban (alt) | [atlassian/pragmatic-drag-and-drop](https://github.com/atlassian/pragmatic-drag-and-drop) | 12.8k | Apache-2.0 |
| Kanban starter | [Georgegriff/react-dnd-kit-tailwind-shadcn-ui](https://github.com/Georgegriff/react-dnd-kit-tailwind-shadcn-ui) | 823 | — |
| Calendar | [fullcalendar/fullcalendar](https://github.com/fullcalendar/fullcalendar) | 20.8k | MIT (core) |
| Calendar (modern) | [schedule-x/schedule-x](https://github.com/schedule-x/schedule-x) | 2.6k | MIT |
| Timeline/Gantt | [frappe/gantt](https://github.com/frappe/gantt) | 6.2k | MIT |
| Timeline (React) | [svar-widgets/react-gantt](https://github.com/svar-widgets/react-gantt) | 216 | MIT |
| Timeline (rich) | [neuronetio/gantt-schedule-timeline-calendar](https://github.com/neuronetio/gantt-schedule-timeline-calendar) | 3.6k | Commercial |
| Gallery | Plain CSS grid plus TanStack Virtual | — | — |
| Map | [maplibre/maplibre-gl-js](https://github.com/maplibre/maplibre-gl-js) | 12k | BSD |
| Charts/dashboards | [apache/echarts](https://github.com/apache/echarts) · [recharts/recharts](https://github.com/recharts/recharts) | 67.7k / 27.7k | Apache-2.0 / MIT |
| Schema diagram | [xyflow/xyflow](https://github.com/xyflow/xyflow) (React Flow) · [chartdb/chartdb](https://github.com/chartdb/chartdb) | 38.9k / 23k | MIT / AGPL |

### E. Forms (Airtable form view, public forms)
| Repo | ★ | License |
|---|---|---|
| [heyform/heyform](https://github.com/heyform/heyform) | 9.1k | AGPL-3.0 |
| [OpnForm/OpnForm](https://github.com/OpnForm/OpnForm) | 4.0k | AGPL-style |
| [formbricks/formbricks](https://github.com/formbricks/formbricks) | 13.2k | AGPL + EE |
| [surveyjs/survey-library](https://github.com/surveyjs/survey-library) | 4.9k | **MIT** (form renderer). Best one to embed. |

### F. Realtime collaboration (live cursors, multiplayer edits)
| Repo | ★ | License | Notes |
|---|---|---|---|
| [share/sharedb](https://github.com/share/sharedb) | 6.6k | MIT | **What Teable uses.** OT over JSON. A natural fit for row/cell ops. |
| [yjs/yjs](https://github.com/yjs/yjs) | 23k | MIT | CRDT. Best for rich-text long fields and offline. |
| [rocicorp/mono](https://github.com/rocicorp/mono) (Zero) | 3.4k | Apache-2.0 | Sync engine (Replicache successor; the old repo is archived). |
| [electric-sql/electric](https://github.com/electric-sql/electric) | 10.4k | Apache-2.0 | Postgres → client sync. |
| [liveblocks/liveblocks](https://github.com/liveblocks/liveblocks) | 4.8k | Hosted | Presence/comments as a service. |

### G. Automations (triggers → actions), scripts, webhooks
| Repo | ★ | License | Notes |
|---|---|---|---|
| [n8n-io/n8n](https://github.com/n8n-io/n8n) | 210k | Sustainable Use | Gold-standard node editor UX. Study only. |
| [activepieces/activepieces](https://github.com/activepieces/activepieces) | 25.4k | **MIT core** | Embeddable. "Pieces" model ≈ Airtable automation actions. |
| [automatisch/automatisch](https://github.com/automatisch/automatisch) | 14k | AGPL + EE | Simple Zapier-style trigger/action model. |
| [windmill-labs/windmill](https://github.com/windmill-labs/windmill) | 18.5k | AGPL | Runs user scripts (like Airtable's "Run script" action). |
| [triggerdotdev/trigger.dev](https://github.com/triggerdotdev/trigger.dev) · [temporalio/temporal](https://github.com/temporalio/temporal) | 16.7k / 24k | Apache / MIT | Durable job execution behind automations. |
| [novuhq/novu](https://github.com/novuhq/novu) | 40k | MIT core | Notifications (email/in-app) for automations and @mentions. |

### H. Interfaces (Airtable Interface Designer / app builder)
| Repo | ★ | License |
|---|---|---|
| [appsmithorg/appsmith](https://github.com/appsmithorg/appsmith) | 41k | Apache-2.0 |
| [ToolJet/ToolJet](https://github.com/ToolJet/ToolJet) | 41k | AGPL-3.0 |
| [Budibase/budibase](https://github.com/Budibase/budibase) | 28k | GPL/mixed |
| [illacloud/illa-builder](https://github.com/illacloud/illa-builder) | 12.3k | Apache-2.0 |
| [lowcoder-org/lowcoder](https://github.com/lowcoder-org/lowcoder) | 1.6k | AGPL |

### I. Platform plumbing
| Need | Repo | ★ | License |
|---|---|---|---|
| Auth (SSO, orgs, roles) | [better-auth/better-auth](https://github.com/better-auth/better-auth) | 30.6k | MIT |
| Permissions (workspace → base → table → field) | [openfga/openfga](https://github.com/openfga/openfga) · [authzed/spicedb](https://github.com/authzed/spicedb) | 6.1k / 7.2k | Apache-2.0 |
| Attachments | [transloadit/uppy](https://github.com/transloadit/uppy) + [tus/tusd](https://github.com/tus/tusd) | 31k / 3.9k | MIT |
| Search across records | [meilisearch/meilisearch](https://github.com/meilisearch/meilisearch) · [typesense/typesense](https://github.com/typesense/typesense) | 59.8k / 27k | MIT core / GPL |
| Rich text long field | [ueberdosis/tiptap](https://github.com/ueberdosis/tiptap) | 39k | MIT |
| Instant REST over Postgres | [PostgREST/postgrest](https://github.com/PostgREST/postgrest) · [supabase/supabase](https://github.com/supabase/supabase) | 27.7k / 114k | MIT / Apache |
| Backend-in-a-box (prototype) | [pocketbase/pocketbase](https://github.com/pocketbase/pocketbase) | 61.6k | MIT (⚠ marked archived on GitHub) |
| Headless CMS/admin over SQL | [directus/directus](https://github.com/directus/directus) | 38.7k | BSL |
| Spreadsheet SDK (if you want Excel-mode) | [dream-num/univer](https://github.com/dream-num/univer) | 22.9k | Apache-2.0 |

---

## 4. Airtable feature checklist → where to learn it

| # | Airtable feature | Best reference | Reusable lib |
|---|---|---|---|
| 1 | Workspaces / bases / tables | Teable, Baserow | better-auth (orgs) |
| 2 | ~30 field types (text, number, select, date, attachment, checkbox, rating, barcode, button, user, created/modified time, autonumber…) | `Airtable/blocks` types, pyairtable models | — |
| 3 | Linked records, lookup, rollup, count | Teable `packages/core`, Baserow fields | — |
| 4 | Formulas | Teable `Formula.g4` (MIT) | formulajs |
| 5 | Grid view (freeze, resize, fill handle, expand record) | Teable grid | glide-data-grid |
| 6 | Filter / sort / group / hide / row height / color | NocoDB, Teable | TanStack Table |
| 7 | Kanban, calendar, gallery, timeline, Gantt, list views | NocoDB, APITable | dnd-kit, schedule-x, frappe-gantt |
| 8 | Form view + public share links | NocoDB, Baserow | SurveyJS |
| 9 | Realtime multiplayer + presence | Teable (ShareDB), APITable | sharedb, yjs |
| 10 | Comments, @mentions, record history / revision | Teable, APITable | novu, tiptap |
| 11 | Permissions (workspace/base/table/field/view-lock) | Grist access rules, Teable | openfga |
| 12 | Automations (trigger → actions, run script) | Baserow, activepieces | activepieces, trigger.dev |
| 13 | Interfaces (dashboards/apps on data) | Baserow app builder, Appsmith | echarts, React Flow |
| 14 | Extensions / Blocks SDK | `Airtable/blocks` | — |
| 15 | REST API + webhooks + personal tokens + OAuth | `airtable.js`, `pyairtable`, `airtable-swagger` | PostgREST (idea) |
| 16 | Import CSV/Excel/Airtable, export | `backup-airtable` | SheetJS |
| 17 | Search across base | — | meilisearch |
| 18 | AI fields / agents / MCP | `airtable-mcp-server`, Teable AI | Claude API |
| 19 | Sync tables (cross-base) | Teable, NocoDB | electric-sql |
| 20 | Scale (100k+ rows/table) | Teable (Postgres + canvas) | glide-data-grid, TanStack Virtual |

---

## 5. Recommended path (minimal decisions)

1. **Clone and run Teable locally.** It's your living spec and nearest twin.
2. **Stack:** Next.js + NestJS (or Hono) + Postgres + Drizzle + ShareDB + glide-data-grid + Teable's MIT `formula`/`core` packages.
3. **MVP order:** tables/fields → grid → links/lookups/rollups → formulas → filter/sort/group → kanban/calendar/form → realtime → permissions → API → automations → interfaces.
4. **License guardrail:** take code freely from **MIT/Apache** repos (Teable `packages/*`, Baserow core, Grist, glide, TanStack, dnd-kit, sharedb, yjs, activepieces core). Treat **AGPL / Sustainable Use / BSL** repos (NocoDB, n8n, Teable apps, APITable, ToolJet, Directus) as **read-only references** unless you plan to open-source your product under the same terms.

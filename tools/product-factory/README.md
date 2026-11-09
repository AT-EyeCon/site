# Product Factory 🏭

**What it does:** turns one command into a draft $27–37 digital product, using free AI.
Like a printing press: you design the page once (a "spec"), and it prints the whole book.

## One-time setup (5 min)
1. Install Node.js (nodejs.org, LTS) if you don't have it.
2. Get a free Gemini key: aistudio.google.com → Get API key.
3. In this folder, copy `.env.example` to `.env` and paste the key after `GEMINI_API_KEY=`.
   More keys (Groq, Mistral, Cerebras, OpenRouter) = fewer slowdowns. It switches automatically.

## Make a product (about 10 min of the computer working, then your review)
```bash
cd tools/product-factory
node factory.mjs --list
node factory.mjs specs/parent-communication-pack.json
```
Then open `output/<product>/REVIEW.md` and follow the checklist.

## Ready-to-run products
| Spec | Product | Price |
|---|---|---|
| `cvi-goal-bank.json` | 75 CVI goals across 3 levels | $27 |
| `parent-communication-pack.json` | 54 family letters/emails | $27 |
| `om-lesson-plans.json` | 60 O&M lessons, preschool → adult | $37 |

**New product idea?** Copy any spec, then change the title, sections and columns. That's it.

## Rules
- Your expert review is the product. Never sell unreviewed AI output.
- Free AI tiers may train on what you send. These specs contain no student data; keep it that way.
- `.env` and `output/` are never committed (see `.gitignore`).

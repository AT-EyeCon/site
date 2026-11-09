# The Vault, TVI Toolkit: site

Static site on **Cloudflare Pages**. Checkout runs through **Payhip**.
Two free AI tools bring TVIs in and point them to the $147 Pro Bundle:
- **Goal Drafter** (`/goal-drafter.html`): free on Cloudflare Workers AI
- **Image Describer** (`/describe.html`): needs a free `GEMINI_API_KEY` secret (Cloudflare has no strong free vision model)

Plus **`tools/product-factory/`**: drafts new $27 products with free AI (see its README).

## Go-live checklist (about 20 min)

1. **Paste your Payhip links** into `config.js`. That's the only file with links; every button reads from it.
2. **Turn on the free AI.** Cloudflare dashboard → Workers & Pages → your project → Settings → Bindings → Add → **Workers AI**, variable name `AI`. Free, no key needed.
   (`wrangler.toml` does this too, but its `name` must match your Pages project name. If it doesn't, change the name or delete the file.)
3. **Optional backups** if Cloudflare's free quota runs out. Add these as *Secrets* (Settings → Variables and Secrets):
   `GEMINI_API_KEY` (aistudio.google.com), `GROQ_API_KEY` (console.groq.com), `OPENROUTER_API_KEY` (openrouter.ai).
   The drafter tries them in order: Cloudflare → Gemini → Groq → OpenRouter.
   **The Image Describer requires `GEMINI_API_KEY`.** `MISTRAL_API_KEY` is an optional backup.
4. **Rate limiting.** Cloudflare → Security → WAF → Rate limiting rule: paths `/api/draft-goal` and `/api/describe-image`, 10 requests/min per IP.
5. **Add your product image** at `assets/mockup-tvi-toolkit-pro.png` (it's hidden until the file exists).
6. Deploy, open `/goal-drafter.html`, and draft one goal to confirm.

## Optional model overrides (env vars)
`CF_MODEL`, `GEMINI_MODEL`, `GROQ_MODEL`, `OPENROUTER_MODEL`. Use these if a provider renames its model.

## Files
- `index.html`: sales page
- `goal-drafter.html` + `goal-drafter.js`: free tool (5 drafts per browser per day)
- `functions/api/draft-goal.js`: AI backend (keys stay server-side; blocks names, dates, IDs, emails, phones)
- `config.js`: your links
- `styles.css`: high-contrast, accessible styles with dark mode

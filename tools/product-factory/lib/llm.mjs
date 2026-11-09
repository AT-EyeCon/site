// One function, many free LLMs. Tries each provider you have a key for, in order.
// Keys come from environment variables or a .env file next to factory.mjs (never committed).
// All of these speak the OpenAI chat format, so only the URL/model differ.

export const PROVIDERS = [
  { name: "gemini",     key: "GEMINI_API_KEY",     url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", model: "gemini-3.8-flash" },
  { name: "gemini-backup", key: "GEMINI_API_KEY", url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", model: "gemini-3.6-flash" },
  { name: "gemini-lite",   key: "GEMINI_API_KEY", url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", model: "gemini-3.5-flash-lite" },
  { name: "groq",       key: "GROQ_API_KEY",       url: "https://api.groq.com/openai/v1/chat/completions",                         model: "llama-3.3-70b-versatile" },
  { name: "mistral",    key: "MISTRAL_API_KEY",    url: "https://api.mistral.ai/v1/chat/completions",                               model: "mistral-small-latest" },
  { name: "cerebras",   key: "CEREBRAS_API_KEY",   url: "https://api.cerebras.ai/v1/chat/completions",                              model: "llama-3.3-70b" },
  { name: "openrouter", key: "OPENROUTER_API_KEY", url: "https://openrouter.ai/api/v1/chat/completions",                            model: "meta-llama/llama-3.3-70b-instruct:free" },
];

export function available(env = process.env) {
  return PROVIDERS.filter((p) => env[p.key]).map((p) => ({
    ...p,
    model: env[p.name.toUpperCase().replace(/-/g, "_") + "_MODEL"] || p.model, // e.g. GEMINI_MODEL=gemini-3.6-flash
    apiKey: env[p.key],
  }));
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Returns the first provider's text answer. Rotates providers on errors/rate limits.
export async function chat(messages, { env = process.env, temperature = 0.7, maxTokens = 12000, log = console.error } = {}) {
  const list = available(env);
  if (!list.length) throw new Error("No API keys found. Add at least one (e.g. GEMINI_API_KEY) to tools/product-factory/.env");
  for (let attempt = 0; attempt < 4; attempt++) {
    for (const p of list) {
      try {
        const res = await fetch(p.url, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${p.apiKey}` },
          body: JSON.stringify({ model: p.model, messages, temperature, max_tokens: maxTokens }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const text = data?.choices?.[0]?.message?.content;
        if (text) return { text, provider: p.name };
        throw new Error("empty answer");
      } catch (e) {
        log(`  ↳ ${p.name} failed (${e.message}), trying next…`);
      }
    }
    if (attempt === 3) break;
    const wait = env.FACTORY_RETRY_MS ? Number(env.FACTORY_RETRY_MS) : 30000;
    log(`  ↳ all providers busy; waiting ${Math.round(wait / 1000)}s and retrying once…`);
    await sleep(wait);
  }
  throw new Error("Every provider failed 4 rounds in a row. Check your keys or try again later.");
}

// Pull the first JSON array/object out of a model reply.
export function extractJSON(text) {
  const s = String(text);
  const i = Math.min(...["[", "{"].map((c) => (s.indexOf(c) < 0 ? Infinity : s.indexOf(c))));
  const j = Math.max(s.lastIndexOf("]"), s.lastIndexOf("}"));
  if (!isFinite(i) || j <= i) return null;
  try { return JSON.parse(s.slice(i, j + 1)); } catch { return null; }
}

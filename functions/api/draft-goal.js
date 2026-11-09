// Cloudflare Pages Function: POST /api/draft-goal
// Drafts ONE ECC-aligned SMART goal from de-identified inputs.
//
// Providers are tried in order. The first one that is configured AND answers wins:
//   1. Cloudflare Workers AI  -> needs the "AI" binding (free, no key)
//   2. Google Gemini          -> secret GEMINI_API_KEY
//   3. Groq                   -> secret GROQ_API_KEY
//   4. OpenRouter (free tier) -> secret OPENROUTER_API_KEY
// Model names can be overridden with env vars (see README) because providers rename them often.

export const ECC_AREAS = [
  "Compensatory / Functional Academic Skills (incl. braille & communication modes)",
  "Orientation & Mobility",
  "Social Interaction",
  "Independent Living",
  "Recreation & Leisure",
  "Career Education",
  "Assistive Technology",
  "Sensory Efficiency",
  "Self-Determination",
];
const GRADES = ["Birth–3 (Early Intervention)", "Preschool", "K–2", "3–5", "6–8", "9–12", "Transition (18–21)"];
const LEVELS = ["Emerging (needs full support)", "Developing (needs moderate prompting)", "Approaching (needs minimal prompting)", "Generalizing (independent in some settings)"];
const SETTINGS = ["General education classroom", "Resource / pull-out", "Home / community", "School campus", "Work-based setting", "Virtual / hybrid"];

const MAX_FOCUS = 160;
const SAFE_WORDS = new Set(("braille brailler note touch perkins google docs apple watch ipad iphone voiceover jaws nvda zoomtext " +
  "victor reader stream seeing ai be my eyes microsoft word office chromebook android talkback magnifier cctv " +
  "nemeth ueb code unified english expanded core curriculum white cane monocular telescope smart board " +
  "orientation mobility independent living").split(" "));

// Blocks the most common kinds of identifying info. Not perfect; the UI also warns users.
export function findPII(text) {
  const checks = [
    [/[\w.+-]+@[\w-]+\.[\w.]+/, "an email address"],
    [/\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b/, "a phone number"],
    [/\b\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}\b/, "a date"],
    [/\b\d{5,}\b/, "an ID number"],
    [/\b(?:named|name is|called)\s+[A-Z]/i, "a name"],
    [/\b(?:Mr|Mrs|Ms|Miss|Dr)\.?\s+[A-Z]/, "a person's name"],
  ];
  for (const [re, label] of checks) if (re.test(text)) return label;
  // Two capitalized words in a row ("Jane Doe") unless they're known tool/product words.
  for (const m of text.matchAll(/\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b/g)) {
    if (!SAFE_WORDS.has(m[1].toLowerCase()) && !SAFE_WORDS.has(m[2].toLowerCase())) return "what looks like a full name";
  }
  return null;
}

export function validate(body) {
  const b = body || {};
  if (!ECC_AREAS.includes(b.ecc)) return { error: "Pick an ECC area." };
  if (!GRADES.includes(b.grade)) return { error: "Pick a grade band." };
  if (!LEVELS.includes(b.level)) return { error: "Pick a current performance level." };
  if (!SETTINGS.includes(b.setting)) return { error: "Pick a setting." };
  const focus = String(b.focus || "").trim().replace(/\s+/g, " ");
  if (focus.length < 3) return { error: "Describe the skill focus in a few words." };
  if (focus.length > MAX_FOCUS) return { error: `Keep the skill focus under ${MAX_FOCUS} characters.` };
  const pii = findPII(focus);
  if (pii) return { error: `Remove ${pii}. Never enter student-identifying information.` };
  return { value: { ecc: b.ecc, grade: b.grade, level: b.level, setting: b.setting, focus } };
}

const SYSTEM = `You are a veteran Teacher of Students with Visual Impairments (TVI) writing IEP goals.
Write measurable, IDEA-aligned, ECC-aligned SMART goals in professional, neutral legal language.
Rules:
- Refer to the learner only as "the student". Never invent names, ages, dates, or diagnoses.
- The annual goal follows: "By the end of the IEP period, given [conditions/supports], the student will [observable behavior] with [criterion] across [number] consecutive data sessions, as measured by [method]."
- Benchmarks are 3 short-term objectives that step up from the stated current level.
- Keep it realistic for the grade band and current level.
Respond with ONLY valid JSON, no markdown, in this exact shape:
{"goal":"...","benchmarks":["...","...","..."],"measurement":"...","accommodations":["...","..."],"plaafp_starter":"..."}
"plaafp_starter" is one sentence a TVI could start a present-levels statement with, using [brackets] where the teacher must add real data.`;

function userPrompt(v) {
  return `ECC area: ${v.ecc}
Grade band: ${v.grade}
Current level: ${v.level}
Setting: ${v.setting}
Skill focus: ${v.focus}`;
}

export function parseModelJSON(text) {
  if (!text) return null;
  const s = String(text);
  const start = s.indexOf("{");
  const end = s.lastIndexOf("}");
  if (start < 0 || end <= start) return null;
  try {
    const j = JSON.parse(s.slice(start, end + 1));
    if (typeof j.goal !== "string" || !Array.isArray(j.benchmarks)) return null;
    const str = (x) => String(x ?? "").slice(0, 900);
    return {
      goal: str(j.goal),
      benchmarks: j.benchmarks.slice(0, 4).map(str),
      measurement: str(j.measurement),
      accommodations: Array.isArray(j.accommodations) ? j.accommodations.slice(0, 4).map(str) : [],
      plaafp_starter: str(j.plaafp_starter),
    };
  } catch {
    return null;
  }
}

async function openAICompatible(url, key, model, messages, extraHeaders = {}) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}`, ...extraHeaders },
    body: JSON.stringify({ model, messages, temperature: 0.4, max_tokens: 900 }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data?.choices?.[0]?.message?.content;
}

export function providers(env) {
  const list = [];
  if (env.AI) {
    list.push({
      name: "cloudflare",
      run: async (messages) => {
        const out = await env.AI.run(env.CF_MODEL || "@cf/meta/llama-3.3-70b-instruct-fp8-fast", { messages, max_tokens: 900, temperature: 0.4 });
        const r = out?.response;
        return typeof r === "string" ? r : JSON.stringify(r);
      },
    });
  }
  if (env.GEMINI_API_KEY) {
    list.push({ name: "gemini", run: (m) => openAICompatible("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", env.GEMINI_API_KEY, env.GEMINI_MODEL || "gemini-2.5-flash", m) });
  }
  if (env.GROQ_API_KEY) {
    list.push({ name: "groq", run: (m) => openAICompatible("https://api.groq.com/openai/v1/chat/completions", env.GROQ_API_KEY, env.GROQ_MODEL || "llama-3.3-70b-versatile", m) });
  }
  if (env.OPENROUTER_API_KEY) {
    list.push({ name: "openrouter", run: (m) => openAICompatible("https://openrouter.ai/api/v1/chat/completions", env.OPENROUTER_API_KEY, env.OPENROUTER_MODEL || "meta-llama/llama-3.3-70b-instruct:free", m, { "X-Title": "The Vault TVI Goal Drafter" }) });
  }
  return list;
}

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });

export async function onRequestPost({ request, env }) {
  if (!(request.headers.get("Content-Type") || "").includes("application/json")) return json({ error: "Send JSON." }, 415);
  let body;
  try { body = await request.json(); } catch { return json({ error: "Bad request." }, 400); }

  const checked = validate(body);
  if (checked.error) return json({ error: checked.error }, 400);

  const list = providers(env);
  if (!list.length) return json({ error: "The drafter isn't configured yet. (Owner: add the AI binding or an API key.)" }, 503);

  const messages = [{ role: "system", content: SYSTEM }, { role: "user", content: userPrompt(checked.value) }];
  for (const p of list) {
    try {
      const result = parseModelJSON(await p.run(messages));
      if (result) return json({ ...result, provider: p.name });
    } catch (e) {
      console.log(`provider ${p.name} failed: ${e.message}`); // shows in Cloudflare logs; no user input logged
    }
  }
  return json({ error: "The free AI is busy right now. Try again in a minute." }, 503);
}


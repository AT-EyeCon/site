// Cloudflare Pages Function: POST /api/describe-image
// Turns a classroom image (worksheet, diagram, chart, photo) into accessible descriptions for students with visual impairments.
//
// Vision providers, tried in order (add any as Secrets in Cloudflare):
//   1. Google Gemini   -> GEMINI_API_KEY      (best free vision model; default)
//   2. Mistral         -> MISTRAL_API_KEY
//   3. OpenRouter      -> OPENROUTER_API_KEY + OPENROUTER_VISION_MODEL (a free vision model id)
// Optional model overrides: GEMINI_VISION_MODEL, MISTRAL_VISION_MODEL.

const MAX_BYTES = 4 * 1024 * 1024; // the page shrinks images well below this
const PURPOSES = ["Worksheet or handout", "Diagram or chart", "Map", "Photo", "Math or science figure", "Book illustration"];
const GRADES = ["Preschool", "K–2", "3–5", "6–8", "9–12", "Adult"];

export function validate(b) {
  b = b || {};
  const m = /^data:image\/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)$/.exec(String(b.image || ""));
  if (!m) return { error: "Upload a PNG, JPG, or WebP image." };
  if (m[2].length * 0.75 > MAX_BYTES) return { error: "That image is too large. Try a smaller one." };
  if (!PURPOSES.includes(b.purpose)) return { error: "Pick what kind of image this is." };
  if (!GRADES.includes(b.grade)) return { error: "Pick a grade level." };
  return { value: { image: b.image, purpose: b.purpose, grade: b.grade } };
}

const SYSTEM = `You are a TVI (Teacher of Students with Visual Impairments) and certified image describer following DIAGRAM Center and BANA guidance.
Describe the image for a student who cannot see it, at the given grade level.
Rules:
- Be objective. Describe what is shown, not what it means, unless the meaning is the point (e.g. a chart's trend).
- Go from general to specific. Transcribe all instructional text exactly, but replace any person's name, student ID, or school name with [Name] / [ID] / [School].
- Do not guess identities of people.
Reply with ONLY valid JSON, no markdown:
{"alt_text":"one sentence, max 150 characters","extended_description":"full description in reading order, paragraphs separated by \\n\\n","text_in_image":"exact transcription of any instructional text, or empty string","tactile_tips":["2-4 tips for making a tactile graphic of this image"],"teaching_notes":"1-2 sentences on what to pre-teach or check for understanding"}`;

export function parse(text) {
  const s = String(text || "");
  const i = s.indexOf("{"), j = s.lastIndexOf("}");
  if (i < 0 || j <= i) return null;
  try {
    const o = JSON.parse(s.slice(i, j + 1));
    if (typeof o.alt_text !== "string" || typeof o.extended_description !== "string") return null;
    const str = (x, n) => String(x ?? "").slice(0, n);
    return {
      alt_text: str(o.alt_text, 300),
      extended_description: str(o.extended_description, 6000),
      text_in_image: str(o.text_in_image, 4000),
      tactile_tips: Array.isArray(o.tactile_tips) ? o.tactile_tips.slice(0, 5).map((t) => str(t, 400)) : [],
      teaching_notes: str(o.teaching_notes, 800),
    };
  } catch { return null; }
}

export function providers(env) {
  const list = [];
  if (env.GEMINI_API_KEY) list.push({ name: "gemini", url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", key: env.GEMINI_API_KEY, model: env.GEMINI_VISION_MODEL || "gemini-3.6-flash" });
  if (env.MISTRAL_API_KEY) list.push({ name: "mistral", url: "https://api.mistral.ai/v1/chat/completions", key: env.MISTRAL_API_KEY, model: env.MISTRAL_VISION_MODEL || "mistral-small-latest" });
  if (env.OPENROUTER_API_KEY && env.OPENROUTER_VISION_MODEL) list.push({ name: "openrouter", url: "https://openrouter.ai/api/v1/chat/completions", key: env.OPENROUTER_API_KEY, model: env.OPENROUTER_VISION_MODEL });
  return list;
}

const json = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });

export async function onRequestPost({ request, env }) {
  if (Number(request.headers.get("Content-Length") || 0) > MAX_BYTES * 1.5) return json({ error: "That image is too large." }, 413);
  let body;
  try { body = await request.json(); } catch { return json({ error: "Bad request." }, 400); }
  const v = validate(body);
  if (v.error) return json({ error: v.error }, 400);

  const list = providers(env);
  if (!list.length) return json({ error: "The describer isn't configured yet. (Owner: add GEMINI_API_KEY.)" }, 503);

  const messages = [
    { role: "system", content: SYSTEM },
    { role: "user", content: [
      { type: "text", text: `Image type: ${v.value.purpose}\nGrade level: ${v.value.grade}` },
      { type: "image_url", image_url: { url: v.value.image } },
    ] },
  ];
  for (const p of list) {
    try {
      const res = await fetch(p.url, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${p.key}` },
        body: JSON.stringify({ model: p.model, messages, temperature: 0.2, max_tokens: 2000 }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const out = parse(data?.choices?.[0]?.message?.content);
      if (out) return json({ ...out, provider: p.name });
    } catch (e) {
      console.log(`vision provider ${p.name} failed: ${e.message}`);
    }
  }
  return json({ error: "The free AI is busy right now. Try again in a minute." }, 503);
}

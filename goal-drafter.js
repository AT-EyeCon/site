// Front end for the free Goal Drafter. Option lists MUST match functions/api/draft-goal.js.
(function () {
  var OPTIONS = {
    ecc: [
      "Compensatory / Functional Academic Skills (incl. braille & communication modes)",
      "Orientation & Mobility", "Social Interaction", "Independent Living", "Recreation & Leisure",
      "Career Education", "Assistive Technology", "Sensory Efficiency", "Self-Determination"
    ],
    grade: ["Birth–3 (Early Intervention)", "Preschool", "K–2", "3–5", "6–8", "9–12", "Transition (18–21)"],
    level: ["Emerging (needs full support)", "Developing (needs moderate prompting)", "Approaching (needs minimal prompting)", "Generalizing (independent in some settings)"],
    setting: ["General education classroom", "Resource / pull-out", "Home / community", "School campus", "Work-based setting", "Virtual / hybrid"]
  };
  var DAILY_FREE = 5; // soft limit per browser per day; nudges heavy users toward the bundle

  var $ = function (id) { return document.getElementById(id); };
  Object.keys(OPTIONS).forEach(function (key) {
    var sel = $(key);
    sel.add(new Option("Choose…", ""));
    OPTIONS[key].forEach(function (o) { sel.add(new Option(o, o)); });
  });

  // Usage counter (wrapped: storage can be blocked)
  var today = new Date().toISOString().slice(0, 10);
  function getUsed() {
    try { var s = JSON.parse(localStorage.getItem("vaultDrafter") || "{}"); return s.day === today ? s.n : 0; } catch (e) { return 0; }
  }
  function setUsed(n) { try { localStorage.setItem("vaultDrafter", JSON.stringify({ day: today, n: n })); } catch (e) {} }
  function showRemaining() {
    var left = Math.max(0, DAILY_FREE - getUsed());
    $("remaining").textContent = left + " free draft" + (left === 1 ? "" : "s") + " left today.";
  }
  showRemaining();

  $("focus").addEventListener("input", function () { $("focus-count").textContent = this.value.length + " / 160"; });

  // Same checks as the server, so users get instant feedback.
  var SAFE = new Set(("braille brailler note touch perkins google docs apple watch ipad iphone voiceover jaws nvda zoomtext victor reader stream seeing ai be my eyes microsoft word office chromebook android talkback magnifier cctv nemeth ueb code unified english expanded core curriculum white cane monocular telescope smart board orientation mobility independent living").split(" "));
  function findPII(t) {
    var checks = [
      [/[\w.+-]+@[\w-]+\.[\w.]+/, "an email address"], [/\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b/, "a phone number"],
      [/\b\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}\b/, "a date"], [/\b\d{5,}\b/, "an ID number"],
      [/\b(?:named|name is|called)\s+[A-Z]/i, "a name"], [/\b(?:Mr|Mrs|Ms|Miss|Dr)\.?\s+[A-Z]/, "a person's name"]
    ];
    for (var i = 0; i < checks.length; i++) if (checks[i][0].test(t)) return checks[i][1];
    var re = /\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b/g, m;
    while ((m = re.exec(t))) if (!SAFE.has(m[1].toLowerCase()) && !SAFE.has(m[2].toLowerCase())) return "what looks like a full name";
    return null;
  }

  function showError(msg) { var e = $("error"); e.textContent = msg; e.hidden = !msg; }
  function fillList(el, items) {
    el.textContent = "";
    items.forEach(function (t) { var li = document.createElement("li"); li.textContent = t; el.appendChild(li); });
  }

  var last = null;
  $("drafter").addEventListener("submit", async function (ev) {
    ev.preventDefault();
    showError("");
    var data = {};
    ["ecc", "grade", "level", "setting", "focus"].forEach(function (k) { data[k] = $(k).value.trim(); });
    if (!data.ecc || !data.grade || !data.level || !data.setting) return showError("Please choose an option in every dropdown.");
    if (data.focus.length < 3) return showError("Describe the skill focus in a few words.");
    var pii = findPII(data.focus);
    if (pii) return showError("Remove " + pii + ". Never enter student-identifying information.");
    if (getUsed() >= DAILY_FREE) {
      return showError("You've used today's " + DAILY_FREE + " free drafts. Come back tomorrow, or get all 540+ goals in the Pro Bundle.");
    }

    var btn = $("submit");
    btn.disabled = true; btn.textContent = "Drafting…";
    $("output").setAttribute("aria-busy", "true");
    try {
      var res = await fetch("/api/draft-goal", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
      var out = await res.json().catch(function () { return { error: "Something went wrong. Try again." }; });
      if (!res.ok || out.error) throw new Error(out.error || "Something went wrong. Try again.");
      last = out;
      $("r-goal").textContent = out.goal;
      fillList($("r-bench"), out.benchmarks);
      $("r-measure").textContent = out.measurement;
      fillList($("r-acc"), out.accommodations);
      $("r-plaafp").textContent = out.plaafp_starter;
      $("placeholder").hidden = true;
      $("result").hidden = false;
      setUsed(getUsed() + 1);
      showRemaining();
      $("out-title").focus && $("out-title").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) {
      showError(e.message);
    } finally {
      btn.disabled = false; btn.textContent = "Draft my goal";
      $("output").setAttribute("aria-busy", "false");
    }
  });

  $("copy").addEventListener("click", async function () {
    if (!last) return;
    var text = "ANNUAL GOAL\n" + last.goal +
      "\n\nBENCHMARKS\n" + last.benchmarks.map(function (b, i) { return (i + 1) + ". " + b; }).join("\n") +
      "\n\nMEASUREMENT\n" + last.measurement +
      "\n\nACCOMMODATIONS\n" + last.accommodations.map(function (a) { return "- " + a; }).join("\n") +
      "\n\nPLAAFP STARTER\n" + last.plaafp_starter +
      "\n\n(Drafted with the free TVI Goal Drafter from The Vault. Review before use.)";
    try { await navigator.clipboard.writeText(text); this.textContent = "Copied ✓"; }
    catch (e) { this.textContent = "Select and copy manually"; }
    var b = this; setTimeout(function () { b.textContent = "Copy all"; }, 2000);
  });
})();

// Front end for the free Image Describer. Lists MUST match functions/api/describe-image.js.
(function () {
  var PURPOSES = ["Worksheet or handout", "Diagram or chart", "Map", "Photo", "Math or science figure", "Book illustration"];
  var GRADES = ["Preschool", "K–2", "3–5", "6–8", "9–12", "Adult"];
  var DAILY_FREE = 5;
  var MAX_SIDE = 1600; // shrink big phone photos; also strips location metadata

  var $ = function (id) { return document.getElementById(id); };
  [["purpose", PURPOSES], ["grade", GRADES]].forEach(function (p) {
    var sel = $(p[0]); sel.add(new Option("Choose…", ""));
    p[1].forEach(function (o) { sel.add(new Option(o, o)); });
  });

  var today = new Date().toISOString().slice(0, 10);
  function getUsed() { try { var s = JSON.parse(localStorage.getItem("vaultDescriber") || "{}"); return s.day === today ? s.n : 0; } catch (e) { return 0; } }
  function setUsed(n) { try { localStorage.setItem("vaultDescriber", JSON.stringify({ day: today, n: n })); } catch (e) {} }
  function showRemaining() { var l = Math.max(0, DAILY_FREE - getUsed()); $("remaining").textContent = l + " free description" + (l === 1 ? "" : "s") + " left today."; }
  showRemaining();

  function showError(m) { $("error").textContent = m; $("error").hidden = !m; }

  var dataUrl = null;
  $("file").addEventListener("change", function () {
    showError(""); dataUrl = null; $("preview").hidden = true;
    var f = this.files && this.files[0];
    if (!f) return;
    if (!/^image\/(png|jpeg|webp)$/.test(f.type)) return showError("Please choose a PNG, JPG, or WebP image.");
    var img = new Image();
    img.onload = function () {
      var scale = Math.min(1, MAX_SIDE / Math.max(img.width, img.height));
      var c = document.createElement("canvas");
      c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale);
      var ctx = c.getContext("2d"); ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, c.width, c.height);
      ctx.drawImage(img, 0, 0, c.width, c.height);
      dataUrl = c.toDataURL("image/jpeg", 0.85);
      $("preview").src = dataUrl; $("preview").alt = "Preview of the uploaded image"; $("preview").hidden = false;
      URL.revokeObjectURL(img.src);
    };
    img.onerror = function () { showError("Couldn't read that image. Try another file."); };
    img.src = URL.createObjectURL(f);
  });

  function fill(el, items) { el.textContent = ""; items.forEach(function (t) { var li = document.createElement("li"); li.textContent = t; el.appendChild(li); }); }

  var last = null;
  $("describer").addEventListener("submit", async function (ev) {
    ev.preventDefault(); showError("");
    if (!dataUrl) return showError("Choose an image first.");
    if (!$("purpose").value || !$("grade").value) return showError("Choose an image type and grade level.");
    if (getUsed() >= DAILY_FREE) return showError("You've used today's " + DAILY_FREE + " free descriptions. Come back tomorrow!");
    var btn = $("submit"); btn.disabled = true; btn.textContent = "Describing…"; $("output").setAttribute("aria-busy", "true");
    try {
      var res = await fetch("/api/describe-image", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: dataUrl, purpose: $("purpose").value, grade: $("grade").value }) });
      var out = await res.json().catch(function () { return { error: "Something went wrong. Try again." }; });
      if (!res.ok || out.error) throw new Error(out.error || "Something went wrong. Try again.");
      last = out;
      $("r-alt").textContent = out.alt_text;
      var ext = $("r-ext"); ext.textContent = "";
      out.extended_description.split(/\n\n+/).forEach(function (para) { var p = document.createElement("p"); p.textContent = para; ext.appendChild(p); });
      $("r-text").textContent = out.text_in_image; $("r-text-wrap").hidden = !out.text_in_image;
      fill($("r-tips"), out.tactile_tips); $("r-notes").textContent = out.teaching_notes;
      $("placeholder").hidden = true; $("result").hidden = false;
      setUsed(getUsed() + 1); showRemaining();
    } catch (e) { showError(e.message); }
    finally { btn.disabled = false; btn.textContent = "Describe this image"; $("output").setAttribute("aria-busy", "false"); }
  });

  $("copy").addEventListener("click", async function () {
    if (!last) return;
    var t = "ALT TEXT\n" + last.alt_text + "\n\nEXTENDED DESCRIPTION\n" + last.extended_description +
      (last.text_in_image ? "\n\nTEXT IN IMAGE\n" + last.text_in_image : "") +
      "\n\nTACTILE GRAPHIC TIPS\n" + last.tactile_tips.map(function (x) { return "- " + x; }).join("\n") +
      "\n\nTEACHING NOTES\n" + last.teaching_notes + "\n\n(Described with the free Image Describer from The Vault. Review before use.)";
    var b = this;
    try { await navigator.clipboard.writeText(t); b.textContent = "Copied ✓"; } catch (e) { b.textContent = "Select and copy manually"; }
    setTimeout(function () { b.textContent = "Copy all"; }, 2000);
  });
})();

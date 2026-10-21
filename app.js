// ---------- rendering ----------
const fmt = (x, d = 1) => (x == null || !isFinite(x)) ? "—" : x.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const fmtT = t => `${t > 0 ? "" : t < 0 ? "−" : ""}${Math.abs(t).toFixed(1)} °C`;
function tColor(t) {
  const stops = [[-60, [47, 92, 225]], [0, [47, 125, 225]], [15, [70, 170, 210]], [28, [140, 150, 158]], [45, [222, 140, 60]], [100, [217, 84, 43]]];
  if (t <= stops[0][0]) return `rgb(${stops[0][1]})`;
  for (let i = 1; i < stops.length; i++) if (t <= stops[i][0]) {
    const [t0, c0] = stops[i - 1], [t1, c1] = stops[i], f = (t - t0) / (t1 - t0);
    return `rgb(${c0.map((c, j) => Math.round(c + (c1[j] - c) * f)).join(",")})`;
  }
  return `rgb(${stops[stops.length - 1][1]})`;
}
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function paramFields(def, values, prefix) {
  return Object.entries(def.params).map(([k, [label, unit, , step]]) =>
    `<label class="field"><span>${esc(label)}${unit ? ` <span class="num">(${esc(unit)})</span>` : ""}</span><input type="number" id="${prefix}-${k}" data-k="${k}" step="${step}" value="${values[k]}"></label>`).join("");
}
function typeSelect(st) {
  return `<select aria-label="Stage type" data-swap="${st.id}">${Object.entries(STAGES).map(([k, d]) => `<option value="${k}" ${k === st.type ? "selected" : ""}>${esc(d.name)}</option>`).join("")}</select>`;
}
function gauge(n) {
  const c = tColor(n.T);
  return `<div class="link" style="--tcol:${c}"><div class="gauge" style="--tcol:${c}"><div class="t">${fmtT(n.T)}</div><div class="p">${fmt(n.P - PA, 1)} bar(g)</div><div class="m">${fmt(n.m * 1000, 1)} g/s</div></div></div>`;
}
function stageStat(st) {
  const i = st._info || {};
  const bits = [];
  if (i.work) bits.push(`Shaft work out <b class="num">${fmt(i.work / 1000, 2)} kW</b>`);
  if (i.eta != null) bits.push(`Effective efficiency <b class="num">${fmt(i.eta * 100, 0)} %</b>`);
  if (i.heat) bits.push(`Heat rejected <b class="num">${fmt(i.heat / 1000, 1)} kW</b>`);
  if (i.jt) bits.push(`Joule–Thomson cooling <b class="num">${fmt(i.jt, 1)} K</b>`);
  if (i.dTc != null) bits.push(`Cold side −${fmt(i.dTc, 1)} K · hot side +${fmt(i.hot, 0)} K (dumped)`);
  return bits.length ? `<div class="stat">${bits.join("<br>")}</div>` : "";
}

let dragId = null;
function render() {
  const r = compute(S);
  const chain = document.getElementById("chain");
  let h = "";
  // source card
  h += `<article class="card fixed"><div class="card-h"><span class="title">Source</span><span class="tag">start</span></div><div class="card-b">
    <label class="field wide"><span>Type</span><select id="src-type" data-srctype="1"><option value="compressor" ${S.source.type === "compressor" ? "selected" : ""}>Compressor</option><option value="tank" ${S.source.type === "tank" ? "selected" : ""}>Storage tank</option></select></label>
    ${paramFields(SOURCES[S.source.type], S.source.p, "src")}
    ${S.source.type === "compressor" ? `<div class="stat">Supplies <b class="num">${fmt(r.mSupply * 1000, 1)} g/s</b></div>` : `<div class="stat">Usable air <b class="num">${fmt(r.storage ? r.storage.usable : 0, 2)} kg</b></div>`}
  </div></article>`;
  h += gauge(r.nodes[0]);
  S.stages.forEach((st, idx) => {
    const d = STAGES[st.type];
    const vanePick = st.type === "vane" ? `<label class="field wide"><span>Model</span><select data-vane="${st.id}"><option value="">Custom</option>${Object.keys(VANE_PRESETS).map(k => `<option ${VANE_PRESETS[k].power === st.p.power && VANE_PRESETS[k].cons === st.p.cons ? "selected" : ""}>${k}</option>`).join("")}</select></label>` : "";
    h += `<article class="card" draggable="true" data-id="${st.id}">
      <div class="card-h"><span class="grip" title="Drag to move" aria-hidden="true">⋮⋮</span>${typeSelect(st)}${d.exp ? '<span class="tag exp">expander</span>' : ""}</div>
      <div class="card-b" data-stage="${st.id}">${vanePick}${paramFields(d, st.p, "s" + st.id)}${stageStat(st)}</div>
      <div class="card-f"><button class="icon" type="button" data-mv="-1" data-id="${st.id}" aria-label="Move left" ${idx === 0 ? "disabled" : ""}>←</button><button class="icon" type="button" data-mv="1" data-id="${st.id}" aria-label="Move right" ${idx === S.stages.length - 1 ? "disabled" : ""}>→</button><button class="icon" type="button" data-del="${st.id}" aria-label="Remove stage">Remove</button></div>
    </article>`;
    h += gauge(r.nodes[idx + 1]);
  });
  h += `<article class="card fixed"><div class="card-h"><span class="title">Outlet</span><span class="tag">end</span></div><div class="card-b" data-outlet="1">${paramFields(OUTLET, S.outlet, "out")}</div></article>`;
  h += `<div class="add"><label class="field"><span>Add a stage</span><select id="addType">${Object.entries(STAGES).map(([k, d]) => `<option value="${k}">${esc(d.name)}</option>`).join("")}</select></label><button class="primary" type="button" id="addBtn">Add before outlet</button></div>`;
  chain.innerHTML = h;
  renderResults(r);
  renderChart(r);
  try { localStorage.setItem("aircycle-state", JSON.stringify(S)); } catch (e) {}
}

function renderResults(r) {
  const btu = r.cool * 3.412;
  const k = [
    { cls: "hero", v: fmtT(r.T), s: "Outlet temperature" },
    { v: `${fmt(r.dT, 1)}<span class="u">K</span>`, s: "ΔT below ambient" },
    { v: `${fmt(r.m * 1000, 1)}<span class="u">g/s</span>`, s: `Air mass flow · ${fmt(r.m * 3600, 0)} kg/h` },
    { cls: "hero", v: `${fmt(r.cool / 1000, 2)}<span class="u">kW</span>`, s: `Cooling capacity · ${fmt(btu, 0)} Btu/h` },
    { v: `${fmt(r.v, 2)}<span class="u">m/s</span>`, s: r.face != null ? `Through holes · face ${fmt(r.face, 2)} m/s` : "Nozzle exit speed" },
    { v: r.cop != null ? fmt(r.cop, 2) : "—", s: r.copNet != null ? `COP · ${fmt(r.copNet, 2)} with ${S.rec} % shaft work recovered` : (S.source.type === "tank" ? "COP, including the energy to fill the tank" : "COP (cooling ÷ compressor power)") },
  ];
  if (r.tOn != null) k.push({ v: `${fmt(r.tOn, 0)}<span class="u">s</span>`, s: r.tOff != null ? `Burst length · recharge ${fmt(r.tOff / 60, 1)} min` : "Run time from full tank" });
  document.getElementById("results").innerHTML = k.map(x => `<div class="kpi ${x.cls || ""}"><div class="v">${x.v}</div><div class="s">${x.s}</div></div>`).join("");
  const rows = [
    ["Volumetric flow at outlet", `${fmt(r.Q * 1000, 1)} L/s`],
    ["Outlet pressure", `${fmt(r.P - PA, 2)} bar(g)`],
    ["Reynolds number", fmt(r.Re, 0)],
    ["Archimedes number (≫1 sinks, ≪0.1 jets)", fmt(r.Ar, 4)],
    ["Shaft work taken out", `${fmt(r.work / 1000, 2)} kW`],
    ["Ambient air it can cool by 10 K", `${fmt(r.ent * 1000 / 1.16, 0)} L/s`],
    ["Compressor power for the air used", `${fmt(r.pIn / 1000, 2)} kW`],
    ["Compression energy per kg of air", `${fmt(r.eSpec / 1000, 0)} kJ/kg`],
    ["Shaft work recovered as power", `${fmt(r.wRec / 1000, 2)} kW`],
    ["Holds −10 K in a cross-breeze up to", `${fmt(r.breeze, 2)} m/s`],
  ];
  if (r.coldFrac < 1) rows.push(["Share of supply air leaving cold", `${fmt(r.coldFrac * 100, 0)} %`]);
  document.getElementById("detail").innerHTML = rows.map(([a, b]) => `<tr><td>${a}</td><td>${b}</td></tr>`).join("");
  document.getElementById("warns").innerHTML = r.warns.length ? r.warns.map(w => `<div class="warn">${esc(w)}</div>`).join("") : `<div class="okmsg">No warnings for this configuration.</div>`;
  renderCop(r);
}

function renderCop(r) {
  const items = [["This design", r.cop, "var(--cold)"]];
  if (r.copNet != null) items.push([`With ${S.rec} % recovery`, r.copNet, "var(--cold)"]);
  items.push(["Car AC (typical)", 2, "var(--muted)"], ["Split AC, Dubai (typical)", 3, "var(--muted)"], ["District cooling, UAE", 3.9, "var(--muted)"]);
  if (r.carnot != null) items.push(["Ideal limit for this ΔT", r.carnot, "var(--ok)"]);
  const W = 380, rowH = 24, L = 158, Rr = 46, H = items.length * rowH + 24;
  const lo = -2, hi = 2; // log10 range 0.01 to 100
  const x = v => L + (W - L - Rr) * (Math.log10(Math.max(0.01, Math.min(100, v))) - lo) / (hi - lo);
  let g = "";
  [0.01, 0.1, 1, 10, 100].forEach(t => { g += `<line x1="${x(t)}" x2="${x(t)}" y1="4" y2="${H - 18}" stroke="var(--line)"/><text x="${x(t)}" y="${H - 4}" text-anchor="middle" font-size="10" fill="var(--muted)" font-family="var(--f-num)">${t}</text>`; });
  items.forEach(([lab, v, c], i) => {
    const y = 6 + i * rowH;
    g += `<text x="${L - 8}" y="${y + 13}" text-anchor="end" font-size="11.5" fill="var(--ink)">${esc(lab)}</text>`;
    if (v != null && v > 0) g += `<rect x="${x(0.01)}" y="${y + 3}" width="${Math.max(1, x(v) - x(0.01))}" height="14" rx="3" fill="${c}" opacity="${c === 'var(--muted)' ? .45 : .85}"/><text x="${x(v) + 5}" y="${y + 14}" font-size="11" fill="var(--ink)" font-family="var(--f-num)">${fmt(v, v < 1 ? 2 : 1)}</text>`;
  });
  document.getElementById("copcmp").innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="COP of this design compared with air conditioners, log scale" style="min-width:340px">${g}</svg><div class="muted" style="font-size:11.5px">Log scale. AC values are typical figures; district cooling from 0.8–1.05 kW/RT (UNEP C2E2).</div>`;
}

function renderChart(r) {
  const W = 720, H = 270, L = 52, Rm = 56, T = 30, B = 62;
  const pts = r.nodes.concat([{ label: "Outlet", T: r.T, P: r.P, m: r.m }]);
  const temps = pts.map(p => p.T).concat([S.amb]);
  let lo = Math.floor(Math.min(...temps) / 10) * 10 - 10, hi = Math.ceil(Math.max(...temps) / 10) * 10 + 10;
  const x = i => L + (W - L - Rm) * (pts.length === 1 ? 0.5 : i / (pts.length - 1));
  const y = t => T + (H - T - B) * (1 - (t - lo) / (hi - lo));
  const step = (hi - lo) > 200 ? 50 : (hi - lo) > 80 ? 20 : 10;
  let g = "";
  for (let t = Math.ceil(lo / step) * step; t <= hi; t += step) g += `<line x1="${L}" x2="${W - Rm}" y1="${y(t)}" y2="${y(t)}" stroke="var(--line)" stroke-width="1"/><text x="${L - 8}" y="${y(t) + 4}" text-anchor="end" font-size="11" fill="var(--muted)" font-family="var(--f-num)">${t}</text>`;
  g += `<line x1="${L}" x2="${W - Rm}" y1="${y(S.amb)}" y2="${y(S.amb)}" stroke="var(--muted)" stroke-dasharray="4 4"/><text x="${W - Rm}" y="${y(S.amb) - 6}" text-anchor="end" font-size="11" fill="var(--muted)">ambient ${S.amb} °C</text>`;
  const path = pts.map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p.T)}`).join(" ");
  const area = `${path} L${x(pts.length - 1)},${y(lo)} L${x(0)},${y(lo)} Z`;
  g += `<path d="${area}" fill="var(--cold)" opacity=".07"/><path d="${path}" fill="none" stroke="var(--ink)" stroke-width="1.6" opacity=".6"/>`;
  pts.forEach((p, i) => {
    g += `<circle cx="${x(i)}" cy="${y(p.T)}" r="5" fill="${tColor(p.T)}" stroke="var(--panel)" stroke-width="2"/>`;
    g += `<text x="${x(i)}" y="${y(p.T) - 10}" text-anchor="middle" font-size="11" font-weight="700" fill="${tColor(p.T)}" font-family="var(--f-num)">${Math.round(p.T)}</text>`;
    const lab = p.label.length > 14 ? p.label.slice(0, 13) + "…" : p.label;
    g += `<text transform="translate(${x(i)},${H - B + 14}) rotate(30)" font-size="10.5" fill="var(--muted)">${esc(lab)}</text>`;
  });
  g += `<text x="${L - 8}" y="14" text-anchor="end" font-size="11" fill="var(--muted)">°C</text>`;
  document.getElementById("chart").innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Temperature at each point of the gas path">${g}</svg>`;
}

// ---------- events ----------
const chain = document.getElementById("chain");
chain.addEventListener("input", e => {
  const el = e.target; if (el.type !== "number") return;
  const k = el.dataset.k, val = parseFloat(el.value); if (!isFinite(val)) return;
  const body = el.closest("[data-stage],[data-outlet]");
  if (el.id.startsWith("src-")) S.source.p[k] = val;
  else if (body && body.dataset.outlet) S.outlet[k] = val;
  else if (body) { const st = S.stages.find(s => s.id == body.dataset.stage); st.p[k] = val; }
  const focusId = el.id, pos = el.selectionStart;
  render();
  const again = document.getElementById(focusId); if (again) { again.focus(); try { again.setSelectionRange(pos, pos); } catch (_) {} }
});
chain.addEventListener("change", e => {
  const el = e.target;
  if (el.dataset.swap) { const st = S.stages.find(s => s.id == el.dataset.swap); const old = st.p; st.type = el.value; st.p = defaults(STAGES[el.value]); for (const k in st.p) if (k in old) st.p[k] = old[k]; render(); }
  else if (el.dataset.vane) { const st = S.stages.find(s => s.id == el.dataset.vane); if (VANE_PRESETS[el.value]) Object.assign(st.p, VANE_PRESETS[el.value]); render(); }
  else if (el.dataset.srctype) { S.source = { type: el.value, p: defaults(SOURCES[el.value]) }; if (el.value === "tank") setMode("burst", false); render(); }
});
chain.addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  if (b.id === "addBtn") { S.stages.push(mkStage(document.getElementById("addType").value)); render(); return; }
  if (b.dataset.del) { S.stages = S.stages.filter(s => s.id != b.dataset.del); render(); return; }
  if (b.dataset.mv) { const i = S.stages.findIndex(s => s.id == b.dataset.id), j = i + +b.dataset.mv; if (j < 0 || j >= S.stages.length) return; [S.stages[i], S.stages[j]] = [S.stages[j], S.stages[i]]; render(); }
});
chain.addEventListener("dragstart", e => { const c = e.target.closest(".card[data-id]"); if (!c) return; if (e.target.matches("input,select")) { e.preventDefault(); return; } dragId = c.dataset.id; c.classList.add("dragging"); e.dataTransfer.effectAllowed = "move"; try { e.dataTransfer.setData("text/plain", dragId); } catch (_) {} });
chain.addEventListener("dragend", () => { dragId = null; chain.querySelectorAll(".dragging,.drop-before").forEach(n => n.classList.remove("dragging", "drop-before")); });
chain.addEventListener("dragover", e => { if (!dragId) return; const c = e.target.closest(".card[data-id]"); e.preventDefault(); chain.querySelectorAll(".drop-before").forEach(n => n.classList.remove("drop-before")); if (c && c.dataset.id !== dragId) c.classList.add("drop-before"); });
chain.addEventListener("drop", e => {
  if (!dragId) return; e.preventDefault();
  const c = e.target.closest(".card[data-id]");
  const from = S.stages.findIndex(s => s.id == dragId); const item = S.stages.splice(from, 1)[0];
  if (c && c.dataset.id !== dragId) { const to = S.stages.findIndex(s => s.id == c.dataset.id); S.stages.splice(to, 0, item); } else S.stages.push(item);
  dragId = null; render();
});
function setMode(m, rerender = true) { S.mode = m; document.getElementById("m-cont").setAttribute("aria-pressed", m === "cont"); document.getElementById("m-burst").setAttribute("aria-pressed", m === "burst"); if (rerender) render(); }
document.getElementById("m-cont").addEventListener("click", () => setMode("cont"));
document.getElementById("m-burst").addEventListener("click", () => setMode("burst"));
document.getElementById("preset").addEventListener("change", e => { loadPreset(e.target.value); document.getElementById("amb").value = S.amb; setMode(S.mode); });
document.getElementById("amb").addEventListener("input", e => { const v = parseFloat(e.target.value); if (isFinite(v)) { S.amb = v; render(); } });
document.getElementById("rec").addEventListener("input", e => { const v = parseFloat(e.target.value); if (isFinite(v)) { S.rec = Math.max(0, Math.min(100, v)); render(); } });

// boot
(function () {
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem("aircycle-state") || "null"); } catch (e) {}
  if (saved && saved.stages && saved.source) { S = saved; uid = Math.max(0, ...S.stages.map(s => s.id)) + 1; document.getElementById("preset").value = S.preset || "rental"; }
  else loadPreset("rental");
  document.getElementById("amb").value = S.amb;
  document.getElementById("rec").value = S.rec || 0;
  setMode(S.mode);
})();

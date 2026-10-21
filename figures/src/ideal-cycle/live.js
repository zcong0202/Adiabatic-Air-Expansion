const D = __DATA__;
const P = D.P;
const stage = document.querySelector(".iso-stage");
const svg = stage.querySelector("svg");
const readout = document.querySelector("[data-readout]");
const needleEl = svg.querySelector('[data-part="needle"]');
const gaugeEl = svg.querySelector('[data-part="gauge"]');
const coldEl = svg.querySelector('[data-part="cold"]');
const spinEls = D.couplings.map((_, i) => svg.querySelector(`[data-part="spin${i}"]`));
const still = matchMedia("(prefers-reduced-motion: reduce)");
const NS = "http://www.w3.org/2000/svg";

// ---- model: ideal-gas air, 78 g/s, 30 °C ambient, 10 K heat-exchanger approach ----
const CP = 1005, R = 287, K = 0.2857, M = 0.078, TA = 303.15, APPROACH = 10, PA = 1.013;
const PR_MIN = 1.5, PR_MAX = 9.5;
let mode = "ideal";
function model(pr, which = mode) {
  const T1 = TA + APPROACH; // turbine inlet after the aftercooler
  if (which === "ideal") {
    const wc = R * TA * Math.log(pr);
    const T2 = T1 * Math.pow(pr, -K);
    const wt = CP * (T1 - T2);
    const out = T2;
    const cooling = M * CP * (TA - out);
    const net = M * (wc - wt);
    const stages = [1, 2, 3].map((i) => Math.pow(pr, i / 3));
    const heat = M * wc; // isothermal: all compression work leaves as heat
    return { pr, wc: M * wc, wt: M * wt, net, out, tTurb: T2, cooling, cop: cooling / net, stages, heat, T1 };
  }
  const r = Math.pow(pr, 1 / 3), eta = 0.8, etaT = 0.8, mech = 0.95, duct = 0.12;
  let wc = 0;
  for (let i = 0; i < 3; i++) { const Tin = i === 0 ? TA : TA + APPROACH; wc += CP * Tin * (Math.pow(r, K) - 1) / eta; }
  const T2 = T1 - etaT * T1 * (1 - Math.pow(pr, -K));
  const wt = CP * (T1 - T2) * mech;
  const out = T2 + (TA - T2) * duct;
  const cooling = M * CP * (TA - out);
  const net = M * (wc - wt);
  const stages = [1, 2, 3].map((i) => Math.pow(pr, i / 3));
  const heat = M * (wc - CP * APPROACH * 2);
  return { pr, wc: M * wc, wt: M * wt, net, out, tTurb: T2, cooling, cop: cooling / net, stages, heat, T1 };
}

// ---- chips ----
const wrap = stage.parentElement;
const chipsEl = wrap.querySelector(".ac-chips");
const compareEl = document.querySelector("[data-compare]");
const chartEl = document.querySelector("[data-chart]");
const chips = {};
const lead = document.createElementNS(NS, "svg");
lead.setAttribute("viewBox", `0 0 ${D.W} ${D.H}`);
lead.setAttribute("class", "ac-leads");
chipsEl.appendChild(lead);
for (const c of D.calls) {
  const line = document.createElementNS(NS, "path");
  line.setAttribute("d", `M${c.sx} ${c.sy}L${c.sx} ${(c.sy + c.cy) / 2}L${c.cx} ${(c.sy + c.cy) / 2}L${c.cx} ${c.cy}`);
  line.setAttribute("class", "ac-lead");
  const dot = document.createElementNS(NS, "circle");
  dot.setAttribute("cx", c.sx); dot.setAttribute("cy", c.sy); dot.setAttribute("r", "1.6"); dot.setAttribute("class", "ac-dot");
  lead.append(line, dot);
  const el = document.createElement("div");
  el.className = "ac-chip " + c.rail;
  el.style.left = (c.cx / D.W * 100).toFixed(2) + "%";
  el.style.top = (c.cy / D.H * 100).toFixed(2) + "%";
  chipsEl.appendChild(el);
  chips[c.key] = el;
}
const C = (t) => t - 273.15;
const temp = (t) => { const c = C(t); return (c < 0 ? "−" : "") + Math.abs(c).toFixed(0) + " °C"; };
const kw = (w) => (w / 1000).toFixed(1) + " kW";
const bar = (pr) => (pr * PA).toFixed(1);
function writeValues(m) {
  const set = (key, label, text) => { const html = `<b>${label}</b>${text}`; if (chips[key]._h !== html) { chips[key].innerHTML = html; chips[key]._h = html; } };
  set("motor", "1", `motor ${kw(m.net)} net`);
  set("stages", "2", `${m.stages.map(bar).join(" → ")} bar`);
  set("coolers", "3", `${kw(m.heat)} heat out · ${mode === "ideal" ? "isothermal" : "3 stages η 80%"}`);
  set("turb", "4", `turbine +${kw(m.wt)} to shaft`);
  set("duct", "5", `${temp(m.tTurb)} leaving turbine`);
  set("outlet", "6", `${temp(m.out)} · 78 g/s`);
  set("seat", "7", `${kw(m.cooling)} · COP ${m.cop.toFixed(2)}`);
  const o = model(m.pr, mode === "ideal" ? "real" : "ideal");
  const I = mode === "ideal" ? m : o, Rm = mode === "ideal" ? o : m;
  const cell = (title, a, b, c) => `<div>${title}<b>${a}</b>realistic: ${b}${c ? " · " + c : ""}</div>`;
  const html =
    cell("Motor power (net)", kw(I.net), kw(Rm.net)) +
    cell("Air at the seat", temp(I.out), temp(Rm.out)) +
    cell("Cooling", kw(I.cooling), kw(Rm.cooling)) +
    cell("Cooling ÷ electricity", `COP ${I.cop.toFixed(2)}`, `COP ${Rm.cop.toFixed(2)}`, "split AC 3–4");
  if (compareEl._h !== html) { compareEl.innerHTML = html; compareEl._h = html; }
}
document.querySelectorAll("[data-mode]").forEach((btn) => btn.addEventListener("click", () => {
  mode = btn.dataset.mode;
  document.querySelectorAll("[data-mode]").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
  draw(0);
}));
const valuesBox = document.querySelector("[data-values]");
valuesBox.addEventListener("change", () => wrap.classList.toggle("off", !valuesBox.checked));

// ---- COP chart ----
const CW = 720, CHh = 164, L = 44, Rr = 14, T = 14, B = 34;
const xOf = (pr) => L + (pr - PR_MIN) / (PR_MAX - PR_MIN) * (CW - L - Rr);
const LOG0 = Math.log10(0.1), LOG1 = Math.log10(30);
const yOf = (c) => T + (1 - (Math.log10(Math.max(0.1, Math.min(30, c))) - LOG0) / (LOG1 - LOG0)) * (CHh - T - B);
const curve = (which) => { let d = ""; for (let i = 0; i <= 80; i++) { const pr = PR_MIN + (PR_MAX - PR_MIN) * i / 80; const c = model(pr, which).cop; d += (i ? "L" : "M") + xOf(pr).toFixed(1) + " " + yOf(c).toFixed(1); } return d; };
let chartHtml = `<svg viewBox="0 0 ${CW} ${CHh}" role="img" aria-label="COP against pressure ratio, ideal and realistic machines, log scale, with the split air-conditioner band at COP 3 to 4">`;
chartHtml += `<rect class="band" x="${L}" y="${yOf(4)}" width="${CW - L - Rr}" height="${yOf(3) - yOf(4)}"/><text x="${CW - Rr - 4}" y="${yOf(3) + 12}" text-anchor="end">split air conditioner · COP 3–4</text>`;
for (const c of [0.1, 0.3, 1, 3, 10, 30]) chartHtml += `<line class="grid" x1="${L}" x2="${CW - Rr}" y1="${yOf(c)}" y2="${yOf(c)}"/><text x="${L - 6}" y="${yOf(c) + 3}" text-anchor="end">${c}</text>`;
for (let pr = 2; pr <= 9; pr++) chartHtml += `<text x="${xOf(pr)}" y="${CHh - B + 13}" text-anchor="middle">${pr}</text>`;
chartHtml += `<text x="${(L + CW - Rr) / 2}" y="${CHh - 2}" text-anchor="middle" class="lab">pressure ratio (compressor out ÷ ambient) →</text><text x="${L}" y="${T - 2}" class="lab">COP (log)</text>`;
chartHtml += `<line class="ax" x1="${L}" x2="${L}" y1="${T}" y2="${CHh - B}"/><line class="ax" x1="${L}" x2="${CW - Rr}" y1="${CHh - B}" y2="${CHh - B}"/>`;
chartHtml += `<path class="ideal" d="${curve("ideal")}"/><path class="real" d="${curve("real")}"/>`;
chartHtml += `<text x="${xOf(2.1)}" y="${yOf(model(2.1, "ideal").cop) - 6}" class="lab">ideal</text><text x="${xOf(7.5)}" y="${yOf(model(7.5, "real").cop) + 14}" class="lab">realistic</text>`;
chartHtml += `<line class="curline" data-cl y1="${T}" y2="${CHh - B}"/><circle class="cur" data-cd r="3.5"/></svg>`;
chartEl.innerHTML = chartHtml;
const curLine = chartEl.querySelector("[data-cl]"), curDot = chartEl.querySelector("[data-cd]");

// ---- drawing helpers ----
const T_MIN = -100, T_MAX = 40, FROM = -0.75 * Math.PI, SPAN = 1.5 * Math.PI;
function needlePath(t) {
  const [cx, cy, top] = D.therm;
  const a = FROM + SPAN * (Math.min(T_MAX, Math.max(T_MIN, C(t))) - T_MIN) / (T_MAX - T_MIN);
  return lineOnTop([cx - Math.sin(a) * 1.8, cy + Math.cos(a) * 1.8], [cx + Math.sin(a) * 6.6, cy - Math.cos(a) * 6.6], top + 0.2, P);
}
function gaugePath(pr) {
  const [cx, cy, top] = D.gauge;
  const a = FROM + SPAN * (pr - 1) / (10 - 1);
  return lineOnTop([cx, cy], [cx + Math.sin(a) * 4, cy - Math.cos(a) * 4], top + 0.2, P);
}
function spinPath(c, ph) {
  const F = G.frameOf(c.o, [1, 0, 0], [0, 1, 0], [0, 0, 1]);
  return G.ribsOf(F, c.s0, c.s1, c.r, 6, P, { phase: ph, fade: [0.05, 0.5] }).map(({ d, alpha }) => `<path class="iso-line" data-tone="lo" d="${d}" opacity="${alpha.toFixed(2)}"/>`).join("");
}
const COLS = [];
for (const x of [146.5, 151.5, 156.5, 161.5]) for (const y of [-12, -6, 0, 6, 12]) COLS.push([x, y]);
const drops = [];
COLS.forEach(([x, y], c) => { for (let j = 0; j < 3; j++) { const el = document.createElementNS(NS, "path"); el.setAttribute("class", "ac-drop"); coldEl.appendChild(el); drops.push({ el, x, y, t: (j / 3 + (c * 0.37) % 1) % 1 }); } });
const style = document.createElement("style");
style.textContent = `.ac-drop{fill:none;stroke:var(--anatomy-hi);stroke-width:.6;stroke-linecap:round}`;
document.head.appendChild(style);

// ---- state ----
let pr = 7.3, target = 7.3, phase = 0, frame = 0, last = 0, clock = 0, touring = true, visible = false, idleTimer = 0;
const TOUR = [7.3, 7.3, 9.5, 5, 3, 2, 3, 5];
const tourAt = (t) => TOUR[Math.floor(t / 2.6) % TOUR.length];
function draw(dt) {
  const m = model(pr);
  needleEl.setAttribute("d", needlePath(m.out));
  gaugeEl.setAttribute("d", gaugePath(pr));
  phase += dt * 3;
  spinEls.forEach((el, i) => { el.innerHTML = spinPath(D.couplings[i], phase + i * 0.7); });
  const strength = Math.max(0, Math.min(1, (TA - m.out) / 60));
  const fall = D.diff.top - D.diff.floor;
  drops.forEach((d) => {
    d.t = (d.t + dt * (0.35 + 0.3 * strength)) % 1;
    const z = D.diff.top - 6 - d.t * (fall - 13);
    const [sx, sy] = iso([d.x, d.y, z], P), [ex, ey] = iso([d.x, d.y, z - 5], P);
    d.el.setAttribute("d", `M${sx.toFixed(1)} ${sy.toFixed(1)}L${ex.toFixed(1)} ${ey.toFixed(1)}`);
    d.el.setAttribute("opacity", ((0.25 + 0.75 * strength) * Math.min(1, d.t / 0.25) * Math.min(1, (1 - d.t) / 0.12) * 0.8).toFixed(2));
  });
  writeValues(m);
  curLine.setAttribute("x1", xOf(pr)); curLine.setAttribute("x2", xOf(pr));
  curDot.setAttribute("cx", xOf(pr)); curDot.setAttribute("cy", yOf(m.cop));
  const text = `${mode === "ideal" ? "ideal" : "realistic"} · ratio ${pr.toFixed(1)} · outlet ${temp(m.out)} · ${kw(m.cooling)} · COP ${m.cop.toFixed(2)}`;
  if (readout.textContent !== text) readout.textContent = text;
  stage.setAttribute("aria-valuenow", pr.toFixed(1));
  stage.setAttribute("aria-valuetext", text);
}
function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60;
  last = now;
  const calm = still.matches;
  if (touring) { clock += dt; target = tourAt(clock); }
  pr = calm ? target : pr + (target - pr) * (1 - Math.exp(-dt / 0.6));
  if (Math.abs(target - pr) < 0.005) pr = target;
  draw(calm ? 0 : dt);
  frame = visible && !calm ? requestAnimationFrame(tick) : 0;
}
const run = () => { if (!frame && visible) { last = 0; frame = requestAnimationFrame(tick); } };
const steer = (next) => {
  touring = false;
  target = Math.min(PR_MAX, Math.max(PR_MIN, next));
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => { touring = !still.matches; clock = 0; run(); }, 5000);
  if (still.matches) { pr = target; draw(0); }
  run();
};
new IntersectionObserver((entries) => { visible = entries[entries.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);
if (still.matches) touring = false;
stage.addEventListener("pointermove", (event) => {
  const box = svg.getBoundingClientRect();
  const u = ((event.clientX - box.left) / box.width - 0.1) / 0.8;
  steer(PR_MIN + Math.min(1, Math.max(0, u)) * (PR_MAX - PR_MIN));
});
chartEl.addEventListener("pointermove", (event) => {
  const box = chartEl.querySelector("svg").getBoundingClientRect();
  const x = (event.clientX - box.left) / box.width * CW;
  steer(PR_MIN + (x - L) / (CW - L - Rr) * (PR_MAX - PR_MIN));
});
stage.addEventListener("keydown", (event) => {
  let to = null;
  if (event.key === "ArrowRight" || event.key === "ArrowUp") to = target + 0.5;
  if (event.key === "ArrowLeft" || event.key === "ArrowDown") to = target - 0.5;
  if (event.key === "Home") to = PR_MIN;
  if (event.key === "End") to = PR_MAX;
  if (to === null) return;
  event.preventDefault();
  steer(Math.round(to * 2) / 2);
});
draw(0);

const D = __DATA__;
const P = D.P;
const stage = document.querySelector(".iso-stage");
const svg = stage.querySelector("svg");
const readout = document.querySelector("[data-readout]");
const needleEl = svg.querySelector('[data-part="needle"]');
const knobEl = svg.querySelector('[data-part="knob"]');
const coldEl = svg.querySelector('[data-part="cold"]');
const spinEls = D.couplings.map((_, i) => svg.querySelector(`[data-part="spin${i}"]`));
const still = matchMedia("(prefers-reduced-motion: reduce)");
const NS = "http://www.w3.org/2000/svg";

// ---- model (same numbers as the Air-Cycle Bench calculator) ----
const CP = 1005, M = 0.078, AMB = 30, DUCT = 0.12, W_FULL = 4 * 843, PA = 1.013;
const jt = (p1, p2) => { if (p2 >= p1) return 0; let d = 0; const n = 40, h = (p1 - p2) / n; for (let i = 0; i < n; i++) { const p = p2 + (i + 0.5) * h; d += Math.max(0.02, 0.22 - 0.0006 * p) * h; } return d; };
const SUPPLY = {
  low: { pg: 7.6, tDis: 85, recv: 7.3, e: 300, name: "7.6 bar" },
  high: { pg: 200, tDis: 95, recv: 199.7, e: 1100, name: "200 bar" },
};
let mode = "low";
function model(load) {
  const s = SUPPLY[mode];
  const tCool = AMB + 10;
  const tReg = tCool - jt(s.recv + PA, 6.3 + PA);
  const work = W_FULL * load;
  const motorOut = tReg - jt(6.3 + PA, PA) * (1 - load) - work / (M * CP);
  const out = motorOut + (AMB - motorOut) * DUCT;
  const cooling = M * CP * (AMB - out);
  const rpm = 2400 - 1130 * load;
  const elec = M * s.e; // kW
  return { s, tCool, tReg, work, motorOut, out, cooling, rpm, elec, cop: cooling / 1000 / elec };
}

// ---- value chips on the drawing ----
const wrap = stage.parentElement;
const chipsEl = wrap.querySelector(".ac-chips");
const compareEl = document.querySelector("[data-compare]");
const chips = {};
const lead = document.createElementNS(NS, "svg");
lead.setAttribute("viewBox", `0 0 ${D.W} ${D.H}`);
lead.setAttribute("class", "ac-leads");
chipsEl.appendChild(lead);
for (const c of D.calls) {
  const y2 = c.rail === "top" ? c.cy : c.cy;
  const line = document.createElementNS(NS, "path");
  line.setAttribute("d", `M${c.sx} ${c.sy}L${c.sx} ${(c.sy + y2) / 2}L${c.cx} ${(c.sy + y2) / 2}L${c.cx} ${y2}`);
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
const f1 = (v) => v.toFixed(1), f0 = (v) => Math.round(v).toString();
const temp = (t) => (t < 0 ? "−" : "") + Math.abs(t).toFixed(1) + " °C";
function writeValues(m) {
  const set = (key, label, text) => { const html = `<b>${label}</b>${text}`; if (chips[key]._h !== html) { chips[key].innerHTML = html; chips[key]._h = html; } };
  set("comp", "1", `${m.s.name} · ${m.s.tDis} °C · ${f0(m.elec)} kW`);
  set("cooler", "2", `→ ${f0(m.tCool)} °C`);
  set("tank", "3", `${f1(m.s.recv)} bar · ${f0(m.tCool)} °C`);
  set("reg", "4", `→ 6.3 bar · ${temp(m.tReg)}`);
  set("motors", "5", `4 × LZB46 · ${f1(m.work / 1000)} kW · ${f0(m.rpm)} rpm`);
  set("load", "6", `load ${f0(load * 100)} %`);
  set("outlet", "7", `${temp(m.out)} · 78 g/s · 60 L/s`);
  set("seat", "8", `${m.cooling >= 0 ? "" : "−"}${Math.abs(m.cooling / 1000).toFixed(2)} kW · COP ${m.cop.toFixed(2)}`);
  chips.reg.classList.toggle("hot", mode === "high");
  chips.comp.classList.toggle("hot", mode === "high");
  const other = mode === "low" ? "high" : "low";
  const saved = mode; mode = other; const o = model(load); mode = saved;
  const cell = (title, a, b) => `<div>${title}<b>${a}</b>other supply: ${b}</div>`;
  const html =
    cell("Electricity", `${f0(m.elec)} kW`, `${f0(o.elec)} kW`) +
    cell("Lost in the regulator", `${f0(m.s.recv - 6.3)} bar`, `${f0(o.s.recv - 6.3)} bar`) +
    cell("Air at the seat", temp(m.out), temp(o.out)) +
    cell("Cooling ÷ electricity", `COP ${m.cop.toFixed(2)}`, `COP ${o.cop.toFixed(2)}`);
  if (compareEl._h !== html) { compareEl.innerHTML = html; compareEl._h = html; }
}
document.querySelectorAll("[data-mode]").forEach((btn) => btn.addEventListener("click", () => {
  mode = btn.dataset.mode;
  document.querySelectorAll("[data-mode]").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
  draw(0);
}));
const valuesBox = document.querySelector("[data-values]");
valuesBox.addEventListener("change", () => wrap.classList.toggle("off", !valuesBox.checked));

// ---- drawing helpers ----
const T_MIN = -30, T_MAX = 40, FROM = -0.75 * Math.PI, SPAN = 1.5 * Math.PI;
function needlePath(t) {
  const [cx, cy, top] = D.therm;
  const a = FROM + SPAN * (Math.min(T_MAX, Math.max(T_MIN, t)) - T_MIN) / (T_MAX - T_MIN);
  return lineOnTop([cx - Math.sin(a) * 1.8, cy + Math.cos(a) * 1.8], [cx + Math.sin(a) * 6.6, cy - Math.cos(a) * 6.6], top + 0.2, P);
}
function knobPath(load) {
  const [cx, cy] = D.knob;
  const a = FROM + SPAN * load;
  return lineOnTop([cx, cy], [cx + Math.sin(a) * 4.6, cy - Math.cos(a) * 4.6], 27, P);
}
function spinPath(c, phase) {
  const F = G.frameOf(c.o, [1, 0, 0], [0, 1, 0], [0, 0, 1]);
  const ribs = G.ribsOf(F, c.s0, c.s1, c.r, 6, P, { phase, fade: [0.05, 0.5] });
  return ribs.map(({ d, alpha }) => `<path class="iso-line" data-tone="lo" d="${d}" opacity="${alpha.toFixed(2)}"/>`).join("");
}

// cold air: an even curtain of short streaks falling from the diffuser onto the seat
const COLS = [];
for (const x of [146.5, 151.5, 156.5, 161.5]) for (const y of [-12, -6, 0, 6, 12]) COLS.push([x, y]);
const drops = [];
COLS.forEach(([x, y], c) => {
  for (let j = 0; j < 3; j++) {
    const el = document.createElementNS(NS, "path");
    el.setAttribute("class", "ac-drop");
    coldEl.appendChild(el);
    drops.push({ el, x, y, t: (j / 3 + (c * 0.37) % 1) % 1 });
  }
});
const style = document.createElement("style");
style.textContent = `.ac-drop{fill:none;stroke:var(--anatomy-hi);stroke-width:.6;stroke-linecap:round}`;
document.head.appendChild(style);

// ---- state ----
let load = 1, target = 1, phase = 0, frame = 0, last = 0, clock = 0, touring = true, visible = false, idleTimer = 0;
const TOUR = [1, 1, 0.55, 0, 0, 0.55];
const tourAt = (t) => TOUR[Math.floor(t / 2.6) % TOUR.length];

function draw(dt) {
  const m = model(load);
  needleEl.setAttribute("d", needlePath(m.out));
  knobEl.setAttribute("d", knobPath(load));
  phase += (m.rpm / 60) * 2 * Math.PI * dt * 0.02;
  spinEls.forEach((el, i) => { el.innerHTML = spinPath(D.couplings[i], phase + i * 0.7); });
  const strength = Math.max(0, Math.min(1, (AMB - m.out) / 30));
  const fall = D.diff.top - D.diff.floor;
  drops.forEach((d) => {
    d.t = (d.t + dt * (0.35 + 0.25 * strength)) % 1;
    const z = D.diff.top - 6 - d.t * (fall - 13);
    const [sx, sy] = iso([d.x, d.y, z], P);
    const [ex, ey] = iso([d.x, d.y, z - 5], P);
    d.el.setAttribute("d", `M${sx.toFixed(1)} ${sy.toFixed(1)}L${ex.toFixed(1)} ${ey.toFixed(1)}`);
    const fade = Math.min(1, d.t / 0.25) * Math.min(1, (1 - d.t) / 0.12);
    d.el.setAttribute("opacity", (strength * fade * 0.8).toFixed(2));
  });
  const sign = m.cooling >= 0 ? "" : "−";
  writeValues(m);
  const text = `${m.s.name} · load ${Math.round(load * 100)} % · outlet ${temp(m.out)} · ${sign}${Math.abs(m.cooling / 1000).toFixed(2)} kW`;
  if (readout.textContent !== text) readout.textContent = text;
  stage.setAttribute("aria-valuenow", String(Math.round(load * 100)));
  stage.setAttribute("aria-valuetext", text);
}
function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60;
  last = now;
  const calm = still.matches;
  if (touring) { clock += dt; target = tourAt(clock); }
  load = calm ? target : load + (target - load) * (1 - Math.exp(-dt / 0.6));
  if (Math.abs(target - load) < 0.001) load = target;
  draw(calm ? 0 : dt);
  frame = visible && !calm ? requestAnimationFrame(tick) : 0;
}
const run = () => { if (!frame && visible) { last = 0; frame = requestAnimationFrame(tick); } };
const steer = (next) => {
  touring = false;
  target = Math.min(1, Math.max(0, next));
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => { touring = !still.matches; clock = 0; run(); }, 4000);
  if (still.matches) { load = target; draw(0); }
  run();
};
new IntersectionObserver((entries) => { visible = entries[entries.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);
if (still.matches) touring = false;
stage.addEventListener("pointermove", (event) => {
  const box = svg.getBoundingClientRect();
  steer(((event.clientX - box.left) / box.width - 0.15) / 0.7);
});
stage.addEventListener("keydown", (event) => {
  let to = null;
  if (event.key === "ArrowRight" || event.key === "ArrowUp") to = target + 0.1;
  if (event.key === "ArrowLeft" || event.key === "ArrowDown") to = target - 0.1;
  if (event.key === "Home") to = 0;
  if (event.key === "End") to = 1;
  if (to === null) return;
  event.preventDefault();
  steer(Math.round(to * 10) / 10);
});
draw(0);

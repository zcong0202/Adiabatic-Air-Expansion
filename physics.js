// ---------- physics ----------
const CP = 1005, G = 1.4, GE = (G - 1) / G, R = 287.05, PA = 1.01325, RHO_STD = 1.204; // FAD at 20 °C, 1.013 bar
const K = c => c + 273.15;
function jtDrop(p1, p2) { // K of cooling for isenthalpic p1 -> p2 (bar abs)
  if (p2 >= p1) return 0;
  const mu = p => Math.max(0.02, 0.22 - 0.0006 * p);
  let d = 0, n = 60, h = (p1 - p2) / n;
  for (let i = 0; i < n; i++) d += mu(p2 + (i + 0.5) * h) * h;
  return d;
}

const STAGES = {
  aftercooler: { name: "Aftercooler", params: { approach: ["Outlet above ambient", "K", 10, 1], dp: ["Pressure drop", "bar", 0.1, 0.05] } },
  dryer: { name: "Dryer + filters", params: { dp: ["Pressure drop", "bar", 0.3, 0.05] } },
  receiver: { name: "Receiver tank", params: { vol: ["Volume", "L", 500, 10], pmin: ["Lowest usable", "bar(g)", 4, 0.5] } },
  regulator: { name: "Regulator", params: { set: ["Set pressure", "bar(g)", 6.3, 0.1] } },
  hose: { name: "Hose / duct", params: { loss: ["Moves toward ambient", "%", 12, 1], dp: ["Pressure drop", "bar", 0.05, 0.05] } },
  turbine: { name: "Turbine expander", exp: true, params: { eta: ["Isentropic efficiency", "%", 75, 1], pout: ["Outlet pressure", "bar(g)", 0, 0.1], design: ["Design flow (0 = all)", "g/s", 0, 1], loaded: ["Shaft loaded (1/0)", "", 1, 1] } },
  vane: { name: "Vane air motor", exp: true, params: { count: ["Number of motors", "", 4, 1], power: ["Rated shaft power", "W", 843, 10], cons: ["Rated air use", "L/s FAD", 16.2, 0.1], prated: ["Rated at", "bar(g)", 6.3, 0.1], loaded: ["Shaft loaded (1/0)", "", 1, 1] } },
  vortex: { name: "Vortex tube", exp: true, params: { cold: ["Cold fraction", "%", 80, 5], dtref: ["Cold ΔT at 6.9 bar(g), 80 %", "K", 20, 1], rated: ["Rated air use", "L/min", 200, 10] } },
};
const VANE_PRESETS = { LZB46: { power: 843, cons: 16.2 }, LZB33: { power: 250, cons: 7.9 } };

const SOURCES = {
  compressor: { name: "Compressor", params: { fad: ["Free air delivery", "L/min", 4000, 10], pg: ["Discharge pressure", "bar(g)", 7.6, 0.1], tdis: ["Discharge temperature", "°C", 85, 1], power: ["Power input", "kW", 24, 0.1] } },
  tank: { name: "Storage tank", params: { vol: ["Volume", "L", 12, 1], pg: ["Fill pressure", "bar(g)", 200, 5], t: ["Gas temperature", "°C", 30, 1], pmin: ["Lowest usable", "bar(g)", 10, 1], rate: ["Release rate", "g/s", 4, 0.5], fillE: ["Energy used to fill", "kJ/kg", 1100, 50] } },
};
const OUTLET = { name: "Outlet", params: { kind: ["Type: 1 nozzles · 2 diffuser", "", 2, 1], n: ["Nozzle count", "", 4, 1], d: ["Nozzle diameter", "mm", 70, 1], area: ["Diffuser face area", "m²", 0.5, 0.05], open: ["Diffuser open area", "%", 20, 1], zone: ["Seat zone cross-section", "m²", 1, 0.1] } };

const PRESETS = {
  rental: { mode: "cont", source: { type: "compressor", p: { fad: 4000, pg: 7.6, tdis: 85, power: 24 } },
    stages: [["aftercooler", { approach: 10, dp: 0.1 }], ["dryer", { dp: 0.2 }], ["receiver", { vol: 500, pmin: 4 }], ["regulator", { set: 6.3 }], ["vane", { count: 4, power: 843, cons: 16.2, prated: 6.3, loaded: 1 }], ["hose", { loss: 12, dp: 0 }]],
    outlet: { kind: 2, n: 4, d: 70, area: 0.5, open: 20, zone: 1 } },
  workshopVortex: { mode: "cont", source: { type: "compressor", p: { fad: 260, pg: 8, tdis: 90, power: 2.2 } },
    stages: [["aftercooler", { approach: 8, dp: 0.2 }], ["regulator", { set: 6.9 }], ["vortex", { cold: 80, dtref: 20, rated: 200 }], ["hose", { loss: 10, dp: 0 }]],
    outlet: { kind: 1, n: 1, d: 30, area: 0.5, open: 20, zone: 1 } },
  workshopBurst: { mode: "burst", source: { type: "compressor", p: { fad: 260, pg: 8, tdis: 90, power: 2.2 } },
    stages: [["aftercooler", { approach: 10, dp: 0.1 }], ["receiver", { vol: 300, pmin: 4 }], ["regulator", { set: 6.3 }], ["vane", { count: 1, power: 843, cons: 16.2, prated: 6.3, loaded: 1 }], ["hose", { loss: 12, dp: 0 }]],
    outlet: { kind: 1, n: 2, d: 50, area: 0.5, open: 20, zone: 1 } },
  scuba: { mode: "burst", source: { type: "tank", p: { vol: 12, pg: 200, t: 30, pmin: 10, rate: 4 } },
    stages: [["regulator", { set: 8.5 }], ["hose", { loss: 40, dp: 0 }], ["regulator", { set: 5.9 }], ["vortex", { cold: 80, dtref: 20, rated: 200 }]],
    outlet: { kind: 1, n: 1, d: 30, area: 0.5, open: 20, zone: 1 } },
  junior: { mode: "cont", source: { type: "compressor", p: { fad: 100, pg: 200, tdis: 40, power: 2.2 } },
    stages: [["dryer", { dp: 0 }], ["regulator", { set: 9 }], ["turbine", { eta: 75, pout: 0, design: 0, loaded: 1 }], ["hose", { loss: 10, dp: 0 }]],
    outlet: { kind: 1, n: 1, d: 25, area: 0.5, open: 20, zone: 1 } },
};

let uid = 1;
function defaults(def) { const o = {}; for (const k in def.params) o[k] = def.params[k][2]; return o; }
function mkStage(type, p) { return { id: uid++, type, p: Object.assign(defaults(STAGES[type]), p || {}) }; }
let S;
function loadPreset(key) {
  const pr = PRESETS[key];
  S = { preset: key, amb: S ? S.amb : 30, rec: S ? (S.rec || 0) : 0, mode: pr.mode,
    source: { type: pr.source.type, p: Object.assign(defaults(SOURCES[pr.source.type]), pr.source.p) },
    stages: pr.stages.map(([t, p]) => mkStage(t, p)),
    outlet: Object.assign(defaults(OUTLET), pr.outlet) };
}

function compute(S) {
  const Ta = S.amb, warns = [], nodes = [];
  const src = S.source, sp = src.p;
  let P, T, mSupply, power = null, storage = null, dry = false;
  if (src.type === "compressor") {
    P = sp.pg + PA; T = sp.tdis; mSupply = sp.fad / 60000 * RHO_STD; power = sp.power;
  } else {
    P = sp.pg + PA; T = sp.t; mSupply = sp.rate / 1000;
    const usable = (sp.pg - sp.pmin) * 1e5 * (sp.vol / 1000) / (R * K(sp.t));
    storage = { kind: "tank", usable: Math.max(0, usable) };
  }
  // flow demand from the first expander
  let demand = null, firstExp = S.stages.find(s => STAGES[s.type].exp);
  if (firstExp) {
    const q = firstExp.p;
    if (firstExp.type === "vane") demand = q.count * q.cons / 1000 * RHO_STD;
    if (firstExp.type === "vortex") demand = q.rated / 60000 * RHO_STD;
    if (firstExp.type === "turbine" && q.design > 0) demand = q.design / 1000;
  }
  const recv = S.stages.find(s => s.type === "receiver");
  let m;
  const burst = S.mode === "burst";
  if (src.type === "tank") { m = demand != null ? demand : mSupply; }
  else if (burst) {
    if (!recv) { warns.push("Burst mode needs a receiver tank in the path. Running continuous instead."); m = demand != null ? Math.min(mSupply, demand) : mSupply; }
    else m = demand != null ? demand : mSupply;
  } else {
    m = demand != null ? Math.min(mSupply, demand) : mSupply;
    if (demand != null && demand > mSupply * 1.02) warns.push(`Expander wants ${(demand * 1000).toFixed(1)} g/s but the compressor supplies ${(mSupply * 1000).toFixed(1)} g/s. Motors run at ${(100 * mSupply / demand).toFixed(0)} % load. Try burst mode with a receiver, or a bigger compressor.`);
  }
  nodes.push({ label: src.type === "compressor" ? "Compressor out" : "Tank", T, P, m });
  let work = 0, coldFrac = 1;
  for (const st of S.stages) {
    const q = st.p, info = {};
    switch (st.type) {
      case "aftercooler": { const t2 = Ta + q.approach; info.heat = T > t2 ? m * CP * (T - t2) : 0; T = Math.min(T, t2); P = Math.max(PA, P - q.dp); break; }
      case "dryer": P = Math.max(PA, P - q.dp); dry = true; break;
      case "hose": T = T + (Ta - T) * q.loss / 100; P = Math.max(PA, P - q.dp); break;
      case "receiver": {
        const pmaxg = P - PA;
        const usable = Math.max(0, (pmaxg - q.pmin) * 1e5 * (q.vol / 1000) / (R * K(T)));
        storage = storage || { kind: "receiver", usable, pmaxg };
        if (q.pmin > pmaxg) warns.push("Receiver lowest usable pressure is above its fill pressure.");
        break; }
      case "regulator": {
        const set = q.set + PA;
        if (set >= P) { info.pass = true; warns.push(`Regulator set to ${q.set} bar(g) but inlet is only ${(P - PA).toFixed(1)} bar(g); it passes air through unchanged.`); }
        else { const d = jtDrop(P, set); info.jt = d; T -= d; P = set; }
        break; }
      case "turbine": {
        const p2 = q.pout + PA;
        if (p2 >= P) { warns.push("Turbine outlet pressure is not below its inlet pressure."); break; }
        if (P > 31) warns.push(`Turbine inlet is ${(P - PA).toFixed(0)} bar(g). A single stage above ~30 bar is impractical; add a regulator or stage the expansion.`);
        if (q.loaded) { const dT = q.eta / 100 * K(T) * (1 - Math.pow(p2 / P, GE)); work += m * CP * dT; info.work = m * CP * dT; T -= dT; }
        else { const d = jtDrop(P, p2); T -= d; warns.push("Turbine shaft is unloaded, so it only throttles: almost no cooling."); }
        P = p2; break; }
      case "vane": {
        const pg = P - PA;
        const dem = q.count * q.cons / 1000 * RHO_STD;
        const load = dem > 0 ? Math.min(1, m / dem) : 0;
        const pScale = Math.max(0, Math.min(1.15, pg / q.prated));
        if (pg < q.prated * 0.8) warns.push(`Vane motors are rated at ${q.prated} bar(g) but see ${pg.toFixed(1)} bar(g); shaft power drops.`);
        if (q.loaded && m > 0) {
          const W = q.count * q.power * load * pScale;
          let dT = W / (m * CP);
          const dTs = K(T) * (1 - Math.pow(PA / P, GE));
          if (dT > dTs) dT = dTs;
          info.eta = dTs > 0 ? dT / dTs : 0; info.work = m * CP * dT; work += info.work; T -= dT;
        } else { T -= jtDrop(P, PA); warns.push("Vane motor shaft is unloaded, so it only throttles: almost no cooling."); }
        P = PA; break; }
      case "vortex": {
        const pg = P - PA;
        if (pg < 4 || pg > 8.5) warns.push(`Vortex tubes are usually run at 5.5–7 bar(g); inlet here is ${pg.toFixed(1)} bar(g).`);
        const mc = Math.min(0.95, Math.max(0.05, q.cold / 100));
        const dTc = q.dtref * Math.sqrt((1 - mc) / 0.2) * Math.log(P / PA) / Math.log((6.9 + PA) / PA);
        info.hot = mc / (1 - mc) * dTc; info.dTc = dTc;
        T -= dTc; P = PA; m *= mc; coldFrac *= mc; break; }
    }
    st._info = info;
    nodes.push({ label: STAGES[st.type].name, T, P, m });
  }
  // outlet
  const o = S.outlet, rho = (P * 1e5) / (R * K(T)), Q = m / rho; // m3/s
  let Aopen, D, face = null;
  if (o.kind === 1) { Aopen = o.n * Math.PI * Math.pow(o.d / 2000, 2); D = o.d / 1000; }
  else { Aopen = o.area * o.open / 100; D = Math.sqrt(o.area); face = Q / o.area; }
  const v = Aopen > 0 ? Q / Aopen : 0;
  const dT = Ta - T;
  const cool = m * CP * dT; // W
  const rhoA = (PA * 1e5) / (R * K(Ta));
  const Re = rho * v * D / 1.8e-5;
  const Ar = v > 0 ? 9.81 * (dT / K(Ta)) * D / (v * v) : 0;
  const ent = dT > 10 ? m * ((Ta - 10) - T) / 10 : 0; // kg/s ambient cooled by 10 K
  const breeze = cool / (rhoA * CP * 10 * o.zone);
  // storage timing
  let tOn = null, tOff = null;
  if (storage && (burst || src.type === "tank")) {
    const net = src.type === "tank" ? m : m - mSupply;
    if (net > 0) tOn = storage.usable / net;
    if (src.type === "compressor") tOff = storage.usable / mSupply;
  }
  if (T < 0 && !dry && src.type === "compressor") warns.push("Outlet is below 0 °C without a dryer: expect ice in the expander exhaust.");
  if (T < -100) warns.push("Outlet below −100 °C: check for CO₂ frost and material limits. Air liquefies near −190 °C at 1 bar.");
  if (dT <= 0) warns.push("Outlet air is not colder than ambient, so there is no cooling.");
  if (v > 8) warns.push(`Outlet speed ${v.toFixed(1)} m/s is high for a seat; add nozzles or use a diffuser.`);
  // COP: cooling divided by the compression energy that went into the air actually used
  const eSpec = src.type === "compressor" ? (sp.power * 1000) / mSupply : (sp.fillE ?? 1100) * 1000; // J per kg drawn from the source
  const mIn = coldFrac > 0 ? m / coldFrac : m;
  const pIn = mIn * eSpec; // W
  const rec = S.rec || 0;
  const wRec = work * rec / 100;
  const cop = pIn > 0 ? cool / pIn : null;
  const copNet = rec > 0 && pIn - wRec > 0 ? cool / (pIn - wRec) : null;
  const TaK = K(Ta), ToK = K(T);
  const carnot = dT > 0.5 ? (TaK - ToK) / (TaK * Math.log(TaK / ToK) - (TaK - ToK)) : null;
  return { nodes, m, T, P, dT, cool, Q, v, face, Re, Ar, ent, breeze, work, power, eSpec, pIn, wRec, cop, copNet, carnot, tOn, tOff, warns, coldFrac, storage, mSupply, demand };
}

// Lets Node load this file for tests (ignored in the browser).
if (typeof module !== "undefined") module.exports = { CP, R, PA, RHO_STD, jtDrop, STAGES, SOURCES, OUTLET, PRESETS, defaults, mkStage, compute, loadPreset, getState: () => S };

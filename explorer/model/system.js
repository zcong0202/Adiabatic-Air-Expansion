// ---------- whole system ----------
// Puts compression, expansion, recovery, dryer, auxiliaries and delivery together
// for one state. All powers in W, temperatures in K unless named *C.
(() => {
const node = typeof module !== "undefined";
const P = node ? require("../params.js") : window.EXPLORER_PARAMS;
const AIR = node ? require("./air.js") : window.EXPLORER_AIR;
const { compress, massFactor } = node ? require("./compress.js") : window.EXPLORER_COMPRESS;
const { expand, T_LIQUID } = node ? require("./expand.js") : window.EXPLORER_EXPAND;
const { gridPower } = node ? require("./recover.js") : window.EXPLORER_RECOVER;
const { heatRecovery } = node ? require("./heat.js") : window.EXPLORER_HEAT;

const FRIDGE_DEW = 276.15;  // K, refrigerated dryer pressure dew point (3 °C)
const FRIDGE_POWER = 0.025; // refrigerated dryer electricity as a share of compressor electricity
const T_CHILLED = 280.15;   // K, absorption chilled water

// Smallest electricity that could deliver this cooling: exergy of each cold stream
// warming from its outlet to where it hands its cooling over, plus the chilled water.
function minWork(s, exp, absCool) {
  const CP = P.CONST.CP, Ta = AIR.C2K(s.Ta), Trh = Ta - (s.dTrh || 0);
  let w = 0;
  exp.stages.forEach((st, j) => {
    if (st.q <= 0) return;
    const hi = j === exp.stages.length - 1 ? Ta : Trh;
    w += CP * (Ta * Math.log(hi / st.Tout) - (hi - st.Tout));
  });
  return w + absCool * (Ta - T_CHILLED) / T_CHILLED;
}

// "auto" stage counts (compression and expansion): the fewest stages under the typical
// per-stage limits (rcMax, rtMax), as industry sizes machines, not the count with the best
// COP. A compression count below the feasible minimum is raised to it.
function system(state) {
  const st = { Pa: 1.01325, ...state };
  const comp = st.nComp === Infinity ? null : P.nCompRange(st);
  const exp = P.nExpRange({ ...P.defaults(st.mode || "real"), ...st });
  const ns = !comp ? [Infinity] : st.nComp === "auto" ? [comp.pick] : [Math.max(st.nComp, comp.min)];
  const ne = st.nExp !== "auto" ? [st.nExp] : [exp.pick];
  let best = null;
  for (const nComp of ns) for (const nExp of ne) {
    const r = evaluate({ ...state, nComp, nExp });
    if (!best || r.cop > best.cop) best = r;
  }
  if (comp) {
    best.nCompRange = comp;
    if (st.nComp === "auto") best.nCompAuto = true;
    else if (st.nComp < comp.min) best.nCompRaised = true;
  }
  if (st.nExp === "auto") { best.nExpAuto = true; best.nExpRange = exp; }
  return best;
}


function evaluate(state) {
  const s = P.auto(P.clamp(state));
  const CP = P.CONST.CP, Ta = AIR.C2K(s.Ta), m = s.m / 1000;
  const warn = [];

  const comp = compress(s);
  const exp = expand(s, comp.T1);

  // dryer: none (ideal, dry air) / refrigerated / desiccant
  let dryer = s.dryer;
  if (dryer === "auto") dryer = exp.Tmin >= FRIDGE_DEW ? "fridge" : "desiccant";
  if (dryer === "fridge" && exp.Tmin < FRIDGE_DEW) warn.push("icing");
  if (dryer === "none" && s.mode !== "ideal" && exp.Tmin < AIR.C2K(AIR.dewPoint(s.Ta, s.RH))) warn.push("icing");

  const mc = m * massFactor(s, dryer === "desiccant");
  const Wc = mc * comp.w, Wt = m * exp.w;
  const grid = gridPower(s, Wc, Wt);
  if (grid.surplus) warn.push("surplus");

  const heat = heatRecovery(s, comp);
  const absCool = mc * heat.cool, orcPower = mc * heat.power;
  if (s.heatUse !== "none" && !heat.available) warn.push("heatTooCold");
  if (heat.overCarnot) warn.push("absOverCarnot");


  const rejected = mc * (comp.stages.length ? comp.heat : 0) + mc * heat.rejected;
  const auxFan = s.auxFan / 100 * rejected;
  const auxDryer = dryer === "fridge" ? FRIDGE_POWER * Wc / s.etaDrive : 0;
  const E = Math.max(0, grid.E - orcPower + auxFan + auxDryer);
  if ((s.heatUse === "heat" || s.heatUse === "hp") && grid.E - orcPower + auxFan + auxDryer <= 0) warn.push("creditExceeds");

  const coolAir = m * exp.cool;
  const Q = (coolAir + absCool) * P.HIDDEN.capture;
  const cop = E > 0 ? Q / E : Infinity;
  const Wmin = (m * minWork(s, exp, 0) + minWork(s, { stages: [] }, absCool));
  const copCarnot = Wmin > 0 ? Q / Wmin : Infinity;

  // delivery ends at the nozzle: the air leaves at the last turbine's outlet temperature and
  // no mixing with ambient air is counted (set by CZ). Absorption cooling is reported on its own.
  const Ts = exp.Tout;
  const rhoMix = s.Pa * 1e5 / (P.CONST.R * Ts);
  const area = s.nNozzle * Math.PI * Math.pow(s.dNozzle / 1000, 2) / 4;
  const v = (1 + s.ER) * m / rhoMix / area;
  const Ar = 9.81 * ((Ta - Ts) / Ta) * (s.dNozzle / 1000) / (v * v);
  if (!exp.valid) warn.push("liquefies");
  if (exp.noFlow) warn.push("noExpansion");
  if (exp.throttled) warn.push("throttled");

  return {
    s, comp, exp, heat, dryer, warn,
    m, mc, Wc, Wt, grid: grid.E, recovered: grid.recovered, orcPower, hotWater: mc * (heat.hotWater || 0), auxFan, auxDryer, E,
    coolAir, absCool, Q, cop, copCarnot, carnotShare: isFinite(copCarnot) ? cop / copCarnot : 1,
    Tout: exp.Tout, Tmin: exp.Tmin, Ts, v, Ar, etaIso: comp.etaIso,
  };
}

const API = { system, evaluate, minWork, FRIDGE_DEW, FRIDGE_POWER };
if (node) module.exports = API;
else window.EXPLORER_SYSTEM = API;
})();

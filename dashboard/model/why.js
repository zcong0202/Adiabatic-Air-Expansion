// ---------- why the COP stays low ----------
// Three views of one state for page 4:
// flow: the electricity steps from compressor draw to net use, beside the cooling delivered.
// etaSweep: COP against compressor and turbine efficiency (set equal), once with the state's
//   other losses and once with every other loss at zero (the theoretical-ideal values).
// designPoints: a few pressures and the coldest outlet, at the state's technology and lossless.
(() => {
const node = typeof module !== "undefined";
const P = node ? require("../params.js") : window.EXPLORER_PARAMS;
const { system } = node ? require("./system.js") : window.EXPLORER_SYSTEM;

const COND = ["Ta", "RH", "m", "Pa"];
const cond = s => Object.fromEntries(COND.map(k => [k, s[k]]));

function flow(r) {
  const Ecomp = r.Wc / r.s.etaDrive;
  return {
    Ecomp, recovered: r.recovered, aux: r.auxFan + r.auxDryer, orc: r.orcPower, E: r.E, Q: r.Q, cop: r.cop,
    backWork: r.Wc > 0 ? r.Wt / r.Wc : 0, // share of the compressor's shaft work the turbine produces
  };
}

// % of COP lost when both machine efficiencies drop by one point from the state's values
function amplification(state) {
  const a = system(state), b = system({ ...state, etaC: state.etaC - 0.01, etaT: state.etaT - 0.01 });
  return a.cop > 0 && isFinite(a.cop) ? (a.cop - b.cop) / a.cop : 0;
}

const ETAS = [0.8, 0.82, 0.84, 0.86, 0.88, 0.9, 0.92, 0.94, 0.96, 0.98, 1];
function etaSweep(state) {
  const fr = { ...P.defaults("ideal"), mode: "ideal", ...cond(state), P: state.P };
  return ETAS.map(e => ({
    eta: e,
    cur: system({ ...state, etaC: e, etaT: e }).cop,
    beyond: system({ ...fr, etaC: e, etaT: e }).cop,
  }));
}

// a few pressures with the state's own reheat setting (off by default: plain series)
function designPoints(state) {
  const ideal = { ...P.defaults("ideal"), mode: "ideal", ...cond(state) };
  const rh = state.reheat === true;
  const pts = [
    { key: "p4", P: 4, reheat: rh },
    { key: "pNow", P: state.P, reheat: rh },
    { key: "p20", P: 20, reheat: rh },
    { key: "p200", P: 200, reheat: rh },
  ];
  return pts.map(p => {
    const now = system({ ...state, P: p.P, reheat: p.reheat, nExp: "auto" });
    const best = system({ ...ideal, P: p.P, reheat: p.reheat });
    return { ...p, cop: now.cop, Tmin: now.Tmin - 273.15, Ts: now.Ts - 273.15, warn: now.warn, copIdeal: best.cop, TminIdeal: best.Tmin - 273.15 };
  });
}

const API = { flow, amplification, etaSweep, designPoints, ETAS };
if (node) module.exports = API;
else window.EXPLORER_WHY = API;
})();

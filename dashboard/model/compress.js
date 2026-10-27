// ---------- compression ----------
// Per kg of air compressed. s must already have its "auto" values resolved (params.auto).
// Finite stages: equal pressure ratio per stage, stage 1 draws ambient air, later
// stages start at the cooler temperature. ∞ stages: isothermal at ambient.
// The line pressure drop is applied later, at the turbine inlet.
(() => {
const { CONST } = typeof module !== "undefined" ? require("../params.js") : window.EXPLORER_PARAMS;
const AIR = typeof module !== "undefined" ? require("./air.js") : window.EXPLORER_AIR;

function compress(s) {
  const { CP, R, K } = CONST;
  const Ta = AIR.C2K(s.Ta), pr = s.P / s.Pa;
  if (!isFinite(s.nComp)) {
    const w = R * Ta * Math.log(pr) / s.etaC;
    return { w, T1: Ta, stages: [], heat: w, tSink: Ta, wIso: R * Ta * Math.log(pr), etaIso: s.etaC };
  }
  const tSink = AIR.sinkTemp(s), Tc = tSink + s.dTapp, r = Math.pow(pr, 1 / s.nComp);
  const stages = [];
  let w = 0, heat = 0, Tin = Ta;
  for (let i = 0; i < s.nComp; i++) {
    const Ts = Tin * Math.pow(r, K);
    const Tout = Tin + (Ts - Tin) / s.etaC;
    const wi = CP * (Tout - Tin), qi = CP * (Tout - Tc);
    stages.push({ Tin, Tout, w: wi, q: qi, pOut: s.Pa * Math.pow(r, i + 1) });
    w += wi; heat += qi; Tin = Tc;
  }
  const wIso = R * Ta * Math.log(pr);
  return { w, T1: Tc, stages, heat, tSink, wIso, etaIso: wIso / w };
}

// kg compressed per kg reaching the turbine: leakage, then desiccant purge.
function massFactor(s, desiccant) {
  return 1 / (1 - s.leak / 100) / (desiccant ? 1 - s.purge / 100 : 1);
}

const API = { compress, massFactor };
if (typeof module !== "undefined") module.exports = API;
else window.EXPLORER_COMPRESS = API;
})();

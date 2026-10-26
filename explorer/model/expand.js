// ---------- expansion ----------
// Per kg of air reaching the turbine. s must have its "auto" values resolved.
// The overall ratio (P − line drop, capped at ptMax) / (Pa + back pressure) is split evenly over nExp stages.
// With reheat, air between stages runs through a coil in the nozzle intake and rewarms
// to Ta − dTrh; the entrained ambient air carries that cooling to the outlet. Without
// reheat the stages are plain series and the air keeps getting colder.
(() => {
const { CONST } = typeof module !== "undefined" ? require("../params.js") : window.EXPLORER_PARAMS;
const AIR = typeof module !== "undefined" ? require("./air.js") : window.EXPLORER_AIR;

const T_LIQUID = 133; // K, near air's critical temperature: below this the ideal-gas result is not valid

function expand(s, T1) {
  const { CP, K } = CONST;
  const Ta = AIR.C2K(s.Ta);
  // above the turbine's maximum inlet the air is throttled first: an ideal gas keeps its
  // temperature through a valve, so only the pressure (and the work it could have done) is lost
  const pLine = s.P - s.dpLine, pIn = Math.min(pLine, s.ptMax || Infinity), pOut = s.Pa + s.dpBack;
  const throttled = pLine > pIn;
  const ratio = pIn / pOut;
  if (ratio <= 1) return { ratio, stages: [], w: 0, cool: 0, Tout: T1, Tmin: T1, valid: true, noFlow: true, pIn, throttled };
  const r = Math.pow(ratio, 1 / s.nExp), Trh = Ta - (s.dTrh || 0);
  const stages = [];
  let Tin = T1, p = pIn, w = 0, cool = 0;
  for (let j = 0; j < s.nExp; j++) {
    const Ts = Tin / Math.pow(r, K);
    const Tout = Tin - s.etaT * (Tin - Ts);
    const last = j === s.nExp - 1;
    // cooling handed over by this stage: through the coil to Trh, or at the outlet up to Ta
    const q = last ? CP * (Ta - Tout) : s.reheat ? CP * (Trh - Tout) : 0;
    p /= r;
    stages.push({ Tin, Tout, pOut: p, w: CP * (Tin - Tout), q });
    w += CP * (Tin - Tout); cool += q;
    Tin = last || !s.reheat ? Tout : Trh;
  }
  const Tmin = Math.min(...stages.map(x => x.Tout));
  return { ratio, r, stages, w, cool, Tout: stages.at(-1).Tout, Tmin, valid: Tmin >= T_LIQUID, pIn, throttled };
}

const API = { expand, T_LIQUID };
if (typeof module !== "undefined") module.exports = API;
else window.EXPLORER_EXPAND = API;
})();

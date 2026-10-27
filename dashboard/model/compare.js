// ---------- comparison with air conditioners ----------
// Two views, both per unit of electricity:
// outlet: cooling leaving the outlet (the COP itself).
// AC COPs are scaled from their rating temperature to the current ambient by acDerate.
// net local: cooling minus the condenser heat that drifts back to the cooled spot.
//   An AC rejects Q + W = Q(1 + 1/COP) next to its users; fRet of it comes back.
//   The air cycle rejects its heat at the distant compressor, so nothing comes back.
(() => {
const node = typeof module !== "undefined";
const { system } = node ? require("./system.js") : window.EXPLORER_SYSTEM;

const netLocal = (cop, f) => cop - f * (cop + 1);
// Returning share at which the AC's net local cooling falls to the air cycle's COP.
const breakEvenRet = (copAc, copAir) => Math.min(1, Math.max(0, (copAc - copAir) / (copAc + 1)));
// °C rating condition: spot cooler at 95 °F (maker's data), split at ESMA T3 (46 °C)
const T_RATED = { spot: 35, split: 46 };
const derated = (cop, s, Trated = 35) => cop * Math.max(0, 1 - s.acDerate / 100 * (s.Ta - Trated));

function compare(state, r = system(state)) {
  const f = state.fRet / 100;
  const ac = [
    { key: "spot", rated: state.copSpot, Ts: state.TsSpot },
    { key: "split", rated: state.copSplit, Ts: state.TsSplit },
  ].map(a => { const cop = derated(a.rated, state, T_RATED[a.key]); return { ...a, cop, net: netLocal(cop, f), fEven: breakEvenRet(cop, r.cop) }; });
  const air = { cop: r.cop, net: r.cop, Ts: r.Ts - 273.15 };
  return { ac, air };
}

const API = { compare, netLocal, breakEvenRet, derated, T_RATED };
if (node) module.exports = API;
else window.EXPLORER_COMPARE = API;
})();

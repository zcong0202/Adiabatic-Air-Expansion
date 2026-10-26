// ---------- COP–pressure curve and the optimum ----------
// The curve is not smooth (stage counts and the dryer switch along it), so instead of a
// golden-section search it samples the whole range on a log grid, takes the best point,
// then samples finely between its two neighbours.
(() => {
const node = typeof module !== "undefined";
const X = node ? require("../params.js") : window.EXPLORER_PARAMS;
const { system } = node ? require("./system.js") : window.EXPLORER_SYSTEM;

const N_GRID = 200, N_FINE = 20;

function point(state, P) {
  const r = system({ ...state, P });
  return { P, cop: r.cop, copCarnot: r.copCarnot, Ts: r.Ts, nComp: r.s.nComp, nExp: r.s.nExp, dryer: r.dryer, warn: r.warn };
}

// Log grid over [lo, hi]; returns the points, the optimum and where the dryer changes type.
// Ideal mode has no optimum: its COP equals the Carnot limit and only falls with pressure.
function sweep(state, lo = X.BY_KEY.P.min, hi = X.BY_KEY.P.max) {
  const at = i => lo * Math.pow(hi / lo, i / N_GRID);
  const points = [];
  for (let i = 0; i <= N_GRID; i++) points.push(point(state, at(i)));
  const valid = p => isFinite(p.cop) && !p.warn.includes("liquefies") && !p.warn.includes("noExpansion");
  let k = -1;
  points.forEach((p, i) => { if (valid(p) && (k < 0 || p.cop > points[k].cop)) k = i; });
  let best = k < 0 || state.mode === "ideal" ? null : points[k];
  if (best) {
    const a = at(Math.max(0, k - 1)), b = at(Math.min(N_GRID, k + 1));
    for (let j = 0; j <= N_FINE; j++) {
      const p = point(state, a * Math.pow(b / a, j / N_FINE));
      if (valid(p) && p.cop > best.cop) best = p;
    }
  }
  const dryerSwitch = [];
  for (let i = 1; i < points.length; i++)
    if (points[i].dryer !== points[i - 1].dryer) dryerSwitch.push({ P: points[i].P, from: points[i - 1].dryer, to: points[i].dryer });
  return { points, best, dryerSwitch };
}

// Compressor and turbine efficiency (set equal) that brings the COP at this state up to
// target. Bisection between the current value and 1; null when even 1 falls short.
function breakEven(state, target) {
  const cop = x => system({ ...state, etaC: x, etaT: x }).cop;
  let lo = Math.min(state.etaC, state.etaT), hi = 1;
  if (cop(lo) >= target) return { eta: lo, already: true };
  if (cop(hi) < target) return null;
  for (let i = 0; i < 30; i++) { const mid = (lo + hi) / 2; if (cop(mid) >= target) hi = mid; else lo = mid; }
  return { eta: hi, already: false };
}

const API = { sweep, breakEven, N_GRID, N_FINE };
if (node) module.exports = API;
else window.EXPLORER_SWEEP = API;
})();

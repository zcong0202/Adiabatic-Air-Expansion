// ---------- energy ledger ----------
// Lays the two recoverable streams side by side for one state: the compression heat and the
// turbine's shaft work. A recovery share is applied to each, and the COP read off:
//   work share w: grid electricity saved per unit of turbine shaft work.
//   heat share h: recovered heat ÷ all compression heat, credited at f kWh of electricity per
//     kWh of heat (the same factor as page 1). Recovered heat no longer goes to the seawater,
//     so the seawater pumps shrink with it.
// At the page 1 shares the ledger gives exactly the page 1 COP.
(() => {
const node = typeof module !== "undefined";
const { system } = node ? require("./system.js") : window.EXPLORER_SYSTEM;

function ledger(state) {
  // the cooling water stays as page 1 resolved it (it follows the heat use there)
  const own = system(state).s;
  state = { ...state, cooling: own.cooling, Tw: own.Tw };
  const b = system({ ...state, recPath: "none", heatUse: "none" });
  const s = b.s, stages = b.comp.stages; // no stages when compression is isothermal
  const H = b.mc * (stages.length ? b.comp.heat : 0);
  const Ecomp = b.Wc / s.etaDrive, pump = s.auxFan / 100, dryer = b.auxDryer;
  const Tdis = stages.length ? Math.max(...stages.map(st => st.Tout)) : s.Ta + 273.15;
  const aux = (h = 0) => pump * H * (1 - h) + dryer;

  // COP = cooling ÷ (compressor electricity − w × turbine work + pumps/dryer − h × H × f)
  const cop = (w, h = 0, f = 0) => {
    const E = Ecomp - w * b.Wt + aux(h) - h * H * f;
    return E > 0 ? b.coolAir / E : Infinity;
  };
  const work = [{ key: "none", w: 0 }, { key: "gen", w: 0.9 }]; // generator 0.93 × inverter 0.97
  // each heat use as page 1 runs it: its share is capped by the heat above its supply temperature
  const heat = ["none", "heat", "hp"].map(key => {
    if (key === "none" || !H) return { key, h: 0, f: 0, ok: key === "none" };
    const r = system({ ...state, recPath: "none", heatUse: key });
    return { key, h: r.hotWater / H, f: r.s.heatValue, T: r.s.hwT, ok: r.hotWater > 0 };
  });

  return { base: b, H, Wt: b.Wt, Q: b.coolAir, Ecomp, aux, Tdis, nComp: s.nComp, work, heat, cop };
}

const API = { ledger };
if (node) module.exports = API;
else window.EXPLORER_LEDGER = API;
})();

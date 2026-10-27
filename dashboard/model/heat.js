// ---------- heat recovery ----------
// Per kg of air compressed, from the stage discharge temperatures of compress().
// Only heat above (device minimum drive temperature + cooler approach) is usable.
// absorption: adds COPabs × usable heat to the cooling.
// orc: returns etaORC × usable heat as electricity.
// heat: water-cooled coolers keep hwShare of the compression heat as hot water at hwT, at most
//   the heat above (hwT + cooler approach), credited at heatValue kWh of electricity per kWh
//   of heat (what that heat replaces). power then holds that credit.
// rejected: heat the recovery device itself has to dump (counts toward the fans or tower).
(() => {
const T_CHILLED = 280.15; // K, 7 °C chilled water, for the absorption Carnot check

function heatRecovery(s, comp) {
  const none = { usable: 0, cool: 0, power: 0, rejected: 0, threshold: null, available: false, overCarnot: false };
  if (s.heatUse === "none" || !comp.stages.length) return none;
  const CP = 1005;
  if ((s.heatUse === "heat" || s.heatUse === "hp")) {
    const threshold = s.hwT + 273.15 + s.dTapp;
    const above = comp.stages.reduce((a, st) => a + CP * Math.max(0, st.Tout - threshold), 0);
    const want = s.hwShare / 100 * comp.heat, usable = Math.min(want, above);
    return { ...none, usable, threshold, available: usable > 0, capped: want > above + 1e-9, hotWater: usable, power: usable * s.heatValue, rejected: -usable };
  }
  const Tmin = (s.heatUse === "orc" ? s.TminORC : s.TminAbs) + 273.15;
  const threshold = Tmin + s.dTapp;
  const usable = comp.stages.reduce((a, st) => a + CP * Math.max(0, st.Tout - threshold), 0);
  const out = { ...none, usable, threshold, available: usable > 0 };
  if (s.heatUse === "absorption") {
    const Ta = s.Ta + 273.15;
    const limit = (1 - Ta / Tmin) * T_CHILLED / (Ta - T_CHILLED);
    out.cool = s.copAbs * usable;
    out.rejected = usable + out.cool;
    out.overCarnot = s.copAbs > limit;
    out.carnotLimit = limit;
  } else {
    out.power = s.etaORC / 100 * usable;
    out.rejected = usable - out.power;
  }
  return out;
}

const API = { heatRecovery };
if (typeof module !== "undefined") module.exports = API;
else window.EXPLORER_HEAT = API;
})();

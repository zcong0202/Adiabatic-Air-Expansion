// ---------- work recovery ----------
// Grid electricity for the compressor after the turbine's work is sent back.
// Wc: compressor shaft power (W), Wt: turbine shaft power (W).
// shaft: turbine work offsets compressor shaft work before the motor, so it skips the drive loss.
// gen: generator + inverter feed the motor's DC bus, so only the chain efficiency applies.
(() => {
function gridPower(s, Wc, Wt) {
  const back = s.recPath === "none" ? 0 : Wt * s.etaRec;
  const raw = s.recPath === "shaft" ? (Wc - back) / s.etaDrive : Wc / s.etaDrive - back;
  return { E: Math.max(0, raw), recovered: back, surplus: raw < 0 };
}

const API = { gridPower };
if (typeof module !== "undefined") module.exports = API;
else window.EXPLORER_RECOVER = API;
})();

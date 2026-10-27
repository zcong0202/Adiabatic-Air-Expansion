// ---------- ambient air ----------
(() => {
const C2K = c => c + 273.15;

// Wet-bulb temperature (°C) from dry bulb (°C) and RH (%), Stull (2011),
// J. Appl. Meteor. Climatol. 50, 2267–2269. About ±0.3 K for RH 5–99 %, −20 to 50 °C, sea level.
function wetBulb(T, RH) {
  return T * Math.atan(0.151977 * Math.sqrt(RH + 8.313659)) + Math.atan(T + RH) - Math.atan(RH - 1.676331)
    + 0.00391838 * Math.pow(RH, 1.5) * Math.atan(0.023101 * RH) - 4.686035;
}

// Dew point (°C) by the Magnus formula (Alduchov & Eskridge 1996 coefficients).
function dewPoint(T, RH) {
  const a = 17.625, b = 243.04, g = Math.log(Math.max(RH, 0.1) / 100) + a * T / (b + T);
  return b * g / (a - g);
}

// Temperature (K) the coolers reject heat to.
function sinkTemp(s) {
  if (s.cooling === "tower") return C2K(typeof s.Tw === "number" ? s.Tw : wetBulb(s.Ta, s.RH) + 4); // Tw: the tower water as resolved (or typed)
  if (s.cooling === "water") return C2K(s.Tw);
  return C2K(s.Ta);
}

const API = { C2K, wetBulb, dewPoint, sinkTemp };
if (typeof module !== "undefined") module.exports = API;
else window.EXPLORER_AIR = API;
})();

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "../../kit/iso-kit.mjs";
import * as G from "../../kit/lathe.mjs";
import { tubePieces, tubeSvg } from "../../kit/tube.mjs";
import * as A from "../../kit/audit.mjs";
import { kitScript } from "../../scripts/inline-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const THEME = process.argv.includes("--light") ? "light" : "dark";

const W = 720;
const H = 420;
const PLATE = { x: -214, y: -60, w: 414, d: 120, r: 8 };
const PLATE_H = 10;
const FOOT_H = 5;
const YC = -4; // centre line of the pressure train
const MOTOR_Y = [-30, -10, 10, 30];
const AXZ = 10; // motor axis height
const DUCT_R = 5;

const P = k.fitProjection(
  [...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [96, 0, 97], [124, 0, 97], [-124, 0, 107], [-124, 38, 107], [176, 26, 97], [184, -28, 48]],
  W,
  H,
  { pad: 26, azimuth: 58, elevation: 30 },
);
const KS = G.scaleOf(P);
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const Ln = (d, style) => k.lineSvg(d, style);
const Dots = (points, style) => k.dotsSvg(points, style);
const path3 = (points, closed = false) => k.pathOf(points.map(at), closed);
const f2 = (v) => Math.round(v * 100) / 100;

const R = A.recorder(P);
const record = R.solid;
function put(name, ref, svg, shapes = [], { bias = 0, ...rest } = {}) {
  return R.put({ name, at: ref, bias, svg, shapes, piece: "rig", ...rest });
}
function box(name, [x0, y0, z0], [x1, y1, z1], style = {}, { r = 0.6, steps = 3, bevel = 0.4, extra = "", inner = "", bias = 0, owner } = {}) {
  const plan = { x: x0, y: y0, w: x1 - x0, d: y1 - y0, r };
  const shape = record(A.slab(plan, z0, z1 - z0, { name, owner }, steps));
  put(name, [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2], S(k.slabOf(plan, z0, z1 - z0, P, steps, bevel), { tone: "mid", ...style, inner }) + extra, [shape], { bias });
  return plan;
}
function cyl(name, cx, cy, r, z, h, style = {}, { steps = 32, bevel = 0, extra = "", inner = "", bias = 0, owner } = {}) {
  const shape = record(A.cylinder(cx, cy, r, z, h, { name, owner }));
  put(name, [cx, cy, z + h / 2], S(k.cylinder(cx, cy, r, z, h, P, steps, bevel), { tone: "mid", ...style, inner }) + extra, [shape], { bias });
}
function turned(name, F, profile, style = {}, { extra = "", inner = "", bias = 0, owner, attrs } = {}) {
  const paths = G.solidOf(profile, F, P, {});
  const mid = (profile[0][0] + profile[profile.length - 1][0]) / 2;
  const shape = record(A.solid(F, profile, { name, owner }));
  put(name, G.add3(F.o, G.mul3(F.a, mid)), S(paths, { tone: "mid", ...style, inner }) + extra, [shape], { bias, attrs });
}
function pipe(name, points, r, { tone = "hi", bend, rings, maxLength = 14, bias = 0.05, limp = false, touch } = {}) {
  const route = G.fillet(points, bend ?? Math.max(3, r * 2.6), 10, { P, tube: r });
  R.route(name, route, r, { limp, touch, piece: "rig" });
  tubePieces(route, r, P, { maxLength, spacing: Math.max(0.6, Math.min(1.6, r)), ...(rings ? { rings } : {}) }).forEach((piece, index) =>
    put(`${name}:${index}`, piece.mid, tubeSvg(piece, { tone }), [A.tube(piece.points, piece.radii)], { bias, route: name, chunk: index }),
  );
  return route;
}
const byDepth = (points) => [...points].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
const dial = (cx, cy, r, z, h, { ticks = 40, every = 5, from = -0.75 * Math.PI, span = 1.5 * Math.PI } = {}) => {
  const top = z + h;
  const t = k.radialTicks(cx, cy, r - 2.4, ticks, every, top, [0.9, 2], P, from, span);
  return (
    Ln(k.knurl(cx, cy, r, top - 2.2, top, Math.round(r * 4), P, 0.3), { tone: "lo" }) +
    Ln(k.ring(cx, cy, r - 1.4, top, P, 48), { tone: "lo" }) +
    Ln(t.minor, { tone: "lo" }) +
    Ln(t.major, { tone: "mid" }) +
    Ln(k.ring(cx, cy, 1, top, P, 12), { tone: "mid" })
  );
};
const needle = (cx, cy, r, top, angle) =>
  k.lineOnTop([cx - Math.sin(angle) * 1.6, cy + Math.cos(angle) * 1.6], [cx + Math.sin(angle) * r, cy - Math.cos(angle) * r], top + 0.2, P);

// ---------- base plate ----------
const back = [];
back.push(`<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - FOOT_H, PLATE_H, P)}"/>`);
for (const [x, y] of byDepth(k.corners(PLATE, 22))) {
  back.push(S(k.cylinder(x, y, 7, -PLATE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
  back.push(S(k.cylinder(x, y, 5.4, -PLATE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
}
back.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.6), { tone: "mid", inner: Ln(k.sideSeam(PLATE, -4, P, 8), { tone: "faint" }) }));
back.push(Ln(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "lo" }));
const plateScrews = k.corners(PLATE, 10);
back.push(Ln(plateScrews.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }));
back.push(Dots(plateScrews.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
record(A.slab(PLATE, -PLATE_H, PLATE_H, { name: "stand.plate", ground: true }, 8));
const STRIP = { x: PLATE.x + 16, y: PLATE.y + PLATE.d - 13, w: 300, d: 6, r: 1 };
back.push(S(k.slabOf(STRIP, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
const ticks = k.topTicks(STRIP.x + 4, STRIP.x + STRIP.w - 4, 4, 5, STRIP.y, 0.6, [1.8, 3.4], P);
back.push(Ln(ticks.minor, { tone: "lo" }), Ln(ticks.major, { tone: "mid" }));
const LABEL = { x: STRIP.x + STRIP.w + 10, y: PLATE.y + PLATE.d - 20, w: 34, d: 13, r: 1.2 };
back.push(S(k.slabOf(LABEL, 0, 0.8, P, 3), { tone: "lo", crease: "none" }));
back.push(Ln(k.planOutline(k.insetPlan(LABEL, 1.4), 0.8, P, 3), { tone: "faint" }));
back.push(Ln([22, 15, 19].map((w, i) => k.lineOnTop([LABEL.x + 4, LABEL.y + 3.4 + i * 3], [LABEL.x + 4 + w, LABEL.y + 3.4 + i * 3], 0.8, P)).join(""), { tone: "lo", free: true }));
back.push(Dots([at([LABEL.x + LABEL.w - 2.6, LABEL.y + 2.4, 0.8]), at([LABEL.x + LABEL.w - 2.6, LABEL.y + LABEL.d - 2.4, 0.8])], { size: 0.45 }));
// floor mat that marks the seat zone
const MAT = { x: 116, y: -38, w: 72, d: 76, r: 3 };
back.push(S(k.slabOf(MAT, 0, 0.6, P, 4), { tone: "lo", crease: "none" }));
back.push(Ln(k.planOutline(k.insetPlan(MAT, 3), 0.6, P, 4), { tone: "faint" }));
record(A.slab(MAT, 0, 0.6, { name: "stand.mat", ground: true }, 4));

const seg = (a, b) => { const [x0, y0] = at(a), [x1, y1] = at(b); return `M${x0.toFixed(2)} ${y0.toFixed(2)}L${x1.toFixed(2)} ${y1.toFixed(2)}`; };
// ---------- 1. motor ----------
const AX = 12; // crankshaft height
const XF = (x, y = 0, z = AX) => G.frameOf([x, y, z], [1, 0, 0], [0, 1, 0], [0, 0, 1]);
box("motor.foot", [-194, -12, 0], [-160, 12, 1], { tone: "lo" }, { r: 1 });
turned("motor", XF(-196), [[0, 9], [1.4, 11], [34, 11], [36, 9]], { tone: "mid" }, { extra: k.fadedSvg(G.ribsOf(XF(-196), 3, 33, 11, 34, P, { fade: [0.1, 0.55], seams: true }), { tone: "lo" }) });
box("motor.terminal", [-186, -6, 23], [-174, 6, 27], { tone: "mid" }, { r: 1, bevel: 0.4, extra: Dots([at([-184.5, -4.5, 27]), at([-175.5, 4.5, 27])], { size: 0.45 }) });
turned("motor.shaft", XF(-160), [[0, 2.2], [4, 2.2]], { tone: "mid" });
turned("motor.coupling", XF(-156), [[0, 4.4], [5, 4.4]], { tone: "mid" }, { extra: '<g data-part="spin0"></g>' });
turned("crank.shaft", XF(-151), [[0, 2.2], [1, 2.2]], { tone: "mid" });

// ---------- 2. three-stage compressor on one crankcase ----------
const CASE = { x: -150, y: -20, w: 100, d: 40, r: 3 };
box("crankcase", [CASE.x, CASE.y, 0], [CASE.x + CASE.w, CASE.y + CASE.d, 24], { tone: "mid" }, {
  r: 3, steps: 4, bevel: 0.8,
  inner: Ln(k.sideSeam(CASE, 8, P, 4), { tone: "faint" }),
  extra: Dots([[-146, 16], [-54, 16], [-146, -16], [-54, -16]].map(([x, y]) => at([x, y, 24])), { size: 0.45 }) + Ln(k.planOutline({ x: -146, y: 6, w: 10, d: 10, r: 2 }, 24, P, 3), { tone: "faint" }),
});
const STAGES = [
  { x: -130, r: 12, top: 56, out: -124, inn: null },
  { x: -96, r: 9.5, top: 50, out: -93, inn: -100 },
  { x: -66, r: 7.5, top: 46, out: -62, inn: -69 },
];
STAGES.forEach((s, i) => {
  cyl(`stage${i}.barrel`, s.x, 0, s.r, 24, s.top - 28, { tone: "hi", crease: "lo" }, {
    steps: 48, extra: Ln(k.knurl(s.x, 0, s.r, 27, s.top - 6, Math.round(s.r * 3.2), P, 0.3), { tone: "lo" }) + Ln(k.sideArc(s.x, 0, s.r, 27, P, 32) + k.sideArc(s.x, 0, s.r, s.top - 6, P, 32), { tone: "faint" }),
  });
  box(`stage${i}.head`, [s.x - s.r - 1.5, -s.r - 1.5, s.top - 4], [s.x + s.r + 1.5, s.r + 1.5, s.top], { tone: "mid" }, {
    r: 2, steps: 4, bevel: 0.5, extra: Dots(k.corners({ x: s.x - s.r - 1.5, y: -s.r - 1.5, w: 2 * s.r + 3, d: 2 * s.r + 3 }, 2).map(([x, y]) => at([x, y, s.top])), { size: 0.45 }),
  });
  for (const px of [s.out, s.inn].filter((v) => v !== null)) cyl(`stage${i}.port${px}`, px, 0, 3.4, s.top, 1.6, { tone: "mid" }, { steps: 24 });
});
cyl("intake", -136, 0, 3.6, 56, 6, { tone: "mid" }, { steps: 28, extra: Ln(k.knurl(-136, 0, 3.6, 57, 61, 16, P, 0.3), { tone: "lo" }) });
cyl("intake.cap", -136, 0, 2.4, 62, 1.4, { tone: "mid" }, { steps: 20, extra: Dots([at([-136, 0, 63.4])], { size: 0.45, tone: "hi" }) });

// ---------- 3. intercoolers and aftercooler (front row) ----------
const COOLERS = [
  { name: "ic1", x0: -128, x1: -96, ports: [-124, -100] },
  { name: "ic2", x0: -94, x1: -66, ports: [-93, -69] },
  { name: "ac", x0: -63, x1: -33, ports: [-61, -36] },
];
const CY0 = 30, CY1 = 46, CZ = 36;
COOLERS.forEach((c) => {
  const fins = Array.from({ length: Math.floor((c.x1 - c.x0 - 4) / 2) + 1 }, (_, i) => seg([c.x0 + 2 + i * 2, CY1, 3], [c.x0 + 2 + i * 2, CY1, CZ - 3], P)).join("");
  box(c.name, [c.x0, CY0, 0], [c.x1, CY1, CZ], { tone: "mid" }, {
    r: 0.8, steps: 2, bevel: 0.4,
    inner: Ln(k.sideSeam({ x: c.x0, y: CY0, w: c.x1 - c.x0, d: CY1 - CY0, r: 0.8 }, 3, P, 2) + k.sideSeam({ x: c.x0, y: CY0, w: c.x1 - c.x0, d: CY1 - CY0, r: 0.8 }, CZ - 3, P, 2), { tone: "faint" }),
    extra: Ln(fins, { tone: "lo" }),
  });
  for (const px of c.ports) cyl(`${c.name}.port${px}`, px, 38, 3.4, CZ, 1.6, { tone: "mid" }, { steps: 24 });
});
cyl("ac.gauge", -48.5, 38, 5.2, CZ, 4, { tone: "hi", crease: "lo" }, {
  steps: 48, extra: dial(-48.5, 38, 5.2, CZ, 4, { ticks: 20, every: 5 }) + `<path data-part="gauge" class="iso-line" data-tone="hi" data-free="start" d=""/>`,
});

// ---------- 4. expansion turbine on the same shaft ----------
turned("crank.out", XF(-50), [[0, 2.2], [1.5, 2.2]], { tone: "mid" });
turned("turb.coupling", XF(-48.5), [[0, 4.4], [4.5, 4.4]], { tone: "mid" }, { extra: '<g data-part="spin1"></g>' });
turned("turb.shaft", XF(-44), [[0, 2.2], [2, 2.2]], { tone: "mid" });
const TB = { x: -42, y: -15, w: 20, d: 30, r: 6 };
box("turbine", [TB.x, TB.y, 0], [TB.x + TB.w, TB.y + TB.d, 30], { tone: "hi", crease: "lo" }, {
  r: 6, steps: 8, bevel: 0.8,
  inner: Ln(k.sideSeam(TB, 10, P, 8) + k.sideSeam(TB, 20, P, 8), { tone: "faint" }),
  extra: Dots(k.corners(TB, 3.5).map(([x, y]) => at([x, y, 30])), { size: 0.45 }),
});
cyl("turb.port", -36, 0, 3.4, 30, 1.6, { tone: "mid" }, { steps: 24 });
{
  const F = XF(-22, 0, 15);
  turned("turb.outlet", F, [[0, 8.2], [3, 8.2]], { tone: "mid" }, { extra: Dots(G.dotsOf(F, 3, 7, 8, P, { all: true }), { size: 0.45 }) });
}
for (const x of [20, 70]) box(`cradle${x}`, [x - 4, -6, 0], [x + 4, 6, 9], { tone: "mid" }, { r: 0.8, bevel: 0.3, extra: Dots([at([x - 2.4, -3.6, 9]), at([x + 2.4, 3.6, 9])], { size: 0.4 }) });

// ---------- 7. seat, diffuser, thermometer ----------
for (const [x, y] of [[132, -22], [132, 22]]) {
  cyl(`post.base${y}`, x, y, 4, 0.6, 2, { tone: "lo" }, { steps: 24 });
  cyl(`post${y}`, x, y, 1.8, 2.6, 81.4, { tone: "mid" }, { steps: 20, extra: Ln(k.sideArc(x, y, 1.8, 40, P, 12), { tone: "faint" }) });
}
const DIF = { x: 124, y: -28, w: 48, d: 56, r: 2 };
box("diffuser", [DIF.x, DIF.y, 84], [DIF.x + DIF.w, DIF.y + DIF.d, 96], { tone: "mid" }, {
  r: 2, steps: 4, bevel: 0.6,
  extra: Ln(k.planOutline(k.insetPlan(DIF, 4), 96, P, 4), { tone: "faint" }) + Dots(k.corners(DIF, 3).map(([x, y]) => at([x, y, 96])), { size: 0.45 }),
});
for (const [x, y] of [[142, -14], [164, -14], [142, 14], [164, 14]]) cyl(`chair.leg${x}${y}`, x, y, 1.4, 0.6, 27.4, { tone: "mid" }, { steps: 16 });
box("chair.seat", [138, -18, 28], [168, 18, 32], { tone: "mid" }, { r: 2, steps: 4, bevel: 0.6, extra: Ln(k.planOutline({ x: 141, y: -15, w: 24, d: 30, r: 2 }, 32, P, 4), { tone: "faint" }) });
box("chair.back", [138, -18, 32], [142, 18, 64], { tone: "mid" }, { r: 1.2, steps: 3, bevel: 0.5 });
box("chair.cushion", [143, -15, 32], [166, 15, 34], { tone: "mid" }, { r: 2.4, steps: 5, bevel: 0.5 });
cyl("therm.base", 184, -28, 4, 0.6, 2, { tone: "lo" }, { steps: 24 });
cyl("therm.post", 184, -28, 1.6, 2.6, 37.4, { tone: "mid" }, { steps: 16 });
cyl("therm.dial", 184, -28, 9, 40, 5, { tone: "hi", crease: "lo" }, {
  steps: 64, bevel: 0.5,
  extra: dial(184, -28, 9, 40, 5, { ticks: 50, every: 10 }) + `<path data-part="needle" class="iso-line" data-tone="lit" data-free="start" style="stroke-width:1.1" d=""/>`,
});

// ---------- pipes and the cold duct ----------
const P1 = 2.2;
pipe("p.s1", [[-124, 0, 57.6], [-124, 0, 104], [-124, 38, 104], [-124, 38, CZ + 1.6]], P1, { bend: 11 });
pipe("p.s2in", [[-100, 38, CZ + 1.6], [-100, 38, 98], [-100, 0, 98], [-100, 0, 51.6]], P1, { bend: 11 });
pipe("p.s2", [[-93, 0, 51.6], [-93, 0, 92], [-93, 38, 92], [-93, 38, CZ + 1.6]], P1, { bend: 11 });
pipe("p.s3in", [[-69, 38, CZ + 1.6], [-69, 38, 86], [-69, 0, 86], [-69, 0, 47.6]], P1, { bend: 11 });
pipe("p.s3", [[-62, 0, 47.6], [-62, 0, 80], [-62, 38, 80], [-62, 38, CZ + 1.6]], P1, { bend: 11, maxLength: 8 });
pipe("p.turb", [[-36, 38, CZ + 1.6], [-36, 38, 62], [-36, 0, 62], [-36, 0, 31.6]], P1, { bend: 11 });
pipe("cable.motor", [[-180, 6, 25], [-180, 22, 25], [-180, 22, 3.5], [-180, 40, 3.5]], 0.9, { tone: "mid", bend: 3, limp: true });
box("socket", [-186, 40, 0], [-174, 48, 7], { tone: "mid" }, { r: 1, bevel: 0.4, extra: Ln(k.planOutline({ x: -183.5, y: 42, w: 7, d: 4, r: 1 }, 7, P, 3), { tone: "faint" }) + Dots([at([-184.4, 44, 7]), at([-175.6, 44, 7])], { size: 0.45 }) });
const DUCT = [[-19, 0, 15], [96, 0, 15], [96, 0, 90], [121, 0, 90]];
{
  const FF = G.frameOf([121, 0, 90], [1, 0, 0], [0, 1, 0], [0, 0, 1]);
  turned("duct.flange", FF, [[0, 7.2], [3, 7.2]], { tone: "mid" }, { extra: Dots(G.dotsOf(FF, 0, 5.9, 8, P, { fade: [0.04, 0.42] }), { size: 0.45 }) });
}
pipe("duct", DUCT, 6, { bend: 15, rings: { pitch: 3.2, fade: [0.1, 0.55] }, maxLength: 16, touch: ["cradle20", "cradle70"] });

A.settle(R, P);
R.items.sort((a, b) => a.key - b.key);
const indexOf = (name) => R.items.findIndex((item) => item.name === name);
const coldSlot = Math.max(indexOf("chair.seat"), indexOf("chair.back"));
const groups = R.items.map((item, index) => `<g class="it" data-name="${item.name}">${item.svg}</g>${index === coldSlot ? '<g data-part="cold"></g>' : ""}`);

const svg = k.figureSvg({
  width: W,
  height: H,
  label:
    "A bench model of an ideal air-cycle cooler. An electric motor turns one crankshaft that drives a three-stage piston compressor and, at its far end, an expansion turbine. Between the stages the air passes through two intercoolers and an aftercooler in a row at the front. The turbine's cold exhaust runs along an insulated duct to a diffuser above a chair; a thermometer beside the chair reads the outlet temperature.",
  body: [...back, `<g>${groups.join("")}</g>`],
});

const CALL = [
  { key: "motor", at: [-178, 0, 27], rail: "top", chars: 18 },
  { key: "stages", at: [-130, 0, 64], rail: "top", chars: 22 },
  { key: "turb", at: [-32, 0, 30], rail: "top", chars: 27 },
  { key: "outlet", at: [150, 0, 96], rail: "top", chars: 17 },
  { key: "coolers", at: [-80, 46, 18], rail: "bottom", chars: 34 },
  { key: "duct", at: [40, 6, 15], rail: "bottom", chars: 22 },
  { key: "seat", at: [158, 15, 33], rail: "bottom", chars: 24 },
];
const CH = 6.6, GAP = 8, EDGE = 8;
const plateFront = (x) => at([x, PLATE.y + PLATE.d, -PLATE_H - FOOT_H])[1];
const calls = CALL.map((c) => { const [sx, sy] = at(c.at); return { ...c, sx: f2(sx), sy: f2(sy), w: c.chars * CH + 14 }; });
for (const rail of ["top", "bottom"]) {
  const list = calls.filter((c) => c.rail === rail).sort((a, b) => a.sx - b.sx);
  list.forEach((c) => { c.cx = Math.min(W - EDGE - c.w / 2, Math.max(EDGE + c.w / 2, c.sx)); });
  for (let pass = 0; pass < 20; pass++) {
    for (let i = 1; i < list.length; i++) { const a = list[i - 1], b = list[i]; const need = a.cx + a.w / 2 + GAP + b.w / 2; if (b.cx < need) b.cx = need; }
    const last = list[list.length - 1]; const over = last.cx + last.w / 2 - (W - EDGE); if (over > 0) list.forEach((c) => (c.cx -= over));
    list.forEach((c) => { c.cx = Math.max(EDGE + c.w / 2, c.cx); });
  }
  list.forEach((c) => { c.cy = rail === "top" ? 20 : Math.min(H - 6, plateFront(Math.max(PLATE.x, Math.min(PLATE.x + PLATE.w, c.at[0]))) + 10); c.cx = f2(c.cx); c.cy = f2(c.cy); });
}
const COUP = [{ o: [-156, 0, AX], s0: 0, s1: 5, r: 4.4 }, { o: [-48.5, 0, AX], s0: 0, s1: 4.5, r: 4.4 }];
const DATA = { W, H, calls: calls.map(({ key, sx, sy, cx, cy, rail }) => ({ key, sx, sy, cx, cy, rail })), P, couplings: COUP, gauge: [-48.5, 38, CZ + 4], therm: [184, -28, 45], diff: { x0: 144, x1: 165, y0: -15, y1: 15, top: 84, floor: 34 } };
const latheSource = readFileSync(join(HERE, "..", "..", "kit", "lathe.mjs"), "utf8").replace(/^import .*$/m, "").replace(/^export /gm, "");
const latheScript = `const G = (() => {${latheSource}\nreturn { frameOf, ribsOf, fadeOf };})();\n`;
const LIVE = readFileSync(join(HERE, "live.js"), "utf8").replace("__DATA__", JSON.stringify(DATA));

const body = k.plateHtml({
  fig: "Fig 2",
  title: "Ideal air cycle",
  hint: "Move across to set the pressure ratio",
  readout: "ideal · ratio 7.3 · outlet −96 °C · 9.8 kW · COP 3.45",
  keys: [
    { mark: "lit", label: "Thermometer needle: air temperature leaving the diffuser" },
    { mark: "raised", label: "Three compressor stages with coolers between them: the closer to isothermal, the less work" },
    { mark: "flat", label: "Turbine on the same crankshaft: its work goes straight back into the compressor" },
  ],
  caption:
    "The theoretical limit of the air cycle. Compression is isothermal (each stage cooled back toward ambient), the turbine expands the air isentropically, and all of its shaft work goes straight back into the compressor. At a pressure ratio of 7.3 (the 7.3 bar supply used before), 78 g/s of air leaves the turbine at −96 °C, the seat gets 9.8 kW, and the motor only supplies the 2.9 kW gap between compressor and turbine: COP about 3.4. The 2.1 quoted earlier also paid for compressing to 8.6 bar and throttling down to 7.3. Lower the ratio and the ideal COP climbs, because the cycle lifts heat over a smaller temperature step. Switch to realistic machines (80 % stage and turbine efficiency, 95 % of turbine work recovered, 12 % duct gain) and COP falls to 0.6–0.8 at any ratio: below a split air conditioner's 3–4. Ideal-gas model, 30 °C ambient, 10 K heat-exchanger approach; computed, not measured.",
  body: `<style>${readFileSync(join(HERE, "..", "air-cycle", "air-cycle.css"), "utf8")}${readFileSync(join(HERE, "ideal.css"), "utf8")}</style><div class="ac-wrap"><div class="iso-stage" tabindex="0" role="slider" aria-label="Pressure ratio: left and right arrows change it" aria-valuemin="1.5" aria-valuemax="9.5" aria-valuenow="7.3">${svg}</div><div class="ac-chips" aria-hidden="true"></div></div>
<div class="ac-controls"><span class="ac-label">Machines</span><div class="ac-seg" role="group" aria-label="Machine efficiency"><button type="button" data-mode="ideal" aria-pressed="true">Ideal</button><button type="button" data-mode="real" aria-pressed="false">Realistic</button></div><label class="ac-toggle"><input type="checkbox" data-values checked> Values on the drawing</label></div>
<div class="ic-chart" data-chart></div>
<div class="ac-compare" data-compare></div>`,
});
const page = k.pageHtml({ title: "Ideal air cycle", theme: THEME, body, script: kitScript() + latheScript + LIVE, width: 760 });
const name = THEME === "light" ? "ideal-cycle-light.html" : "ideal-cycle.html";
writeFileSync(join(HERE, name), page);
console.log("wrote", name, `${(page.length / 1024).toFixed(0)} KB`, `${R.items.length} items`, `scale ${KS.toFixed(3)}`);
A.auditOrExit(R, P, {});

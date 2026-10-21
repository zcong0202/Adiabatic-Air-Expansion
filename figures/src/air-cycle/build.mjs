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
  [...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [0, 0, 95], [124, 0, 95], [-172, -12, 56], [-136, 46, 7], [176, 26, 97], [184, -28, 48], [-104, YC, 91]],
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

// ---------- 1. compressor ----------
box("comp.skid", [-198, -36, 0], [-124, 26, 4], { tone: "lo" }, { r: 1.5 });
const vents = Array.from({ length: 6 }, (_, i) => {
  const x0 = -184 + i * 8;
  return path3([[x0, 20, 12], [x0 + 4, 20, 12], [x0 + 4, 20, 28], [x0, 20, 28]], true);
}).join("");
box("comp.housing", [-192, -30, 4], [-130, 20, 34], { tone: "mid" }, {
  r: 2, steps: 4, bevel: 0.8,
  inner: Ln(k.sideSeam({ x: -192, y: -30, w: 62, d: 50, r: 2 }, 9, P, 4), { tone: "faint" }),
  extra: Ln(vents, { tone: "faint" }) + Dots([at([-188, 20, 31]), at([-134, 20, 31]), at([-188, 20, 7]), at([-134, 20, 7])], { size: 0.45 }),
});
cyl("comp.motor", -172, -10, 10, 34, 18, { tone: "mid" }, {
  steps: 48, bevel: 0.6,
  extra: Ln(k.knurl(-172, -10, 10, 36, 50, 36, P, 0.3), { tone: "lo" }) + Ln(k.sideArc(-172, -10, 10, 36, P, 32) + k.sideArc(-172, -10, 10, 50, P, 32), { tone: "faint" }),
});
cyl("comp.motorcap", -172, -10, 6, 52, 3, { tone: "mid" }, { steps: 32, extra: Dots([at([-172, -10, 55])], { size: 0.5, tone: "hi" }) });
box("comp.guard", [-160, -26, 34], [-140, 4, 44], { tone: "mid" }, { r: 4, steps: 5, bevel: 0.5, extra: Ln(k.planOutline({ x: -157, y: -23, w: 14, d: 24, r: 3 }, 44, P, 5), { tone: "faint" }) });
cyl("comp.filter", -184, 10, 5, 34, 7, { tone: "mid" }, { steps: 32, extra: Ln(k.knurl(-184, 10, 5, 35, 40, 22, P, 0.3), { tone: "lo" }) + Ln(k.sideArc(-184, 10, 5, 35, P, 24) + k.sideArc(-184, 10, 5, 40, P, 24), { tone: "faint" }) });
cyl("comp.filtercap", -184, 10, 3.4, 41, 1.6, { tone: "mid" }, { steps: 24, extra: Dots([at([-184, 10, 42.6])], { size: 0.45, tone: "hi" }) });
box("socket", [-142, 38, 0], [-130, 46, 7], { tone: "mid" }, { r: 1, bevel: 0.4, extra: Ln(k.planOutline({ x: -139.5, y: 40, w: 7, d: 4, r: 1 }, 7, P, 3), { tone: "faint" }) + Dots([at([-140.4, 42, 7]), at([-131.6, 42, 7])], { size: 0.45 }) });
cyl("comp.gaugepost", -142, 12, 2.4, 34, 3, { tone: "mid" }, { steps: 16 });
cyl("comp.gauge", -142, 12, 6.5, 37, 4, { tone: "hi", crease: "lo" }, {
  steps: 48, extra: dial(-142, 12, 6.5, 37, 4, { ticks: 30, every: 5 }) + Ln(needle(-142, 12, 4.4, 41, -0.75 * Math.PI + 1.5 * Math.PI * 0.76), { tone: "hi", free: "start" }),
});

// ---------- 2. aftercooler ----------
const AC = { x: -116, y: -24, w: 24, d: 40 };
const fins = Array.from({ length: 11 }, (_, i) => k.lineOnTop([AC.x + 2 + i * 2, AC.y + 0.6], [AC.x + 2 + i * 2, AC.y + AC.d - 0.6], 30, P)).join("");
box("cooler", [AC.x, AC.y, 0], [AC.x + AC.w, AC.y + AC.d, 30], { tone: "mid" }, {
  r: 0.6, steps: 2, bevel: 0.4,
  extra: Ln(fins, { tone: "lo" }) + Ln(k.ring(-104, 16, 7, 0, P, 1), { tone: "faint" }) + Ln(path3(Array.from({ length: 33 }, (_, i) => [-104 + 7 * Math.cos((i / 32) * 2 * Math.PI), 16, 15 + 7 * Math.sin((i / 32) * 2 * Math.PI)]), true), { tone: "lo" }) +
    Ln(path3(Array.from({ length: 33 }, (_, i) => [-104 + 4.6 * Math.cos((i / 32) * 2 * Math.PI), 16, 15 + 4.6 * Math.sin((i / 32) * 2 * Math.PI)]), true), { tone: "faint" }),
});

// ---------- 3. receiver tank ----------
cyl("tank.stand", -70, YC, 18, 0, 5, { tone: "lo" }, { steps: 56 });
cyl("tank.shell", -70, YC, 16, 5, 54, { tone: "hi", crease: "lo" }, {
  steps: 72, bevel: 0.8,
  extra: Ln(k.sideArc(-70, YC, 16, 17, P, 48) + k.sideArc(-70, YC, 16, 47, P, 48), { tone: "faint" }) + Ln(k.ring(-70, YC, 13.4, 59, P, 64), { tone: "faint" }) + Dots([0, 1, 2, 3, 4, 5].map((i) => at([-70 + 14.6 * Math.cos(i * Math.PI / 3 + 0.3), YC + 14.6 * Math.sin(i * Math.PI / 3 + 0.3), 59])), { size: 0.45 }),
});
cyl("tank.valve", -70, -15, 1.8, 59, 4, { tone: "mid" }, { steps: 16 });
cyl("tank.valvecap", -70, -15, 2.8, 63, 2, { tone: "mid" }, { steps: 20 });
for (const x of [-75, -65]) cyl(`tank.port${x}`, x, YC, 3.6, 59, 2, { tone: "mid" }, { steps: 24 });

// ---------- 4. regulator ----------
box("reg.body", [-36, -14, 0], [-14, 6, 20], { tone: "mid" }, { r: 1.2, bevel: 0.6, extra: Dots([at([-34, 6, 18]), at([-16, 6, 18]), at([-34, 6, 2]), at([-16, 6, 2])], { size: 0.45 }) });
cyl("reg.port", -30, YC, 3.6, 20, 1.6, { tone: "mid" }, { steps: 24 });
cyl("reg.knob", -20, -3, 4.6, 20, 5, { tone: "mid" }, { steps: 32, extra: Ln(k.knurl(-20, -3, 4.6, 20, 25, 24, P), { tone: "lo" }) + Ln(k.lineOnTop([-20, -3], [-16.4, -3], 25, P), { tone: "hi", free: "end" }) });

// ---------- 5. manifold, motors, couplings, generators ----------
box("manifold", [-6, -42, 2], [6, 42, 24], { tone: "mid" }, {
  r: 1, bevel: 0.6,
  inner: Ln(k.sideSeam({ x: -6, y: -42, w: 12, d: 84, r: 1 }, 13, P, 3), { tone: "faint" }),
  extra: Dots([-38, -20, 20, 38].map((y) => at([0, y, 24])), { size: 0.45 }),
});
cyl("manifold.port", 0, 0, 6.4, 24, 1.6, { tone: "mid" }, { steps: 32 });
const COUPLING = [];
MOTOR_Y.forEach((y, i) => {
  const F = G.frameOf([6, y, AXZ], [1, 0, 0], [0, 1, 0], [0, 0, 1]);
  const motor = [[0, 4.6], [2, 4.6], [2, 5.6], [24, 5.6], [24, 4.8], [26, 4.8]];
  const ribs = G.ribsOf(F, 3.5, 22.5, 5.6, 22, P, { fade: [0.1, 0.55], seams: true });
  turned(`motor${i}`, F, motor, { tone: "hi", lit: false }, { extra: k.fadedSvg(ribs, { tone: "lo" }), owner: `motor${i}` });
  turned(`shaft${i}`, F, [[26, 1.8], [31, 1.8]], { tone: "mid" }, { owner: `motor${i}` });
  turned(`coupling${i}`, F, [[31, 4.2], [36, 4.2]], { tone: "mid" }, { owner: `motor${i}`, extra: `<g data-part="spin${i}"></g>` });
  COUPLING.push({ o: F.o, s0: 31, s1: 36, r: 4.2 });
  turned(`gen${i}`, F, [[36, 6.6], [37, 8], [59, 8], [60, 6.6]], { tone: "mid" }, {
    owner: `motor${i}`,
    extra: k.fadedSvg(G.ribsOf(F, 38, 58, 8, 30, P, { fade: [0.1, 0.55], seams: true }), { tone: "lo" }),
  });
  box(`genfoot${i}`, [46, y - 5, 0], [56, y + 5, 2.2], { tone: "lo" }, { r: 0.6, owner: `motor${i}` });
});
box("busbar", [66, -40, 2], [68.5, 40, 18], { tone: "mid" }, { r: 0.6, extra: Dots(MOTOR_Y.map((y) => at([68.5, y, 15])), { size: 0.5, tone: "hi" }) });

// ---------- 6. load bank ----------
const LB = { x: 80, y: -24, w: 26, d: 48 };
const slots = Array.from({ length: 5 }, (_, i) => {
  const x0 = LB.x + 3 + i * 4.6;
  return path3([[x0, LB.y + LB.d, 4], [x0 + 2, LB.y + LB.d, 4], [x0 + 2, LB.y + LB.d, 18], [x0, LB.y + LB.d, 18]], true);
}).join("");
const KNOB = [93, 10];
const loadTicks = k.radialTicks(KNOB[0], KNOB[1], 9.4, 10, 5, 22, [0.9, 1.8], P, -0.75 * Math.PI, 1.5 * Math.PI);
box("load.bank", [LB.x, LB.y, 0], [LB.x + LB.w, LB.y + LB.d, 22], { tone: "mid" }, {
  r: 1.2, bevel: 0.6,
  extra: Ln(slots, { tone: "faint" }) + Ln(k.ring(KNOB[0], KNOB[1], 10.4, 22, P, 48), { tone: "lo" }) + Ln(loadTicks.minor, { tone: "lo" }) + Ln(loadTicks.major, { tone: "mid" }) + Dots([at([LB.x + 3, LB.y + 3, 22]), at([LB.x + 3, LB.y + LB.d - 3, 22])], { size: 0.45 }),
});
cyl("load.knob", KNOB[0], KNOB[1], 5.4, 22, 5, { tone: "mid" }, {
  steps: 36, extra: Ln(k.knurl(KNOB[0], KNOB[1], 5.4, 22, 27, 28, P), { tone: "lo" }) + `<path data-part="knob" class="iso-line" data-tone="hi" data-free="end" d=""/>`,
});
for (const y of [-6, 4]) pipe(`cable${y}`, [[68.5, y, 9], [80, y, 9]], 0.8, { tone: "mid" });

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
cyl("hanger.base", 74, 0, 3.6, 0, 1.6, { tone: "lo" }, { steps: 24 });
cyl("hanger.post", 74, 0, 1.5, 1.6, 81.4, { tone: "mid" }, { steps: 16, extra: Ln(k.sideArc(74, 0, 1.5, 30, P, 12) + k.sideArc(74, 0, 1.5, 60, P, 12), { tone: "faint" }) });
box("hanger.cradle", [71, -5, 83], [77, 5, 85], { tone: "mid" }, { r: 0.8, steps: 3, bevel: 0.3 });
cyl("therm.base", 184, -28, 4, 0.6, 2, { tone: "lo" }, { steps: 24 });
cyl("therm.post", 184, -28, 1.6, 2.6, 37.4, { tone: "mid" }, { steps: 16 });
cyl("therm.dial", 184, -28, 9, 40, 5, { tone: "hi", crease: "lo" }, {
  steps: 64, bevel: 0.5,
  extra: dial(184, -28, 9, 40, 5, { ticks: 50, every: 10 }) + `<path data-part="needle" class="iso-line" data-tone="lit" data-free="start" style="stroke-width:1.1" d=""/>`,
});

// ---------- pipes and the cold duct ----------
pipe("p.cooler", [[-130, YC, 18], [-116, YC, 18]], 2.4);
pipe("p.tankin", [[-104, YC, 30], [-104, YC, 88], [-75, YC, 88], [-75, YC, 61]], 2.4, { bend: 6 });
pipe("p.tankout", [[-65, YC, 61], [-65, YC, 88], [-30, YC, 88], [-30, YC, 21.6]], 2.4, { bend: 6 });
pipe("p.feed", [[-14, YC, 8], [-6, YC, 8]], 2.4);
pipe("cable.power", [[-136, 20, 12], [-136, 28, 12], [-136, 28, 3.5], [-136, 38, 3.5]], 0.9, { tone: "mid", bend: 3, limp: true });
const DUCT = [[0, 0, 25.6], [0, 0, 90], [121, 0, 90]];
{
  const FF = G.frameOf([121, 0, 90], [1, 0, 0], [0, 1, 0], [0, 0, 1]);
  turned("duct.flange", FF, [[0, 7.2], [3, 7.2]], { tone: "mid" }, { extra: Dots(G.dotsOf(FF, 0, 5.9, 8, P, { fade: [0.04, 0.42] }), { size: 0.45 }) });
}
pipe("duct", DUCT, DUCT_R, { bend: 13, rings: { pitch: 3.2, fade: [0.1, 0.55] }, maxLength: 16, touch: ["hanger.cradle", "hanger.post"] });

A.settle(R, P);
R.items.sort((a, b) => a.key - b.key);
const indexOf = (name) => R.items.findIndex((item) => item.name === name);
const coldSlot = Math.max(indexOf("chair.seat"), indexOf("chair.back"));
const groups = R.items.map((item, index) => `<g class="it" data-name="${item.name}">${item.svg}</g>${index === coldSlot ? '<g data-part="cold"></g>' : ""}`);

const svg = k.figureSvg({
  width: W,
  height: H,
  label:
    "A bench model of the air-cycle seat. From left: a compressor, a finned aftercooler, a receiver tank, a regulator, a manifold feeding four vane air motors, each turning a generator through a coupling. The generators feed a load bank with a load knob. The motors' cold exhaust leaves the manifold through an insulated duct that rises to a diffuser above a chair; a thermometer beside the chair reads the outlet temperature.",
  body: [...back, `<g>${groups.join("")}</g>`],
});

// value callouts: a dot on the part, a leader, and a chip on a rail above or below the bench
const CALL = [
  { key: "comp", at: [-160, -6, 44], rail: "top", chars: 27 },
  { key: "tank", at: [-70, YC, 59], rail: "top", chars: 20 },
  { key: "outlet", at: [150, 0, 96], rail: "top", chars: 27 },
  { key: "cooler", at: [-104, -4, 30], rail: "top", chars: 10 },
  { key: "reg", at: [-25, 6, 12], rail: "bottom", chars: 23 },
  { key: "motors", at: [20, 30, 15.6], rail: "bottom", chars: 30 },
  { key: "load", at: [93, 24, 12], rail: "bottom", chars: 12 },
  { key: "seat", at: [158, 15, 33], rail: "bottom", chars: 21 },
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
const DATA = { W, H, calls: calls.map(({ key, sx, sy, cx, cy, rail }) => ({ key, sx, sy, cx, cy, rail })), P, couplings: COUPLING, knob: KNOB, therm: [184, -28, 45], diff: { x0: 144, x1: 165, y0: -15, y1: 15, top: 84, floor: 34 } };
const latheSource = readFileSync(join(HERE, "..", "..", "kit", "lathe.mjs"), "utf8").replace(/^import .*$/m, "").replace(/^export /gm, "");
const latheScript = `const G = (() => {${latheSource}\nreturn { frameOf, ribsOf, fadeOf };})();\n`;
const LIVE = readFileSync(join(HERE, "live.js"), "utf8").replace("__DATA__", JSON.stringify(DATA));

const body = k.plateHtml({
  fig: "Fig 1",
  title: "Air-cycle seat",
  hint: "Move across to set the generator load",
  readout: "7.6 bar · load 100 % · outlet 0.8 °C · 2.29 kW",
  keys: [
    { mark: "lit", label: "Thermometer needle: air temperature leaving the diffuser" },
    { mark: "raised", label: "Four vane air motors: the shaft work they give up is what cools the air" },
    { mark: "flat", label: "Load knob: how much work the generators take off the shafts" },
  ],
  caption:
    "Compressed air at 6.3 bar(g) drives four vane air motors (Atlas Copco LZB46, 843 W each at 16.2 L/s). Each turns a generator and the load bank burns off what they make. At 100 % load the shafts take out 3.4 kW, so 78 g/s of air reaches the seat at about 1 °C: 2.3 kW of cooling on a 30 °C day. Turn the load down and the motors spin freely and do no work, so the air only throttles and comes out warmer than the day. Switch the supply to 200 bar: the motors still run at 6.3 bar, so the regulator throws the extra pressure away. Throttling 200 to 6.3 bar does cool the air by about 30 K, but compressing to 200 bar costs about 1,100 kJ per kg against 300 kJ at 7.6 bar, so the electricity rises 3.7 times and the COP falls from 0.10 to 0.05. Values are calculated with an ideal-gas model, not measured.",
  body: `<style>${readFileSync(join(HERE, "air-cycle.css"), "utf8")}</style><div class="ac-wrap"><div class="iso-stage" tabindex="0" role="slider" aria-label="Generator load: left and right arrows change it" aria-valuemin="0" aria-valuemax="100" aria-valuenow="100">${svg}</div><div class="ac-chips" aria-hidden="true"></div></div>
<div class="ac-controls"><span class="ac-label">Supply</span><div class="ac-seg" role="group" aria-label="Supply pressure"><button type="button" data-mode="low" aria-pressed="true">7.6 bar compressor</button><button type="button" data-mode="high" aria-pressed="false">200 bar compressor</button></div><label class="ac-toggle"><input type="checkbox" data-values checked> Values on the drawing</label></div>
<div class="ac-compare" data-compare></div>`,
});
const page = k.pageHtml({ title: "Air-cycle seat", theme: THEME, body, script: kitScript() + latheScript + LIVE, width: 760 });
const name = THEME === "light" ? "air-cycle-light.html" : "air-cycle.html";
writeFileSync(join(HERE, name), page);
console.log("wrote", name, `${(page.length / 1024).toFixed(0)} KB`, `${R.items.length} items`, `scale ${KS.toFixed(3)}`);
A.auditOrExit(R, P, {});

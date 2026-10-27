// ---------- page 2: the plant, drawn with the anatomy kit ----------
// One pure function of a spec (stage counts, machine types, powers) that returns the SVG.
// World units are centimetres, so a 175 cm person stands at true scale
// beside machines sized from their power. Runs in a Web Worker on the page and in Node
// for the geometry audit (explorer/plant/audit.mjs).
import * as k from "../kit/iso-kit.mjs";
import * as G from "../kit/lathe.mjs";
import { tubePieces, tubeSvg } from "../kit/tube.mjs";
import * as A from "../kit/audit.mjs";

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const f2 = v => Math.round(v * 100) / 100;

// Rough sizes until step 9.5 replaces them with product data.
// The drawing caps each factor so the scene stays legible; raw holds the uncapped factors,
// which the size table uses, so the listed dimensions keep following the flow.
export function sizes(spec) {
  const raw = {
    fc: Math.cbrt(Math.max(spec.kwC, 0.5) / 15),    // compressor frame, 1 at 15 kW
    fd: Math.cbrt(Math.max(spec.flow, 0.01) / 0.078), // flow-sized parts
    ft: Math.cbrt(Math.max(spec.kwT, 0.2) / 6),     // turbine frame
  };
  const fc = clamp(raw.fc, 0.65, 1.9), fd = clamp(raw.fd, 0.7, 1.6), ft = clamp(raw.ft, 0.6, 1.6);
  return { fc, fd, ft, raw, capped: raw.fc > 1.9 || raw.fd > 1.6 || raw.ft > 1.6 };
}

// Particles riding each flow path at a steady screen speed (px/s), spaced gap px apart:
// red compression heat, yellow shaft work and electricity, blue cooling. SMIL animateMotion,
// so the drawing animates on its own once it is on the page.
function flowSvg(flows, at) {
  const groups = { heat: [], work: [], cold: [] };
  flows.forEach(([kind, points, { gap = 20, speed = 55, fade = false } = {}], index) => {
    const xy = points.map(at);
    let L = 0;
    for (let i = 1; i < xy.length; i++) L += Math.hypot(xy[i][0] - xy[i - 1][0], xy[i][1] - xy[i - 1][1]);
    if (L < 4) return;
    const id = `flow${index}`, n = Math.max(2, Math.round(L / gap)), dur = (L / speed).toFixed(2);
    const out = groups[kind];
    out.push(`<path id="${id}" d="M${xy.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join("L")}" fill="none" stroke="none"/>`);
    for (let j = 0; j < n; j++) {
      const begin = `-${(dur * j / n).toFixed(2)}s`;
      const fadeAnim = fade ? `<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.4;1" dur="${dur}s" begin="${begin}" repeatCount="indefinite"/>` : "";
      out.push(`<g class="fp"><circle r="4.2" class="fh"/><circle r="1.7"/><animateMotion dur="${dur}s" begin="${begin}" repeatCount="indefinite"><mpath href="#${id}"/></animateMotion>${fadeAnim}</g>`);
    }
  });
  return Object.entries(groups).map(([kind, out]) => `<g class="flow" data-flow="${kind}" aria-hidden="true">${out.join("")}</g>`).join("");
}

export function buildPlant(spec, { width = 1200, height = 640 } = {}) {
  const { fc, fd, ft, raw, capped } = sizes(spec);
  const iso = spec.nComp === "iso";
  const nC = iso ? 5 : spec.nComp;
  const nE = spec.nExp;
  const atPlant = spec.rec === "shaft";
  const coil = nE > 1 && spec.reheat;

  // ---------- layout (cm) ----------
  const AX = 34 * fc;                  // shaft height
  const MOT = { x0: 0, len: 52 * fc, r: 19 * fc };
  const PITCH = 44 * fc;
  const CASE = { x: MOT.len + 12 * fc, y: -24 * fc, w: nC * PITCH + 12 * fc, d: 48 * fc, r: 3 };
  const CASE_H = 44 * fc;
  const stageX = i => CASE.x + 6 * fc + (i + 0.5) * PITCH;
  const stageR = i => 14 * fc * Math.max(0.42, Math.pow(spec.stageRatio || 2, -i / 2));
  const BAR_H = 34 * fc;
  const caseEnd = CASE.x + CASE.w;
  const CY0 = CASE.y + CASE.d + 24 * fc, CD = 20 * fc;  // cooler row in front
  const CH = clamp(Math.sqrt(Math.max(spec.duty, 0.5) / 25 / nC) * 100, CASE_H + 18, 110); // face from 25 kW per m²
  // head plates at least 18 cm wide so each stage's inlet and outlet ports sit far enough apart
  // for the cooler between two stages to span from one stage's outlet to the next one's inlet
  const headW = i => Math.max(stageR(i) + 2, 9);
  const outX = i => stageX(i) + headW(i) - 3.6, inX = i => stageX(i) - headW(i) + 3.6;
  const coolX = i => [outX(i) - 3.6, (i < nC - 1 ? inX(i + 1) : outX(i) + 44 * fc) + 3.6];
  let x = caseEnd + 26;
  const TURB_P = atPlant ? { x0: caseEnd + 14 * ft, y: 0 } : null;
  if (atPlant) x = caseEnd + 14 * ft + nE * 30 * ft + 40;
  const DRY = { x: Math.max(x, coolX(nC - 1)[1] + 40), yc: CY0 + CD / 2 };
  const dryW = spec.dryer === "desiccant" ? 64 * fd : spec.dryer === "fridge" ? 56 * fd : 0;
  const plantEnd = DRY.x + dryW + 70;
  const GAP0 = plantEnd + 30, GAP1 = GAP0 + 70;     // floor break between the plant room and the seats
  const SEAT0 = GAP1 + 60;
  const TS = { x: SEAT0, y: -150 };                  // turbine skid at the seats
  const nN = clamp(spec.nNozzle, 1, 5);
  const SEATX = i => SEAT0 + 150 + i * 90;
  const seatEnd = SEATX(nN - 1) + 120;
  const FLOOR_P = { x: -170, y: -230, w: plantEnd + 170, d: CY0 + CD + 120 + 230, r: 10 };
  const FLOOR_S = { x: GAP1, y: -230, w: seatEnd - GAP1 + 60, d: 470, r: 10 };
  const HEADER_Y = 40;
  const RT = 13 * ft, TZ = Math.max(RT + 2, 16);      // turbine casing radius; axis height on the seat skid

  const W = width, H = height;
  const P = k.fitProjection([
    ...k.boxCorners(FLOOR_P, -12, 0), ...k.boxCorners(FLOOR_S, -12, 0),
    [SEATX(0), HEADER_Y, 262], [-120, CY0, 200], [TS.x, TS.y, 120],
  ], W, H, { pad: 18, azimuth: 52, elevation: 30 });
  const at = p => k.iso(p, P);
  const S = (paths, style) => k.solidSvg(paths, style);
  const Ln = (d, style) => k.lineSvg(d, style);
  const Dots = (points, style) => k.dotsSvg(points, style);
  const R = A.recorder(P);
  const record = R.solid;
  const put = (name, ref, svg, shapes = [], { bias = 0, ...rest } = {}) => R.put({ name, at: ref, bias, svg, shapes, piece: "plant", ...rest });
  function box(name, [x0, y0, z0], [x1, y1, z1], style = {}, { r = 0.8, steps = 3, bevel = 0.5, extra = "", inner = "", bias = 0, owner } = {}) {
    const plan = { x: x0, y: y0, w: x1 - x0, d: y1 - y0, r };
    const shape = record(A.slab(plan, z0, z1 - z0, { name, owner }, steps));
    put(name, [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2], S(k.slabOf(plan, z0, z1 - z0, P, steps, bevel), { tone: "mid", ...style, inner }) + extra, [shape], { bias });
    return plan;
  }
  function cyl(name, cx, cy, r, z, h, style = {}, { steps = 32, bevel = 0, extra = "", inner = "", bias = 0, owner } = {}) {
    const shape = record(A.cylinder(cx, cy, r, z, h, { name, owner }));
    put(name, [cx, cy, z + h / 2], S(k.cylinder(cx, cy, r, z, h, P, steps, bevel), { tone: "mid", ...style, inner }) + extra, [shape], { bias });
  }
  function turned(name, F, profile, style = {}, { extra = "", inner = "", bias = 0, owner } = {}) {
    const paths = G.solidOf(profile, F, P, {});
    const mid = (profile[0][0] + profile[profile.length - 1][0]) / 2;
    const shape = record(A.solid(F, profile, { name, owner }));
    put(name, G.add3(F.o, G.mul3(F.a, mid)), S(paths, { tone: "mid", ...style, inner }) + extra, [shape], { bias });
  }
  function pipe(name, points, r, { tone = "hi", bend, rings, maxLength = 40, bias = 0.05, limp = false, touch } = {}) {
    const route = G.fillet(points, bend ?? Math.max(4, r * 3), 10, { P, tube: r });
    R.route(name, route, r, { limp, touch, piece: "plant" });
    tubePieces(route, r, P, { maxLength, spacing: Math.max(0.8, Math.min(2, r)), ...(rings ? { rings } : {}) }).forEach((piece, index) =>
      put(`${name}:${index}`, piece.mid, tubeSvg(piece, { tone }), [A.tube(piece.points, piece.radii)], { bias, route: name, chunk: index }));
    return route;
  }
  const XF = (x0, y0, z0) => G.frameOf([x0, y0, z0], [1, 0, 0], [0, 1, 0], [0, 0, 1]);
  const ZF = (x0, y0, z0) => G.frameOf([x0, y0, z0], [0, 0, 1], [1, 0, 0], [0, 1, 0]);
  const DOWN = (x0, y0, z0) => G.frameOf([x0, y0, z0], [0, 0, -1], [1, 0, 0], [0, -1, 0]);
  const seg = (a, b) => { const [x0, y0] = at(a), [x1, y1] = at(b); return `M${x0.toFixed(2)} ${y0.toFixed(2)}L${x1.toFixed(2)} ${y1.toFixed(2)}`; };
  const calls = [];
  // energy flows drawn as moving particles over the drawing: [kind, world points, options]
  const flows = [];
  const flow = (kind, points, opts = {}) => { flows.push([kind, points, opts]); };
  const call = (key, p) => { const [sx, sy] = at(p); calls.push({ key, sx: f2(sx / W * 100), sy: f2(sy / H * 100) }); };

  // ---------- floors ----------
  const back = [];
  for (const [name, F] of [["stand.floorP", FLOOR_P], ["stand.floorS", FLOOR_S]]) {
    back.push(`<path class="iso-halo" d="${k.haloOf(F, -12, 12, P)}"/>`);
    back.push(S(k.slabOf(F, -12, 12, P, 8, 1.2), { tone: "lo", inner: Ln(k.sideSeam(F, -5, P, 8), { tone: "faint" }) }));
    back.push(Ln(k.planOutline(k.insetPlan(F, 8), 0, P, 8), { tone: "faint" }));
    record(A.slab(F, -12, 12, { name, ground: true }, 8));
  }

  // ---------- motor and compressor ----------
  box("motor.foot", [MOT.x0 + 4, -14 * fc, 0], [MOT.len - 4, 14 * fc, AX - MOT.r], { tone: "lo" }, { r: 1 });
  turned("motor", XF(MOT.x0, 0, AX), [[0, MOT.r * 0.85], [2, MOT.r], [MOT.len - 2, MOT.r], [MOT.len, MOT.r * 0.85]], { tone: "mid" },
    { extra: k.fadedSvg(G.ribsOf(XF(MOT.x0, 0, AX), 4, MOT.len - 4, MOT.r, 18, P, { fade: [0.1, 0.55], seams: true }), { tone: "lo" }) });
  box("motor.terminal", [MOT.len * 0.35, -8 * fc, AX + MOT.r], [MOT.len * 0.65, 8 * fc, AX + MOT.r + 9 * fc], { tone: "mid" }, { r: 1 });
  turned("motor.coupling", XF(MOT.len, 0, AX), [[0, 6 * fc], [CASE.x - MOT.len, 6 * fc]], { tone: "mid" });
  call("motor", [MOT.len / 2, 0, AX + MOT.r + 9 * fc]);
  box("crankcase", [CASE.x, CASE.y, 0], [caseEnd, CASE.y + CASE.d, CASE_H], { tone: "mid" }, {
    r: 3, steps: 4, bevel: 0.8, inner: Ln(k.sideSeam(CASE, CASE_H * 0.3, P, 4), { tone: "faint" }),
    extra: Dots(k.corners(CASE, 5).map(([a, b]) => at([a, b, CASE_H])), { size: 0.5 }),
  });
  for (let i = 0; i < nC; i++) {
    const sx = stageX(i), r = stageR(i), top = CASE_H + BAR_H;
    cyl(`stage${i}.barrel`, sx, 0, r, CASE_H, BAR_H - 6, { tone: "hi", crease: "lo" }, {
      steps: 40, extra: Ln(k.knurl(sx, 0, r, CASE_H + 3, top - 9, Math.max(8, Math.round(r * 1.6)), P, 0.3), { tone: "lo" }),
    });
    const hw = headW(i), hd = r + 2;
    box(`stage${i}.head`, [sx - hw, -hd, top - 6], [sx + hw, hd, top], { tone: "mid" }, {
      r: 2, steps: 3, extra: Dots(k.corners({ x: sx - hw, y: -hd, w: 2 * hw, d: 2 * hd }, 2.5).map(([a, b]) => at([a, b, top])), { size: 0.45 }),
    });
    cyl(`stage${i}.out`, outX(i), 0, 3.2, top, 2, { tone: "mid" }, { steps: 20 });
    if (i > 0) cyl(`stage${i}.in`, inX(i), 0, 3.2, top, 2, { tone: "mid" }, { steps: 20 });
  }
  call(iso ? "stagesIso" : "stages", [stageX(0), 0, CASE_H + BAR_H]);

  // ---------- coolers (one after every stage) and heat rejection ----------
  for (let i = 0; i < nC; i++) {
    const [x0, x1] = coolX(i);
    const fins = Array.from({ length: Math.floor((x1 - x0 - 6) / 3) + 1 }, (_, j) => seg([x0 + 3 + j * 3, CY0 + CD, 4], [x0 + 3 + j * 3, CY0 + CD, CH - 4])).join("");
    const plan = { x: x0, y: CY0, w: x1 - x0, d: CD, r: 1 };
    box(`cooler${i}`, [x0, CY0, 0], [x1, CY0 + CD, CH], { tone: "mid" }, {
      r: 1, steps: 2, inner: Ln(k.sideSeam(plan, 4, P, 2) + k.sideSeam(plan, CH - 4, P, 2), { tone: "faint" }), extra: Ln(fins, { tone: "lo" }),
    });
    for (const px of [x0 + 3.6, x1 - 3.6])
      cyl(`cooler${i}.port${Math.round(px)}`, px, CY0 + CD / 2, 3.2, CH, 2, { tone: "mid" }, { steps: 20 });
    if (spec.cooling === "air") {
      // fan between the two ports
      const cx = (x0 + x1) / 2, cy = CY0 + CD / 2, rf = Math.max(3, Math.min(CD * 0.4, (x1 - x0) / 2 - 8.5));
      cyl(`cooler${i}.fan`, cx, cy, rf, CH, 3, { tone: "mid" }, { steps: 28, extra: Ln(k.ring(cx, cy, rf * 0.45, CH + 3, P, 16), { tone: "lo" }) });
    }
  }
  call("coolers", [(coolX(0)[0] + coolX(nC - 1)[1]) / 2, CY0 + CD, CH * 0.5]);
  // compression heat leaves each cooler's front face (to the hot-water loop or the sea)
  for (let i = 0; i < nC; i++) {
    const [x0, x1] = coolX(i);
    for (const u of [0.3, 0.7]) {
      const cx = x0 + (x1 - x0) * u;
      flow("heat", [[cx, CY0 + CD, CH * 0.6], [cx, CY0 + CD + 40, CH * 0.35], [cx, CY0 + CD + 110, 4]], { gap: 26, speed: 34, fade: true });
    }
  }
  const STAGE_TOP = CASE_H + BAR_H + 2;
  for (let i = 0; i < nC; i++) {
    const out = outX(i), lift = Math.max(STAGE_TOP, CH) + 24 + (nC - i) * 32 * fc;
    flow("heat", pipe(`p.s${i}`, [[out, 0, STAGE_TOP], [out, 0, lift], [out, CY0 + CD / 2, lift], [out, CY0 + CD / 2, CH + 2]], 2.4, { bend: 9 }));
    if (i < nC - 1) {
      const inn = inX(i + 1), l2 = lift - 6;
      pipe(`p.i${i}`, [[inn, CY0 + CD / 2, CH + 2], [inn, CY0 + CD / 2, l2], [inn, 0, l2], [inn, 0, STAGE_TOP]], 2.4, { bend: 9 });
    }
  }
  // seawater cooling is not drawn: the coolers' callout names it
  if (spec.cooling === "tower") {
    const xe = coolX(0)[0];
    const rT = clamp(40 * Math.sqrt(Math.max(spec.duty, 1) / 50), 30, 85), hT = 170, tx = -60 - rT, ty = CY0 + CD / 2;
    const F = ZF(tx, ty, 0);
    turned("tower", F, [[0, rT], [hT * 0.75, rT * 0.86], [hT, rT * 0.86]], { tone: "mid" }, {
      extra: k.fadedSvg(G.ribsOf(F, 10, hT * 0.55, rT * 0.98, 36, P, { fade: [0.1, 0.55], seams: true, r1: rT * 0.9 }), { tone: "lo" }),
    });
    turned("tower.stack", ZF(tx, ty, hT), [[0, rT * 0.6], [16, rT * 0.62]], { tone: "mid" }, { extra: Ln(k.ring(tx, ty, rT * 0.3, hT + 16, P, 32), { tone: "lo" }) });
    const rAt = z => rT * (1 - 0.14 * z / (hT * 0.75));
    for (const [z, n] of [[14, "sup"], [30, "ret"]]) pipe(`p.cw.${n}`, [[tx + rAt(z) - 0.05, ty, z], [xe, ty, z]], 3, { tone: "mid", bend: 6 });
    call("tower", [tx, ty, hT + 16]);
  }

  // ---------- heat recovery behind the compressor ----------
  if (spec.heat === "absorption" || spec.heat === "orc") {
    const kw = spec.heat === "absorption" ? spec.kwAbs : spec.kwOrc * 10;
    const V = clamp(spec.heat === "absorption" ? 0.04 * kw : 0.03 * kw, 0.35, 6) * 1e6; // cm³
    const b = Math.cbrt(V / 0.84), bx0 = CASE.x, by1 = CASE.y - 40, by0 = by1 - 0.6 * b;
    box("hr.cabinet", [bx0, by0, 0], [bx0 + b, by1, 1.1 * b], { tone: "mid" }, { r: 2, steps: 3, inner: Ln(k.sideSeam({ x: bx0, y: by0, w: b, d: 0.6 * b, r: 2 }, 0.55 * b, P, 3), { tone: "faint" }) });
    if (spec.heat === "absorption") {
      for (const [j, rr] of [[0, 0.13], [1, 0.11]]) {
        const yy = by0 + 0.6 * b * (0.3 + 0.4 * j);
        turned(`hr.shell${j}`, XF(bx0 + 0.05 * b, yy, 1.1 * b + rr * b), [[0, rr * b * 0.8], [2, rr * b], [0.9 * b - 2, rr * b], [0.9 * b, rr * b * 0.8]], { tone: "hi", crease: "lo" });
      }
    } else {
      turned("hr.expander", XF(bx0 + 0.2 * b, by0 + 0.3 * b, 1.1 * b + 0.12 * b), [[0, 0.1 * b], [0.25 * b, 0.12 * b], [0.4 * b, 0.08 * b]], { tone: "hi", crease: "lo" });
    }
    const hx = CASE.x + 10 * fc;
    flow("heat", pipe("p.hr", [[hx, CASE.y, CASE_H * 0.6], [hx, (by1 + CASE.y) / 2, CASE_H * 0.6], [hx, (by1 + CASE.y) / 2, 20], [hx, by1, 20]], 2.6, { tone: "mid", bend: 8 }));
    call(spec.heat === "absorption" ? "absorber" : "orc", [bx0 + b / 2, (by0 + by1) / 2, 1.1 * b + 0.25 * b]);
  }

  // ---------- expansion turbine train (on the compressor shaft, or on a skid at the seats) ----------
  // side: the inlet is the first stage's end face and the outlet is added on the last stage's side
  function turbineTrain(x0, y0, z, name, { endR = 0, side = false } = {}) {
    const rt = RT, len = 22 * ft;
    for (let j = 0; j < nE; j++) {
      const F = XF(x0 + j * (len + 8 * ft), y0, z);
      turned(`${name}${j}`, F, [[0, rt * 0.6], [3, rt], [len - 3, rt], [len, j === nE - 1 ? Math.max(rt * 0.6, endR) : rt * 0.6]], { tone: "hi", crease: "lo" },
        { extra: Dots(G.dotsOf(F, 3, rt * 0.82, 10, P, { fade: [0.04, 0.42] }), { size: 0.45 }) });
      if (j < nE - 1) turned(`${name}.shaft${j}`, XF(x0 + j * (len + 8 * ft) + len, y0, z), [[0, 3 * ft], [8 * ft, 3 * ft]], { tone: "mid" });
      if (!side || (j > 0 && j < nE - 1)) cyl(`${name}${j}.port`, x0 + j * (len + 8 * ft) + len / 2, y0, 3.2, z + rt - 0.5, 3, { tone: "mid" }, { steps: 20 });
    }
    return { end: x0 + nE * (len + 8 * ft) - 8 * ft, rt, len, top: z + rt + 2.5, port: j => x0 + j * (len + 8 * ft) + len / 2 };
  }

  // ---------- dryer ----------
  const lastOut = coolX(nC - 1)[1] - 3.6;
  let dryIn = null, dryOut = [lastOut, CY0 + CD / 2, CH + 2];
  if (spec.dryer === "fridge") {
    const w = 56 * fd, d = 50 * fd, h = 86 * fd;
    DRY.y = DRY.yc - d / 2;
    const plan = { x: DRY.x, y: DRY.y, w, d, r: 2 };
    const vents = Array.from({ length: 6 }, (_, j) => seg([DRY.x + 8 + j * (w - 16) / 5, DRY.y + d, 12], [DRY.x + 8 + j * (w - 16) / 5, DRY.y + d, h * 0.45])).join("");
    box("dryer", [DRY.x, DRY.y, 0], [DRY.x + w, DRY.y + d, h], { tone: "mid" }, { r: 2, steps: 3, inner: Ln(k.sideSeam(plan, h * 0.55, P, 3), { tone: "faint" }), extra: Ln(vents, { tone: "lo" }) });
    cyl("dryer.in", DRY.x + 12, DRY.yc, 3.2, h, 2, { tone: "mid" }, { steps: 20 });
    dryIn = [DRY.x + 12, DRY.yc, h + 2];
    if (atPlant) { cyl("dryer.out", DRY.x + w - 12, DRY.yc, 3.2, h, 2, { tone: "mid" }, { steps: 20 }); dryOut = [DRY.x + w - 12, DRY.yc, h + 2]; }
    else { turned("dryer.out", G.frameOf([DRY.x + w - 12, DRY.y, TZ], [0, -1, 0], [1, 0, 0], [0, 0, 1]), [[0, 3.2], [3, 3.2]], { tone: "mid" }); dryOut = [DRY.x + w - 12, DRY.y - 3, TZ]; }
    call("dryerF", [DRY.x + w / 2, DRY.yc, h]);
  } else if (spec.dryer === "desiccant") {
    const rr = 12 * fd, h = 130 * fd, cy = DRY.yc, mh = 14 * fd;
    const base = { x: DRY.x, y: cy - rr - mh - 4, w: 64 * fd, d: 2 * rr + 5 + mh + 4, r: 2 };
    DRY.y = base.y; DRY.d = base.d;
    box("dryer.base", [base.x, base.y, 0], [base.x + base.w, base.y + base.d, 8], { tone: "lo" }, { r: 2 });
    const cxs = [base.x + base.w * 0.27, base.x + base.w * 0.73];
    cxs.forEach((cx, j) => turned(`dryer.tower${j}`, ZF(cx, cy, 8), [[0, rr], [h - rr * 0.6, rr, 1], [h - rr * 0.2, rr * 0.7, 1], [h, rr * 0.2]], { tone: "hi", crease: "lo" }));
    // switching manifold behind the twin towers, on the compressor side
    const my = cy - rr - mh / 2, mz = atPlant ? 8 + mh : Math.max(8 + mh, TZ + 7);
    box("dryer.valves", [cxs[0], cy - rr - mh, 8], [cxs[1], cy - rr, mz], { tone: "mid" }, { r: 1 });
    cyl("dryer.in", cxs[0] + 5, my, 3.2, mz, 2, { tone: "mid" }, { steps: 20 });
    dryIn = [cxs[0] + 5, my, mz + 2];
    if (atPlant) { cyl("dryer.out", cxs[1] - 5, my, 3.2, mz, 2, { tone: "mid" }, { steps: 20 }); dryOut = [cxs[1] - 5, my, mz + 2]; }
    else { turned("dryer.out", G.frameOf([cxs[1] - 5, cy - rr - mh, TZ], [0, -1, 0], [1, 0, 0], [0, 0, 1]), [[0, 3.2], [3, 3.2]], { tone: "mid" }); dryOut = [cxs[1] - 5, cy - rr - mh - 3, TZ]; }
    call("dryerD", [(cxs[0] + cxs[1]) / 2, cy, h + 8]);
  }
  if (dryIn) {
    const z = DRY.zp = Math.max(CH + 30, dryIn[2] + 30), y0 = CY0 + CD / 2;
    const pts = [[lastOut, y0, CH + 2], [lastOut, y0, z], [lastOut, dryIn[1], z], [dryIn[0], dryIn[1], z], [dryIn[0], dryIn[1], dryIn[2]]];
    pipe("p.dry", pts.filter((p, i) => i === 0 || Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1], p[2] - pts[i - 1][2]) > 1), 2.4, { bend: 14 });
  }

  // ---------- turbines ----------
  // At the seats the train lies low on a skid behind the showers: compressed air comes in at the
  // first stage's end face, cold air leaves the last stage's side straight towards the header.
  const H0 = SEATX(0) - 60, H1 = SEATX(nN - 1) + 50;
  const hr = atPlant ? 9 : Math.min(8, 0.7 * RT);
  const HZ = atPlant ? AX : TZ;                       // header height: on the floor, through the tees
  let turbIn, turbOut, tt, coldStart;
  if (atPlant) {
    turned("turb.coupling", XF(caseEnd, 0, AX), [[0, 6 * fc], [14 * ft, 6 * fc]], { tone: "mid" });
    tt = turbineTrain(caseEnd + 14 * ft, 0, AX, "turb", { endR: hr + 0.6 });
    box("turb.foot", [caseEnd + 14 * ft, -tt.rt, 0], [tt.end, tt.rt, AX - tt.rt + 0.5], { tone: "lo" }, { r: 1 });
    turbIn = [tt.port(0), 0, tt.top]; turbOut = [tt.end, 0, AX];
    call("turbShaft", [tt.port(nE - 1), 0, tt.top + 6]);
    // turbine work goes back down the shaft into the compressor
    flow("work", [[tt.end, 0, AX], [caseEnd - 10, 0, AX]], { gap: 16 });
  } else {
    const len = 22 * ft;
    const x0 = Math.max(GAP1 + 70, H1 - (nE - 1) * (len + 8 * ft) - len / 2);
    tt = turbineTrain(x0, TS.y, TZ, "turb", { side: true });
    box("skid", [x0 - 20, TS.y - RT - 8, 0], [tt.end + (spec.rec === "gen" ? 70 * ft : 20), TS.y + RT + 8, TZ - RT + 0.5], { tone: "lo" }, { r: 2 });
    // cold outlet on the last stage's side, facing the seats
    const px = tt.port(nE - 1), pr = hr + 1, y0 = Math.sqrt(RT * RT - pr * pr) - 1;
    turned(`turb${nE - 1}.out`, G.frameOf([px, TS.y + y0, TZ], [0, 1, 0], [1, 0, 0], [0, 0, 1]), [[0, pr], [RT + 3 - y0, pr]], { tone: "mid" }, { owner: `turb${nE - 1}`, bias: 10 });
    coldStart = [px, TS.y + RT + 3, TZ];
    if (spec.rec === "gen") {
      const gl = 46 * ft, gr = RT, gx = tt.end + 8 + gl / 2, F = XF(tt.end + 8, TS.y, TZ);
      turned("gen.shaft", XF(tt.end, TS.y, TZ), [[0, 3 * ft], [8, 3 * ft]], { tone: "mid" });
      turned("generator", F, [[0, gr * 0.85], [2, gr], [gl - 2, gr], [gl, gr * 0.85]], { tone: "mid" }, { extra: k.fadedSvg(G.ribsOf(F, 4, gl - 4, gr, 16, P, { fade: [0.1, 0.55], seams: true }), { tone: "lo" }) });
      box("generator.terminal", [gx - 7, TS.y - 7, TZ + gr - 0.4], [gx + 7, TS.y + 7, TZ + gr + 9], { tone: "mid" }, { r: 1 });
      call("generator", [gx + 12, TS.y, TZ + gr]);
      // shaft work into the generator, then as electricity back to the motor in the compressor room
      flow("work", [[tt.port(0), TS.y, TZ], [gx, TS.y, TZ]], { gap: 16 });
      flow("work", [[gx, TS.y, TZ + gr + 9], [gx, TS.y - RT - 30, 2], [GAP1 - 20, TS.y - RT - 30, 2], [MOT.len / 2, TS.y - RT - 30, 2], [MOT.len / 2, -14 * fc, AX + MOT.r]], { gap: 22, speed: 70 });
    }
    turbIn = [x0, TS.y, TZ]; turbOut = coldStart;
    call("turbSeat", [tt.port(0), TS.y, TZ + RT]);
  }

  // ---------- the line to the seats, low on floor sleepers ----------
  const lineR = 3.2;
  const LZ = atPlant ? AX : TZ;
  const LY = atPlant ? -60 : DRY.y - 40;
  const CRADLES = [plantEnd - 20, GAP1 + 30];
  const rLine = atPlant ? hr : lineR;
  for (const cx of CRADLES) box(`cradle${Math.round(cx)}`, [cx - 6, LY - 6, 0], [cx + 6, LY + 6, LZ - rLine], { tone: "mid" }, { r: 1 });
  const cradles = CRADLES.map(cx => `cradle${Math.round(cx)}`);
  if (!atPlant) {
    const xa = turbIn[0] - 40;
    const head = dryIn ? [dryOut] // the dryer's outlet faces the line on its back
      : [dryOut, [dryOut[0], dryOut[1], dryOut[2] + 20], [dryOut[0] + 40, dryOut[1], dryOut[2] + 20], [dryOut[0] + 40, LY, dryOut[2] + 20], [dryOut[0] + 40, LY, LZ]];
    const pts = [...head, [head[head.length - 1][0], LY, LZ], [xa, LY, LZ], [xa, TS.y, LZ], turbIn];
    pipe("line", pts.filter((p, i) => i === 0 || Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1], p[2] - pts[i - 1][2]) > 1), lineR,
      { tone: "hi", bend: 16, maxLength: 60, touch: cradles });
  } else {
    // dried air goes back over to the turbine inlet on the shaft
    const z = dryIn ? DRY.zp : dryOut[2] + 30;
    // from a dryer beyond the turbine: back over the shaft; straight from the aftercooler: along the cooler row first
    const pts = dryIn ? [dryOut, [dryOut[0], dryOut[1], z], [dryOut[0], 0, z], [turbIn[0], 0, z], turbIn]
      : Math.abs(turbIn[0] - dryOut[0]) > 40 ? [dryOut, [dryOut[0], dryOut[1], z], [turbIn[0], dryOut[1], z], [turbIn[0], 0, z], turbIn]
        : [dryOut, [dryOut[0], dryOut[1], z], [turbIn[0], 0, z], turbIn]; // too close for an L: one slanted run
    pipe("p.turbIn", pts.filter((p, i) => i === 0 || Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1], p[2] - pts[i - 1][2]) > 1), 2.4, { bend: 14 });
  }
  call("gap", [(GAP0 + GAP1) / 2, LY, LZ + 10]);

  // ---------- cold header on the floor, a shower-head outlet over each standing place ----------
  // the header is cut at every tee block, which carries it off the floor and the riser up
  const TW = 9, tz = HZ + hr + 2, rings = { pitch: 6, fade: [0.1, 0.55] };
  const cold = atPlant
    ? [turbOut, [tt.end + 60, 0, AX], [tt.end + 60, LY, AX], [H1, LY, AX], [H1, HEADER_Y, AX], [SEATX(nN - 1) + TW, HEADER_Y, AX]]
    : [coldStart, [coldStart[0], HEADER_Y, HZ], [SEATX(nN - 1) + TW, HEADER_Y, HZ]];
  flow("cold", [turbIn, [tt.port(nE - 1), turbIn[1], turbIn[2]]], { gap: 14 });
  flow("cold", pipe("cold", cold, hr, { tone: "hi", bend: atPlant ? 28 : 16, rings, maxLength: 40, touch: atPlant ? cradles : [] }));
  for (let i = nN - 1; i > 0; i--) flow("cold", pipe(`header${i}`, [[SEATX(i) - TW, HEADER_Y, HZ], [SEATX(i - 1) + TW, HEADER_Y, HZ]], hr, { tone: "hi", rings }));
  pipe("header0", [[SEATX(0) - TW, HEADER_Y, HZ], [H0 + 3, HEADER_Y, HZ]], hr, { tone: "hi", rings });
  turned("header.cap", XF(H0, HEADER_Y, HZ), [[0, hr + 1], [3, hr + 1]], { tone: "mid" });
  const SH = 238, ARM = 50, rR = 3.5, CZ = 112, CL = 22;   // shower arm height and reach, riser radius, reheat coil
  for (let i = 0; i < nN; i++) {
    const nx = SEATX(i);
    box(`tee${i}`, [nx - TW, HEADER_Y - hr - 2, 0], [nx + TW, HEADER_Y + hr + 2, tz], { tone: "mid" }, { r: 1 });
    let rz = tz;
    if (coil) {
      // the reheat coil is a finned section of the riser
      pipe(`riser${i}.low`, [[nx, HEADER_Y, tz], [nx, HEADER_Y, CZ]], rR, { tone: "hi" });
      const Fc = ZF(nx, HEADER_Y, CZ);
      turned(`coil${i}`, Fc, [[0, 7.5], [CL, 7.5]], { tone: "mid" }, { extra: k.fadedSvg(G.ribsOf(Fc, 2, CL - 2, 7.5, 18, P, { fade: [0.1, 0.55], seams: true }), { tone: "lo" }) });
      rz = CZ + CL;
    }
    flow("cold", [[nx, HEADER_Y, tz], ...pipe(`riser${i}`, [[nx, HEADER_Y, rz], [nx, HEADER_Y, SH], [nx, HEADER_Y + ARM, SH]], rR, { tone: "hi", bend: 14 })], { gap: 16 });
    // cold air falling from the shower head over the standing place
    for (const [dx, dy] of [[-8, -6], [0, 0], [8, 6], [-4, 9], [5, -9]])
      flow("cold", [[nx + dx * 0.4, HEADER_Y + ARM + 6 + dy * 0.4, SH - 18], [nx + dx * 2.2, HEADER_Y + ARM + 6 + dy * 2.2, 70]], { gap: 30, speed: 45, fade: true });
    box(`shower${i}.hub`, [nx - 6, HEADER_Y + ARM, SH - 8], [nx + 6, HEADER_Y + ARM + 12, SH + 6], { tone: "mid" }, { r: 1.5 });
    const F = DOWN(nx, HEADER_Y + ARM + 6, SH - 8);
    turned(`shower${i}`, F, [[0, 4], [3, 4], [7, 16], [10, 16]], { tone: "hi", crease: "lo" },
      { extra: Dots(G.dotsOf(F, 10, 11, 14, P, { fade: [0.05, 0.5] }), { size: 0.4 }) });
  }
  // motor power into the compressor
  flow("work", [[MOT.x0 + 4, 0, AX], [CASE.x + 12, 0, AX]], { gap: 14 });
  call("nozzles", [SEATX(nN - 1), HEADER_Y + ARM + 6, SH + 6]);
  if (coil) call("coils", [SEATX(nN - 1), HEADER_Y, 112]);
  call("header", [(H0 + H1) / 2, HEADER_Y, HZ + hr]);

  // ---------- a person, 175 cm, standing under the first shower head ----------
  const PX = SEATX(0), PY = HEADER_Y + ARM + 6;
  for (const dy of [-9, 9]) {
    cyl(`person.shoe${dy}`, PX + 3, PY + dy, 5.5, 0, 4, { tone: "lo" }, { steps: 18 });
    turned(`person.leg${dy}`, ZF(PX, PY + dy, 4), [[0, 5.5], [42, 6.5, 1], [82, 8]], { tone: "mid" });
  }
  turned("person.torso", ZF(PX, PY, 86), [[0, 17], [14, 16, 1], [40, 15, 1], [56, 19, 1], [62, 16, 1], [64, 7]], { tone: "mid" });
  for (const dy of [-24.3, 24.3]) turned(`person.arm${dy}`, ZF(PX, PY + dy, 82), [[0, 4.2], [60, 5.4]], { tone: "mid" });
  turned("person.neck", ZF(PX, PY, 150), [[0, 6], [3, 6]], { tone: "mid" });
  put("person.head", [PX, PY, 164], S(G.sphereOf([PX, PY, 164], 11, P), { tone: "mid" }), [record(A.ball([PX, PY, 164], 11, { name: "person.head" }))]);
  call("person", [PX, PY + 12, 0]);

  // scaled from the drawn size by how far the cap held each factor back
  const up = (key, ...v) => v.map(x => x * raw[key] / ({ fc, fd, ft })[key]);
  const kCool = Math.sqrt(Math.max(spec.duty, 0.5) / 25 / nC) * 100 / CH;
  const dims = [["compressor", ...up("fc", caseEnd, Math.max(CASE.d, 2 * MOT.r), STAGE_TOP)], ["coolers", ...[coolX(0)[1] - coolX(0)[0], CD, CH].map((v, i) => (i === 1 ? v : v * Math.max(1, kCool)))]];
  if (spec.dryer === "fridge") dims.push(["dryerF", ...up("fd", 56 * fd, 50 * fd, 86 * fd)]);
  if (spec.dryer === "desiccant") dims.push(["dryerD", ...up("fd", 64 * fd, DRY.d, 130 * fd)]);
  dims.push(["turbine", ...up("ft", tt.end - (tt.port(0) - tt.len / 2), 2 * tt.rt, 2 * tt.rt)]);
  dims.push(["person", 40, 30, 175]);

  A.settle(R, P);
  R.items.sort((a, b) => a.key - b.key);
  const groups = R.items.map(item => `<g class="it" data-name="${item.name}">${item.svg}</g>`);
  const svg = k.figureSvg({
    width: W, height: H,
    label: "The air-cycle plant at true scale: motor and staged piston compressor with a cooler after every stage, dryer, the air line to the seats, the expansion turbine, and the cold-air header on the floor with a shower-head outlet over each standing place. A 175 cm person gives the scale.",
    body: [...back, `<g>${groups.join("")}</g>`, flowSvg(flows, at)],
  });
  // judged by eye: pipe ends on the cooler tops sit in front of the long crankcase, and the stage
  // pipes leave the heads right above their own barrels; the crowding check treats both as rods
  const crowd = [["p.*", "crankcase"], ["cold", "skid"], ["p.*", n => /^stage\d+\.barrel/.test(n)]];
  // the wide outlet flange sits into the turbine casing's curve; 0.25 px² drawn the other way
  const allow = [["turb*", "turb*"]];
  return { svg, calls, dims, capped, crowd, allow, W, H, R, P, count: R.items.length };
}

// ---------- explorer page ----------
// Page 1: parameter rail, COP–pressure chart, comparison with air conditioners.
// Page 2: the plant drawn in isometric, sized from the same result, with a readout rail.
// Both pages read one state object, so any change on page 1 redraws page 2.
(() => {
const X = window.EXPLORER_PARAMS;
const { system } = window.EXPLORER_SYSTEM;
const { compare } = window.EXPLORER_COMPARE;
const { sweep, breakEven } = window.EXPLORER_SWEEP;
const { ledger } = window.EXPLORER_LEDGER;
const WHY = window.EXPLORER_WHY;
const NS = "http://www.w3.org/2000/svg";
const $ = id => document.getElementById(id);

// ---- strings ----
const T = {
  title: { zh: "Adiabatic Air Expansion Dashboard", en: "Adiabatic Air Expansion Dashboard" },
  page1: { zh: "第 1 页 · 参数与曲线", en: "Page 1 · Parameters and curve" },
  page2: { zh: "第 2 页 · 设备与流程（按比例）", en: "Page 2 · Plant and flow (to scale)" },
  page4: { zh: "第 4 页 · 效率为什么上不去", en: "Page 4 · Why the COP stays low" },
  wfTitle: { zh: "电从哪里来、冷送出多少（kW）", en: "Where the electricity goes, and the cooling delivered (kW)" },
  wfLead: { zh: "涡轮把压缩功的 <b>{b}</b> 还回来，净用电只是两个大数之差。所以压缩机和涡轮效率各降 1 个百分点，COP 就降 <b>{a}</b>。", en: "The turbine hands back <b>{b}</b> of the compressor's work, so net electricity is the small difference of two large flows: one point less efficiency on both machines costs <b>{a}</b> of the COP." },
  wfComp: { zh: "压缩机用电", en: "Compressor" },
  wfRec: { zh: "涡轮回收", en: "Turbine back" },
  wfAux: { zh: "海水泵/干燥", en: "Pumps/dryer" },
  wfOrc: { zh: "ORC", en: "ORC" },
  wfHw: { zh: "热折合电", en: "Heat credit" },

  wfNet: { zh: "净用电", en: "Net" },
  wfCool: { zh: "送出冷量", en: "Cooling" },
  wpTitle: { zh: "设计点对比", en: "Design points" },
  wpLead: { zh: "压力越高、出风越冷，COP 越低；即使机器无损，200 bar 也只有 <b>{c}</b>，而且出口远低于空气液化温度。", en: "Higher pressure and a colder outlet both lower the COP; even lossless, 200 bar gives only <b>{c}</b>, with the outlet far below the temperature where air liquefies." },
  wp_p4: { zh: "4 bar", en: "4 bar" },
  wp_p20: { zh: "20 bar", en: "20 bar" },
  wp_pNow: { zh: "当前 {p} bar", en: "Now, {p} bar" },
  wp_p200: { zh: "200 bar", en: "200 bar" },
  wpNow: { zh: "当前技术水平", en: "This technology level" },
  wpIdeal: { zh: "无损机器", en: "Lossless machines" },
  wpLiquid: { zh: "空气会液化", en: "air liquefies" },
  wpOut: { zh: "涡轮出口", en: "turbine out" },
  weTitle: { zh: "COP 随压缩机与涡轮效率变化（两者取相同值）", en: "COP against compressor and turbine efficiency (set equal)" },
  weLead: { zh: "两台机器都做到完美、其他损失维持当前档，COP 也只有 <b>{c}</b>。即使其他损失全部为零，效率也要到 <b>{x}</b> 才追平户外点冷机。", en: "Even with both machines perfect and the other losses at this level, COP reaches only <b>{c}</b>. With every other loss at zero, efficiency must still reach <b>{x}</b> to match the outdoor spot cooler." },
  weLeadNoAc: { zh: "两台机器都做到完美、其他损失维持当前档，COP 也只有 <b>{c}</b>；其他损失也全部为零时是 <b>{d}</b>。", en: "Even with both machines perfect and the other losses at this level, COP reaches only <b>{c}</b>; with every other loss at zero too, <b>{d}</b>." },
  weNever: { zh: "达不到", en: "never" },
  weCur: { zh: "其他损失：当前档", en: "Other losses: this level" },
  weBeyond: { zh: "其他损失：理论理想", en: "Other losses: theoretical ideal" },
  weBand: { zh: "工业最高 0.88–0.92", en: "Best in service 0.88–0.92" },
  weQatar: { zh: "卡塔尔区域供冷冷站实测 3.7–4.0", en: "Qatar Cool plants, measured 3.7–4.0" },
  weAxis: { zh: "压缩机与涡轮等熵效率", en: "Compressor and turbine isentropic efficiency" },
  page3: { zh: "第 3 页 · 回收比例与 COP", en: "Page 3 · Recovery shares and COP" },
  lTitle: { zh: "回收比例对 COP 的影响", en: "How the recovery shares set the COP" },
  lComp: { zh: "压缩机用电", en: "Compressor electricity" },
  lHeat: { zh: "压缩热", en: "Compression heat" },
  lHeatSub: { zh: "最高排气 {t} °C。能回收的上限 = 高于“供水温度 + 冷却器温差”的那段热，且不超过设定的 {s}%：海水淡化（{ta} °C 供水）{a} kW，热泵热水器（{tb} °C 供水）{b} kW", en: "Hottest discharge {t} °C. Recoverable at most = the heat above supply temperature plus cooler approach, and no more than the set {s}%: desalination ({ta} °C supply) {a} kW, heat-pump water heater ({tb} °C supply) {b} kW" },
  lWork: { zh: "涡轮机械功", en: "Turbine shaft work" },
  lCool: { zh: "送出冷量", en: "Cooling delivered" },
  lAux: { zh: "海水泵 / 干燥机", en: "Seawater pumps / dryer" },
  lStages: { zh: "压缩级数", en: "Compression stages" },
  lW: { zh: "机械功回收比例", en: "Work recovery share" },
  lWHint: { zh: "涡轮轴功里有多少变成省下的电。0% = 涡轮功白白耗掉（刹车）；90% = 发电机 0.93 × 变频器 0.97，即第 1 页的设置；滑块上限 95%（高效发电机约 0.97 × 变频器约 0.98，待核实）。", en: "How much of the turbine shaft work comes back as electricity. 0% = the work is thrown away (a brake); 90% = generator 0.93 × inverter 0.97, the page 1 setting; the slider stops at 95% (a high-efficiency generator ~0.97 × inverter ~0.98, to check)." },
  lH: { zh: "热回收比例", en: "Heat recovery share" },
  lHHint: { zh: "压缩热里有多少被回收利用，每 kWh 按所选用途的折合系数计电（海水淡化 0.04，热泵热水器 0.33）；回收的热不再排走，泵也少用电。滑块上限由供水温度决定：只有比供水温度更热的那段热能用上，所以海水淡化最多 {a}，热泵热水器最多 {b}。", en: "How much of the compression heat is put to use, each kWh credited at the chosen use's factor (desalination 0.04, heat-pump water heater 0.33); recovered heat is not rejected, so the pumps use less too. The slider stops where the supply temperature allows: only heat hotter than the supply can be used, so desalination at most {a}, heat-pump water heater at most {b}." },
  lFormula: { zh: "COP = 冷量 ÷（压缩机用电 − 功回收比例 × 涡轮轴功 + 海水泵/干燥机 − 热回收比例 × 压缩热 × 折合系数）", en: "COP = cooling ÷ (compressor electricity − work share × turbine shaft work + pumps/dryer − heat share × compression heat × factor)" },
  lCop: { zh: "此比例下 COP", en: "COP at these shares" },
  lNow: { zh: "第 1 页当前配置", en: "Page 1 setup" },
  lMethods: { zh: "回收方式与对应比例（点一行套用）", en: "Recovery methods and their shares (tap to apply)" },
  lMethod: { zh: "方式", en: "Method" },
  lShare: { zh: "比例", en: "Share" },
  m_w_none: { zh: "功：不回收", en: "Work: none" },
  m_w_gen: { zh: "功：涡轮发电送回（0.93 × 0.97）", en: "Work: generator back to grid (0.93 × 0.97)" },
  m_h_none: { zh: "热：不回收", en: "Heat: none" },
  m_h_heat: { zh: "热：海水淡化（× {f}）", en: "Heat: desalination (× {f})" },
  m_h_hp: { zh: "热：热泵热水器（× {f}）", en: "Heat: heat-pump water heater (× {f})" },
  tooCold: { zh: "排气不够热", en: "discharge too cool" },
  lAxisX: { zh: "机械功回收比例", en: "Work recovery share" },
  lChart: { zh: "COP 随机械功回收比例变化，每条线是一种热回收方式", en: "COP against work recovery share; one line per heat recovery method" },
  footer: { zh: "绿点 = 有来源，黄点 = 待核实，灰点 = 占位。点参数名可看依据。默认工况：35 °C、53% RH。", en: "Green dot = sourced, amber = to check, grey = placeholder. Tap a parameter name for its basis. Default case: 35 °C, 53% RH." },
  custom: { zh: "已修改", en: "edited" },
  advanced: { zh: "更多参数", en: "More parameters" },
  tech: { zh: "技术水平", en: "Technology level" },
  techSrc: { zh: "一键套用一整套工程参数：工业最高水平 = 今天在役设备能做到的最好值；理论理想 = 无任何损失。各项取值和来源在工程师参数里，点参数名可看", en: "Applies a whole set of engineer parameters: Industry best = the best values in service today; Theoretical ideal = no losses at all. Each value and its source is in the engineer parameters; tap a name" },
  mainParams: { zh: "主要参数", en: "Main settings" },
  engineer: { zh: "工程师参数（{n} 项，点名称看依据）", en: "Engineer parameters ({n}; tap a name for its basis)" },
  auto: { zh: "自动", en: "Auto" },
  mTyp: { zh: "建议值", en: "Suggested" },
  mMaxL: { zh: "上限", en: "Top" },
  basisComp: { zh: "总压比 {p} ÷ {pa} = {pr}，每级不超过 {lim}（常见值）→ {n} 级，每级 {per}{cap}", en: "Overall ratio {p} ÷ {pa} = {pr}; at most {lim} per stage (typical) → {n} stages of {per} each{cap}" },
  basisExp: { zh: "总膨胀比 {p} ÷ {pa} = {pr}（涡轮入口 ÷ 排气背压），每个不超过 {lim}（常见值）→ {n} 个，每个 {per}{cap}", en: "Overall ratio {p} ÷ {pa} = {pr} (turbine inlet ÷ discharge back pressure); at most {lim} each (typical) → {n} turbines of {per} each{cap}" },
  basisIso: { zh: "理论理想：等温压缩，相当于无穷多级、级间冷到环境温度", en: "Theoretical ideal: isothermal compression, i.e. infinitely many stages cooled to ambient" },
  basisCap: { zh: "（已到 5 级上限）", en: " (at the 5-stage cap)" },
  cop: { zh: "COP", en: "COP" },
  pressure: { zh: "压力", en: "Pressure" },
  cooling: { zh: "冷量", en: "Cooling" },
  power: { zh: "用电", en: "Electricity" },
  supply: { zh: "出风口温度", en: "Outlet air" },
  stages: { zh: "级数（压缩 / 膨胀）", en: "Stages (comp. / exp.)" },
  optimum: { zh: "最优压力", en: "Best pressure" },
  setOpt: { zh: "设为最优", en: "Use best" },
  noOpt: { zh: "全理想：压力越低 COP 越高，没有最优点", en: "Ideal: COP only rises as pressure falls, no optimum" },
  axisX: { zh: "压力 bar(abs)", en: "Pressure bar(abs)" },
  cCarnot: { zh: "卡诺极限", en: "Carnot limit" },
  cIdeal: { zh: "理论理想", en: "Theoretical ideal" },
  cFrontier: { zh: "工业最高水平", en: "Industry best" },
  cCurrent: { zh: "当前配置", en: "Current setup" },
  spot: { zh: "户外点冷机", en: "Outdoor spot cooler" },
  split: { zh: "分体空调 5 星", en: "Split AC, 5-star" },
  air: { zh: "空气循环", en: "Air cycle" },
  outlet: { zh: "出风口 COP", en: "COP at the outlet" },
  net: { zh: "现场净冷量 / 用电", en: "Net local cooling per unit of power" },
  netLine: { zh: "净值", en: "net" },
  evenRet: { zh: "空调排热回流超过 {a} 时胜过点冷机，超过 {b} 时胜过分体空调（现取 {f}）。", en: "Beats the spot cooler once more than {a} of its exhaust heat returns, and the split AC beyond {b} (now {f})." },
  evenEta: { zh: "压缩与透平效率同时做到 <b>{e}</b>，出风口 COP 追平点冷机。", en: "Compressor and turbine efficiency of <b>{e}</b> each matches the spot cooler at the outlet." },
  evenEtaNo: { zh: "只提高压缩与透平效率追不平点冷机：其他损失把 COP 封顶。", en: "Better compressor and turbine efficiency alone cannot match the spot cooler; other losses cap the COP." },
  evenEtaYes: { zh: "出风口 COP 已不低于点冷机。", en: "Already at or above the spot cooler at the outlet." },
  dryerSwitch: { zh: "换吸附式干燥", en: "desiccant dryer from here" },
  overIndustry: { zh: "超出工业最高 {v}", en: "above industry best {v}" },
  warn_icing: { zh: "结冰风险：干燥器不够", en: "Icing risk: dryer not enough" },
  warn_surplus: { zh: "透平功大于压缩功", en: "Turbine work exceeds compressor work" },
  warn_heatTooCold: { zh: "排气不够热，热回收不工作", en: "Discharge too cool to drive heat recovery" },
  warn_absOverCarnot: { zh: "吸收式 COP 超过其卡诺上限", en: "Absorption COP above its Carnot limit" },
  warn_liquefies: { zh: "低于 −140 °C，空气可能液化，结果无效", en: "Below −140 °C, air may liquefy; result invalid" },
  warn_noExpansion: { zh: "压降吃掉全部压差", en: "Pressure drops use up the whole pressure" },
  warn_throttled: { zh: "超过涡轮最高入口压力，先经减压阀节流（这部分压力白白损失）", en: "Above the turbine's maximum inlet pressure: throttled first (that pressure is wasted)" },
  warn_frostbite: { zh: "送风低于 0 °C，有冻伤风险", en: "Supply below 0 °C, frostbite risk" },
  nStages: { zh: "{n} 级", en: "{n} stages" },
  plantRoom: { zh: "压缩机房", en: "Compressor room" },
  seats: { zh: "座位区", en: "Seating" },
  farAway: { zh: "≈ 远距离，不按比例", en: "≈ long run, not to scale" },
  person: { zh: "人 1.75 m", en: "Person, 1.75 m" },
  compressor: { zh: "压缩机", en: "Compressor" },
  motor: { zh: "电机", en: "Motor" },
  waterLoop: { zh: "海水冷却回路", en: "Seawater cooling loop" },

  ruler: { zh: "3 m 标尺（每格 10 cm）", en: "3 m rule, 10 cm ticks" },
  drawing: { zh: "正在重绘…", en: "Redrawing…" },
  isothermal: { zh: "等温（理想）", en: "isothermal (ideal)" },
  coolers: { zh: "级间冷却器", en: "Intercoolers" },
  coolersSub: { zh: "排入 {w} °C {m} {q} kW", en: "{q} kW to {w} °C {m}" },
  mSea: { zh: "海水", en: "seawater" },
  mTower: { zh: "冷却塔水", en: "cooling-tower water" },
  noteHeat: { zh: "压缩热回收：{h} kW 热水（{T} °C）{to}", en: "Compression heat recovery: {h} kW of {T} °C hot water {to}" },
  noteWork: { zh: "轴功回收：发电 {p} kW 送回压缩机房", en: "Shaft work recovery: {p} kW generated, sent back to the compressor room" },
  hwToDesal: { zh: "送海水淡化", en: "for desalination" },
  hwToHp: { zh: "替代热泵热水器", en: "instead of heat-pump heaters" },
  tower: { zh: "开式湿式冷却塔", en: "Open wet cooling tower" },
  heatNone: { zh: "压缩热不回收，全部排掉", en: "compression heat not recovered, all rejected" },
  dryerF: { zh: "冷冻式干燥机", en: "Refrigerated dryer" },
  dryerD: { zh: "吸附式干燥机", en: "Desiccant dryer" },
  purgeSub: { zh: "再生耗气 {p}%（这部分压缩空气用来吹干吸附剂，不进涡轮）", en: "{p}% purge air (compressed air used to dry the desiccant, never reaches the turbine)" },
  absorber: { zh: "溴化锂吸收式制冷机", en: "Lithium-bromide absorption chiller" },
  orc: { zh: "有机朗肯循环（ORC）发电机组", en: "Organic Rankine cycle (ORC) power unit" },
  turbine: { zh: "透平", en: "Turbine" },
  generator: { zh: "发电机", en: "Generator" },
  shaft: { zh: "与压缩机同轴", en: "on the compressor shaft" },
  coil: { zh: "回热盘管", en: "Reheat coil" },
  nozzle: { zh: "淋浴式出风口", en: "Shower-head outlet" },
  cable: { zh: "发电机电缆", en: "Generator cable" },
  cableSub: { zh: "与气管分开走", en: "kept apart from the air lines" },
  panel: { zh: "配电柜", en: "Switchboard" },
  panelSub: { zh: "电送回压缩机房", en: "power back to the compressor room" },
  coldDuct: { zh: "冷风总管（保温）", en: "Cold-air header (insulated)" },
  airLine: { zh: "压缩空气管", en: "Compressed-air line" },
  rStations: { zh: "流程各点", en: "Along the flow" },
  rEnergy: { zh: "能量（kW）", en: "Energy (kW)" },
  ambient: { zh: "环境", en: "Ambient" },
  compOut: { zh: "压缩第 {i} 级出口", en: "Compressor stage {i} out" },
  turbIn: { zh: "透平入口", en: "Turbine inlet" },
  throttle: { zh: "减压阀节流后", en: "After the throttle valve" },
  expOut: { zh: "膨胀第 {i} 级出口", en: "Expansion stage {i} out" },
  expIn: { zh: "冷排回热后进第 {i} 级", en: "Rewarmed in the coil, into stage {i}" },
  sketch: { zh: "示意", en: "schematic" },
  eComp: { zh: "压缩机用电", en: "Compressor electricity" },
  eRec: { zh: "回收的透平功", en: "Turbine work recovered" },
  eAux: { zh: "海水泵 / 干燥机", en: "Seawater pumps / dryer" },
  eOrc: { zh: "ORC 发电", en: "ORC power" },
  eHw: { zh: "回收热折合电（× {f}）", en: "Recovered-heat credit (× {f})" },
  hotWaterUnit: { zh: "热回收换热器（热水送往海水淡化厂）", en: "Heat-recovery exchanger (hot water to the desalination plant)" },
  hotWaterHp: { zh: "热回收换热器（热水替代热泵热水器）", en: "Heat-recovery exchanger (hot water instead of heat-pump heaters)" },
  warn_creditExceeds: { zh: "回收热折合的电超过系统总用电，COP 失去意义：这时它更像一台热水器，冷只是副产品", en: "Heat credit exceeds all electricity used; COP loses meaning: the system is a water heater with cooling on the side" },
  hwRow: { zh: "回收热（不计入用电）", en: "Recovered heat (not electricity)" },
  fComp: { zh: "压缩功 {w} ÷ 电机效率 {e}", en: "compression work {w} ÷ motor efficiency {e}" },
  fRec: { zh: "涡轮轴功 {w} × 回收链效率 {e}", en: "turbine shaft work {w} × recovery chain {e}" },
  fAux: { zh: "排入海水的热 {q} × {p}%", en: "heat to seawater {q} × {p}%" },
  fDry: { zh: " + 冷干机 {d}", en: " + refrigerated dryer {d}" },
  fHw: { zh: "压缩热 {H} × {p}", en: "compression heat {H} × {p}" },
  fHwCap: { zh: "（设定 {s}%，被 {T} °C 供水温度限住）", en: " (set {s}%, limited by the {T} °C supply)" },
  fHwVal: { zh: "回收热 {h} × {f}", en: "recovered heat {h} × {f}" },
  fCool: { zh: "{m} kg/s × 1.005 × ({a} − ({o})) °C", en: "{m} kg/s × 1.005 × ({a} − ({o})) °C" },
  eNet: { zh: "净用电", en: "Net electricity" },
  qAir: { zh: "冷风冷量", en: "Cooling by air" },
  qAbs: { zh: "吸收式冷量（7 °C 冷水）", en: "Absorption cooling (7 °C water)" },
  qTot: { zh: "总冷量", en: "Total cooling" },
};
// the public site is English only (no language toggle)
const lang = "en";
const t = (k, vars = {}) => (T[k] ? T[k][lang] : k).replace(/\{(\w+)\}/g, (_, v) => vars[v]);
const L = o => (o ? o[lang] || o.en : "");

// ---- formatting ----
const fmt = (v, d = 2) => (v === Infinity ? "∞" : typeof v === "number" ? (Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(d)) : String(v));
const kw = w => (w / 1000).toFixed(1);
const C = k => (k - 273.15).toFixed(1);
const pct = f => Math.round(f * 100) + "%";

// ---- state ----
let base = "best", edited = false;
let s = X.defaults(base);
const COND = ["Ta", "RH", "m", "Pa"];

function setMode(m) { base = m; edited = false; const keep = { P: s.P }; s = { ...X.defaults(m), ...keep }; buildRail(); schedule(); }
// moving the pressure puts the flow back at that pressure's top
function setVal(k, v) { s = X.clamp({ ...s, [k]: v, ...(k === "P" ? { m: "auto" } : {}) }); edited = true; schedule(); }

// ---- header ----
function buildHeader() {
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  document.querySelectorAll("[data-t]").forEach(el => { el.textContent = t(el.dataset.t); });
  const modes = $("modes"); if (!modes) return; modes.textContent = "";
  for (const m of ["best", "ideal"]) {
    const b = document.createElement("button");
    b.type = "button"; b.dataset.mode = m; b.title = L(X.MODES[m]);
    b.textContent = L(X.MODES[m].short) + (m === base && edited ? " · " + t("custom") : "");
    b.setAttribute("aria-pressed", m === base);
    b.onclick = () => setMode(m);
    modes.append(b);
  }
  document.querySelectorAll("#lang button").forEach(b => b.setAttribute("aria-pressed", b.dataset.lang === lang));
}

// ---- parameter rail ----
const refs = {};
const P_LO = X.BY_KEY.P.min, P_HI = X.BY_KEY.P.max;
const hi = p => (p.dynMax ? p.dynMax(s) : p.max); // mass flow's top follows pressure
const toPos = (p, v) => p.scale === "log" ? Math.round(1000 * Math.log(v / p.min) / Math.log(hi(p) / p.min)) : v;
const fromPos = (p, x) => p.scale === "log" ? +(p.min * Math.pow(hi(p) / p.min, x / 1000)).toPrecision(3) : +x;
const flowTxt = g => `${+(g / 1000).toPrecision(3)}`; // g/s inside, kg/s on screen

function control(p) {
  const wrap = document.createElement("div");
  wrap.className = "ctl";
  const lab = document.createElement("div");
  lab.className = "lab";
  lab.innerHTML = `<span><i class="dot ${p.status}"></i>${L(p)}</span><span class="val"></span>`;
  const src = document.createElement("div");
  src.className = "src"; src.hidden = true;
  src.textContent = L(p.src) + (p.bestSrc ? ` · ${L(X.MODES.best)} ${p.best}：${L(p.bestSrc)}` : "");
  lab.onclick = () => { src.hidden = !src.hidden; };
  const flag = document.createElement("div"); flag.className = "flag"; flag.hidden = true;
  wrap.append(lab);
  const v = s[p.key], autoable = p.real === "auto" || p.ideal === "auto";
  const id = "c-" + p.key;
  let body;
  if (p.control === "slider") {
    body = document.createElement("input");
    body.type = "range"; body.id = id;
    body.min = p.scale === "log" ? 0 : p.min; body.max = p.scale === "log" ? 1000 : p.max; body.step = p.scale === "log" ? 1 : p.step;
    body.value = toPos(p, v);
    body.setAttribute("aria-label", L(p));
    body.oninput = () => setVal(p.key, fromPos(p, body.value));
  } else if (p.control === "number") {
    body = document.createElement("input");
    body.type = "number"; body.id = id; body.min = p.min; body.max = p.max; body.step = p.step;
    body.setAttribute("aria-label", L(p));
    if (v !== "auto") body.value = v;
    body.onchange = () => setVal(p.key, body.value === "" && autoable ? "auto" : Math.min(p.max, Math.max(p.min, +body.value)));
  } else if (p.control === "auto") {
    body = document.createElement("div"); body.className = "hint basis";
  } else if (p.control === "stepper") {
    body = document.createElement("div"); body.className = "stepper";
    const opts = [...(autoable ? ["auto"] : []), ...Array.from({ length: p.max - p.min + 1 }, (_, i) => p.min + i), ...(p.allowInfinity ? [Infinity] : [])];
    for (const o of opts) {
      const b = document.createElement("button"); b.type = "button";
      b.textContent = o === "auto" ? t("auto") : o === Infinity ? "∞" : o;
      b.setAttribute("aria-pressed", o === v);
      b.onclick = () => { body.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b)); setVal(p.key, o); };
      body.append(b);
    }
  } else if (p.control === "segmented") {
    body = document.createElement("div"); body.className = "seg";
    const opts = [...(autoable && !("auto" in p.options) ? [["auto", { zh: "自动", en: "Auto" }]] : []), ...Object.entries(p.options)];
    for (const [k, o] of opts) {
      const b = document.createElement("button"); b.type = "button"; b.textContent = L(o);
      b.setAttribute("aria-pressed", k === v);
      b.onclick = () => { body.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b)); setVal(p.key, k); };
      body.append(b);
    }
  } else if (p.control === "select") {
    body = document.createElement("select"); body.id = id; body.setAttribute("aria-label", L(p));
    const opts = [...(autoable && !("auto" in p.options) ? [["auto", { zh: "自动", en: "Auto" }]] : []), ...Object.entries(p.options)];
    for (const [k, o] of opts) { const op = document.createElement("option"); op.value = k; op.textContent = L(o); op.selected = k === v; body.append(op); }
    body.onchange = () => setVal(p.key, body.value);
  } else if (p.control === "toggle" && p.options) {
    body = document.createElement("div"); body.className = "stepper";
    const on = v === "all" ? Object.keys(p.options) : v;
    for (const [k, o] of Object.entries(p.options)) {
      const b = document.createElement("button"); b.type = "button"; b.textContent = L(o);
      b.setAttribute("aria-pressed", on.includes(k));
      b.onclick = () => {
        const cur = s[p.key] === "all" ? Object.keys(p.options) : s[p.key];
        const next = cur.includes(k) ? cur.filter(x => x !== k) : [...cur, k];
        b.setAttribute("aria-pressed", next.includes(k)); setVal(p.key, next);
      };
      body.append(b);
    }
  } else {
    body = document.createElement("input"); body.type = "checkbox"; body.id = id; body.checked = !!v;
    body.setAttribute("aria-label", L(p));
    body.onchange = () => setVal(p.key, body.checked);
  }
  const note = document.createElement("div"); note.className = "hint"; note.hidden = !p.dynMax;
  wrap.append(body, note, flag, src);
  if (p.presets) { // quick reference values under a number input
    const row = document.createElement("div"); row.className = "stepper presets";
    for (const o of p.presets) {
      const b = document.createElement("button"); b.type = "button"; b.textContent = L(o);
      b.onclick = () => { body.value = o.v; setVal(p.key, o.v); };
      row.append(b);
    }
    body.after(row);
  }
  refs[p.key] = { wrap, val: lab.querySelector(".val"), body, flag, p, note };
  return wrap;
}

// Why the stage count is what it is: overall ratio, count, ratio per stage against its limit.
function basis(key, r) {
  const S = r.s;
  if (key === "nComp") {
    if (S.nComp === Infinity) return t("basisIso");
    const pr = S.P / S.Pa, per = Math.pow(pr, 1 / S.nComp);
    return t("basisComp", { p: fmt(S.P, 1), pa: fmt(S.Pa, 2), pr: fmt(pr, 1), n: S.nComp, per: fmt(per, 2), lim: fmt(S.rcMax, 1), cap: per > S.rcMax + 1e-9 ? t("basisCap") : "" });
  }
  const pin = X.turbineInlet(S), pout = S.Pa + S.dpBack, pr = pin / pout, per = Math.pow(pr, 1 / S.nExp);
  return t("basisExp", { p: fmt(pin, 1), pa: fmt(pout, 2), pr: fmt(pr, 1), n: S.nExp, per: fmt(per, 2), lim: fmt(S.rtMax, 1), cap: per > S.rtMax + 1e-9 ? t("basisCap") : "" });
}

// The face of the panel holds the technology level and the few front controls; every other
// parameter sits in one collapsed engineer drawer, grouped as before.
let drawerOpen = false;
function buildRail() {
  const rail = $("rail"); rail.textContent = "";
  for (const k of Object.keys(refs)) delete refs[k];
  const h = document.createElement("h3"); h.textContent = t("mainParams"); rail.append(h);
  const tech = document.createElement("div"); tech.className = "ctl";
  const lab = document.createElement("div"); lab.className = "lab";
  lab.innerHTML = `<span><i class="dot sourced"></i>${t("tech")}</span>`;
  const src = document.createElement("div"); src.className = "src"; src.hidden = true; src.textContent = t("techSrc");
  lab.onclick = () => { src.hidden = !src.hidden; };
  const modes = document.createElement("div"); modes.className = "seg modes"; modes.id = "modes"; modes.setAttribute("role", "group");
  tech.append(lab, modes, src); rail.append(tech);
  buildHeader();
  for (const p of X.PARAMS.filter(p => p.front)) rail.append(control(p));

  const drawer = document.createElement("details"); drawer.className = "drawer"; drawer.open = drawerOpen;
  drawer.ontoggle = () => { drawerOpen = drawer.open; };
  const sm = document.createElement("summary"); sm.textContent = t("engineer", { n: X.PARAMS.filter(p => !p.front && !p.noUi && p.group !== "delivery").length });
  drawer.append(sm); rail.append(drawer);
  for (const [g, gl] of Object.entries(X.GROUPS)) {
    const ps = X.PARAMS.filter(p => p.group === g && !p.front && !p.noUi && g !== "delivery"); // delivery ends at the nozzle; no mixing or AC inputs
    if (!ps.length) continue;
    const h = document.createElement("h3"); h.textContent = L(gl); drawer.append(h);
    for (const p of ps.filter(p => !p.advanced)) drawer.append(control(p));
    const adv = ps.filter(p => p.advanced);
    if (adv.length) {
      const d = document.createElement("details"); d.className = "adv";
      const sm = document.createElement("summary"); sm.textContent = t("advanced"); d.append(sm);
      for (const p of adv) d.append(control(p));
      drawer.append(d);
    }
  }
}

function refreshRail(r) {
  for (const { wrap, val, flag, p, body } of Object.values(refs)) {
    wrap.hidden = !X.visible(p, s);
    const v = s[p.key], res = r.s[p.key];
    let txt = v === "auto" ? `${t("auto")} → ${fmt(res)}` : typeof v === "boolean" || Array.isArray(v) || v === "all" ? "" : p.options ? "" : fmt(v, p.step < 0.1 ? 2 : 1);
    if (p.key === "nComp" && v !== "auto" && r.nCompRaised) txt += ` → ${r.s.nComp}`;
    if (p.key === "m") { const b = X.mMax(s.P); txt = `${flowTxt(res)} kg/s`; refs.m.note.textContent = `${t("mTyp")} ${flowTxt(b.typ)}：${lang === "zh" ? b.typZh : b.typEn}。${t("mMaxL")} ${flowTxt(b.max)}：${L(b)}`; }
    if (p.control === "auto") { txt = res === Infinity ? "∞" : String(res); body.textContent = basis(p.key, r); }
    val.textContent = txt + (txt && p.unit && p.key !== "m" ? " " + p.unit : "");
    if (p.control === "number" && v === "auto") body.placeholder = fmt(res);
    const im = p.industryMax;
    flag.hidden = !(im && typeof res === "number" && res > im.value);
    if (im) flag.textContent = t("overIndustry", { v: im.value }) + " · " + L(im);
  }
  if (refs.P) { refs.P.body.value = toPos(refs.P.p, s.P); }
  if (refs.m) { refs.m.body.value = toPos(refs.m.p, r.s.m); }
}

// ---- compute (throttled to one frame) ----
let pending = false;
function schedule() { if (!pending) { pending = true; requestAnimationFrame(run); } }
const cache = {};
function tierSweep(mode) {
  const cond = Object.fromEntries(COND.map(k => [k, s[k]]));
  const key = mode + JSON.stringify(cond);
  if (!cache[key]) cache[key] = sweep({ ...X.defaults(mode), ...cond });
  return cache[key];
}

function run() {
  pending = false;
  buildHeader();
  const r = system(s);
  const c = compare(s, r);
  const cur = sweep(s);
  const tiers = { ideal: tierSweep("ideal") };
  refreshRail(r);
  drawKpis(r, cur);
  drawChart(r, c, cur, tiers);
  drawCompare(r, c);
  drawPlant(r);
  drawReadout(r);
  drawLedger();
  drawWhy(r, c);
}

// ---- page 1: numbers ----
function drawKpis(r, cur) {
  const k = (cls, key, v, unit = "") => `<div class="kpi ${cls}"><div class="k">${t(key)}</div><div class="v">${v}<small>${unit}</small></div></div>`;
  const n = r.s.nComp === Infinity ? "∞" : r.s.nComp;
  let opt = cur.best
    ? `<div class="kpi"><div class="k">${t("optimum")}</div><div class="v">${fmt(cur.best.P, 1)}<small>bar · COP ${fmt(cur.best.cop)}</small> <button type="button" class="pill info" id="useOpt">${t("setOpt")}</button></div></div>`
    : `<div class="kpi"><div class="k">${t("optimum")}</div><div class="v"><small>${t("noOpt")}</small></div></div>`;
  $("kpis").innerHTML =
    k("cop", "cop", fmt(r.cop)) + k("", "pressure", fmt(s.P, 1), "bar") + k("", "cooling", kw(r.Q), "kW") + k("", "power", kw(r.E), "kW") +
    k("", "supply", C(r.Ts), "°C") + k("", "stages", `${n} / ${r.s.nExp}`) + opt;
  const u = $("useOpt"); if (u) u.onclick = () => setVal("P", +cur.best.P.toPrecision(3));
  const bad = new Set(["liquefies", "noExpansion", "creditExceeds"]);
  $("warns").innerHTML = r.warn.map(w => `<span class="pill ${bad.has(w) ? "bad" : "warn"}">${t("warn_" + w)}</span>`).join("");
}

// ---- page 1: chart ----
function el(tag, attrs = {}, text) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text !== undefined) e.textContent = text;
  return e;
}
function drawChart(r, c, cur, tiers) {
  const box = $("chart");
  const W = Math.max(520, box.clientWidth || 800), H = Math.max(260, box.clientHeight || 320);
  const m = { l: 44, r: 128, t: 12, b: 30 };
  const yLog = s.yLog !== false;
  const shown = (s.curves === "all" ? ["carnot", "ideal", "current", "ac"] : s.curves).filter(k => SHOW_AC || k !== "ac");
  // linear axis: fit the curves shown, rounded up to a step of 0.5 (ideal or Carnot can reach far higher)
  const okPt = p => !p.warn.includes("liquefies") && !p.warn.includes("noExpansion");
  const tops = [
    ...(shown.includes("carnot") ? cur.points.filter(okPt).map(p => p.copCarnot) : []),
    ...(shown.includes("ideal") ? tiers.ideal.points.filter(okPt).map(p => p.cop) : []),
    ...(shown.includes("current") ? cur.points.filter(okPt).map(p => p.cop) : []),
  ].filter(isFinite);
  const linMax = Math.min(20, Math.max(1, Math.ceil(Math.max(...tops, 0) * 1.1 / 0.5) * 0.5));
  const yMin = yLog ? 0.1 : 0, yMax = yLog ? 100 : linMax;
  const x = P => m.l + (W - m.l - m.r) * Math.log(P / P_LO) / Math.log(P_HI / P_LO);
  const y = v => {
    const cl = Math.min(yMax, Math.max(yMin || 1e-3, v));
    return yLog ? m.t + (H - m.t - m.b) * (1 - Math.log(cl / yMin) / Math.log(yMax / yMin)) : m.t + (H - m.t - m.b) * (1 - cl / yMax);
  };
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "COP vs pressure" });
  for (const P of [1.1, 2, 5, 10, 20, 50, 100, 200].filter(P => P <= P_HI)) {
    svg.append(el("line", { class: "grid", x1: x(P), x2: x(P), y1: m.t, y2: H - m.b }));
    svg.append(el("text", { x: x(P), y: H - m.b + 14, "text-anchor": "middle" }, P));
  }
  const yStep = yMax <= 3 ? 0.25 : yMax <= 6 ? 1 : yMax <= 12 ? 2 : 5;
  const yt = yLog ? [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100] : Array.from({ length: Math.floor(yMax / yStep + 1e-9) + 1 }, (_, i) => +(i * yStep).toFixed(2));
  for (const v of yt) {
    svg.append(el("line", { class: "grid", x1: m.l, x2: W - m.r, y1: y(v), y2: y(v) }));
    svg.append(el("text", { x: m.l - 6, y: y(v) + 4, "text-anchor": "end" }, v));
  }
  svg.append(el("text", { x: (m.l + W - m.r) / 2, y: H - 2, "text-anchor": "middle" }, t("axisX")));
  svg.append(el("text", { x: m.l + 4, y: m.t + 10 }, "COP"));
  const line = (pts, key, cls) => {
    const ok = pts.filter(p => isFinite(p[key]) && p[key] > 0 && !p.warn.includes("liquefies") && !p.warn.includes("noExpansion"));
    if (!ok.length) return null;
    const d = ok.map((p, i) => `${i ? "L" : "M"}${x(p.P).toFixed(1)} ${y(p[key]).toFixed(1)}`).join("");
    svg.append(el("path", { d, class: cls }));
    return ok[ok.length - 1];
  };
  const tagAt = (pt, key, txt, cls) => { if (pt) svg.append(el("text", { x: W - m.r + 6, y: y(pt[key]) + 4, class: "lbl " + cls }, txt)); };
  const ends = [];
  if (shown.includes("carnot")) ends.push([line(cur.points, "copCarnot", "c-carnot"), "copCarnot", t("cCarnot"), ""]);
  if (shown.includes("ideal")) ends.push([line(tiers.ideal.points, "cop", "c-ideal"), "cop", t("cIdeal"), "lbl-cold"]);
  if (shown.includes("current")) ends.push([line(cur.points, "cop", "c-current"), "cop", t("cCurrent"), ""]);
  if (shown.includes("ac")) {
    for (const a of c.ac) {
      svg.append(el("line", { class: "c-ac", x1: m.l, x2: W - m.r, y1: y(a.cop), y2: y(a.cop) }));
      svg.append(el("line", { class: "c-acnet", x1: m.l, x2: W - m.r, y1: y(a.net), y2: y(a.net) }));
      ends.push([{ v: a.cop }, "v", `${t(a.key)} ${fmt(a.cop)}`, "lbl-hot"]);
      ends.push([{ v: a.net }, "v", `${t("netLine")} ${fmt(a.net)}`, "lbl-hot"]);
    }
  }
  // right-hand labels, nudged apart so they never overlap
  const labs = ends.filter(e => e[0]).map(([pt, key, txt, cls]) => ({ yy: y(pt[key]) + 4, txt, cls })).sort((a, b) => a.yy - b.yy);
  for (let i = 1; i < labs.length; i++) if (labs[i].yy - labs[i - 1].yy < 12) labs[i].yy = labs[i - 1].yy + 12;
  for (const l of labs) svg.append(el("text", { x: W - m.r + 6, y: l.yy, class: "lbl " + l.cls }, l.txt));
  // the dryer can switch several times close together (stage counts change with pressure):
  // every switch gets its line, but a label only where it clears the previous one
  let lastLbl = -Infinity;
  for (const d of cur.dryerSwitch) {
    svg.append(el("line", { class: "grid", x1: x(d.P), x2: x(d.P), y1: m.t, y2: H - m.b, "stroke-dasharray": "1 3" }));
    if (x(d.P) - lastLbl < 110) continue;
    svg.append(el("text", { x: x(d.P) + 3, y: m.t + 10 }, t("dryerSwitch")));
    lastLbl = x(d.P);
  }
  svg.append(el("line", { class: "cur", x1: x(s.P), x2: x(s.P), y1: m.t, y2: H - m.b }));
  if (cur.best) svg.append(el("circle", { class: "opt", cx: x(cur.best.P), cy: y(cur.best.cop), r: 5 }));
  if (isFinite(r.cop)) svg.append(el("circle", { class: "now", cx: x(s.P), cy: y(r.cop), r: 4 }));
  svg.onclick = ev => {
    const b = svg.getBoundingClientRect(), px = (ev.clientX - b.left) / b.width * W;
    const P = P_LO * Math.pow(P_HI / P_LO, (px - m.l) / (W - m.l - m.r));
    if (P >= P_LO && P <= P_HI) setVal("P", +P.toPrecision(3));
  };
  box.textContent = ""; box.append(svg);
}

// ---- page 1: comparison ----
function drawCompare(r, c) {
  document.querySelector(".cmp").hidden = !SHOW_AC;
  if (!SHOW_AC) return;
  const spot = c.ac.find(a => a.key === "spot"), split = c.ac.find(a => a.key === "split");
  const rows = [["outlet", "cop"], ["net", "net"]];
  const max = Math.max(1, r.cop, spot.cop, split.cop) * 1.05;
  let h = "";
  for (const [hk, key] of rows) {
    h += `<div class="h">${t(hk)}</div>`;
    for (const [name, v, cls] of [[t("air"), key === "cop" ? r.cop : r.cop, "air"], [t("spot"), spot[key], ""], [t("split"), split[key], ""]]) {
      const w = Math.max(0, Math.min(100, (isFinite(v) ? v : max) / max * 100));
      h += `<span>${name}</span><div class="bar ${cls}"><i style="width:${w.toFixed(1)}%"></i></div><span class="n">${fmt(v)}</span>`;
    }
  }
  $("bars").innerHTML = h;
  let n = `<p>${t("evenRet", { a: "<b>" + pct(spot.fEven) + "</b>", b: "<b>" + pct(split.fEven) + "</b>", f: s.fRet + "%" })}</p>`;
  if (s.mode !== "ideal" && isFinite(r.cop)) {
    if (r.cop >= spot.cop) n += `<p>${t("evenEtaYes")}</p>`;
    else {
      const be = breakEven(s, spot.cop);
      n += `<p>${be ? t("evenEta", { e: be.eta.toFixed(3) }) : t("evenEtaNo")}</p>`;
    }
  }
  $("note").innerHTML = n;
}

// ---- page 2: isometric plant ----
// ---- page 2: the plant, drawn with the anatomy kit (explorer/plant) ----
// The drawing is a pure function of a small spec taken from the same result as page 1.
// Building it settles the depth order of ~200 parts (1–2 s), so it runs in a worker and
// each spec's SVG is cached; sizes are rounded to ~10% steps so a slider drag reuses them.
const PLANT_SIZE = { width: 1200, height: 640 };
const q = (v, step = 0.1) => +Math.exp(Math.round(Math.log(Math.max(v, 1e-3)) / step) * step).toPrecision(3);
function plantSpec(r) {
  const S = r.s, iso = S.nComp === Infinity;
  return {
    nComp: iso ? "iso" : S.nComp, nExp: S.nExp, cooling: iso ? "air" : S.cooling === "tower" ? "water" : S.cooling, dryer: r.dryer,
    heat: S.heatUse === "absorption" && r.absCool > 0 ? "absorption" : S.heatUse === "orc" && r.orcPower > 0 ? "orc" : "none",
    rec: S.recPath, reheat: !!S.reheat,
    kwC: q(r.Wc / S.etaDrive / 1000), kwT: q(Math.max(r.Wt, 1) / 1000),
    duty: q(Math.max(r.mc * (r.comp.stages.length ? r.comp.heat : 0), 100) / 1000),
    kwAbs: q(Math.max(r.absCool, 1) / 1000), kwOrc: q(Math.max(r.orcPower, 1) / 1000), flow: q(r.mc),
    stageRatio: q(Math.pow(S.P / S.Pa, 1 / (iso ? 5 : S.nComp)), 0.05), nNozzle: S.nNozzle, dNozzle: S.dNozzle,
  };
}
const plantCache = new Map();
let plantWorker, plantBusy = null, plantNext = null, plantLib = null, plantShown = null, plantR = null;
function plantRequest(spec) {
  const key = JSON.stringify(spec);
  if (plantCache.has(key)) return showPlant(plantCache.get(key));
  $("stage").classList.add("busy"); $("stage").dataset.busy = t("drawing");
  if (plantBusy) { plantNext = spec; return; }
  plantBusy = key;
  if (plantWorker === undefined) {
    try {
      plantWorker = new Worker(new URL("plant/worker.mjs", document.baseURI), { type: "module" });
      plantWorker.onmessage = ({ data }) => plantDone(data);
      plantWorker.onerror = () => { plantWorker = null; plantFallback(spec); };
    } catch { plantWorker = null; }
  }
  if (plantWorker) plantWorker.postMessage({ id: key, spec, size: PLANT_SIZE });
  else plantFallback(spec);
}
async function plantFallback(spec) {
  try {
    plantLib = plantLib || await import(new URL("plant/plant.mjs", document.baseURI).href);
    const { svg, calls, dims, capped } = plantLib.buildPlant(spec, PLANT_SIZE);
    plantDone({ id: JSON.stringify(spec), svg, calls, dims, capped });
  } catch (err) { plantDone({ id: JSON.stringify(spec), error: String(err) }); }
}
function plantDone(data) {
  plantBusy = null;
  if (!data.error) {
    plantCache.set(data.id, data);
    if (plantCache.size > 40) plantCache.delete(plantCache.keys().next().value);
  } else console.error(data.error);
  const next = plantNext; plantNext = null;
  if (next) return plantRequest(next);
  if (!data.error) showPlant(data);
}
// Presented on a big screen: black background and white lines whatever the system theme.
document.documentElement.dataset.theme = "dark";
const isDark = () => document.documentElement.dataset.theme === "dark";
// callout text for each anchor the drawing reports
function callText(key, r) {
  const S = r.s, kwE = r.Wc / S.etaDrive / 1000, duty = (r.mc * (r.comp.stages.length ? r.comp.heat : 0) - (r.hotWater || 0)) / 1000; // heat left for the coolers
  const turb = t("nStages", { n: S.nExp }) + ` · ${kw(r.Wt)} kW`;
  switch (key) {
    case "motor": return [t("motor"), `${kwE.toFixed(1)} kW`];
    case "stages": return [t("compressor"), t("nStages", { n: S.nComp })];
    case "stagesIso": return [t("compressor"), t("isothermal")];
    case "coolers": return [t("coolers"), t("coolersSub", { w: S.Tw, m: t(S.cooling === "tower" ? "mTower" : "mSea"), q: duty.toFixed(1) })];
    case "tower": return [t("tower"), `${duty.toFixed(1)} kW${S.heatUse === "none" ? " · " + t("heatNone") : ""}`];
    case "water": return [t("waterLoop"), `${S.Tw} °C`];
    case "absorber": return [t("absorber"), `${kw(r.absCool)} kW`];
    case "orc": return S.heatUse === "heat" || S.heatUse === "hp" ? [t(S.heatUse === "hp" ? "hotWaterHp" : "hotWaterUnit"), `${kw(r.hotWater)} kW · ${S.hwT} °C`] : [t("orc"), `${kw(r.orcPower)} kW`];
    case "dryerF": return [t("dryerF"), ""];
    case "dryerD": return [t("dryerD"), t("purgeSub", { p: S.purge })];
    case "turbShaft": return [t("turbine"), turb + " · " + t("shaft")];
    case "turbSeat": return [t("turbine"), turb];
    case "generator": return [t("generator"), `${kw(r.recovered)} kW`];
    case "gap": return [t("farAway"), ""];
    case "header": return [t("coldDuct"), `${C(r.exp.stages.length ? r.exp.stages[r.exp.stages.length - 1].Tout : r.Ts)} °C`];
    case "nozzles": return [`${t("nozzle")} × ${S.nNozzle}`, `${C(r.Ts)} °C · ${t("sketch")}`];
    case "coils": return [t("coil"), t("nStages", { n: S.nExp - 1 })];
    case "person": return [t("person"), ""];
    case "cable": return [t("cable"), t("cableSub")];
    case "panel": return [t("panel"), t("panelSub")];
    case "ruler": return [t("ruler"), ""];
    default: return [key, ""];
  }
}
// Parts are numbered along the flow (power and compression first, then drying, the line, the
// turbine and the outlets), so the legend reads like the process.
const NOT_NUMBERED = ["person", "ruler", "gap"];
// Notes written beside the drawing, each with an arrow to its part: [anchor, offset as a share
// of the figure (into empty space), text]
function plantNotes(r) {
  const S = r.s, out = [];
  out.push(["gap", [0.03, -0.24], t("farAway")]);
  if (r.hotWater > 0) out.push(["coolers", [-0.16, 0.3], t("noteHeat", { h: kw(r.hotWater), T: S.hwT, to: t(S.heatUse === "hp" ? "hwToHp" : "hwToDesal") })]);
  if (r.recovered > 0) out.push(["generator", [-0.04, -0.24], t("noteWork", { p: kw(r.recovered) })]);
  return out;
}
const CALL_ORDER = ["motor", "stages", "stagesIso", "coolers", "tower", "water", "absorber", "orc", "dryerF", "dryerD", "gap", "turbShaft", "turbSeat", "generator", "cable", "panel", "header", "coils", "nozzles", "person", "ruler"];
function showPlant(data) {
  plantShown = data;
  const r = plantR, st = $("stage");
  st.classList.remove("busy");
  // the person stays in the drawing without a number; the floor break is labelled where it is
  const calls = data.calls.filter(c => !NOT_NUMBERED.includes(c.key)).sort((a, b) => CALL_ORDER.indexOf(a.key) - CALL_ORDER.indexOf(b.key));
  const notes = plantNotes(r).map(([k, d, text]) => ({ c: data.calls.find(c => c.key === k), d, text })).filter(n => n.c);
  st.innerHTML = `<div class="iso plant" data-theme="${isDark() ? "dark" : "light"}"><div class="fig">${data.svg}<div class="marks"><svg aria-hidden="true"></svg>${notes.map(n => `<div class="onfig" data-sx="${n.c.sx}" data-sy="${n.c.sy}" data-dx="${n.d[0]}" data-dy="${n.d[1]}"${n.c.key === "gap" ? "" : ' data-numbered="1"'}>${n.text}</div>`).join("")}${calls.map((c, i) =>
    `<div class="mk" data-k="${c.key}" data-sx="${c.sx}" data-sy="${c.sy}">${i + 1}</div>`).join("")}</div></div><div class="legend">${calls.map((c, i) => {
    const [a, b] = callText(c.key, r);
    return `<div class="lg" data-k="${c.key}"><i>${i + 1}</i><b>${a}</b>${b ? `<span>${b}</span>` : ""}</div>`;
  }).join("")}</div></div>`;
  placeMarks(st.querySelector(".plant"));
  drawPlant.dims = data.dims; drawPlant.capped = data.capped;
  drawReadout(r);
}
// Each marker sits on its part; one that would cover another is lifted clear and keeps a short
// tick down to a dot on its part. Hovering a marker or its legend entry lights up both.
function placeMarks(plant) {
  const fig = plant.querySelector(".fig"), W = fig.clientWidth, H = fig.clientHeight, placed = [], ticks = [];
  const d = plant.querySelector(".mk")?.offsetWidth || 20;
  for (const m of plant.querySelectorAll(".mk")) {
    const ax = m.dataset.sx / 100 * W, ay = m.dataset.sy / 100 * H;
    let y = ay;
    while (placed.some(p => Math.hypot(p[0] - ax, p[1] - y) < d + 3)) y -= d + 3;
    placed.push([ax, y]);
    m.style.left = ax + "px"; m.style.top = y + "px";
    if (y !== ay) ticks.push(`<line x1="${ax}" y1="${ay}" x2="${ax}" y2="${y + d / 2}"/><circle cx="${ax}" cy="${ay}" r="2"/>`);
  }
  // notes sit out in empty space, with an arrow back to their part
  for (const n of plant.querySelectorAll(".onfig")) {
    const ax = n.dataset.sx / 100 * W, ay = n.dataset.sy / 100 * H, dy = +n.dataset.dy;
    const lx = Math.min(W - 8, Math.max(8, ax + n.dataset.dx * W)), ly = ay + dy * H;
    n.style.left = lx + "px"; n.style.top = ly + "px";
    n.style.transform = `translate(-50%, ${dy > 0 ? "4px" : "calc(-100% - 4px)"})`;
    const w = n.offsetWidth; // keep the text inside the figure
    if (lx - w / 2 < 0) n.style.left = w / 2 + "px"; else if (lx + w / 2 > W) n.style.left = W - w / 2 + "px";
    // stop short of a numbered marker on the same spot, so the arrowhead shows
    const L = Math.hypot(ax - lx, ay - ly), cut = n.dataset.numbered ? (d / 2 + 3) / L : 0;
    ticks.push(`<line class="note" x1="${lx}" y1="${ly}" x2="${ax - (ax - lx) * cut}" y2="${ay - (ay - ly) * cut}" marker-end="url(#arrow)"/>`);
  }
  plant.querySelector(".marks svg").innerHTML = `<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" style="fill:var(--muted)"/></marker></defs>` + ticks.join("");
  const light = (k, on) => plant.querySelectorAll(`[data-k="${k}"]`).forEach(e => e.classList.toggle("hl", on));
  plant.querySelectorAll(".mk, .lg").forEach(e => {
    e.addEventListener("pointerenter", () => light(e.dataset.k, true));
    e.addEventListener("pointerleave", () => light(e.dataset.k, false));
  });
}
function drawPlant(r) {
  plantR = r;
  plantRequest(plantSpec(r));
}


function drawReadout(r) {
  const S = r.s;
  const rows = [[t("ambient"), `${S.Ta.toFixed(1)} °C`, `${S.Pa.toFixed(2)} bar`, ""]];
  r.comp.stages.forEach((st, i) => rows.push([t("compOut", { i: i + 1 }), `${C(st.Tout)} °C`, `${st.pOut.toFixed(1)} bar`, "hot"]));
  if (r.exp.throttled) rows.push([t("throttle"), `${C(r.comp.T1)} °C`, `${(S.P - S.dpLine).toFixed(1)} → ${r.exp.pIn.toFixed(1)} bar`, ""]);
  rows.push([t("turbIn"), `${C(r.comp.T1)} °C`, `${X.turbineInlet(S).toFixed(1)} bar`, ""]);
  // between stages the air rewarms in a reheat coil (that is where the cooling is handed over),
  // so each stage starts warm again; show that row or the outlets look stuck at one temperature
  r.exp.stages.forEach((st, i) => {
    if (i > 0 && S.reheat) rows.push([t("expIn", { i: i + 1 }), `${C(st.Tin)} °C`, `${r.exp.stages[i - 1].pOut.toFixed(2)} bar`, ""]);
    rows.push([t("expOut", { i: i + 1 }), `${C(st.Tout)} °C`, `${st.pOut.toFixed(2)} bar`, "cold"]);
  });
  const eComp = r.Wc / S.etaDrive, eAux = r.auxFan + r.auxDryer, H = r.mc * (r.comp.stages.length ? r.comp.heat : 0);
  const hw = r.hotWater || 0, heatOn = S.heatUse === "heat" || S.heatUse === "hp";
  const minus = v => "−" + kw(v);
  // [label, value, how it is worked out, class]
  const en = [
    [t("eComp"), kw(eComp), t("fComp", { w: kw(r.Wc), e: fmt(S.etaDrive) }), ""],
    ...(r.recovered > 0 ? [[t("eRec"), minus(r.recovered), t("fRec", { w: kw(r.Wt), e: fmt(S.etaRec) }), "cold"]] : []),
    [t("eAux"), kw(eAux), t("fAux", { q: kw(H - hw), p: fmt(S.auxFan, 0) }) + (r.auxDryer > 0 ? t("fDry", { d: kw(r.auxDryer) }) : ""), ""],
    ...(hw > 0 ? [[t("hwRow"), kw(hw), t("fHw", { H: kw(H), p: pct(hw / H) }) + (r.heat.capped ? t("fHwCap", { s: fmt(S.hwShare, 0), T: fmt(S.hwT, 0) }) : ""), "hot"]] : []),
    ...(r.orcPower > 0 ? [[t(heatOn ? "eHw" : "eOrc", { f: S.heatValue }), minus(r.orcPower), heatOn ? t("fHwVal", { h: kw(hw), f: S.heatValue }) : "", ""]] : []),
    [t("eNet"), kw(r.E), [kw(eComp), ...(r.recovered > 0 ? ["− " + kw(r.recovered)] : []), "+ " + kw(eAux), ...(r.orcPower > 0 ? ["− " + kw(r.orcPower)] : [])].join(" "), ""],
    [t("qAir"), kw(r.coolAir), t("fCool", { m: fmt(r.m, 2), a: fmt(S.Ta, 1), o: C(r.exp.Tout) }), "cold"],
    ...(r.absCool > 0 ? [[t("qAbs"), kw(r.absCool), "", "cold"], [t("qTot"), kw(r.Q), "", "cold"]] : []),
    ["COP", fmt(r.cop), `${kw(r.Q)} ÷ ${kw(r.E)}`, "cold"],
  ];
  const tr = (cells, cls) => `<tr class="${cls}">${cells.map(c => `<td>${c}</td>`).join("")}</tr>`;
  $("readout").innerHTML =
    `<h3>${t("rStations")}</h3><table>${rows.map(([a, b, c, cls]) => tr([a, b, c], cls)).join("")}</table>` +
    `<h3>${t("rEnergy")}</h3><table class="en">${en.map(([a, b, f, cls]) => `<tr class="${cls}"><td>${a}<div class="how">${f}</div></td><td>${b}</td></tr>`).join("")}</table>`;
}

buildRail();
schedule();
// Scale each 1600 × 900 slide to the window, so both pages stay exactly 16:9.
// ---- page 3: energy ledger ----
// The two streams that could be recovered, with a share applied to each. The shares are
// the page's own (not part of the model state); a recovery method is just a preset share.
let lw = 0.9, lh = 0, lk = "none", lState = null, lSync = "";
const lF = Lg => Lg.heat.find(h => h.key === lk).f;
// Full rebuild when the model state changes; a slider drag only refreshes the numbers and
// the chart (lUpdate), so the slider under the pointer is never replaced mid-drag.
function drawLedger() {
  const st = { ...s, nComp: s.nComp === "auto" ? system(s).s.nComp : s.nComp };
  const Lg = ledger(st), r0 = system(s), cmp = compare(s, r0);
  // a new page 1 setup resets the shares to it, so the ledger starts at the page 1 COP
  const key = JSON.stringify(s);
  if (key !== lSync) {
    lSync = key;
    lw = r0.s.recPath === "none" ? 0 : r0.s.etaRec;
    lk = Lg.heat.some(h => h.key === r0.s.heatUse) ? r0.s.heatUse : "none";
    lh = Lg.H ? (r0.hotWater || 0) / Lg.H : 0;
  }
  lState = { Lg, cmp };
  const opts = X.BY_KEY.heatUse.options;
  // the sliders stop at what the equipment can do: work at 95%, heat at the share the supply temperature allows
  lw = Math.min(lw, 0.95);
  const hMax = Math.max(Lg.heat.find(h => h.key === lk).h, 0.005);
  lh = Math.min(lh, hMax);
  $("ledger").innerHTML = `
    <h3>${t("lTitle")}</h3>
    <div class="lctl"><div class="lab"><span>${t("lW")}</span><span class="val" id="lwv"></span></div>
      <input type="range" id="lw" min="0" max="0.95" step="0.01" value="${lw}" aria-label="${t("lW")}"><div class="hint">${t("lWHint")}</div></div>
    <div class="lctl"><div class="lab"><span>${t("lH")}</span><span class="val" id="lhv"></span></div>
      <div class="seg" id="lk">${Lg.heat.map(h => `<button type="button" data-k="${h.key}">${L(opts[h.key])}</button>`).join("")}</div>
      <input type="range" id="lh" min="0" max="${hMax}" step="0.005" value="${lh}" aria-label="${t("lH")}"${lk === "none" ? " hidden" : ""}><div class="hint">${t("lHHint", { a: pct(Lg.heat.find(h => h.key === "heat").h), b: pct(Lg.heat.find(h => h.key === "hp").h) })}</div></div>
    <div class="lbig"><div><div class="k">${t("lCop")}</div><div class="v" id="lcop"></div></div>
      <div><div class="k">${t("lNow")}</div><div class="v" style="font-size:26px;color:var(--ink)">${fmt(r0.cop)}</div></div></div>
    <div class="hint">${t("lFormula")}</div><div class="hint" id="lform"></div>
`;
  $("lw").oninput = e => { lw = +e.target.value; lUpdate(); };
  $("lh").oninput = e => { lh = +e.target.value; lUpdate(); };
  document.querySelectorAll("#lk button").forEach(b => b.onclick = () => {
    lk = b.dataset.k;
    const h = Lg.heat.find(x => x.key === lk);
    lh = h.h;
    drawLedger();
  });
  document.querySelectorAll(".ltab tr.pick").forEach(tr => tr.onclick = () => {
    const m = lMethods(lState.Lg).find(x => x.id === tr.dataset.id);
    if (m.kind === "w") lw = m.v; else { lh = m.v; lk = m.key; }
    drawLedger();
  });
  lUpdate();
}

function lMethods(Lg) {
  return [
    ...Lg.work.map(m => ({ id: "w_" + m.key, kind: "w", v: m.w, ok: true, on: Math.abs(lw - m.w) < 1e-6, cop: Lg.cop(m.w, lh, lF(Lg)) })),
    ...Lg.heat.map(m => ({ id: "h_" + m.key, kind: "h", key: m.key, v: m.h, f: m.f, ok: m.ok, on: lk === m.key && Math.abs(lh - m.h) < 1e-6, cop: Lg.cop(lw, m.h, m.f) })),
  ];
}

function lUpdate() {
  const { Lg, cmp } = lState;
  const methods = lMethods(Lg), f = lF(Lg), h = lk === "none" ? 0 : lh;
  $("lwv").textContent = pct(lw);
  $("lhv").textContent = lk === "none" ? "0%" : pct(lh);
  $("lcop").textContent = fmt(Lg.cop(lw, h, f));
  $("lform").textContent = `= ${kw(Lg.Q)} ÷ (${kw(Lg.Ecomp)} − ${pct(lw)} × ${kw(Lg.Wt)} + ${kw(Lg.aux(h))} − ${pct(h)} × ${kw(Lg.H)} × ${f})`;
  document.querySelectorAll("#lk button").forEach(b => b.setAttribute("aria-pressed", b.dataset.k === lk));
  document.querySelectorAll(".ltab tr[data-id]").forEach(tr => {
    const m = methods.find(x => x.id === tr.dataset.id);
    tr.classList.toggle("on", m.on);
    if (m.ok) tr.querySelector(".cop").textContent = fmt(m.cop);
  });
  drawLedgerChart(Lg, cmp);
}

function drawLedgerChart(Lg, cmp) {
  const box = $("lchart");
  const W = Math.max(420, box.clientWidth || 900), H = Math.max(300, box.clientHeight || 600);
  const m = { l: 46, r: 210, t: 30, b: 40 };
  const xs = w => m.l + (W - m.r - m.l) * w;
  const lines = Lg.heat.filter(h => h.ok);
  const curve = (h, f) => Array.from({ length: 51 }, (_, i) => i / 50).map(w => [w, Lg.cop(w, h, f)]);
  const all = [...lines.map(h => curve(h.h, h.f)), curve(lk === "none" ? 0 : lh, lF(Lg))];
  const acList = SHOW_AC ? cmp.ac : [];
  const acs = acList.map(a => a.cop);
  const yMax = Math.min(12, Math.max(...acs, ...all.flat().map(p => p[1]).filter(isFinite)) * 1.1);
  const ys = v => H - m.b - (H - m.t - m.b) * Math.min(v, yMax) / yMax;
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": t("lChart") });
  svg.append(el("text", { x: m.l, y: 16, class: "title" }, t("lChart")));
  const step = yMax > 6 ? 2 : yMax > 3 ? 1 : 0.5;
  for (let v = 0; v <= yMax + 1e-9; v += step) {
    svg.append(el("line", { x1: m.l, x2: W - m.r, y1: ys(v), y2: ys(v), class: "grid" }));
    svg.append(el("text", { x: m.l - 6, y: ys(v) + 4, "text-anchor": "end" }, fmt(v, v % 1 ? 1 : 0)));
  }
  for (let w = 0; w <= 1 + 1e-9; w += 0.2) svg.append(el("text", { x: xs(w), y: H - m.b + 16, "text-anchor": "middle" }, pct(w)));
  svg.append(el("text", { x: (m.l + W - m.r) / 2, y: H - 6, "text-anchor": "middle" }, t("lAxisX")));
  svg.append(el("line", { x1: m.l, x2: m.l, y1: m.t, y2: H - m.b, class: "axis" }));
  svg.append(el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b, class: "axis" }));
  // work methods: vertical marks
  for (const w of Lg.work.filter(w => w.key !== "none")) {
    svg.append(el("line", { x1: xs(w.w), x2: xs(w.w), y1: m.t, y2: H - m.b, class: "mark" }));
    svg.append(el("text", { x: xs(w.w) + 4, y: m.t + 10 }, t("m_w_" + w.key).split("（")[0].split(" (")[0]));
  }
  // air conditioners for reference
  acList.forEach(a => {
    svg.append(el("line", { x1: m.l, x2: W - m.r, y1: ys(a.cop), y2: ys(a.cop), class: "ac" }));
  });
  const labels = [];
  acList.forEach(a => labels.push({ y: ys(a.cop), text: `${t(a.key)} ${fmt(a.cop)}`, color: "var(--ac)" }));
  const colors = { none: "var(--muted)", heat: "var(--frontier)", hp: "var(--hot)" };
  const path = pts => pts.filter(p => isFinite(p[1])).map((p, i) => `${i ? "L" : "M"}${xs(p[0]).toFixed(1)},${ys(p[1]).toFixed(1)}`).join("");
  lines.forEach((h, i) => {
    const pts = curve(h.h, h.f);
    svg.append(el("path", { d: path(pts), class: "ln", stroke: colors[h.key] }));
    const end = pts[pts.length - 1][1];
    labels.push({ y: ys(end), text: `${t("m_h_" + h.key, { f: h.f }).replace(/^热：|^Heat: /, "").split("（")[0].split(" (")[0]} ${fmt(end)}`, color: colors[h.key] });
  });
  const cur = curve(lk === "none" ? 0 : lh, lF(Lg));
  svg.append(el("path", { d: path(cur), class: "ln", stroke: "var(--cold)", "stroke-width": 2.6 }));
  const c = Lg.cop(lw, lk === "none" ? 0 : lh, lF(Lg));
  if (isFinite(c)) svg.append(el("circle", { cx: xs(lw), cy: ys(c), r: 6, class: "pt" }));
  // right-hand labels, nudged apart
  labels.sort((a, b) => a.y - b.y);
  for (let i = 1; i < labels.length; i++) if (labels[i].y - labels[i - 1].y < 14) labels[i].y = labels[i - 1].y + 14;
  for (const l of labels) svg.append(el("text", { x: W - m.r + 8, y: l.y + 4, fill: l.color, style: `fill:${l.color}` }, l.text));
  box.textContent = ""; box.append(svg);
}

// ---- page 4: why the COP stays low ----
// The air conditioners (spot cooler, split AC) are left out of every view for now: their
// ratings are not yet on the same footing as the model. Flip to bring them back.
const SHOW_AC = false;
const SHOW_PLANT = false; // the Qatar chiller-plant band on page 4: self-reported and plant-only, so off for now
const QATAR = { lo: 3.7, hi: 4.0 }; // Qatar Cool plant kW/TR 0.87–0.95, measured 2010–12 (see the memo's sources)
function drawWhy(r, c) {
  // flow: electricity steps, then the cooling beside them
  const f = WHY.flow(r), amp = WHY.amplification(s);
  const steps = [
    { k: "wfComp", from: 0, to: f.Ecomp, cls: "var(--ac)" },
    { k: "wfRec", from: f.Ecomp, to: f.Ecomp - f.recovered, cls: "var(--good)" },
    { k: "wfAux", from: f.Ecomp - f.recovered, to: f.Ecomp - f.recovered + f.aux, cls: "var(--warn)" },
    ...(f.orc > 0 ? [{ k: s.heatUse === "heat" || s.heatUse === "hp" ? "wfHw" : "wfOrc", from: f.Ecomp - f.recovered + f.aux, to: f.E, cls: "var(--good)" }] : []),
    { k: "wfNet", from: 0, to: f.E, cls: "var(--ink)" },
    { k: "wfCool", from: 0, to: f.Q, cls: "var(--cold)", gap: true },
  ];
  const FW = 560, FH = 230, fy0 = 14, fy1 = 196, top = Math.max(...steps.map(x => Math.max(x.from, x.to)), 1);
  const fy = v => fy1 - (fy1 - fy0) * v / top;
  const bw = 58, gapX = (FW - 20) / (steps.length + 0.5);
  let svg = `<svg viewBox="0 0 ${FW} ${FH}" role="img" aria-label="${t("wfTitle")}">`;
  let xPos = 10;
  steps.forEach((st, i) => {
    if (st.gap) xPos += gapX * 0.5;
    const yA = fy(Math.max(st.from, st.to)), yB = fy(Math.min(st.from, st.to));
    svg += `<rect x="${xPos}" y="${yA}" width="${bw}" height="${Math.max(1, yB - yA)}" fill="${st.cls}" opacity="${st.k === "wfNet" ? 0.9 : 0.85}"><title>${t(st.k)} ${kw(Math.abs(st.to - st.from))} kW</title></rect>`;
    const sign = st.k === "wfRec" || st.k === "wfOrc" || st.k === "wfHw" ? "−" : st.k === "wfAux" ? "+" : "";
    svg += `<text class="ink" x="${xPos + bw / 2}" y="${yA - 5}" text-anchor="middle">${sign}${kw(Math.abs(st.to - st.from))}</text>`;
    svg += `<text x="${xPos + bw / 2}" y="${fy1 + 16}" text-anchor="middle">${t(st.k)}</text>`;
    if (i < steps.length - 1 && !steps[i + 1].gap && st.k !== "wfNet") svg += `<line x1="${xPos + bw}" x2="${xPos + gapX}" y1="${fy(st.to)}" y2="${fy(st.to)}" stroke="var(--muted)" stroke-dasharray="2 2"/>`;
    xPos += gapX;
  });
  svg += `<text class="big" x="${FW - 10}" y="${fy0 + 4}" text-anchor="end">COP = ${kw(f.Q)} ÷ ${kw(f.E)} = ${fmt(f.cop)}</text></svg>`;
  $("wflow").innerHTML = `<h3>${t("wfTitle")}</h3><p class="lead">${t("wfLead", { b: pct(f.backWork), a: (amp * 100).toFixed(1) + "%" })}</p>${svg}`;

  // design points
  const pts = WHY.designPoints(s);
  const cold = pts.find(p => p.key === "p200");
  const spot = c.ac.find(a => a.key === "spot").cop;
  const PW = 560, rowH = 46, PH = 34 + pts.length * rowH + 10, lx = 196, rx = PW - 70;
  const vmax = Math.max(5, ...pts.map(p => isFinite(p.copIdeal) ? p.copIdeal : 0), QATAR.hi) * 1.05;
  const px = v => lx + (rx - lx) * Math.min(v, vmax) / vmax;
  let ps = `<svg viewBox="0 0 ${PW} ${PH}" role="img" aria-label="${t("wpTitle")}">`;
  ps += `<rect x="${lx}" y="10" width="10" height="8" fill="var(--cold)"/><text x="${lx + 14}" y="18">${t("wpNow")}</text>`;
  ps += `<rect x="${lx + 130}" y="10" width="10" height="8" fill="none" stroke="var(--muted)"/><text x="${lx + 144}" y="18">${t("wpIdeal")}</text>`;
  if (SHOW_AC) ps += `<line x1="${px(spot)}" x2="${px(spot)}" y1="26" y2="${PH - 6}" stroke="var(--ac)" stroke-dasharray="5 4"/><text x="${px(spot) + 4}" y="${PH - 6}">${t("spot")} ${fmt(spot)}</text>`;
  pts.forEach((p, i) => {
    const y = 34 + i * rowH;
    ps += `<text class="ink" x="0" y="${y + 13}">${t("wp_" + p.key, { p: fmt(s.P, 1) })}</text>`;
    ps += `<text x="0" y="${y + 28}">${t("wpOut")} ${p.Tmin.toFixed(0)} °C${p.warn.includes("liquefies") ? " · " + t("wpLiquid") : ""}</text>`;
    if (isFinite(p.copIdeal)) ps += `<rect x="${lx}" y="${y + 19}" width="${px(p.copIdeal) - lx}" height="12" fill="none" stroke="var(--muted)"><title>${t("wpIdeal")} ${fmt(p.copIdeal)}</title></rect><text x="${px(p.copIdeal) + 6}" y="${y + 29}">${fmt(p.copIdeal)}</text>`;
    ps += `<rect x="${lx}" y="${y + 3}" width="${Math.max(1, px(p.cop) - lx)}" height="14" fill="var(--cold)"><title>${t("wpNow")} ${fmt(p.cop)}</title></rect><text class="ink" x="${px(p.cop) + 6}" y="${y + 14}">${fmt(p.cop)}</text>`;
  });
  ps += `</svg>`;
  $("wpts").innerHTML = `<h3>${t("wpTitle")}</h3><p class="lead">${t("wpLead", { c: fmt(cold.copIdeal) })}</p>${ps}`;

  // efficiency sweep
  const sw = WHY.etaSweep(s);
  const lastCur = sw.at(-1).cur;
  let cross = null;
  for (let i = 1; i < sw.length; i++) if (sw[i - 1].beyond < spot && sw[i].beyond >= spot) cross = sw[i - 1].eta + (spot - sw[i - 1].beyond) / (sw[i].beyond - sw[i - 1].beyond) * (sw[i].eta - sw[i - 1].eta);
  if (cross === null && sw[0].beyond >= spot) cross = sw[0].eta;
  $("wetaLead").innerHTML = `<h3 style="font:600 15px var(--f-display);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0 0 4px">${t("weTitle")}</h3><p class="lead" style="font-size:13px;margin:0 0 8px">${(SHOW_AC ? t("weLead", { c: fmt(lastCur), x: cross === null ? t("weNever") : cross.toFixed(2) }) : t("weLeadNoAc", { c: fmt(lastCur), d: fmt(sw.at(-1).beyond) }))}</p>`;
  const box = $("weta");
  const W = Math.max(420, box.clientWidth || 860), H = Math.max(260, box.clientHeight || 600);
  const m = { l: 44, r: 250, t: 14, b: 44 };
  const ex = v => m.l + (W - m.l - m.r) * (v - 0.8) / 0.2;
  const yMax = Math.min(6, Math.max(SHOW_PLANT ? QATAR.hi : 0, ...sw.map(x => x.beyond).filter(isFinite)) * 1.08);
  const ey = v => H - m.b - (H - m.t - m.b) * Math.min(v, yMax) / yMax;
  const g = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": t("weTitle") });
  g.append(el("rect", { x: ex(0.88), y: m.t, width: ex(0.92) - ex(0.88), height: H - m.t - m.b, fill: "var(--ac)", opacity: 0.18 }));
  g.append(el("text", { x: ex(0.88), y: m.t + 12 }, t("weBand")));
  if (SHOW_PLANT) g.append(el("rect", { x: m.l, y: ey(QATAR.hi), width: W - m.l - m.r, height: ey(QATAR.lo) - ey(QATAR.hi), fill: "var(--ac)", opacity: 0.25 }));
  for (let v = 0; v <= yMax + 1e-9; v += 1) {
    g.append(el("line", { x1: m.l, x2: W - m.r, y1: ey(v), y2: ey(v), stroke: "var(--rule)" }));
    g.append(el("text", { x: m.l - 6, y: ey(v) + 4, "text-anchor": "end" }, String(v)));
  }
  for (let v = 0.8; v <= 1.0001; v += 0.05) g.append(el("text", { x: ex(v), y: H - m.b + 16, "text-anchor": "middle" }, v.toFixed(2)));
  g.append(el("text", { x: (m.l + W - m.r) / 2, y: H - 8, "text-anchor": "middle" }, t("weAxis")));
  const labels = SHOW_PLANT ? [{ y: ey((QATAR.lo + QATAR.hi) / 2), text: t("weQatar"), fill: "var(--muted)" }] : [];
  if (SHOW_AC) {
    g.append(el("line", { x1: m.l, x2: W - m.r, y1: ey(spot), y2: ey(spot), stroke: "var(--ac)", "stroke-dasharray": "6 4" }));
    labels.push({ y: ey(spot), text: `${t("spot")} ${fmt(spot)}`, fill: "var(--muted)" });
  }
  const line = (key, color, w) => {
    const d = sw.map((p, i) => `${i ? "L" : "M"}${ex(p.eta).toFixed(1)},${ey(p[key]).toFixed(1)}`).join("");
    g.append(el("path", { d, fill: "none", stroke: color, "stroke-width": w }));
    sw.forEach(p => { const dot = el("circle", { cx: ex(p.eta), cy: ey(p[key]), r: 3, fill: color }); dot.append(el("title", {}, `${p.eta.toFixed(2)}: COP ${fmt(p[key])}`)); g.append(dot); });
  };
  line("beyond", "var(--muted)", 2);
  line("cur", "var(--cold)", 3);
  labels.push({ y: ey(sw.at(-1).beyond), text: `${t("weBeyond")} ${fmt(sw.at(-1).beyond)}`, fill: "var(--muted)" });
  labels.push({ y: ey(lastCur), text: `${t("weCur")} ${fmt(lastCur)}`, fill: "var(--cold)" });
  // where this page-1 state sits
  // (the two efficiencies can differ on page 1; their mean puts the mark on the curve's scale)
  const here = (r.s.etaC + r.s.etaT) / 2;
  if (here >= 0.8 && here <= 1) {
    const hc = el("circle", { cx: ex(here), cy: ey(r.cop), r: 7, fill: "none", stroke: "var(--ink)", "stroke-width": 2 }); hc.append(el("title", {}, `${t("cCurrent")}: COP ${fmt(r.cop)}`)); g.append(hc);
    g.append(el("text", { x: ex(here) + 12, y: ey(r.cop) + 22, style: "fill:var(--ink)" }, `${t("cCurrent")} ${fmt(r.cop)}`));
  }
  if (SHOW_AC && cross !== null) g.append(el("circle", { cx: ex(cross), cy: ey(spot), r: 6, fill: "none", stroke: "var(--ink)" }));
  labels.sort((a, b) => a.y - b.y);
  for (let i = 1; i < labels.length; i++) if (labels[i].y - labels[i - 1].y < 15) labels[i].y = labels[i - 1].y + 15;
  for (const l of labels) g.append(el("text", { x: W - m.r + 8, y: l.y + 4, style: `fill:${l.fill}` }, l.text));
  box.textContent = ""; box.append(g);
}

function fitSlides() {
  const w = Math.min(innerWidth - 32, (innerHeight - 24) * 16 / 9);
  document.documentElement.style.setProperty("--sw", w + "px");
  document.documentElement.style.setProperty("--s", w / 1600);
}
fitSlides();
// the chart is sized from its box, which settles only after fonts and the first layout
let chartSize = "";
new ResizeObserver(([e]) => { const k = Math.round(e.contentRect.width) + "x" + Math.round(e.contentRect.height); if (k !== chartSize) { chartSize = k; schedule(); } }).observe($("chart"));
let wSize = "";
new ResizeObserver(([e]) => { const k = Math.round(e.contentRect.width) + "x" + Math.round(e.contentRect.height); if (k !== wSize) { wSize = k; schedule(); } }).observe($("weta"));
let lSize = "";
new ResizeObserver(([e]) => { const k = Math.round(e.contentRect.width) + "x" + Math.round(e.contentRect.height); if (k !== lSize) { lSize = k; schedule(); } }).observe($("lchart"));
let rz; addEventListener("resize", () => { fitSlides(); clearTimeout(rz); rz = setTimeout(schedule, 150); });
})();

// ---------- parameter registry ----------
// Single source of every number the explorer uses. Each entry carries both
// languages, the ideal and realistic defaults, its range, the control the
// panel draws for it, and where the default comes from.
// status: "fixed" = physical constant, "sourced" = checked against a cited source,
// "pending" = estimate still to be checked, "placeholder" = chosen for now, no basis yet.

const CONST = { CP: 1005, R: 287.05, GAMMA: 1.4 }; // dry air near 300 K
CONST.K = CONST.R / CONST.CP; // (γ − 1)/γ for an ideal gas with these cp and R

const GROUPS = {
  conditions: { zh: "工况", en: "Conditions" },
  components: { zh: "部件", en: "Components" },
  recovery: { zh: "回收", en: "Recovery" },
  delivery: { zh: "送风与对比", en: "Delivery & comparison" },
  curve: { zh: "曲线", en: "Curve" },
};

const MODES = {
  ideal: { zh: "理论理想", en: "Theoretical ideal", short: { zh: "理论理想", en: "Theoretical ideal" } },
  best: { zh: "工业最高水平", en: "Industry best", short: { zh: "工业最高水平", en: "Industry best" } },
  real: { zh: "工业现状", en: "Industry today", short: { zh: "现有工业", en: "Today" } },
  frontier: { zh: "突破目标（超出当前工业水平）", en: "Beyond industry today", short: { zh: "突破目标", en: "Beyond" } },
  custom: { zh: "自定义", en: "Custom" },
};

// control: slider | number | stepper | segmented | select | toggle
// advanced: true puts it in the collapsed advanced area
// showIf(state): hides the control when it has no meaning for the current setup
// "auto" as a default means the model chooses it (see auto() below)
// front: shown on the face of the panel; everything else sits in the engineer drawer
// best: default in the "industry best" mode = the best value in service today (falls back to real),
//   with bestSrc saying where that value comes from
// frontier: default in the "beyond industry" mode (falls back to real); industryMax: the best
// value in service today, shown beside any frontier value that exceeds it
const PARAMS = [
  // ---- conditions ----
  { key: "P", group: "conditions", front: true, control: "slider", scale: "log", unit: "bar(abs)",
    zh: "压力", en: "Pressure", ideal: 4, real: 4, min: 1.1, max: 200, step: 0.1,
    status: "sourced", src: {
      zh: "上限 200 bar = 工业透平膨胀机的最高入口压力（Atlas Copco 膨胀机“入口压力最高 200 bar(a)”；Baker Hughes 为 150 bar）。再高没有能直接接收的空气涡轮，只能先节流，白白损失。参考：Huntorf 储能电站盐穴 43–70 bar",
      en: "Top of 200 bar = the highest inlet pressure of industrial turboexpanders (Atlas Copco: \"inlet pressures of up to 200 bar (a)\"; Baker Hughes: 150 bar). No air turbine takes more, so anything higher would be throttled and wasted. For reference, Huntorf CAES caverns run 43–70 bar" },
    marks: [7, 43, 70, 200] },
  { key: "Ta", group: "conditions", front: true, control: "slider", unit: "°C",
    zh: "环境温度", en: "Ambient temperature", ideal: 35, real: 35, min: 15, max: 50, step: 0.5,
    status: "sourced", src: { zh: "默认 35 °C（按 CZ 设定）。参考：迪拜 8 月平均日最高气温 42.1 °C（迪拜气象局；NOAA 1991–2020 迪拜机场 41.9 °C）；纪录最高 49.0 °C", en: "Default 35 °C (set by CZ). For reference, Dubai August mean daily maximum 42.1 °C (Dubai Meteorological Office; NOAA 1991–2020 Dubai airport normals 41.9 °C); record 49.0 °C" } },
  { key: "RH", group: "conditions", control: "slider", unit: "%",
    zh: "相对湿度", en: "Relative humidity", ideal: 53, real: 53, min: 0, max: 100, step: 1,
    status: "sourced", src: { zh: "迪拜 8 月平均相对湿度 53%（迪拜气象局）。这是全天平均，午后最热时更低，因此露点和湿球温度偏保守；用于露点、干燥器选择和冷却塔湿球温度，不计潜热", en: "Dubai August mean relative humidity 53% (Dubai Meteorological Office). A daily mean, lower in the hot afternoon, so dew point and wet bulb err high; drives dew point, dryer choice and cooling-tower wet bulb, no latent load" } },
  { key: "m", group: "conditions", control: "slider", scale: "log", unit: "kg/s",
    zh: "质量流量", en: "Mass flow", ideal: "auto", real: "auto", min: 10, max: 500000, step: 1, // g/s; shown in kg/s
    dynMax: s => mMax(s.P).max,
    status: "sourced", src: { zh: "压缩机吸入的空气量，全部经涡轮从出风口排出（出口卷入的环境空气另计）。内部以 g/s 计算、以 kg/s 显示。COP 与流量无关；流量决定冷量、kW 和设备尺寸。拖压力时跳到该压力段常见工业机组的建议值，之后可在 0.01 kg/s 到该段单台上限之间自由拖动。≤ 10 bar：建议 5.1 kg/s（Atlas Copco ZH 9000 离心机，254.9 m³/min），上限约 500 kg/s（MAN AR-MAX1 空分主空压机，150 万 m³/h，64 MW，Turbomachinery Magazine）。10–70 bar：建议 1.07 kg/s（Atlas Copco PBE 1600 VSD+，25 bar，3200 m³/h），上限 108 kg/s（Huntorf 储能电站压缩，46–66 bar，60 MW）。70–200 bar：建议 0.54 kg/s（Burckhardt 标准高压往复机，约 1500 Nm³/h，待核实），上限约 45 kg/s（油气回注离心压缩机到 650 barg、32 MW 燃机驱动，Turbomachinery Magazine；按本模型 1→200 bar 每 kg 约 0.70 MJ 电耗折算，估算）", en: "Air drawn in by the compressor, all of it leaving the turbines at the outlets (ambient air entrained there comes on top). Kept in g/s inside, shown in kg/s. COP does not depend on flow; flow sets the cooling, the kW and the equipment sizes. Moving the pressure sets a suggested value, a common industrial unit for the band; drag freely afterwards from 0.01 kg/s to the band's single-unit top. ≤ 10 bar: suggested 5.1 kg/s (Atlas Copco ZH 9000 centrifugal, 254.9 m³/min), top ~500 kg/s (MAN AR-MAX1 air-separation main air compressor, 1.5 million m³/h, 64 MW, Turbomachinery Magazine). 10–70 bar: suggested 1.07 kg/s (Atlas Copco PBE 1600 VSD+, 25 bar, 3200 m³/h), top 108 kg/s (Huntorf CAES charging, 46–66 bar, 60 MW). 70–200 bar: suggested 0.54 kg/s (Burckhardt standard high-pressure reciprocating, ~1500 Nm³/h, to check), top ~45 kg/s (oil-and-gas reinjection centrifugals to 650 barg on a 32 MW gas turbine, Turbomachinery Magazine; converted at this model's ~0.70 MJ/kg for 1 to 200 bar, an estimate)" } },
  { key: "Pa", group: "conditions", control: "number", advanced: true, unit: "bar",
    zh: "大气压", en: "Atmospheric pressure", ideal: 1.01325, real: 1.01325, min: 0.9, max: 1.05, step: 0.001,
    status: "fixed", src: { zh: "标准大气压", en: "Standard atmosphere" } },

  // ---- components ----
  { key: "nComp", group: "components", control: "auto", unit: "",
    zh: "压缩级数（随压力自动）", en: "Compression stages (set by pressure)", ideal: Infinity, real: "auto", min: 1, max: 5, step: 1, allowInfinity: true,
    status: "sourced", src: { zh: "随压力自动，不手调：取让每级压比不超过 3 的最少级数（不为刷 COP 而堆级数）。每级 3 = 常见值：厂房用齿轮式离心机 2–4 级、每级约 2.25（Turbomachinery Magazine）。理论理想 = 等温压缩（无穷多级）。上限 5 级 = 工业最高：Sauer 往复式高压空压机“最多五级”、终压 500 barg；Sauer Hurricane 4 级到 400 barg；厂房用齿轮式离心机 2–4 级、每级约 2.25（Turbomachinery Magazine）。每级 4.5 = Hurricane 4 级到 400 bar 的平均每级压比", en: "Set by pressure, not by hand: the fewest stages that keep each stage at or under 3 (no stacking stages for COP). 3 per stage is typical: plant-air integrally geared centrifugals run 2–4 stages at ~2.25 each (Turbomachinery Magazine). Theoretical ideal = isothermal compression (infinitely many stages). Cap of 5 = industrial maximum: Sauer high-pressure reciprocating units use \"up to five stages\" to 500 barg; Sauer Hurricane, 4 stages to 400 barg; plant-air integrally geared units 2–4 stages at ~2.25 per stage (Turbomachinery Magazine). 4.5 per stage = Hurricane's average over 4 stages to 400 bar" } },
  { key: "rcMax", group: "components", control: "number", unit: "", noUi: true, // fixed; stated in the stage-count basis
    zh: "每级压缩比上限（自动选级用）", en: "Per-stage compression ratio limit (for auto stages)", ideal: 3, real: 3, min: 1.5, max: 4.5, step: 0.1,
    status: "sourced", src: { zh: "常见值 3：厂房用齿轮式离心机 2–4 级、每级约 2.25（Turbomachinery Magazine）；工业上限 4.5 = Sauer Hurricane 4 级到 400 bar 的平均每级压比", en: "Typical 3: plant-air integrally geared centrifugals run 2–4 stages at ~2.25 each (Turbomachinery Magazine); industrial limit 4.5 = Sauer Hurricane's average over 4 stages to 400 bar" } },
  { key: "etaC", group: "components", control: "slider", unit: "",
    best: 0.88, bestSrc: { zh: "大型离心压缩机单级等熵效率约 0.85–0.88（待核实）", en: "Large centrifugal stage isentropic efficiency ~0.85–0.88 (to check)" },
    zh: "每级压缩等熵效率 ηₛ", en: "Compressor stage isentropic efficiency ηₛ", ideal: 1, real: 0.8, frontier: 0.92, min: 0.6, max: 1, step: 0.01,
    industryMax: { value: 0.88, zh: "大型离心机单级约 0.85–0.88（待核实）", en: "Large centrifugal stage ~0.85–0.88 (to check)" },
    status: "pending", src: { zh: "沿用 Fig 2；活塞约 0.65–0.75、螺杆 0.75–0.85、离心 0.80–0.88", en: "Fig 2 value; piston ~0.65–0.75, screw 0.75–0.85, centrifugal 0.80–0.88" } },
  { key: "etaT", group: "components", control: "slider", unit: "",
    best: 0.92, bestSrc: { zh: "透平膨胀机效率“从 85% 左右到 90% 出头”，取上端（Chart Industries）", en: "Turboexpanders run \"between the mid-80s and low-90s\"; top end used (Chart Industries)" },
    zh: "涡轮等熵效率 ηₜ", en: "Turbine isentropic efficiency ηₜ", ideal: 1, real: 0.85, frontier: 0.93, min: 0.5, max: 1, step: 0.01,
    industryMax: { value: 0.92, zh: "透平膨胀机效率“从 85% 左右到 90% 出头”（Chart Industries）", en: "Turboexpanders run \"between the mid-80s and low-90s\" (Chart Industries)" },
    status: "pending", src: { zh: "小型径流涡轮常见值", en: "Typical small radial turbine" } },
  { key: "nExp", group: "components", control: "auto", unit: "",
    zh: "涡轮个数（随压力自动）", en: "Turbines (set by pressure)", ideal: "auto", real: "auto", min: 1, max: 5, step: 1,
    status: "pending", src: { zh: "随压力自动，不手调：取让每个涡轮膨胀比不超过 4 的最少个数（4 = “典型单级透平膨胀机压比 4:1，视工况可到 14:1”，Turbomachinery Magazine）；涡轮之间回热即供冷。最多 5 个与压缩对称，暂无直接工业来源（Huntorf 为 2 级加再热）", en: "Set by pressure, not by hand: the fewest turbines that keep each at or under 4 (\"typical single-stage turboexpander pressure ratio is 4:1\", up to 14:1, Turbomachinery Magazine); reheat between them is the cooling. At most 5 mirrors compression, no direct industrial source yet (Huntorf: 2 stages with reheat)" } },
  { key: "rtMax", group: "components", control: "number", unit: "", noUi: true, // fixed; stated in the stage-count basis
    zh: "每个涡轮膨胀比上限（自动选级用）", en: "Per-turbine expansion ratio limit (for auto stages)", ideal: 4, real: 4, min: 2, max: 14, step: 0.5,
    status: "sourced", src: { zh: "常见值 4：“典型单级透平膨胀机压比 4:1，视工况可到 14:1”（Turbomachinery Magazine）", en: "Typical 4: \"typical single-stage turboexpander pressure ratio is 4:1\", up to 14:1 depending on the process (Turbomachinery Magazine)" } },
  { key: "reheat", group: "components", control: "toggle", noUi: true, // off by CZ's choice; the model keeps it
    zh: "级间回热", en: "Reheat between stages", ideal: false, real: false,
    status: "fixed", src: { zh: "不回热（按 CZ 设定）：涡轮串联，管内空气不在中途回温，只算出风口放出的冷量；等价于一次膨胀到底", en: "No reheat (set by CZ): turbines in plain series, the pipe air is not rewarmed on the way, and only the cooling released at the outlets counts; same as one expansion" } },
  { key: "dTrh", group: "components", control: "slider", unit: "K", noUi: true, showIf: s => s.reheat && (s.nExp === "auto" || s.nExp > 1),
    best: 5, bestSrc: { zh: "空气-空气盘管较好设计约 5 K（待核实）", en: "Well-designed air-to-air coil ~5 K (to check)" },
    zh: "冷排接近温差", en: "Reheat coil approach", ideal: 0, real: 10, frontier: 2, min: 0, max: 20, step: 0.5,
    status: "pending", src: { zh: "冷排装在喷嘴吸风口，管内空气回暖到 Tₐ − ΔT；冷排压降并入管路压降", en: "Coil sits in the nozzle intake; pipe air rewarms to Tₐ − ΔT; coil pressure drop is inside the line drop" } },
  { key: "dTapp", group: "components", control: "slider", advanced: true, unit: "K", showIf: s => s.nComp !== Infinity,
    best: 5, bestSrc: { zh: "美国专利 US 6692235（多级离心空压机板翅式级间冷却器）：接近温差“小于 15 °F、最低小于 3 °F”，350 hp 样机三级实测 6.1、14.6、3.0 °F（3.4、8.1、1.7 K），取约 5 K", en: "US patent 6692235 (plate-fin intercoolers on a packaged multi-stage centrifugal): approach \"less than 15 degrees and as low as less than 3 degrees\" °F; a 350 hp unit measured 6.1, 14.6 and 3.0 °F (3.4, 8.1, 1.7 K) on its three stages; ~5 K used" },
    zh: "级间冷却器出口温差（高于冷却介质）", en: "Intercooler approach (above the coolant)", ideal: 0, real: 10, frontier: 2, min: 0, max: 20, step: 0.5,
    status: "sourced", src: { zh: "每级压缩后的空气被冷却到“冷却介质温度 + 此温差”再进下一级；只在有限级数时存在冷却器", en: "After each stage the air is cooled to the coolant temperature plus this approach before the next stage; coolers exist only with finite stages" } },
  { key: "cooling", group: "components", control: "select", noUi: true, showIf: s => s.nComp !== Infinity, // follows the heat recovery choice (set by CZ)
    zh: "级间冷却方式", en: "Intercooling method", ideal: "auto", real: "auto",
    options: { air: { zh: "风冷换热器（干式，按环境干球温度）", en: "Air-cooled exchanger (dry, at ambient dry bulb)" }, tower: { zh: "开式湿式冷却塔（按湿球温度）", en: "Open wet cooling tower (at wet bulb)" }, water: { zh: "自定义冷却水温", en: "Custom cooling-water temperature" } },
    status: "pending", src: { zh: "自动：热泵热水器 → 冷却塔；不回收或海水淡化 → 海水。冷却塔水温 = 湿球温度 + 4 K", en: "Auto: heat-pump water heater → cooling tower; none or desalination → seawater. Tower water = wet bulb + 4 K" } },
  { key: "dpLine", group: "components", control: "number", unit: "bar",
    best: 0.1, bestSrc: { zh: "Atlas Copco：固定压缩空气管网“应按管内压降不超过 0.1 bar 设计”（到最远用气点，含软管与接头）。不含干燥器和过滤器本身的压降，所以偏乐观", en: "Atlas Copco: fixed compressed-air networks \"should be dimensioned, so pressure drops in the pipes don't exceed 0.1 bar\" (to the most remote point, hoses and couplings included). Dryer and filter drops are not included, so this errs optimistic" },
    zh: "管路压降（压缩机到涡轮）", en: "Line pressure drop (compressor to turbine)", ideal: 0, real: 0.25, frontier: 0.05, min: 0, max: 1, step: 0.01,
    status: "sourced", src: { zh: "干燥器 + 过滤器 + 管路常见量级", en: "Dryer + filters + piping, typical magnitude" } },
  { key: "dpBack", group: "components", control: "number", unit: "bar",
    best: 0.02, bestSrc: { zh: "短送风管、大口径喷嘴（待核实）", en: "Short duct, wide nozzles (to check)" },
    zh: "排气背压（涡轮出口到出风口）", en: "Exhaust back pressure (turbine outlet to nozzle)", ideal: 0, real: 0.05, frontier: 0.02, min: 0, max: 0.5, step: 0.01,
    status: "pending", src: { zh: "推动冷风通过送风管和喷嘴", en: "Pushes the cold air through duct and nozzles" } },
  { key: "leak", group: "components", control: "number", advanced: true, unit: "%",
    best: 2, bestSrc: { zh: "新建、全焊接短管路的较好水平约 2%（待核实）", en: "New, welded short line, good practice ~2% (to check)" },
    zh: "泄漏率", en: "Leakage", ideal: 0, real: 5, frontier: 0, min: 0, max: 30, step: 0.5,
    status: "pending", src: { zh: "新装短管路取 5%；工厂老管网常见 20–30%", en: "5% for a new short line; old plant networks 20–30%" } },
  { key: "etaDrive", group: "components", control: "number", advanced: true, unit: "",
    best: 0.95, bestSrc: { zh: "大功率 IE4/IE5 电机 × 变频器（待核实）", en: "Large IE4/IE5 motor × VFD (to check)" },
    zh: "驱动效率（电机 × 变频器）", en: "Drive efficiency (motor × VFD)", ideal: 1, real: 0.9, frontier: 0.97, min: 0.8, max: 1, step: 0.01,
    industryMax: { value: 0.95, zh: "大功率 IE4/IE5 电机约 0.96–0.97 × 变频器 0.98（待核实）", en: "Large IE4/IE5 motor ~0.96–0.97 × VFD 0.98 (to check)" },
    status: "pending", src: { zh: "约 15 kW IE3/IE4 电机 0.92–0.94 × 变频器 0.97", en: "~15 kW IE3/IE4 motor 0.92–0.94 × VFD 0.97" } },
  { key: "auxFan", group: "components", control: "number", advanced: true, unit: "% of heat rejected",
    zh: "散热辅机功耗", en: "Heat-rejection auxiliaries", ideal: 0, real: "auto", min: 0, max: 10, step: 0.1,
    status: "pending", src: { zh: "自动：风冷 2%、冷却塔 3%（水泵 + 塔风扇）", en: "Auto: 2% air-cooled, 3% cooling tower (pump + fan)" } },
  { key: "dryer", group: "components", control: "select", advanced: true,
    zh: "干燥器", en: "Dryer", ideal: "none", real: "auto",
    options: { none: { zh: "无（干空气）", en: "None (dry air)" }, auto: { zh: "自动", en: "Auto" }, fridge: { zh: "冷冻式", en: "Refrigerated" }, desiccant: { zh: "吸附式", en: "Desiccant" } },
    status: "pending", src: { zh: "涡轮出口 > 3 °C 用冷冻式（约 2–3% 压缩功），否则吸附式", en: "Turbine outlet > 3 °C: refrigerated (~2–3% of compressor work); else desiccant" } },
  { key: "purge", group: "components", control: "number", advanced: true, unit: "%",
    best: 5, bestSrc: { zh: "鼓风热再生吸附式约 0–5% 耗气（待核实）", en: "Blower-purge heated desiccant ~0–5% purge (to check)" },
    zh: "吸附式再生耗气", en: "Desiccant purge air", ideal: 0, real: 15, min: 0, max: 30, step: 0.5,
    status: "pending", src: { zh: "无热再生吸附式常见值", en: "Typical heatless desiccant dryer" } },

  // ---- recovery ----
  { key: "recPath", group: "recovery", control: "segmented",
    zh: "功回收路径", en: "Work recovery", ideal: "gen", real: "gen",
    options: { none: { zh: "无", en: "None" }, gen: { zh: "发电", en: "Generator" } },
    status: "fixed", src: { zh: "发电：涡轮在座位区、压缩机在远处机房，两者不在一根轴上，涡轮功只能发电送回。同轴只在涡轮装在机房里时成立（那时冷风要长距离输送）", en: "Generator: the turbines sit at the seats and the compressor in a distant plant room, so they cannot share a shaft and the turbine work goes back as electricity. A shared shaft only works with the turbine in the plant room (cold air then has to travel the distance)" } },
  { key: "etaRec", group: "recovery", control: "number", unit: "",
    zh: "回收链效率", en: "Recovery chain efficiency", ideal: 1, real: "auto", min: 0.5, max: 1, step: 0.01,
    status: "pending", src: { zh: "自动：同轴 0.97；发电 0.90（发电机约 0.93 × 变频器 0.97）", en: "Auto: shaft 0.97; generator 0.90 (generator ~0.93 × VFD 0.97)" } },
  { key: "heatUse", group: "recovery", control: "segmented", showIf: s => s.nComp !== Infinity,
    zh: "压缩热回收方式", en: "Compression-heat recovery", ideal: "none", real: "heat",
    options: { none: { zh: "无", en: "None" }, heat: { zh: "海水淡化", en: "Desalination" }, hp: { zh: "热泵热水器", en: "Heat-pump water heater" } },
    status: "sourced", src: { zh: "级间冷却器用水冷，压缩热进到水里；回收的那部分以热水送往同址的海水淡化厂，或替代热泵热水器供生活热水，余下排入海水。Atlas Copco 能量回收装置最多回收压缩机输入电能的 94%，水温最高 90 °C", en: "Water-cooled intercoolers put the compression heat into water; the recovered part goes as hot water to a co-located desalination plant, or replaces heat-pump water heaters for sanitary hot water, and the rest to seawater. Atlas Copco energy recovery takes up to 94% of the compressor's electrical input, water up to 90 °C" } },
  { key: "Tw", group: "recovery", control: "number", unit: "°C", showIf: s => s.nComp !== Infinity,
    zh: "冷却水温度（海水 / 冷却塔水，随热回收方式）", en: "Cooling water temperature (seawater / tower water, follows heat recovery)", ideal: "auto", real: "auto", min: 5, max: 40, step: 0.5,
    status: "sourced", src: { zh: "级间冷却器都是水冷，冷却水从哪来跟着热回收方式走。不回收或海水淡化：厂址在海边，用海水，迪拜 8 月海水平均约 33 °C（dubai-online.com）。热泵热水器：用热方是酒店、宿舍等，不一定靠海，余热排到开式冷却塔，水温 = 湿球温度 + 4 K（冷却塔逼近温度常取 3–5 K，待核实），35 °C、53% 时约 31 °C", en: "The intercoolers are always water-cooled; where the water comes from follows the heat recovery choice. None or desalination: a coastal site on seawater, which averages ~33 °C in August in Dubai (dubai-online.com). Heat-pump water heater: the heat user is a hotel or staff housing, not necessarily by the sea, so the rest of the heat goes to an open cooling tower at wet bulb + 4 K (tower approach usually 3–5 K, to check), ~31 °C at 35 °C and 53%" } },
  { key: "hwShare", group: "recovery", control: "slider", unit: "%", showIf: s => (s.heatUse === "heat" || s.heatUse === "hp"),
    zh: "压缩热回收比例（输入）", en: "Compression-heat recovery share (input)", ideal: 94, real: 94, min: 0, max: 100, step: 1,
    status: "sourced", src: { zh: "默认 94% = Atlas Copco 能量回收装置上限。实际还受“供水温度 + 冷却器温差”以上可取热量的限制，流程表里显示实际回收的比例", en: "Default 94% = the Atlas Copco energy-recovery ceiling. It is also capped by the heat available above supply temperature plus cooler approach; the readout shows the share actually recovered" } },
  { key: "heatValue", group: "recovery", control: "number", unit: "kWh电/kWh热", showIf: s => (s.heatUse === "heat" || s.heatUse === "hp"),
    zh: "每 kWh 回收热折合多少电", en: "Electricity credited per kWh of recovered heat", ideal: "auto", real: "auto", min: 0, max: 1, step: 0.01,
    status: "sourced", src: { zh: "自动：海水淡化 0.04，热泵热水器 0.33。海水淡化：热供低温多效蒸馏 MED（低于 70 °C 运行，电耗低于 1.0 kWh/m³，Veolia），造水比 GOR 约 10 时每 m³ 约 65 kWh 热（GOR 待核实）；造出的水替代反渗透（整厂实际 3–4 kWh/m³，Harvard 资料，取 3.5），(3.5 − 1.0) ÷ 65 ≈ 0.04。即每 kWh 热造出的淡水，替代反渗透省下约 0.04 kWh 电。热泵热水器：回收热直接当生活热水用，省下热泵本来要耗的电；热泵热水器 COP 约 3，1 ÷ 3 ≈ 0.33（待核实）", en: "Auto: desalination 0.04, heat-pump water heater 0.33. Desalination: heat feeds low-temperature MED (below 70 °C, under 1.0 kWh/m³ of electricity, Veolia), ~65 kWh of heat per m³ at a GOR of ~10 (GOR to check); its water replaces reverse osmosis (3–4 kWh/m³ for a whole plant in practice, Harvard notes; 3.5 used): (3.5 − 1.0) ÷ 65 ≈ 0.04. Each kWh of heat makes water that saves ~0.04 kWh of RO electricity. Heat-pump water heater: the recovered heat is used directly as sanitary hot water, saving what the heat pump would have used; heat-pump water heater COP ~3, 1 ÷ 3 ≈ 0.33 (to check)" } },
  { key: "hwT", group: "recovery", control: "number", unit: "°C", advanced: true, showIf: s => (s.heatUse === "heat" || s.heatUse === "hp"),
    zh: "回收热水的供水温度", en: "Recovered hot-water supply temperature", ideal: "auto", real: "auto", min: 30, max: 90, step: 1,
    status: "sourced", src: { zh: "自动：海水淡化 70 °C，热泵热水器 60 °C。低温多效蒸馏在低于 70 °C 下运行（Veolia）；生活热水常用 55–60 °C；Atlas Copco 回收装置最高 90 °C。只有高于“此温度 + 冷却器温差”的那段压缩热能回收", en: "Auto: desalination 70 °C, heat-pump water heater 60 °C. Low-temperature MED runs below 70 °C (Veolia); sanitary hot water is usually 55–60 °C; Atlas Copco recovery goes up to 90 °C. Only compression heat above this plus the cooler approach can be recovered" } },
  { key: "etaORC", group: "recovery", control: "number", unit: "%", showIf: s => s.heatUse === "orc",
    zh: "ORC 发电效率", en: "ORC efficiency", ideal: 10, real: 10, min: 0, max: 20, step: 0.5,
    status: "pending", src: { zh: "150–250 °C 热源约 8–15%，100 °C 约 5–8%", en: "~8–15% from 150–250 °C, 5–8% near 100 °C" } },
  { key: "TminORC", group: "recovery", control: "number", unit: "°C", showIf: s => s.heatUse === "orc",
    zh: "ORC 最低热源温度", en: "ORC minimum source temperature", ideal: 80, real: 80, min: 60, max: 200, step: 1,
    status: "pending", src: { zh: "低温 ORC 常见下限", en: "Typical low-temperature ORC floor" } },
  { key: "absType", group: "recovery", control: "segmented", showIf: s => s.heatUse === "absorption",
    zh: "吸收式机型", en: "Absorption type", ideal: "single", real: "single",
    options: { single: { zh: "单效", en: "Single-effect" }, double: { zh: "双效", en: "Double-effect" } },
    status: "pending", src: { zh: "溴化锂-水", en: "LiBr–water" } },
  { key: "copAbs", group: "recovery", control: "number", unit: "", showIf: s => s.heatUse === "absorption",
    zh: "吸收式热力 COP", en: "Absorption thermal COP", ideal: "auto", real: "auto", min: 0.3, max: 1.6, step: 0.05,
    status: "pending", src: { zh: "自动：单效 0.7、双效 1.2", en: "Auto: single 0.7, double 1.2" } },
  { key: "TminAbs", group: "recovery", control: "number", unit: "°C", showIf: s => s.heatUse === "absorption",
    zh: "吸收式最低驱动温度", en: "Absorption minimum drive temperature", ideal: "auto", real: "auto", min: 60, max: 200, step: 1,
    status: "pending", src: { zh: "自动：单效 90 °C、双效 150 °C", en: "Auto: single 90 °C, double 150 °C" } },

  // ---- delivery & comparison ----
  { key: "ER", group: "delivery", control: "slider", unit: "",
    zh: "喷嘴引射比", en: "Nozzle entrainment ratio", ideal: 5, real: 5, min: 0, max: 10, step: 0.1,
    status: "pending", src: { zh: "每份冷风吸入的环境空气份数；仅靠余压驱动，可达值待查或实测", en: "Ambient air drawn in per part of cold air; driven by residual pressure only, achievable value to check or measure" } },
  { key: "nNozzle", group: "delivery", control: "number", unit: "",
    zh: "喷嘴个数", en: "Nozzle count", ideal: 4, real: 4, min: 1, max: 20, step: 1,
    status: "placeholder", src: { zh: "例如每座位一个", en: "For example one per seat" } },
  { key: "dNozzle", group: "delivery", control: "number", unit: "mm",
    zh: "喷嘴直径", en: "Nozzle diameter", ideal: 50, real: 50, min: 10, max: 200, step: 1,
    status: "placeholder", src: { zh: "占位值", en: "Placeholder" } },
  { key: "copSplit", group: "delivery", control: "number", unit: "",
    zh: "分体空调 COP（46 °C 额定）", en: "Split AC COP (rated at 46 °C)", ideal: 2.64, real: 2.64, min: 1, max: 8, step: 0.01,
    status: "sourced", src: { zh: "阿联酋 ESMA 能效标签（UAE.S 5010-1）：分体机在 T3 工况（室外 46 °C）下 5 星要求 EER ≥ 9.01 Btu/Wh，即 COP 2.64；1 星下限 6.80（COP 1.99）。取市场最高档。参考：欧洲高端机 Daikin FTXM35A 在 35 °C 下 EER 4.63（Eurovent）", en: "UAE ESMA label (UAE.S 5010-1): split units at T3 (46 °C outdoor) need EER ≥ 9.01 Btu/Wh for 5 stars, i.e. COP 2.64; 1 star from 6.80 (COP 1.99). Top band used. For reference, Daikin FTXM35A rates EER 4.63 at 35 °C (Eurovent)" } },
  { key: "TsSplit", group: "delivery", control: "number", unit: "°C",
    zh: "分体空调出风温度", en: "Split AC supply temperature", ideal: 13, real: 13, min: 5, max: 25, step: 0.5,
    status: "pending", src: { zh: "常见出风温度，第 9 步查源", en: "Typical supply air; to source in step 9" } },
  { key: "copSpot", group: "delivery", control: "number", unit: "",
    zh: "户外点冷机 COP（35 °C 额定）", en: "Outdoor spot cooler COP (rated at 35 °C)", ideal: 2.9, real: 2.9, min: 0.5, max: 6, step: 0.1,
    status: "sourced", src: { zh: "MovinCool Classic Plus 26：35 °C、60% RH 下制冷 24,000 BTU/h（7.0 kW），耗电 2.4 kW，COP 2.9（含除湿潜热）", en: "MovinCool Classic Plus 26: 24,000 BTU/h (7.0 kW) at 95 °F, 60% RH on 2.4 kW, COP 2.9 (latent included)" } },
  { key: "TsSpot", group: "delivery", control: "number", unit: "°C",
    zh: "户外点冷机出风温度", en: "Spot cooler supply temperature", ideal: 14, real: 14, min: 5, max: 25, step: 0.5,
    status: "pending", src: { zh: "常见出风温度，第 9 步查源", en: "Typical supply air; to source in step 9" } },

  { key: "acDerate", group: "delivery", control: "number", advanced: true, unit: "%/°C",
    zh: "空调 COP 随气温下降", en: "AC COP loss per °C", ideal: 2.04, real: 2.04, min: 0, max: 5, step: 0.01,
    status: "sourced", src: { zh: "分体空调实测：室外每升高 1 °C，COP 降 2.04%（IIETA 现场测试）；两种空调都按此从各自额定气温（点冷机 35 °C、分体 46 °C）折算到当前气温", en: "Split AC field test: COP falls 2.04% per °C of outdoor temperature (IIETA); both ACs are scaled from their rating temperature (spot 35 °C, split 46 °C) to the current ambient" } },
  { key: "fRet", group: "delivery", control: "slider", unit: "%",
    zh: "空调排热回流比例", en: "AC exhaust heat returning to the cooled spot", ideal: 15, real: 15, min: 0, max: 100, step: 1,
    status: "pending", src: { zh: "空调冷凝器排出的热（冷量 + 电）有多少回到被冷却的人附近；空气循环的热在远处压缩机房排掉，取 0。暂无点冷机实测；借用类比：工业空冷器热风回流实测 13.6%、24%、25% 以上（Hudson/Chart《Hot Air Recirculation》）。页面同时给出打平所需的回流比例", en: "Share of the AC condenser heat (cooling + power) that comes back to the people being cooled; the air cycle rejects its heat at the distant compressor, so 0. No spot-cooler measurement yet; by analogy, industrial air coolers measured 13.6%, 24% and over 25% hot-air recirculation (Hudson/Chart, Hot Air Recirculation). The page also shows the share at which the two break even" } },

  // ---- curve ----
  { key: "yLog", group: "curve", control: "toggle", advanced: true,
    zh: "纵轴对数", en: "Log COP axis", ideal: false, real: false,
    status: "fixed", src: { zh: "显示设置", en: "Display setting" } },
  { key: "curves", group: "curve", control: "toggle",
    zh: "显示曲线", en: "Curves shown", ideal: ["current"], real: ["current"], // Carnot and ideal sit 3–10× higher and squash the real curves; off by default
    options: { carnot: { zh: "卡诺极限", en: "Carnot limit" }, ideal: { zh: "理论理想", en: "Theoretical ideal" }, current: { zh: "当前配置", en: "Current setup" } },
    status: "fixed", src: { zh: "显示设置", en: "Display setting" } },
];

// Kept out of the panel: both machines are assumed to deliver the same share of
// their cooling to people, so it cancels in the comparison. Replace with measured
// values later.
const HIDDEN = { capture: 1 };

const BY_KEY = Object.fromEntries(PARAMS.map(p => [p.key, p]));

// Defaults for a mode. Custom starts from realistic; frontier falls back to realistic.
function defaults(mode = "real") {
  const s = { mode };
  for (const p of PARAMS) s[p.key] = mode === "ideal" ? p.ideal : mode === "frontier" && "frontier" in p ? p.frontier : mode === "best" && "best" in p ? p.best : p.real;
  return s;
}

// Wet-bulb temperature (°C), Stull (2011); same as model/air.js, which loads after this file.
const wetBulb = (T, RH) => T * Math.atan(0.151977 * Math.sqrt(RH + 8.313659)) + Math.atan(T + RH) - Math.atan(RH - 1.676331)
  + 0.00391838 * Math.pow(RH, 1.5) * Math.atan(0.023101 * RH) - 4.686035;

// Resolves every "auto" value against the rest of the state.
function auto(s) {
  const r = { ...s };
  // the cooling water follows the heat use: hot water for heat pumps means an inland user and a tower
  if (r.cooling === "auto") r.cooling = r.heatUse === "hp" ? "tower" : "water";
  if (r.Tw === "auto") r.Tw = r.cooling === "tower" ? Math.round((wetBulb(r.Ta, r.RH) + 4) * 10) / 10 : 33;
  if (r.nExp === "auto") r.nExp = nExpRange(r).pick;
  if (r.m === "auto") r.m = mMax(r.P).typ;
  if (r.heatValue === "auto") r.heatValue = r.heatUse === "hp" ? 0.33 : 0.04;
  if (r.hwT === "auto") r.hwT = r.heatUse === "hp" ? 60 : 70;
  if (r.recPath === "auto") r.recPath = "gen"; // turbines at the seats, compressor in the plant room
  if (r.etaRec === "auto") r.etaRec = r.recPath === "gen" ? 0.9 : r.recPath === "shaft" ? 0.97 : 0;
  if (r.auxFan === "auto") r.auxFan = r.nComp === Infinity ? 0 : r.cooling === "air" ? 2 : 3;
  if (r.copAbs === "auto") r.copAbs = r.absType === "double" ? 1.2 : 0.7;
  if (r.TminAbs === "auto") r.TminAbs = r.absType === "double" ? 150 : 90;
  return r;
}

// Clamps numeric values into range; "auto", Infinity (stages) and option keys pass through.
function clamp(s) {
  const r = { ...s };
  for (const p of PARAMS) {
    const v = r[p.key];
    if (typeof v !== "number" || p.min === undefined) continue;
    if (v === Infinity && p.allowInfinity) continue;
    r[p.key] = Math.min(p.dynMax ? p.dynMax(r) : p.max, Math.max(p.min, v));
  }
  return r;
}

// Largest single compressor in service at this discharge pressure, in g/s (sources on PARAMS.m).
// typ = a common single unit in the same pressure band, the value "auto" suggests.
const M_MAX = [
  { upTo: 10, max: 500000, zh: "单台离心空压机上限（MAN AR-MAX1，64 MW）", en: "largest single centrifugal (MAN AR-MAX1, 64 MW)",
    typ: 5100, typZh: "Atlas Copco ZH 9000 离心机（5–10 bar，254.9 m³/min，用于 1–20 MW 压缩机房）", typEn: "Atlas Copco ZH 9000 centrifugal (5–10 bar, 254.9 m³/min, for 1–20 MW compressor rooms)" },
  { upTo: 70, max: 108000, zh: "Huntorf 储能电站压缩流量（60 MW）", en: "Huntorf CAES charging flow (60 MW)",
    typ: 1070, typZh: "Atlas Copco PBE 1600 VSD+（25 bar，3200 m³/h）", typEn: "Atlas Copco PBE 1600 VSD+ (25 bar, 3200 m³/h)" },
  { upTo: Infinity, max: 45000, zh: "回注压缩机级别（650 barg、32 MW 驱动），按 1→200 bar 每 kg 约 0.70 MJ 折成空气流量，估算", en: "reinjection-compressor class (650 barg, 32 MW driver), converted to air from 1 to 200 bar at ~0.70 MJ/kg, an estimate",
    typ: 540, typZh: "Burckhardt 标准高压往复机上限（约 1500 Nm³/h，最高 500 bar，待核实）", typEn: "Burckhardt standard high-pressure reciprocating, top of range (~1500 Nm³/h, up to 500 bar, to check)" },
];
const mMax = P => M_MAX.find(b => P <= b.upTo);

// Stage counts at this pressure. min = fewest that keep every stage under the industrial
// limit; pick = fewest under the typical per-stage limit (rcMax / rtMax), which "auto" uses.
const stagesFor = (pr, limit, cap) => Math.min(cap, Math.max(1, pr <= 1 ? 1 : Math.ceil(Math.log(pr) / Math.log(limit) - 1e-9)));

// Compression: no stage above MAX_STAGE_RATIO, no more than MAX_STAGES (the most any
// industrial air compressor uses, up to 500 bar).
const MAX_STAGE_RATIO = 4.5;
const MAX_STAGES = 5;
function nCompRange(s) {
  const pr = s.P / s.Pa;
  const min = stagesFor(pr, MAX_STAGE_RATIO, MAX_STAGES);
  return { min, max: MAX_STAGES, pick: Math.max(min, stagesFor(pr, s.rcMax || 3, MAX_STAGES)) };
}

// Expansion, from the turbine's own ratio: inlet = line pressure capped at the turbine's
// maximum inlet (anything above is throttled away first), outlet = ambient + back pressure.
const MAX_EXP_RATIO = 14;
const MAX_EXP_STAGES = 5;
const turbineInlet = s => Math.min(s.P - (s.dpLine || 0), s.ptMax || Infinity);
function nExpRange(s) {
  const pr = turbineInlet(s) / (s.Pa + (s.dpBack || 0));
  const min = stagesFor(pr, MAX_EXP_RATIO, MAX_EXP_STAGES);
  return { min, max: MAX_EXP_STAGES, pick: Math.max(min, stagesFor(pr, s.rtMax || 4, MAX_EXP_STAGES)) };
}

function visible(p, s) { return !p.showIf || p.showIf(s); }

const API = { CONST, GROUPS, MODES, PARAMS, HIDDEN, BY_KEY, MAX_STAGE_RATIO, MAX_STAGES, MAX_EXP_RATIO, MAX_EXP_STAGES, defaults, auto, clamp, visible, nCompRange, nExpRange, turbineInlet, mMax, M_MAX };
if (typeof module !== "undefined") module.exports = API;
else window.EXPLORER_PARAMS = API;

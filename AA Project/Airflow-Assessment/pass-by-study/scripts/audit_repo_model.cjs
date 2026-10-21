// Reproducible review probes. Does not change the calculator or its test fixtures.
const fs = require('node:fs');
const path = require('node:path');
const repo = path.resolve(__dirname, '../../../..');
const B = require(path.join(repo, 'physics.js'));
const preset = key => { B.loadPreset(key); return structuredClone(B.getState()); };
const run = state => B.compute(structuredClone(state));
const brief = r => ({ mass_kg_s: r.m, supply_c: r.T, cold_power_w: r.cool,
  shaft_w: r.work, allocated_compressor_w: r.pIn, cop_allocated: r.cop,
  runtime_s: r.tOn, warnings: r.warns });

const state = preset('rental');
const nominal = run(state);
const highLoss = structuredClone(state);
highLoss.stages.find(s => s.type === 'hose').p.dp = 0.5;
const highLossResult = run(highLoss);
const smaller = structuredClone(state);
smaller.source.p.fad = 2000;
const smallerResult = run(smaller);

const burstState = preset('workshopBurst');
const burstResult = run(burstState);
const receiver = burstState.stages.find(s => s.type === 'receiver');
const receiverNode = burstResult.nodes.find(n => n.label === 'Receiver tank');
const receiverBounds = [6.3, 6.8].map(minimum => {
  const inventory = Math.max(0, burstResult.storage.pmaxg - minimum) * 1e5 *
    receiver.p.vol / 1000 / (B.R * (receiverNode.T + 273.15));
  return { receiver_minimum_bar_g: minimum, inventory_kg: inventory,
    constant_temperature_runtime_s: inventory / (burstResult.demand - burstResult.mSupply) };
});
const rhoAmbient = B.PA * 1e5 / (B.R * (state.amb + 273.15));
const mixLimit = delta => {
  const warm = Math.max(0, nominal.m * ((state.amb - delta) - nominal.T) / delta);
  return { target_drop_k: delta, maximum_added_warm_mass_kg_s: warm,
    maximum_total_mixed_mass_kg_s: warm + nominal.m,
    uniform_wind_exchange_bound_m_s: warm / (rhoAmbient * state.outlet.zone) };
};

const tankResult = run(preset('scuba'));
const totalTankDraw = tankResult.m / tankResult.coldFrac;
const motorOut = smallerResult.nodes.find(n => n.label === 'Vane air motor').T;
const uaNominal = -nominal.m * B.CP * Math.log(1 - 0.12);
const fixedUaSmallSupply = state.amb + (motorOut - state.amb) *
  Math.exp(-uaNominal / (smallerResult.m * B.CP));

const result = {
  date: '2026-10-21',
  scope: 'Code and first-principles comparison. No supplier validation, new CFD or new Lean build.',
  agreement: { repository_nominal: brief(nominal),
    imported_source: JSON.parse(fs.readFileSync(path.join(__dirname, '../source-input.json'))),
    note: 'Near-1C agreement shares the same loaded-motor assumptions; it is not independent validation.' },
  findings: {
    receiver: { preset: 'workshopBurst', motor_set_pressure_bar_g: 6.3,
      configured_minimum_bar_g: receiver.p.pmin, reported: brief(burstResult),
      independent_inventory_bounds: receiverBounds,
      limitation: '6.3 bar gives zero regulator headroom. 6.8 bar reserves an assumed 0.5 bar; neither is a transient hardware prediction.' },
    cold_hose_backpressure: { nominal: brief(nominal),
      entered_downstream_loss_bar: 0.5, output: brief(highLossResult),
      issue: 'Positive exhaust loss is clipped at atmospheric pressure. Motor exhaust pressure is not coupled back to the motor model.' },
    wind_metric: { reported_for_10k_m_s: nominal.breeze,
      uniform_adiabatic_mixing_bounds: [mixLimit(10), mixLimit(6)],
      issue: 'The wind expression counts total cooled mixture capacity as added warm-air capacity. Even the corrected bound is not a wind-tolerance prediction.' },
    vortex_tank_mass_balance: { reported_runtime_s: tankResult.tOn,
      constant_temperature_inventory_runtime_s: tankResult.storage.usable / totalTankDraw,
      source_draw_kg_s: totalTankDraw, cold_exit_kg_s: tankResult.m,
      inventory_kg: tankResult.storage.usable,
      implied_total_draw_kg_at_reported_runtime: totalTankDraw * tankResult.tOn,
      issue: 'Storage depletion uses cold outlet flow instead of total tank draw, omitting hot vortex exhaust.' },
    reduced_flow_and_heat_gain: { compressor_fad_l_min: 2000,
      reported: brief(smallerResult),
      ua_w_k_calibrated_to_nominal_12_percent: uaNominal,
      supply_c_if_same_ua_and_same_motor_state: fixedUaSmallSupply,
      limitation: 'Motor power/flow scaling is assumed. The fixed-UA result only isolates the hose assumption; it is not a new source prediction.' },
    system_energy: { declared_compressor_kw: state.source.p.power,
      allocated_used_air_kw: nominal.pIn / 1000,
      issue: 'Allocated air-energy COP is not measured complete-plant COP. Part-load fuel/electricity, treatment and auxiliary consumption are not resolved.' },
    schematic_figures: { nature: 'Parameterized illustrative animations, not CFD.',
      ideal_cycle: 'Hypothetical compressor/expander work recovery. Its 80% expander efficiency is not the four-motor catalogue point.' },
    shared_limits: ['No complete pressure-flow network in either the calculator or prescribed-inlet outdoor CFD.',
      'No reported 3D cooled-air mass/volume/persistence from the current CFD campaign.',
      'Source exhaust temperature, load, treatment, heat pickup and transients remain conditional.']
  },
  existing_test_scope: 'The six supplied tests lock prior preset outputs and a JT approximation. They do not check these pressure, mixing and storage constraints.'
};
const output = path.join(__dirname, '../results/repo-model-audit.json');
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({ output: path.relative(repo, output),
  source_c: nominal.T, source_kw: nominal.cool / 1000,
  burst_reported_s: burstResult.tOn, burst_inventory_bounds: receiverBounds,
  wind_reported_m_s: nominal.breeze, wind_mixing_bound_m_s: mixLimit(10).uniform_wind_exchange_bound_m_s,
  vortex_reported_s: tankResult.tOn, vortex_inventory_s: tankResult.storage.usable / totalTankDraw }, null, 2));

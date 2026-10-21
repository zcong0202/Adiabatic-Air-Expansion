import AAThermo.Model

/-! Exact rational scenario checks. Inputs are assumptions, not measurements. -/
namespace AA

/-- A conservative mathematical envelope, conditional on alpha and retention. -/
theorem assumed_current_envelope_passes (alpha r : ℝ)
    (ha : (3:ℝ)/10 ≤ alpha) (hr : (9:ℝ)/10 ≤ r) :
    6 < retainedAreaDrop 34 34 5 alpha r := by
  have hp : (3:ℝ)/10 * ((9:ℝ)/10) ≤ alpha * r :=
    mul_le_mul ha hr (by norm_num) (by linarith)
  dsimp [retainedAreaDrop]
  nlinarith

/-- The original CFD fraction is only an assumed decimal in this certificate. -/
theorem rounded_cfd_fraction_dry_passes :
    6 < retainedAreaDrop 35 35 5 ((3146378:ℝ)/10000000) 1 := by
  norm_num [retainedAreaDrop]

theorem poor_delivery_fails :
    retainedAreaDrop 34 34 5 ((15:ℝ)/100) 1 < 6 := by
  norm_num [retainedAreaDrop]

theorem hot_entrainment_can_fail :
    retainedAreaDrop 34 40 5 ((3:ℝ)/10) ((9:ℝ)/10) < 6 := by
  norm_num [retainedAreaDrop]

/-- At 60% capture, 2 g/s source and 5 g/s warm inflow: 5 C delivery fails. -/
theorem assumed_mass_balance_fails :
    mixDrop 34 ((6:ℝ)/10 * ((2:ℝ)/1000)) ((5:ℝ)/1000) 5 34 0 1005 < 6 := by
  norm_num [mixDrop, mixTemp]

/-- A warmer/cold-mass mixture example from the meeting. -/
theorem half_cold_mass_not_ten_degrees :
    mixTemp ((1:ℝ)/2) 1 0 20 0 1005 = (40:ℝ)/3 := by
  norm_num [mixTemp]

theorem three_stages_at_three_to_one_insufficient
    (p1 p2 p3 : ℝ) (h1 : 200 ≤ 3*p1) (h2 : p1 ≤ 3*p2)
    (h3 : p2 ≤ 3*p3) (hend : p3 = 5) : False := by
  nlinarith

theorem bauer_100_vs_200_duty (pulse period : ℝ)
    (budget : 200*pulse ≤ 100*period) : 2*pulse ≤ period := by
  linarith

theorem burst_2_to_10_requires_15s (period : ℝ)
    (budget : 10*3 ≤ 2*period) : 15 ≤ period := by
  linarith

end AA

#print axioms AA.mixing_target_iff
#print axioms AA.required_mass_iff
#print axioms AA.source_too_warm
#print axioms AA.required_area_fraction_iff
#print axioms AA.finite_area_average
#print axioms AA.area_fraction_bounds
#print axioms AA.finite_flux_necessary
#print axioms AA.retention_bounds
#print axioms AA.heat_budget_iff
#print axioms AA.exposure_time_budget_iff
#print axioms AA.fixed_mixing_required_mass
#print axioms AA.more_cold_mass_helps
#print axioms AA.scaling_both_flows_preserves_drop
#print axioms AA.ideal_gas_throttle_temperature
#print axioms AA.ideal_ratio_bounds
#print axioms AA.expander_bounds
#print axioms AA.vortex_hot_temperature
#print axioms AA.vortex_fraction_bound
#print axioms AA.buffer_inventory_iff
#print axioms AA.duty_budget_iff
#print axioms AA.uniform_target_capacity_iff
#print axioms AA.assumed_current_envelope_passes
#print axioms AA.rounded_cfd_fraction_dry_passes
#print axioms AA.poor_delivery_fails
#print axioms AA.hot_entrainment_can_fail
#print axioms AA.assumed_mass_balance_fails
#print axioms AA.half_cold_mass_not_ten_degrees
#print axioms AA.three_stages_at_three_to_one_insufficient
#print axioms AA.bauer_100_vs_200_duty
#print axioms AA.burst_2_to_10_requires_15s

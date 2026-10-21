import AAThermo.CFDDesign

/-! Conditional outdoor pass-by timing and sampled-temperature algebra.
No theorem asserts an actual jet footprint, motor state or human benefit. -/
namespace AA

theorem passby_crossing_upper (width speed exposure : ℝ)
    (hs : 0 < speed) (htravel : speed * exposure ≤ width) :
    exposure ≤ width / speed := by
  apply (le_div_iff₀ hs).mpr
  nlinarith

theorem valve_period_can_exceed_exposure (width speed exposure valve : ℝ)
    (hs : 0 < speed) (htravel : speed * exposure ≤ width)
    (hwidth : width < speed * valve) : exposure < valve := by
  nlinarith

theorem pulse_mass_upper (flow duration mass : ℝ)
    (hf : 0 ≤ flow) (hd : duration ≤ 30)
    (hb : mass = flow * duration) : mass ≤ 30 * flow := by
  nlinarith

theorem sampled_cooling_dose_lower {ι : Type*} (s : Finset ι)
    (dt deficit : ι → ℝ) (drop : ℝ)
    (hdt : ∀ i ∈ s, 0 ≤ dt i)
    (hdrop : ∀ i ∈ s, drop ≤ deficit i) :
    drop * (∑ i ∈ s, dt i) ≤ ∑ i ∈ s, dt i * deficit i := by
  rw [Finset.mul_sum]
  apply Finset.sum_le_sum
  intro i hi
  nlinarith [hdt i hi, hdrop i hi]

theorem strict_cold_fraction_threshold (ambient source fraction deficit target : ℝ)
    (hc : 0 < ambient - source)
    (hb : deficit = fraction * (ambient-source))
    (hf : target / (ambient-source) < fraction) : target < deficit := by
  have := (div_lt_iff₀ hc).mp hf
  nlinarith

theorem reference_passby_crossing : (0.3:ℝ) / 1.2 = 0.25 := by norm_num

theorem nominal_max_pulse_budget :
    (0.0776:ℝ)*30 = 2.328 ∧ (3.888:ℝ)*30/60 = 1.944 := by
  norm_num

end AA
#print axioms AA.passby_crossing_upper
#print axioms AA.valve_period_can_exceed_exposure
#print axioms AA.pulse_mass_upper
#print axioms AA.sampled_cooling_dose_lower
#print axioms AA.strict_cold_fraction_threshold
#print axioms AA.reference_passby_crossing
#print axioms AA.nominal_max_pulse_budget

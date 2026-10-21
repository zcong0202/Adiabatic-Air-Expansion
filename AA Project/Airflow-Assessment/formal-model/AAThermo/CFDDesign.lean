import AAThermo.MotorSeat

/-! Discrete design checks. A CFD solve supports hypotheses; it does not prove
continuum equations, boundary data, turbulence closure or hardware. -/
namespace AA

theorem finite_region_temperature_bound {ι : Type*} (s : Finset ι)
    (w temp : ι → ℝ) (limit : ℝ)
    (hw : 0 < ∑ i ∈ s, w i)
    (hwi : ∀ i ∈ s, 0 ≤ w i)
    (ht : ∀ i ∈ s, temp i ≤ limit) :
    (∑ i ∈ s, w i * temp i) / (∑ i ∈ s, w i) ≤ limit := by
  apply (div_le_iff₀ hw).mpr
  calc
    (∑ i ∈ s, w i * temp i) ≤ ∑ i ∈ s, w i * limit := by
      exact Finset.sum_le_sum (fun i hi => mul_le_mul_of_nonneg_left (ht i hi) (hwi i hi))
    _ = limit * (∑ i ∈ s, w i) := by
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro i hi
      ring

/-- A mesh difference alone does not prove the assumed error envelope. -/
theorem cfd_region_upper_certificate (model computed error limit : ℝ)
    (herror : model ≤ computed + error)
    (hcomputed : computed + error ≤ limit) : model ≤ limit := by linarith

theorem cad_flow_speed_limit (area flow speed limit : ℝ)
    (ha : 0 < area) (hb : flow = area*speed)
    (hf : flow ≤ area*limit) : speed ≤ limit := by nlinarith

theorem cold_path_heat_allowance (capacity ts tm heat allowance : ℝ)
    (hc : 0 < capacity) (hb : capacity*(ts-tm) = heat)
    (hh : heat ≤ capacity*allowance) : ts-tm ≤ allowance := by nlinarith

theorem refinement_upper_bound_improves (oldMean newMean oldError newError : ℝ)
    (h : newMean+newError < oldMean+oldError) :
    newMean-oldMean < oldError-newError := by linarith
end AA
#print axioms AA.finite_region_temperature_bound
#print axioms AA.cfd_region_upper_certificate
#print axioms AA.cad_flow_speed_limit
#print axioms AA.cold_path_heat_allowance
#print axioms AA.refinement_upper_bound_improves

namespace AA
/-- Balance and heat limit are explicit physical hypotheses. -/
theorem three_motor_source_certificate (ts heat : ℝ)
    (balance : (58.5492:ℝ)*(40-ts) = 2520-heat)
    (heatLimit : heat ≤ (312.2624:ℝ)) : ts ≤ (2.3:ℝ) := by nlinarith

theorem four_motor_warm_source_certificate (ts heat : ℝ)
    (balance : (78.0656:ℝ)*(40-ts) = 3360-heat)
    (heatLimit : heat ≤ (861.9008:ℝ)) : ts ≤ 8 := by nlinarith

theorem three_motor_supply_with_allowance :
    (3:ℝ)*16.2*60/1000*(115/100) = (3.3534:ℝ) := by norm_num
end AA
#print axioms AA.three_motor_source_certificate
#print axioms AA.four_motor_warm_source_certificate
#print axioms AA.three_motor_supply_with_allowance

namespace AA
/-- Gives the admissible combined upward temperature-error budget. Its
hypothesis is not established by a CFD mesh comparison alone. -/
theorem strict_cooling_error_budget (ambient computed model error drop : ℝ)
    (hmodel : model ≤ computed+error)
    (hbudget : computed+error < ambient-drop) : drop < ambient-model := by linarith
end AA
#print axioms AA.strict_cooling_error_budget

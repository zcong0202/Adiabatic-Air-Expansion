import AAThermo.Model

/-! Conditional, constant-cp steady balances for the 19 October motor-seat scope.
Catalogue data, heat transfer and zone exchange remain explicit hypotheses. -/
namespace AA

noncomputable def motorSupply (tin gain power heat capacity : ℝ) : ℝ :=
  tin + gain - (power - heat) / capacity

theorem motor_source_target_iff (tin gain power heat capacity target : ℝ)
    (hc : 0 < capacity) :
    motorSupply tin gain power heat capacity ≤ target ↔
      capacity * (tin + gain - target) + heat ≤ power := by
  dsimp [motorSupply]
  constructor
  · intro h
    have hmul := (mul_le_mul_of_nonneg_right h (le_of_lt hc))
    field_simp at hmul
    nlinarith
  · intro h
    apply (le_of_mul_le_mul_right ?_ hc)
    field_simp
    nlinarith

/-- Two inlet streams and one net heat load, no radiation/nonuniformity closure. -/
theorem motor_zone_deficit_identity (c w ta ts tz load : ℝ)
    (hb : (c+w)*tz = c*ts + w*ta + load) :
    (c+w)*(ta-tz) = c*(ta-ts)-load := by nlinarith

theorem motor_zone_target_iff (c w ta ts tz load delta : ℝ)
    (hc : 0 < c+w)
    (hb : (c+w)*tz = c*ts + w*ta + load) :
    delta ≤ ta-tz ↔ (c+w)*delta + load ≤ c*(ta-ts) := by
  have hi := motor_zone_deficit_identity c w ta ts tz load hb
  constructor
  · intro h
    have := mul_le_mul_of_nonneg_left h (le_of_lt hc)
    linarith
  · intro h
    have : (c+w)*delta ≤ (c+w)*(ta-tz) := by linarith
    nlinarith

/-- Returning all shaft work as heat to the same zone cancels its cooling term. -/
theorem motor_work_return_cancellation (power capacity rise heat : ℝ) :
    (power-capacity*rise-heat)-power = -capacity*rise-heat := by ring

/-- Necessary supply condition, using a shared free-air reference. -/
theorem four_motor_supply_requirement (flow : ℝ)
    (h : 4*(16.2:ℝ)*60/1000 ≤ flow) : (3.888:ℝ) ≤ flow := by norm_num at h ⊢; exact h

/-- A concrete dry, fully captured reference certificate. No wind map is proved.
C=mdot*cp; heat includes motor and downstream heat pickup. -/
theorem motor_seat_reference_certificate (ts tz warm heat : ℝ)
    (source : (78.0656:ℝ)*(40-ts) = 3360-heat)
    (hh : heat ≤ (312.2624:ℝ))
    (hw0 : 0 ≤ warm) (hw : warm ≤ (120.72:ℝ))
    (zone : ((78.0656:ℝ)+warm)*tz = (78.0656:ℝ)*ts + warm*30 + 100) :
    tz < 20 := by
  have hi := motor_zone_deficit_identity (78.0656:ℝ) warm 30 ts tz 100 zone
  have hdrop : (2267.0816:ℝ) ≤ (78.0656:ℝ)*(30-ts) := by nlinarith
  have hc : 0 < (78.0656:ℝ)+warm := by linarith
  by_contra hn
  have hz : 20 ≤ tz := le_of_not_gt hn
  have hprod : ((78.0656:ℝ)+warm)*(30-tz) ≤ ((78.0656:ℝ)+warm)*10 :=
    mul_le_mul_of_nonneg_left (by linarith) (le_of_lt hc)
  nlinarith

end AA
#print axioms AA.motor_source_target_iff
#print axioms AA.motor_zone_deficit_identity
#print axioms AA.motor_zone_target_iff
#print axioms AA.motor_work_return_cancellation
#print axioms AA.four_motor_supply_requirement
#print axioms AA.motor_seat_reference_certificate

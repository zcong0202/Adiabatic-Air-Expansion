import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Tactic

/-!
# AA dry-air feasibility model

Temperatures used in differences may be Celsius; turbine inputs MUST be Kelvin.
Pressures used in ratios MUST be absolute. SI units throughout.
These theorems prove implications of explicit model assumptions. They do not
prove an empirical source map, turbulence closure, or the installed prototype.
-/

namespace AA

/-- Uniform, well-mixed control-volume temperature. mc is CAPTURED cold flow,
mw is incoming warm flow; heat is an extra sensible load in watts. -/
noncomputable def mixTemp (mc mw td te heat cp : ℝ) : ℝ :=
  (mc * td + mw * te + heat / cp) / (mc + mw)

noncomputable def mixDrop (ta mc mw td te heat cp : ℝ) : ℝ :=
  ta - mixTemp mc mw td te heat cp

/-- Source mass fraction averaged by AREA, not by mass flux. -/
noncomputable def areaDrop (ta te td alpha : ℝ) : ℝ := ta - te + alpha * (te - td)

noncomputable def retainedAreaDrop (ta te ts alpha retention : ℝ) : ℝ :=
  ta - te + alpha * retention * (te - ts)

/-- Constant ambient/heat conductance, dry constant-cp line model. -/
noncomputable def retention (ua mc cp : ℝ) : ℝ := Real.exp (-ua / (mc * cp))

theorem mixDrop_identity (ta mc mw td te heat cp : ℝ)
    (hs : 0 < mc + mw) :
    mixDrop ta mc mw td te heat cp =
      (mc * (ta - td) + mw * (ta - te) - heat / cp) / (mc + mw) := by
  dsimp [mixDrop, mixTemp]
  field_simp; ring

/-- Exact strict target criterion under the well-mixed dry balance. -/
theorem mixing_target_iff (ta mc mw td te heat cp delta : ℝ)
    (hs : 0 < mc + mw) :
    delta < mixDrop ta mc mw td te heat cp ↔
      mw * (te - ta + delta) + heat / cp < mc * (ta - td - delta) := by
  rw [mixDrop_identity ta mc mw td te heat cp hs, lt_div_iff₀ hs]
  constructor <;> intro h <;> nlinarith

/-- Required captured cold mass flow when the cold stream is cold enough. -/
theorem required_mass_iff (ta mc mw td te heat cp delta : ℝ)
    (hs : 0 < mc + mw) (hg : 0 < ta - td - delta) :
    delta < mixDrop ta mc mw td te heat cp ↔
      (mw * (te - ta + delta) + heat / cp) / (ta - td - delta) < mc := by
  rw [mixing_target_iff ta mc mw td te heat cp delta hs, div_lt_iff₀ hg]

/-- If even pure cold delivery cannot beat delta, adding warm air cannot fix it. -/
theorem source_too_warm (ta mc mw td te heat cp delta : ℝ)
    (hs : 0 < mc + mw) (hc : 0 ≤ mc) (hw : 0 ≤ mw)
    (hq : 0 ≤ heat) (hcp : 0 < cp) (hd : 0 < delta)
    (htd : ta - delta ≤ td) (hte : ta ≤ te) :
    ¬ delta < mixDrop ta mc mw td te heat cp := by
  rw [mixing_target_iff ta mc mw td te heat cp delta hs]
  have a : mc * (ta - td - delta) ≤ 0 :=
    mul_nonpos_of_nonneg_of_nonpos hc (by linarith)
  have b : 0 ≤ mw * (te - ta + delta) := mul_nonneg hw (by linarith)
  have c : 0 ≤ heat / cp := div_nonneg hq hcp.le
  linarith

/-- Exact area-mean criterion. No flow-to-alpha relation is assumed. -/
theorem required_area_fraction_iff (ta te td alpha delta : ℝ)
    (hg : 0 < te - td) :
    delta < areaDrop ta te td alpha ↔
      (te - ta + delta) / (te - td) < alpha := by
  rw [div_lt_iff₀ hg]
  dsimp [areaDrop]
  constructor <;> intro h <;> nlinarith

/-- Exact finite-cell area averaging. Fractions need not be uniform. The dry
linear pointwise mixing law and a common retention factor are hypotheses. -/
theorem finite_area_average {n : ℕ} (weights fraction : Fin n → ℝ)
    (ta te ts r : ℝ) (hw : ∑ i, weights i = 1) :
    ta - (∑ i, weights i * (te - fraction i * r * (te-ts))) =
      retainedAreaDrop ta te ts (∑ i, weights i * fraction i) r := by
  have step : (∑ i, weights i * (te - fraction i*r*(te-ts))) =
      (∑ i, weights i*te) - (∑ i, (weights i*fraction i)*r*(te-ts)) := by
    rw [← Finset.sum_sub_distrib]
    apply Finset.sum_congr rfl
    intro i _
    ring
  rw [step, ← Finset.sum_mul, ← Finset.sum_mul, ← Finset.sum_mul, hw]
  dsimp [retainedAreaDrop]
  ring

theorem area_fraction_bounds {n : ℕ} (weights fraction : Fin n → ℝ)
    (hw : ∑ i, weights i = 1) (hwp : ∀ i, 0 ≤ weights i)
    (hf : ∀ i, 0 ≤ fraction i ∧ fraction i ≤ 1) :
    0 ≤ (∑ i, weights i*fraction i) ∧ (∑ i, weights i*fraction i) ≤ 1 := by
  constructor
  · exact Finset.sum_nonneg (fun i _ ↦ mul_nonneg (hwp i) (hf i).1)
  · calc
      (∑ i, weights i*fraction i) ≤ ∑ i, weights i := by
        apply Finset.sum_le_sum
        intro i _
        nlinarith [mul_nonneg (hwp i) (sub_nonneg.mpr (hf i).2)]
      _ = 1 := hw

/-- Necessary energy-flux bound for an area target, with an explicit NORMAL
velocity lower bound and nonnegative local temperature deficits. k = rho*cp.
No conclusion of sufficiency is made. Cell areas are in square metres. -/
theorem finite_flux_necessary {n : ℕ} (area speed deficit : Fin n → ℝ)
    (k low budget delta : ℝ) (hk : 0 < k) (hl : 0 < low)
    (ha : ∀ i, 0 ≤ area i) (hd : ∀ i, 0 ≤ deficit i)
    (hu : ∀ i, low ≤ speed i)
    (energy : k * (∑ i, area i*speed i*deficit i) ≤ budget)
    (pass : delta*(∑ i, area i) < ∑ i, area i*deficit i) :
    k*low*delta*(∑ i, area i) < budget := by
  have bound : low*(∑ i, area i*deficit i) ≤ ∑ i, area i*speed i*deficit i := by
    rw [Finset.mul_sum]
    apply Finset.sum_le_sum
    intro i _
    have h := mul_le_mul_of_nonneg_right (hu i) (mul_nonneg (ha i) (hd i))
    nlinarith
  have h1 := mul_lt_mul_of_pos_left pass (mul_pos hk hl)
  have h2 := mul_le_mul_of_nonneg_left bound hk.le
  nlinarith

theorem retention_bounds (ua mc cp : ℝ) (hu : 0 ≤ ua)
    (hm : 0 < mc) (hc : 0 < cp) :
    0 < retention ua mc cp ∧ retention ua mc cp ≤ 1 := by
  constructor
  · exact Real.exp_pos _
  · apply Real.exp_le_one_iff.mpr
    exact div_nonpos_of_nonpos_of_nonneg (neg_nonpos.mpr hu) (mul_pos hm hc).le

/-- Algebraic form of the hose feasibility bound; B is initial area cooling
amplitude, C is the target plus the hot-entrainment offset, k = mc*cp. -/
theorem heat_budget_iff (ua k B C : ℝ) (hk : 0 < k)
    (hB : 0 < B) (hC : 0 < C) :
    C < B * Real.exp (-ua / k) ↔ ua < k * Real.log (B / C) := by
  have ratio : C / B = (B / C)⁻¹ := by field_simp
  have logratio : Real.log (C / B) = -Real.log (B / C) := by
    rw [ratio, Real.log_inv]
  have divided : C < B * Real.exp (-ua / k) ↔ C / B < Real.exp (-ua / k) := by
    rw [div_lt_iff₀ hB]
    simp only [mul_comm]
  rw [divided, ← Real.log_lt_iff_lt_exp (div_pos hC hB), logratio,
      lt_div_iff₀ hk]
  constructor <;> intro h <;> nlinarith

/-- A separate lumped exposure model, only IF a fitted positive time constant
describes the parcel. It supplies no universal air-reheating time. -/
theorem exposure_time_budget_iff (time tau initial target : ℝ)
    (ht : 0 < tau) (hi : 0 < initial) (hg : 0 < target) :
    target < initial * Real.exp (-time / tau) ↔
      time < tau * Real.log (initial / target) := by
  exact heat_budget_iff time tau initial target ht hi hg

theorem fixed_mixing_required_mass (ua mc cp B C : ℝ)
    (hm : 0 < mc) (hcp : 0 < cp) (hB : 0 < B) (hC : 0 < C)
    (hl : 0 < Real.log (B / C)) :
    C < B * retention ua mc cp ↔
      ua / (cp * Real.log (B / C)) < mc := by
  rw [retention, heat_budget_iff ua (mc * cp) B C (mul_pos hm hcp) hB hC,
      div_lt_iff₀ (mul_pos hcp hl)]
  constructor <;> intro h <;> nlinarith

/-- Monotonicity of loss-free mixing in cold mass, at fixed warm inflow and
delivery state. Source/geometry coupling is outside this theorem. -/
theorem more_cold_mass_helps (ta td te m1 m2 mw cp : ℝ)
    (h1 : 0 < m1 + mw) (h2 : 0 < m2 + mw)
    (hm : m1 ≤ m2) (hw : 0 ≤ mw) (ht : td ≤ te) :
    mixDrop ta m1 mw td te 0 cp ≤ mixDrop ta m2 mw td te 0 cp := by
  dsimp [mixDrop, mixTemp]
  simp only [zero_div, add_zero]
  rw [sub_le_sub_iff_left, div_le_div_iff₀ h2 h1]
  have h := mul_nonneg hw (mul_nonneg (sub_nonneg.mpr hm) (sub_nonneg.mpr ht))
  nlinarith

/-- If cold AND entrained warm flow scale together, the loss-free temperature
is unchanged. Higher throughput alone is not a temperature-drop guarantee. -/
theorem scaling_both_flows_preserves_drop (ta td te mc mw cp scale : ℝ)
    (_hs : 0 < mc + mw) (hk : 0 < scale) :
    mixDrop ta (scale * mc) (scale * mw) td te 0 cp =
      mixDrop ta mc mw td te 0 cp := by
  dsimp [mixDrop, mixTemp]
  simp only [zero_div, add_zero]
  congr 1
  rw [show scale * mc + scale * mw = scale * (mc + mw) by ring]
  rw [show scale * mc * td + scale * mw * te =
      scale * (mc * td + mw * te) by ring]
  exact mul_div_mul_left _ _ (ne_of_gt hk)

/-- Equal-cp ideal gas + isoenthalpic regulator + negligible velocity change. -/
theorem ideal_gas_throttle_temperature (cp t1 t2 : ℝ) (hc : 0 < cp)
    (enthalpy_balance : cp * t1 = cp * t2) : t1 = t2 := by
  nlinarith

/-- Work-producing expansion. Ratio = (Pout/Pin)^((gamma-1)/gamma). -/
noncomputable def expanderTemperature (tin eta ratio : ℝ) : ℝ :=
  tin * (1 - eta * (1 - ratio))

noncomputable def idealRatio (pin pout gamma : ℝ) : ℝ :=
  (pout / pin) ^ ((gamma - 1) / gamma)

theorem ideal_ratio_bounds (pin pout gamma : ℝ)
    (hp : 0 < pout) (hpress : pout < pin) (hg : 1 < gamma) :
    0 < idealRatio pin pout gamma ∧ idealRatio pin pout gamma < 1 := by
  have hpin : 0 < pin := lt_trans hp hpress
  have hratio : pout / pin < 1 := (div_lt_one hpin).mpr hpress
  constructor
  · exact Real.rpow_pos_of_pos (div_pos hp hpin) _
  · exact Real.rpow_lt_one (div_pos hp hpin).le hratio
      (div_pos (by linarith) (by linarith))

theorem expander_bounds (tin eta ratio : ℝ) (ht : 0 ≤ tin)
    (he : 0 ≤ eta) (he1 : eta ≤ 1) (_hr : 0 ≤ ratio) (hr1 : ratio ≤ 1) :
    tin * ratio ≤ expanderTemperature tin eta ratio ∧
      expanderTemperature tin eta ratio ≤ tin := by
  dsimp [expanderTemperature]
  have a := mul_nonneg ht (mul_nonneg he (sub_nonneg.mpr hr1))
  have b := mul_nonneg ht (mul_nonneg (sub_nonneg.mpr he1) (sub_nonneg.mpr hr1))
  constructor <;> nlinarith

/-- A vortex redistributes enthalpy: lower Tc requires hotter rejection or a
different cold fraction. This identity is not a measured vortex performance map. -/
theorem vortex_hot_temperature (tin tc th fraction : ℝ) (hf : fraction < 1)
    (balance : tin = fraction * tc + (1 - fraction) * th) :
    th = (tin - fraction * tc) / (1 - fraction) := by
  apply (eq_div_iff (ne_of_gt (sub_pos.mpr hf))).mpr
  nlinarith

/-- A candidate cold fraction and cold temperature must also fit the rejected
hot-stream energy. This is a necessary dry balance, not a device map. -/
theorem vortex_fraction_bound (tin tc th thMax fraction : ℝ)
    (hf : fraction ≤ 1) (hh : th ≤ thMax) (hg : tc < thMax)
    (balance : tin = fraction*tc + (1-fraction)*th) :
    fraction ≤ (thMax-tin)/(thMax-tc) := by
  rw [le_div_iff₀ (sub_pos.mpr hg)]
  have h := mul_nonneg (sub_nonneg.mpr hf) (sub_nonneg.mpr hh)
  nlinarith

/-- Nonnegative storage inventory imposes a burst mass budget. -/
theorem buffer_inventory_iff (inventory production discharge pulse : ℝ) :
    0 ≤ inventory + (production - discharge) * pulse ↔
      (discharge - production) * pulse ≤ inventory := by
  constructor <;> intro h <;> nlinarith

/-- Storage does not change the average source-flow bound. -/
theorem duty_budget_iff (production discharge pulse period : ℝ)
    (hp : 0 < period) (hd : 0 < discharge) :
    discharge * pulse ≤ production * period ↔
      pulse / period ≤ production / discharge := by
  rw [div_le_div_iff₀ hp hd]
  constructor <;> intro h <;> nlinarith

/-- Shared delivery stage: a uniform target of area A and normal speed u has
mass flow rho*A*u. This is NOT an arbitrary nonuniform area-mean theorem. -/
theorem uniform_target_capacity_iff (cold targetMass gap delta : ℝ)
    (hm : 0 < targetMass) (hg : 0 < gap) :
    delta < cold * gap / targetMass ↔ delta * targetMass / gap < cold := by
  rw [lt_div_iff₀ hm, div_lt_iff₀ hg]

end AA

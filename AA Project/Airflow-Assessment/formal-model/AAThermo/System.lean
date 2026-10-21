import AAThermo.Model

/-! System-level bounds. CFD and catalogue envelopes are hypotheses, not axioms. -/
namespace AA

/-- A conservative area bound IF source/delivery bounds hold simultaneously.
The bound does not certify that CFD errors or hardware variation obey them. -/
theorem robust_area_envelope (ta te ts alpha r amin rmin spanmin hot : ℝ)
    (ha0 : 0 ≤ amin) (hr0 : 0 ≤ rmin) (hs0 : 0 ≤ spanmin)
    (ha : amin ≤ alpha) (hr : rmin ≤ r) (hs : spanmin ≤ te-ts)
    (hh : -hot ≤ ta-te) :
    -hot + amin*rmin*spanmin ≤ retainedAreaDrop ta te ts alpha r := by
  have hap : 0 ≤ alpha := le_trans ha0 ha
  have arp : 0 ≤ alpha*r := mul_nonneg hap (le_trans hr0 hr)
  have har : amin*rmin ≤ alpha*r := mul_le_mul ha hr hr0 hap
  have hprod := mul_le_mul har hs hs0 arp
  dsimp [retainedAreaDrop]
  linarith

/-- A passive nozzle can exchange static enthalpy and kinetic energy.
It does not remove stagnation enthalpy in this adiabatic no-work balance. -/
theorem nozzle_static_kinetic_budget (cp tin tout uin uout : ℝ)
    (balance : cp*tin + uin^2/2 = cp*tout + uout^2/2) :
    cp*(tout-tin) = (uin^2-uout^2)/2 := by
  nlinarith

/-- Inventory swing follows from two uniform isothermal ideal-gas states.
Fast discharge, vessel walls, regulators and minimum flow pressure need more. -/
theorem isothermal_receiver_inventory (v phigh plow gas temp : ℝ) :
    v*phigh/(gas*temp) - v*plow/(gas*temp) =
      v*(phigh-plow)/(gas*temp) := by
  ring

/-- A rational, conservative retention certificate. Uses exp(x) >= 1+x,
not a floating-point evaluation of the exponential. SI units. -/
theorem stock_path_retention (ua mc : ℝ)
    (hu : ua ≤ (16:ℝ)/100) (hm : (24:ℝ)/10000 ≤ mc) :
    (93:ℝ)/100 ≤ retention ua mc 1005 := by
  have hd : 0 < mc*1005 := by nlinarith
  have hfrac : ua/(mc*1005) ≤ (7:ℝ)/100 := by
    apply (div_le_iff₀ hd).mpr
    nlinarith
  have he := Real.add_one_le_exp (-ua/(mc*1005))
  dsimp [retention]
  simp only [neg_div] at he ⊢
  linarith

/-- Conditional >6 K target for the stock reference's declared dry/mixing
envelope, with at most 0.5 K additional moisture warming. Source maps,
CFD fractions and the moisture bound are explicit hypotheses. -/
theorem stock_reference_target_certificate
    (ta te ts alpha ua mc moisture : ℝ)
    (ha : (27:ℝ)/100 ≤ alpha)
    (hu : ua ≤ (16:ℝ)/100) (hm : (24:ℝ)/10000 ≤ mc)
    (hs : 36 ≤ te-ts) (hh : -2 ≤ ta-te) (hw : moisture ≤ (1:ℝ)/2) :
    6 < retainedAreaDrop ta te ts alpha (retention ua mc 1005) - moisture := by
  have hr := stock_path_retention ua mc hu hm
  have h := robust_area_envelope ta te ts alpha (retention ua mc 1005)
    ((27:ℝ)/100) ((93:ℝ)/100) 36 2
    (by norm_num) (by norm_num) (by norm_num) ha hr hs hh
  linarith

end AA

#print axioms AA.robust_area_envelope
#print axioms AA.nozzle_static_kinetic_budget
#print axioms AA.isothermal_receiver_inventory
#print axioms AA.stock_path_retention
#print axioms AA.stock_reference_target_certificate

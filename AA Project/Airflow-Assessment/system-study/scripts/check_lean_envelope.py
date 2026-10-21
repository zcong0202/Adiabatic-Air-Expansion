"""Numerical checks of hypotheses for the separate kernel-checked theorem.
These float checks do not establish actual hardware bounds or CFD accuracy.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];r=json.loads((ROOT/'results/campaign.json').read_text());s=r['config']['stress_ASSUMPTIONS'];checks=[]
for c in r['cases']:
 alpha=c['cfd_mean_fraction']*s['area_fraction_factor'];span=34+s['entrained_air_above_ambient_c']-c['stress_source_c'];warming=c['stressed_dry_drop_c']-c['stressed_equilibrium_moist_drop_c']
 conditions={'area_fraction_at_least_0p27':alpha>=.27,'cold_flow_at_least_2p4_g_s':c['mass_g_s']>=2.4,'UA_at_most_0p16_w_K':c['stress_UA_w_K']<=.16,'source_contrast_at_least_36K':span>=36,'hot_offset_at_most_2K':s['entrained_air_above_ambient_c']<=2,'moisture_warming_at_most_0p5K':warming<=.5,'numerical_case_accepted':c['numerically_accepted']}
 checks.append({'case':c['case'],'computed_hypotheses_match':all(conditions.values()),'conditions':conditions,'effective_area_fraction':alpha,'source_contrast_K':span,'moisture_warming_K':warming})
proof=json.loads((ROOT.parent/'formal-model/proof-verification.json').read_text())
out={'theorem':'AA.stock_reference_target_certificate','Lean_build_succeeded':proof['build_succeeded'],'theorem_present_in_axiom_audit':any(x['name']=='stock_reference_target_certificate' for x in proof['theorems']),'conditional_lower_bound_K':6.5396,'target_strictly_above_K':6,'cases':checks,'actual_hardware_hypotheses_established':False,'scope':'Lean proves the implication over reals. This file only checks numerical model outputs against its hypotheses. Supplier/CFD/moisture bounds are still assumptions.'}
(ROOT/'results/lean-envelope-check.json').write_text(json.dumps(out,indent=2));print(json.dumps({'Lean_build':out['Lean_build_succeeded'],'theorem_audited':out['theorem_present_in_axiom_audit'],'matching_cases':[x['case'] for x in checks if x['computed_hypotheses_match']]},indent=2))

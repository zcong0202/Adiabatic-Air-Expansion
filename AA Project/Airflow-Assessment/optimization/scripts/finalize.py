"""Final evidence check. Reject unfinished work and keep uncertainty visible."""
import json,math
from round_jet import OPT
from search import read_cases
records=read_cases();running=[]
for r in records:
 state=json.loads((OPT/'cases'/r['case']/'run-status.json').read_text())
 if state['status'].startswith('running'):running.append(r['case'])
if running:raise RuntimeError('Cases still running: '+', '.join(running))
by={r['case']:r for r in records};chosen=by['R07_D24_diffuser_3deg_SST']
assert chosen['numerically_accepted'] and chosen['target']['mean_drop_c']>6
for name,tol in [('R12_D24_a3_second_order',.5),('R13_D24_a3_fine',.5)]:
 assert by[name]['numerically_accepted'] and abs(by[name]['target']['mean_drop_c']-chosen['target']['mean_drop_c'])<=tol
assert all(not r['hardware_validated'] for r in records)
geometry=json.loads((OPT/'evidence/candidate-geometry-verification.json').read_text());assert len(geometry)==4 and all(x['watertight'] and x['winding_consistent'] for x in geometry)
accepted=[r['case'] for r in records if r['numerically_accepted']]
rejected=[{'case':r['case'],'failed_checks':[k for k,v in r['numerical_gates'].items() if not v]} for r in records if not r['numerically_accepted']]
checks={'status':'Conditional still-air screening completed','case_count':len(records),'accepted_count':len(accepted),'accepted_cases':accepted,'rejected_cases':rejected,'selected_case':chosen['case'],'selected_mean_drop_c':chosen['target']['mean_drop_c'],'finer_mesh_change_c':by['R13_D24_a3_fine']['target']['mean_drop_c']-chosen['target']['mean_drop_c'],'higher_order_change_c':by['R12_D24_a3_second_order']['target']['mean_drop_c']-chosen['target']['mean_drop_c'],'internal_alternative_closure_accepted':by['R14_D24_a3_kEpsilon']['numerically_accepted'],'all_geometry_checks':'passed','mathematical_objective_checks':'passed; see computation-verification.json','physical_hardware_validation':False,'wind_validation':False,'hot_exhaust_plume_resolved':False,'major_open_inputs':['Actual paired cold-branch flow and temperature with the attachment fitted','Source pressure response, real hot exhaust exposure, humidity and wall heat pickup','Real installation length, connector dimensions and mounting']}
(OPT/'evidence/final-validation.json').write_text(json.dumps(checks,indent=2))
(OPT/'results/internal-validation.json').write_text(json.dumps({'status':'Final audited evidence supersedes the initial unused-epsilon copy error','checks':[{'case':n,'numerically_accepted':by[n]['numerically_accepted'],'mean_drop_c':by[n]['target']['mean_drop_c']} for n in ['R12_D24_a3_second_order','R13_D24_a3_fine','R14_D24_a3_kEpsilon']]},indent=2))
print(json.dumps(checks,indent=2))

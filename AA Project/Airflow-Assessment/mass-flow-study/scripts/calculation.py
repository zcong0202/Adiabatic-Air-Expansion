"""First-principles source budgets and independent jet-scale diagnostics."""
import json,csv,math
from build import STUDY,PA,GAS,CP,SOURCE_C
OUT=STUDY/'results'

def calculate():
    ambient=30;drop=ambient-SOURCE_C;rho=PA/(GAS*(SOURCE_C+273.15));rho_target=PA/(GAS*(ambient-6+273.15));gprime=9.81*(1-(SOURCE_C+273.15)/(ambient+273.15));sources=[]
    for gs in [2,27,52,77]:
        m=gs/1000;energy=m*CP*drop*10;ideal_mass=energy/(CP*6)
        sources.append(dict(total_g_s=gs,source_sensible_w=m*CP*drop,source_mass_10s_kg=m*10,cold_energy_10s_j=energy,ideal_max_mixed_mass_at6_kg=ideal_mass,ideal_max_volume_at6_m3=ideal_mass/rho_target,scope='Loss-free mixing/enthalpy bound over 10 s; not a prediction of resident volume or captured flow.'))
    rows=[]
    for file in OUT.glob('*.json'):
        d=json.loads(file.read_text())
        if not isinstance(d,dict) or 'final' not in d or 'inputs' not in d:continue
        c=d['inputs'];w,h=c['width_m'],c['height_m'];A=w*h;n=c['outlets'];m=c['total_g_s']/1000;U=m/(rho*A*n);Dh=2*w*h/(w+h)
        mix=d['final']['regions'].get('range20to50',{}).get('6',{});ideal=mix.get('source_mass_kg',0)*CP*drop
        mixing_error=(mix.get('deficit_j',0)/ideal-1)*100 if ideal>1e-8 else None
        rows.append(dict(temperature_origin_consistency_error_percent=mixing_error,case=d['case'],total_g_s=c['total_g_s'],outlets=n,per_outlet_g_s=m/n*1000,area_each_m2=A,area_total_m2=A*n,calculated_speed_m_s=U,reynolds=m/n*Dh/(A*1.8e-5),densimetric_froude=U/math.sqrt(gprime*Dh),reduced_gravity_m_s2=gprime,total_momentum_n=m*U,source_sensible_w=m*CP*drop,exit_kinetic_power_w=.5*m*U**2,total_enthalpy_cold_w=m*CP*drop-.5*m*U**2,static_to_total_k=U**2/(2*CP)))
    if rows:
        with (OUT/'calculation-screen.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(sorted(rows,key=lambda r:r['case']))
    data=dict(source_c=SOURCE_C,ambient_c=ambient,source_density_kg_m3=rho,target_24c_density_kg_m3=rho_target,source_budgets=sources,jet_diagnostics=rows,equations={'Q':'mass_flow * cp * (ambient-source)','outlet_speed':'total_mass / (N * rho_source * area_each)','Re':'mass_each * Dh / (area_each * viscosity)','Fr':'U / sqrt(g_reduced * Dh)','g_reduced':'g * (1 - T_source_K/T_ambient_K)'},limits=['Densimetric Froude is a scale diagnostic, not a jet trajectory solution','Energy upper bounds do not include leakage, entrainment losses, escape or sunlight','Source and exit static temperature fixed; native CFD energy audits retain kinetic and gravity terms','Actual motor/collector performance and internal nozzle heat transfer unvalidated'])
    (OUT/'calculations.json').write_text(json.dumps(data,indent=2));print(json.dumps(sources,indent=2))
if __name__=='__main__':calculate()

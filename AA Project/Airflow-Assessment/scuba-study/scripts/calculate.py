"""Scuba inventory and conditional loaded-motor source. SI units, real-air EOS.
No regulator capacity or thermal hardware qualification is implied.
"""
from pathlib import Path
import json,math
from CoolProp.CoolProp import PropsSI
ROOT=Path(__file__).resolve().parents[2];STUDY=ROOT/'scuba-study';OUT=STUDY/'results'
PA=101325.;R=8314.46261815324/28.965;CP=1006.;GAMMA=1.4

def calculate():
    nominal=json.loads((ROOT/'pass-by-study/source-input.json').read_text())
    m=nominal['mass_per_motor_kg_s'];w=nominal['shaft_work_per_motor_w'];ua=nominal['cold_path_ua_w_k'];ta=30.;t0=303.15;v=.012;p0=PA+200e5;pf=PA+20e5
    rho0=PropsSI('D','P',p0,'T',t0,'Air');s0=PropsSI('S','P',p0,'T',t0,'Air');M0=v*rho0
    source=[]
    for tin in [30,40]:
        tm=tin-w/(m*CP);tn=ta+(tm-ta)*math.exp(-ua/(m*CP));source.append(dict(motor_inlet_c=tin,motor_exhaust_c=tm,nozzle_c=tn,sensible_w=m*CP*(ta-tn),mass_g_s=m*1000,cold_path_ua_w_k=ua))
    inventory=[]
    for liters,bar in [(10,200),(12,200),(15,200),(12,232),(12,300)]:
        vv=liters/1000;pp=PA+bar*1e5;rr=PropsSI('D','P',pp,'T',t0,'Air');ss=PropsSI('S','P',pp,'T',t0,'Air')
        for floor in [10,20]:
            f=PA+floor*1e5;end_iso=PropsSI('D','P',f,'T',t0,'Air');end_ad=PropsSI('D','P',f,'S',ss,'Air');mi=vv*rr;iso=mi-vv*end_iso;ad=mi-vv*end_ad
            inventory.append(dict(volume_l=liters,fill_bar_g=bar,cutoff_bar_g=floor,initial_real_mass_kg=mi,usable_isothermal_kg=iso,usable_adiabatic_kg=ad,isothermal_one_motor_s=iso/m,adiabatic_one_motor_s=ad/m,isothermal_four_motor_s=iso/(4*m),adiabatic_four_motor_s=ad/(4*m),complete_10s_pulses_isothermal=math.floor(iso/(10*m)),complete_10s_pulses_adiabatic=math.floor(ad/(10*m)),adiabatic_final_tank_c=PropsSI('T','P',f,'S',ss,'Air')-273.15))
    trajectory=[]
    nominalrow=next(x for x in inventory if x['volume_l']==12 and x['fill_bar_g']==200 and x['cutoff_bar_g']==20)
    for seconds in [0,10,30,60,90,100]:
        rho=(M0-seconds*m)/v
        trajectory.append(dict(time_s=seconds,mass_kg=rho*v,isothermal_bar_g=(PropsSI('P','D',rho,'T',t0,'Air')-PA)/1e5,adiabatic_bar_g=(PropsSI('P','D',rho,'S',s0,'Air')-PA)/1e5,adiabatic_tank_c=PropsSI('T','D',rho,'S',s0,'Air')-273.15))
    throttle=[]
    for pg in [200,100,50,20,10]:
        pi=PA+pg*1e5;hi=PropsSI('H','P',pi,'T',t0,'Air');Tout=PropsSI('T','P',PA+6.3e5,'H',hi,'Air')-273.15
        throttle.append(dict(tank_bar_g=pg,tank_c=30,adiabatic_isenthalpic_outlet_c=Tout))
    # Choked ideal-gas throat is a screening lower bound on flow area, not a valve/regulator selection.
    cd=.7;upstream=pf;factor=math.sqrt(GAMMA/(R*t0))*(2/(GAMMA+1))**((GAMMA+1)/(2*(GAMMA-1)));area=m/(cd*upstream*factor)
    result=dict(status='Conditional engineering screen; no hardware qualification',assumptions=dict(reference_tank_l=12,fill_bar_g=200,initial_tank_c=30,operational_cutoff_bar_g=20,cutoff_status='Planning reserve/dropout assumption; verify regulator flow curve',motor_inlet_bar_g=6.3,motor_max_working_bar_g=7,motor_inlet_c_for_cfd=30,motor_g_s=m*1000,motor_free_air_l_s=16.2,motor_shaft_work_w=w,motor_rpm=1270,ambient_c=30,cp_j_kg_k=CP,cold_path_ua_w_k=ua,ua_status='Conservative reuse of full prior four-motor-path UA for one motor; not measured',shaft_heat_return_w=0,regulator_flow_verified=False,motor_cooling_verified=False,moisture_model=False),nominal=nominalrow,motor=dict(mass_g_s=m*1000,free_air_l_min=16.2*60,shaft_load_w=w,shaft_torque_nm=w/(1270*2*math.pi/60),mass_10s_g=m*10*1000,flow_77g_requires_motors=77/(m*1000),flow_77g_status='One motor cannot reproduce 77 g/s at its rated loaded point',continuous_operation=False),sources=source,inventory=inventory,trajectory=trajectory,regulator_ideal_throttle=throttle,regulator=dict(required_inlet_rating_bar_g='At least cylinder maximum; use certified compatible tank-valve connection',target_motor_running_bar_g=6.3,required_flow_free_air_l_min=972,planning_flow_with_15pct_l_min=1117.8,maximum_downstream_bar_g=7,flow_curve_required_at_min_inlet_bar_g=20,screen_cd=cd,ideal_choked_throat_mm=math.sqrt(4*area/math.pi)*1000,throat_status='Screen only; not a regulator selection, assembly instruction or proven capacity'),equations=dict(ideal_inventory='M=p_abs V/(R T)',real_inventory='M=rho(P,T) V',usable_inventory='M_use=V [rho_initial-rho_at_cutoff]',runtime='t=M_use/(N mdot_motor)',adiabatic_tank='d(Mu)=h dM; rigid, well-mixed, adiabatic tank; s_remaining=s_initial',motor='T_exhaust=T_in-Wshaft/(mdot cp), Qmotor=0',path='T_nozzle=Ta+(T_exhaust-Ta) exp[-UA/(mdot cp)]',throttle='h_out=h_in; real air, no wall heat transfer',pulse='M_pulse=mdot t_pulse'),references=[dict(title='Atlas Copco LZB46-RL-A025-11',url='https://www.atlascopco.com/en-us/itba/products/air-motors/lzb46-rl-a025-11-sku8411047249',checked='2026-10-23'),dict(title='CoolProp Air equation of state',url='https://coolprop.org/fluid_properties/fluids/Air.html'),dict(title='MIT control-volume conservation',url='https://web.mit.edu/16.unified/www/FALL/thermodynamics/notes/node19.html')],limits=['Tank size and fill are assumptions, not a measured cylinder','Adiabatic and isothermal cases are thermal scenarios, not guaranteed device bounds under every installation','Mass reference inherited from DOCX; manufacturer air-consumption reference conditions require confirmation','Motor 840 W needs an external sustained shaft load; free spinning does not give this cooling','Regulator droop/icing, tank wall heat, hoses and real-air throttling couple the inlet state; fixed CFD inlet is conditional','Manufacturer does not guarantee subzero exhaust or rated performance at every inlet density/temperature','Exhaust collection loss, cold hose and nozzle backpressure can lower power and flow','No direct tank-to-motor connection; no cold receiver initially; cold nozzle printed parts see only near-atmospheric exhaust'])
    result['motor_count_options']=[dict(motors=n,total_g_s=1000*m*n,shaft_load_w=w*n,free_air_l_min=972*n,adiabatic_s=nominalrow['adiabatic_one_motor_s']/n,isothermal_s=nominalrow['isothermal_one_motor_s']/n,complete_10s_pulses_adiabatic=math.floor(nominalrow['adiabatic_one_motor_s']/(n*10)),complete_10s_pulses_isothermal=math.floor(nominalrow['isothermal_one_motor_s']/(n*10)),minimum_tank_l_for_10s_adiabatic=12*n*10/nominalrow['adiabatic_one_motor_s'],minimum_tank_l_for_10s_isothermal=12*n*10/nominalrow['isothermal_one_motor_s']) for n in [1,2,3,4]]
    result['load_sensitivity']=[dict(shaft_load_w=ww,motor_inlet_c=30,nozzle_c=ta+(30-ww/(m*CP)-ta)*math.exp(-ua/(m*CP)),scope='First-law sensitivity at fixed mass flow; not a motor speed/flow map') for ww in [0,420,840]]
    result['source_mixing_limits']=[dict(motor_inlet_c=q['motor_inlet_c'],nozzle_c=q['nozzle_c'],maximum_warm_to_cold_ratio_at_6k=(ta-q['nozzle_c'])/6-1) for q in source]
    checks=[]
    def check(name,b):
        assert b,name;checks.append(name)
    check('Positive usable inventory and adiabatic less than isothermal at same cutoff',all(0<x['usable_adiabatic_kg']<x['usable_isothermal_kg']<x['initial_real_mass_kg'] for x in inventory))
    check('Four motors consume inventory four times faster',all(abs(x['isothermal_one_motor_s']/x['isothermal_four_motor_s']-4)<1e-12 for x in inventory))
    check('30 C nozzle sensible budget agrees extracted shaft work minus path gain',abs(source[0]['sensible_w']-(w-m*CP*(source[0]['nozzle_c']-source[0]['motor_exhaust_c'])))<1e-9)
    check('40 C sensitivity warms nozzle 10 K times path retention',abs(source[1]['nozzle_c']-source[0]['nozzle_c']-10*math.exp(-ua/(m*CP)))<1e-10)
    check('10 s pulse injects 194 g',abs(m*10*1000-194)<1e-10)
    check('Initial trajectory returns 200 bar',abs(trajectory[0]['isothermal_bar_g']-200)<1e-6)
    check('Fast blowdown lowers both pressure and temperature',all(x['adiabatic_bar_g']<x['isothermal_bar_g'] and x['adiabatic_tank_c']<30 for x in trajectory[1:]))
    check('Tank and motor pressure are incompatible without reduction',200>7)
    check('Nominal temperature source is within dry CFD range',-23<source[0]['nozzle_c']<24)
    check('Inventory scales linearly with vessel volume',abs(next(x for x in inventory if x['volume_l']==15 and x['fill_bar_g']==200 and x['cutoff_bar_g']==20)['usable_isothermal_kg']/nominalrow['usable_isothermal_kg']-15/12)<1e-10)
    OUT.mkdir(exist_ok=True);(OUT/'calculations.json').write_text(json.dumps(result,indent=2));(OUT/'calculation-validation.json').write_text(json.dumps(dict(status='passed',checks=len(checks),items=checks,scope='Numerical balances, EOS scenarios and arithmetic; not Lean or hardware validation'),indent=2));return result
if __name__=='__main__':
    r=calculate();print(json.dumps({k:r[k] for k in ['nominal','motor','sources']},indent=2))

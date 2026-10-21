"""Execute declared stages. Uses coupled source work/flow and fixed-UA heat path."""
import sys,math,json,subprocess
import seat_cfd as s
if sys.argv[1]=='front10' and not (s.CFD/'cases/C20_three_motor_profile').exists():
 subprocess.run([sys.executable,__file__,'profile3'],check=True)
if sys.argv[1]=='front10' and not (s.CFD/'cases/C21_profile_halfCo_continuation').exists():
 subprocess.run([sys.executable,str(s.CFD/'scripts/continue_case.py'),'C20_three_motor_profile','C21_profile_halfCo_continuation','25','.5'],check=True)
if sys.argv[1]=='rear' and not (s.CFD/'cases/C22_four_motor_profile').exists():
 subprocess.run([sys.executable,__file__,'profile4'],check=True)
if sys.argv[1]=='side10' and not (s.CFD/'cases/C23_four_motor_panel500').exists():
 subprocess.run([sys.executable,__file__,'panel500'],check=True)
stages={
 'panel500':('C23_four_motor_panel500',4,.075,0,'front',None),
 'profile4':('C22_four_motor_profile',4,.075,0,'front',None),
 'profile3':('C20_three_motor_profile',3,.075,0,'front',None),
 'ambient35':('C19_four_motor_ambient35',4,.075,0,'front',None),
 'rear':('C10_rear_final',4,.075,0,'front',None),
 'normal3':('C12_three_motor_final',3,.075,0,'front',None),
 'fine3':('C13_three_motor_fine',3,.05,0,'front',None),
 'front05':('C14_four_motor_front05',4,.075,.5,'front',None),
 'front10':('C15_four_motor_front10',4,.075,1,'front',None),
 'side05':('C16_four_motor_side05',4,.075,.5,'side',None),
 'side10':('C17_four_motor_side10',4,.075,1,'side',None),
 'warm':('C18_four_motor_warm8',4,.075,0,'front',8),
}
name,n,h,wind,direction,warm=stages[sys.argv[1]];s.MASS=.0194*n
source=30+(-3.0407247238220165-30)*math.exp(-10.073720659304923/(s.MASS*1006)) if warm is None else warm
ambient=35 if sys.argv[1]=='ambient35' else 30
if ambient==35: source=35+(-3.0407247238220165-35)*math.exp(-10.073720659304923/(s.MASS*1006))
c=s.build(name,'back' if sys.argv[1]=='rear' else 'side',h,20,wind=wind,direction=direction,source_c=source,ambient_c=ambient,panel_heat=500 if sys.argv[1]=='panel500' else 0)
info=json.loads((c/'case.json').read_text());info.update(active_motors=n,shaft_power_w=n*840,free_air_m3_min=n*.972,duct_UA_w_k=10.073720659304923,source_temperature_status='Fixed-UA loaded-motor calculation' if warm is None else '8 C thermal stress state; requires heat-pickup allowance, not an independent efficiency gain')
(c/'case.json').write_text(json.dumps(info,indent=2))
if sys.argv[1] in ['profile3','profile4','panel500','front10','side05','side10']:
 from profile_transfer import apply
 apply(c)
s.run(c)

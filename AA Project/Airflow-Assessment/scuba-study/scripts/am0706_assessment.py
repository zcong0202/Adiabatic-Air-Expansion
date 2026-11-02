"""AM0706 conditional energy/inventory screen. No new CFD or hardware validation."""
from pathlib import Path
import json
STUDY=Path(__file__).resolve().parents[1]
def build():
    cp=1006.0
    power=3.6*745.6998715822702
    mass=3700/1000/60*1.2
    prior=json.loads((STUDY/'results/am0701-assessment.json').read_text())
    tank=json.loads((STUDY/'results/calculations.json').read_text())['nominal']
    ideal=power/(mass*cp)
    net=0.75*ideal
    seconds={k:tank['usable_'+k+'_kg']/mass for k in ('adiabatic','isothermal')}
    assert abs(mass-0.074)<1e-12
    assert 36<ideal<37 and 27<net<28
    assert abs(power/prior['manufacturer_specs']['power_max_w']-4)<1e-12
    result={
      'model':'Cosmostar AM0706','assessed_on':'2026-11-02',
      'manufacturer_url':'https://www.cosmostar.net/product/air-motor-and-agitator/264-am0706-air-operated-agitator',
      'manufacturer_specs':{'max_power_hp':3.6,'max_power_w':power,'pressure_range_bar_as_published':[1,7],'max_torque_nm':13,'max_speed_rpm':3000,'max_air_consumption_l_min':3700,'consumption_reference_conditions':'Not specified on reviewed manufacturer page','weight_kg':3.33},
      'assumptions':['3700 L/min means free air at reference density 1.2 kg/m3','Maximum power and air consumption occur together','Steady motor state and negligible kinetic/potential energy change','25% shaft-power heat return is a sensitivity, not a measurement','22 C is motor inlet, not necessarily scuba tank-to-regulator outlet'],
      'conditional_results':{'mass_flow_g_s':mass*1000,'motor_drop_no_heat_k':ideal,'motor_drop_heat25_k':net,'motor_exhaust_if_inlet22_heat25_c':22-net,'mass_per_10s_g':mass*10000,'mass_ratio_to_am0701':mass/prior['conditional_assumptions']['mass_flow_kg_s'],'shaft_power_ratio_to_am0701':4,'inventory_only_runtime_s':seconds,'tank_reference':'Existing 12 L / 200 bar gauge / 30 C initial tank, 20 bar gauge cutoff; adiabatic and isothermal scenarios. Not qualified full-flow runtime.','complete_10s_pulses':{k:int(v//10) for k,v in seconds.items()}},
      'limitations':['No paired loaded power/RPM/flow curve','Free-air basis unconfirmed','Higher full-flow regulator/hoses capacity unqualified','Exhaust capture, thread sizes, lubrication, low-temperature and exhaust-backpressure limits unconfirmed','Continuous shaft load up to about 2.7 kW required to reach the screened power','No new nozzle source boundary or CFD validation; do not reuse 77 g/s study as this motor result'],
      'listing_conflict':'Amazon bullets say 6.3 N m while title/manufacturer imply 13 N m. Use official model data; confirm exact supplied variant.',
      'procurement':{'amazon_url':'https://www.amazon.com/dp/B08L93K9NV','amazon_usd':380,'seller':'Cosmostar Tech Ltd','ships_from':'Amazon','displayed_stock':8,'displayed_destination':'Oakland 94621','regular_delivery':'2026-11-07','prime_delivery':'2026-11-04','sf_checkout_confirmed':False,'manufacturer_shop_url':'https://cosmostar.store/products/cosmostar-am0706-3-6-hp-vane-type-air-motor','manufacturer_shop_usd':339,'shop_add_to_cart_enabled':True,'shop_delivery_display':'Nov 5–9; checkout/destination not verified'},
      'decision':'Credible higher-mass-flow POC candidate if rated supply and continuous shaft load can support it. AM0701 remains simpler for first instrumented bench demonstration. No guaranteed >6 K at 20–50 cm.'}
    inlet_check=STUDY/'results/am0706-inlet-check.json'
    if inlet_check.exists():
        result['connection_and_variant_audit']=json.loads(inlet_check.read_text())
        result['decision']='Hold purchase/connection selection pending resolution of 1.7 versus 3.6 HP listing conflict and exact inlet/exhaust drawing. Earlier numerical screen remains conditional, not supplied-hardware validation.'
    (STUDY/'results/am0706-assessment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['conditional_results']))
if __name__=='__main__':build()

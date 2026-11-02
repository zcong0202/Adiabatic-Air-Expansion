"""Retailer-only screen for exact 2AM-NCC-96; not a manufacturer-qualified point."""
from pathlib import Path
import json
STUDY=Path(__file__).resolve().parents[1]
def build():
    mass=30*0.028316846592/60*1.2
    power=0.75*745.6998715822702
    drop=power/(mass*1006)
    assert 16.9<mass*1000<17.1 and 32<drop<33
    result={
      'assessed_on':'2026-11-02','model':'Gast 2AM-NCC-96','url':'https://www.amazon.com/dp/B093T2XX67',
      'retailer_claims':{'power_hp':0.75,'power_w':power,'max_air_flow_cfm':30,'max_rpm':3000,'max_pressure_psi':100,'port_size':'1/4 NPT','shaft_diameter':'1/2 inch','mounting':'hub','rotation':'CCW','included':'muffler','running_torque_at_max_pressure_in_lb':19.5},
      'primary_verification':'Exact model not found in current Gast site search. Existing manufacturer STD113 K sheet covers 2AM-NCC-16, 2AM-NCW-7A and 2AM-NCC-78, not -96. No curve transfer assumed.',
      'conflict':'Previously observed Zoro title says 0.95 HP, feature says 0.75 HP. Current Amazon says 0.75 HP. Exact nameplate/datasheet remains required.',
      'conditional_screen':{'mass_flow_g_s':mass*1000,'power_w':power,'motor_drop_no_heat_k':drop,'motor_drop_heat25_k':0.75*drop,'motor_exhaust_if_motor_inlet22_heat25_c':22-0.75*drop,'assumptions':['30 CFM is free-air flow at assumed 1.2 kg/m3','0.75 HP and 30 CFM occur together','Steady state, negligible kinetic/potential energy change','25% shaft-power heat return is an unmeasured sensitivity','Motor inlet is 22 C; hose pickup and ambient mixing excluded']},
      'purchase_evidence':{'price_usd':299.31,'stock_display':'In Stock','shipper_seller':'Megamart USA','destination_display':'Oakland 94621','delivery_display':'2026-11-05','exact_sf_delivery_confirmed':False},
      'open':['Exact -96 manufacturer loaded power/flow map','Flow reference state','Lubrication and oil carryover','Exhaust collection and allowed backpressure','Actual pressure and cold-temperature operating limits'],
      'decision':'Plausible small POC motor; unqualified pending exact primary data. Retain exclusion from qualified numerical ranking. No demonstrated advantage over AM0701 or matched 20–50 cm CFD.',
      'validation':'Numeric conversion/algebra checks only. No new CFD, Lean proof or measurement.'}
    (STUDY/'results/gast96-assessment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['conditional_screen']))
if __name__=='__main__':build()

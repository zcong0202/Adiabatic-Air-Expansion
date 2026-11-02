"""Conditional AM0701 screen. No measured motor map or new CFD."""
from pathlib import Path
import json, math
STUDY=Path(__file__).resolve().parents[1]
def build():
    hp_w=745.6998715822702
    cp=1006.0
    power=0.9*hp_w
    # Free-air basis and coincident power/flow are assumptions, not vendor confirmation.
    mdot=750/1000/60*1.2
    ideal_drop=power/(mdot*cp)
    rows=[]
    for heat_fraction in (0.0,0.25):
        drop=(1-heat_fraction)*ideal_drop
        motor_c=22-drop
        for ua in (1.0,10.0737206593):
            nozzle_c=30+(motor_c-30)*math.exp(-ua/(mdot*cp))
            rows.append(dict(heat_into_fraction_of_shaft=heat_fraction,motor_drop_k=drop,motor_exhaust_c=motor_c,assumed_path_ua_w_k=ua,nozzle_c=nozzle_c,required_cold_origin_fraction_for_6k=6/(30-nozzle_c)))
    assert abs(mdot-0.015)<1e-12
    assert 44<ideal_drop<45
    assert all(22-r['motor_exhaust_c']>0 and r['motor_exhaust_c']<r['nozzle_c']<30 for r in rows)
    result={
      'model':'Cosmostar AM0701','assessed_on':'2026-11-02',
      'verdict':'Credible standalone motor for instrumented bench POC. Outdoor target and direct exhaust/nozzle compatibility unqualified.',
      'manufacturer_url':'https://www.cosmostar.net/product/air-motor-and-agitator/255-am0701-0-9-hp-air-operated-vane-type-air-motor',
      'manufacturer_specs':{'power_max_hp':0.9,'power_max_w':power,'pressure_range_bar_as_published':[1,7],'rotation_max_rpm':3000,'torque_max_nm':3,'air_consumption_max_l_min':750,'consumption_condition':'6 bar, 3000 RPM','mass_kg':2.61},
      'missing':['Free-air/standard versus compressed-volume basis for 750 L/min','Paired loaded shaft power, RPM and flow curve','Pressure gauge/absolute basis confirmation','Inlet and exhaust thread/dimensions and collected-exhaust routing','Lubrication/oil carryover requirements','Permitted exhaust backpressure and low-temperature/icing limits'],
      'listing_conflict':'Amazon bullets say 1.2 N m and 1100 RPM; manufacturer and title say 3 N m and 3000 RPM. Separate maxima cannot be multiplied into a rated point.',
      'conditional_assumptions':{'all_max_power_and_flow_simultaneous':True,'flow_is_free_air':True,'reference_air_density_kg_m3':1.2,'mass_flow_kg_s':mdot,'cp_j_kg_k':cp,'motor_inlet_c':22,'ambient_c':30,'steady_state':True,'negligible_kinetic_potential_energy_change':True,'heat_fraction_025':'Sensitivity only, not measured','path_ua':'Both sensitivities unmeasured'},
      'formula':'motor drop = (shaft power - heat entering motor)/(mass flow * cp)',
      'sensitivities':rows,
      'procurement':{'amazon_url':'https://www.amazon.com/dp/B08L6BXZBT','amazon_usd':295,'amazon_seller':'Cosmostar Tech Ltd','amazon_fulfilment':'Amazon','amazon_stock_display':8,'amazon_display_destination':'Oakland 94621, not exact SF address','amazon_regular_delivery_display':'2026-11-07','amazon_prime_delivery_display':'2026-11-03','exact_sf_delivery_confirmed':False,'manufacturer_store_url':'https://cosmostar.store/products/cosmostar-am0701-0-9-hp-vanetype-air-motor','store_usd':259,'store_evidence':'Enabled Add to cart and product structured data InStock; full page text also contains Sold out (likely hidden template). Checkout not tested.','store_delivery_display':'Nov 05–09; destination-specific date not verified'},
      'validation':'Numeric conversion and algebra checks only. No new CFD, Lean proof or hardware measurement.'}
    (STUDY/'results/am0701-assessment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'mass_flow_g_s':mdot*1000,'conditional_power_w':power,'zero_heat_drop_k':ideal_drop,'heat25_drop_k':ideal_drop*0.75,'motor_exhaust22_heat25_c':22-ideal_drop*0.75}))
if __name__=='__main__':build()

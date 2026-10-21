(()=>{
 const checks={},near=(x,y)=>Math.abs(x-y)<1e-8;
 aaFormal.preset('current');const base=aaFormal.snapshot();
 let a=aaFormal.evaluate(base);
 checks.saved_area_fraction_identity=near(a.drop,9.124496133349068);
 checks.area_and_uniform_models_are_separate=near(a.uniformDrop,5.612903225806452);
 a=aaFormal.evaluate({...base,ua:.2});
 checks.line_heat_sensitivity=near(a.drop,8.26029409911415);
 checks.required_warm_load_mass=near(a.minMass,2.414771308519725);
 checks.heat_budget_bound=near(a.maxUA,.8425984530101294);
 a=aaFormal.evaluate({...base,alpha:.15});
 checks.energy_pass_can_coexist_with_area_fail=a.drop<6&&a.captured>a.energyRequired;
 checks.flow_alone_at_fixed_alpha_no_loss=near(aaFormal.evaluate({...base,manualMass:4,demand:400}).drop,aaFormal.evaluate(base).drop);
 checks.hot_entrainment_can_fail=aaFormal.evaluate({...base,warm:40,ua:.2}).drop<6;
 checks.ideal_regulator_cannot_make_cold_air=near(aaFormal.evaluate({...base,mode:'ideal_throttle'}).drop,0);
 a=aaFormal.evaluate({...base,mode:'real_throttle'});
 checks.low_pressure_real_regulator_insufficient=near(a.src.tc,32.304716005029434)&&a.drop<6;
 aaFormal.preset('bauer');a=aaFormalLast.result;
 checks.bauer_full_duty_fails=!a.supplyPass&&a.dutyMax===.5;
 checks.source_controls_disable_irrelevant_mass=document.getElementById('afMass').disabled;
 checks.bauer_half_duty_passes=aaFormal.evaluate({...aaFormal.snapshot(),duty:.5}).supplyPass;
 aaFormal.preset('bank');a=aaFormalLast.result;
 checks.bank_scales_source_not_assumed_dilution=near(a.src.mass,10.034319303121796)&&near(a.drop,9.124496133349068);
 aaFormal.preset('hpExp');a=aaFormalLast.result;
 checks.hp_dry_expander_state=near(a.src.tc,-124.40368247298721)&&a.src.stages===4;
 const mismatch=aaFormal.evaluate({...aaFormal.snapshot(),provider:'lp'});
 checks.pressure_mismatch_reported=mismatch.src.warnings.some(w=>w.includes('exceeds the selected supply envelope'));
 let invalid=false;try{aaFormal.evaluate({...base,warm:30});}catch(e){invalid=true;}
 checks.invalid_entrainment_rejected=invalid;
 aaFormal.preset('current');const field=document.getElementById('afUA');field.value='.2';field.dispatchEvent(new Event('input',{bubbles:true}));
 checks.input_event_updates_results=near(aaFormalLast.result.drop,8.26029409911415);
 checks.single_overview_section=document.querySelectorAll('#formal-model').length===1;
 const observed={heat:aaFormalLast.result,current:aaFormal.evaluate(base)};
 aaFormal.preset('current');
 return JSON.stringify({checks,count:Object.keys(checks).length,passed:Object.values(checks).every(Boolean),observed,scope:'Browser floating-point and UI checks, not Lean proofs or hardware validation'},null,2);
})()

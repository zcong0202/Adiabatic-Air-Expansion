(async()=>{
const checks=[];const check=(name,value)=>{checks.push({name,pass:!!value});if(!value)throw Error(name)};
check('Formula tab selected',AA_DashboardUI.selected()==='evidence');
check('Six formula cards',document.querySelectorAll('.formula-card').length===6);
check('Presentation notes downloadable',document.querySelector('#formulas a[download]').getAttribute('href')==='formulas/first-principles.txt');
check('Assumptions collapsed',Array.from(document.querySelectorAll('#formulas details')).every(x=>!x.open));
check('Physics distinction stated',document.querySelector('#formulas').textContent.includes('Open-jet warming is mainly ambient mixing'));
check('Hypothetical lifetime labelled',document.querySelector('#formulas').textContent.includes('This is not a measured or CFD lifetime'));
check('No new proof claim',document.querySelector('#formulas').textContent.includes('No new Lean proof'));
check('MIT foundations linked',document.querySelectorAll('#formulas a[href^="https://web.mit.edu"]').length===2);
for(const tab of ['cfd','components','nozzles','evidence']){AA_DashboardUI.show(tab);check(tab+' navigation',AA_DashboardUI.selected()===tab);check(tab+' formula visibility',document.querySelector('#formulas').hidden===(tab!=='evidence'));}
check('No branding',!document.querySelector('h1')&&!document.body.textContent.includes('AA Cooling Lab'));
check('No horizontal overflow',document.documentElement.scrollWidth<=innerWidth);
window.scrollTo(0,0);return {status:'passed',viewport:{width:innerWidth,height:innerHeight},checks:checks.length,items:checks,scope:'Formula UI and navigation; no new CFD or hardware validation'};
})()

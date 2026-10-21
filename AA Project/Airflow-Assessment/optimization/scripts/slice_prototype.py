"""Use installed Bambu Studio and its actual H2S / Generic PLA presets."""
import json, subprocess, shutil, zipfile
from pathlib import Path
from round_jet import OPT
preset=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
dest=OPT/'deliverables/C24-3deg-print-prototype'
evidence=OPT/'evidence/print-slice';evidence.mkdir(parents=True,exist_ok=True)
index={f.stem:f for f in preset.rglob('*.json')}
def resolve(name,stack=()):
 assert name not in stack, 'Preset inheritance cycle'
 raw=json.loads(index[name].read_text());result={}
 if raw.get('inherits'):result.update(resolve(raw['inherits'],stack+(name,)))
 for included in raw.get('include',[]):result.update(resolve(included,stack+(name,)))
 result.update(raw)
 result.pop('inherits',None);result.pop('include',None)
 return result
machine=resolve('Bambu Lab H2S 0.4 nozzle')
filament=resolve('Generic PLA @BBL H2S')
process=resolve('0.20mm Standard @BBL H2S')
assert len(machine['machine_start_gcode'])>1000 and float(filament['filament_density'][0])>1
mp=evidence/'H2S-resolved-machine.json';mp.write_text(json.dumps(machine,indent=2))
fp=evidence/'H2S-resolved-PLA.json';fp.write_text(json.dumps(filament,indent=2))
process.update(name='AA diffuser 0.20mm H2S',wall_loops='5',enable_support='0',brim_type='outer_only',brim_width='5',brim_object_gap='0.1')
settings=evidence/'AA-process.json';settings.write_text(json.dumps(process,indent=2))
command=['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio',
 '--debug','2','--load-settings',str(mp)+';'+str(settings),
 '--load-filaments',str(fp),
 '--orient','0','--arrange','1','--slice','0','--export-3mf','AA_C24_H2S_PLA_0p4_sliced.3mf',
 '--outputdir',str(evidence),'--export-settings',str(evidence/'resolved-settings.json'),
 str(dest/'AA_C24_3deg_PRINT_mm.stl')]
(evidence/'command.json').write_text(json.dumps(command,indent=2))
with (evidence/'bambu-slice.log').open('w') as log:
 result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=180)
print('Bambu slice exit:',result.returncode)
print((evidence/'bambu-slice.log').read_text()[-6500:])
if result.returncode==0:
 exported=evidence/'AA_C24_H2S_PLA_0p4_sliced.3mf'
 with zipfile.ZipFile(exported) as z:
  assert z.testzip() is None
  gcodes=[n for n in z.namelist() if n.endswith('.gcode')]
  assert gcodes,'No sliced G-code in export; do not label it sliced.'
  gcode=z.read(gcodes[0]).decode()
  summary_keys=['; total layer','; total filament','; model printing time','; max_z_height:','; layer_height =','; nozzle_diameter =','; wall_loops =','; brim_type =','; enable_support =','; curr_bed_type =']
  comments=[line for line in gcode.splitlines() if any(line.startswith(key) for key in summary_keys)]
  assert 'filament_density: 0' not in gcode and ';===== machine: H2S' in gcode
  report={'slice_succeeded':True,'application':'BambuStudio 02.08.02.61','printer':'Bambu Lab H2S 0.4 nozzle','filament_profile':'Generic PLA @BBL H2S (actual PLA not yet identified)','process':'0.20mm Standard @BBL H2S with 5 walls, no supports, 5 mm outer brim','presets_fully_resolved':True,'bed_type':'Cool Plate (default; select your actual plate and re-slice)','gcode_files':gcodes,'physically_printed':False,'source_fit_verified':False,'printer_toolpath_verified':False,'cli_diagnostic':'Invalid T command (T65535). This exact tool command is present in the unchanged installed H2S machine_end_gcode AMS unload template. CLI exit 0 and result.json Success; no plate warning. GUI re-slice required for actual filament and plate.','summary_comments':comments}
 shutil.copy2(exported,dest/exported.name)
 (dest/'slice-verification.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2))
raise SystemExit(result.returncode)

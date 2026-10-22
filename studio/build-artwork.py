import re,xml.etree.ElementTree as E,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'figures/fig1-air-cycle-seat.html').read_text()
svg=max(re.findall(r'<svg\b.*?</svg>',source,re.S),key=len)
root=E.fromstring(svg);E.register_namespace('','http://www.w3.org/2000/svg')
for parent in root.iter():
 for el in list(parent):
  name=el.get('data-name','');part=el.get('data-part','')
  if name.startswith(('chair.','therm.','hanger.','post','diffuser','duct.flange')) or (name.startswith('duct:') and int(name.split(':')[1])>=5) or part in ['cold','needle']:
   parent.remove(el);continue
  if name:
   if name.startswith(('comp.','cooler','p.cooler','cable.power','socket')):group='source'
   elif name.startswith('tank.'):group='tank'
   elif name.startswith(('p.tank','p.feed')):group='pipes'
   elif name.startswith(('motor','shaft','coupling','gen','manifold','reg.','load.','busbar','cable')):group='expansion'
   elif name.startswith('duct:'):group='pipes'
   else:continue
   el.set('data-part-edit',group)
root.set('viewBox','0 0 820 400');root.set('aria-label','Outdoor cooling system illustration: compressor, receiver, loaded air motors and nozzles. Click a component to edit.');root.set('role','group')
# Empty source artwork has no simulation labels or animation scripts.
s=E.tostring(root,encoding='unicode').replace(' xmlns="http://www.w3.org/2000/svg"','')
(ROOT/'studio/artwork.js').write_text('/* Adapted from the repository air-cycle seat artwork. See figures/src/ANATOMY-LICENSE. Seat and enclosure removed. Illustration only. */\nglobalThis.AA_ARTWORK = '+json.dumps(s)+';\n')
css=source[source.index('<style>')+7:source.index('</style>')];css=css[:css.index('*{box-sizing')]
(ROOT/'studio/diagram.css').write_text('/* Original anatomy drawing styles. Attribution: figures/src/ANATOMY-LICENSE. */\n'+css)

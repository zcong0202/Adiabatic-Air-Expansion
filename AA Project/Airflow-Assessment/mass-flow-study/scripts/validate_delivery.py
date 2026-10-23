"""Check delivered plots, native meshes, CAD links and local report references."""
import json,hashlib
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
from PIL import Image
from build import STUDY
OUT=STUDY/'results'
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        self.links.extend(v for k,v in attrs if k in ['href','src'] and v)
def main():
    names=json.loads((OUT/'campaign-status.json').read_text())['completed'];count=0
    for name in names:
        d=json.loads((OUT/(name+'.json')).read_text())
        frame_audit=json.loads((OUT/(name+'-timeline-audit.json')).read_text());assert frame_audit['file_sha256']==hashlib.sha256((OUT/(name+'-timeline.js')).read_bytes()).hexdigest();assert frame_audit['frames']==11 and frame_audit['times_s']==list(range(11));assert frame_audit['field_signature']==hashlib.sha256(json.dumps(d['field_sha256'],sort_keys=True).encode()).hexdigest()
        for suffix in ['-sections.png','-volume.png','-range-volume.png']:
            p=OUT/(name+suffix)
            with Image.open(p) as im:assert min(im.size)>400;im.verify()
            count+=1
        for suffix in ['-sections.js','-volume.js','-range-volume.js']:
            p=OUT/(name+suffix);v=json.loads(p.read_text().split('=',1)[1].rstrip(';'));assert v['case']==name
        for region,suffix in [('domain','-cold-air.glb'),('range20to50','-range-cold-air.glb')]:
            if d['final']['regions'][region]['6']['volume_m3']>0:assert (OUT/(name+suffix)).stat().st_size>0
        assert (STUDY/d['cad_assembly']['glb']).stat().st_size>0
    parser=Links();parser.feed((OUT/'index.html').read_text());checked=[]
    for link in parser.links:
        url=urlsplit(link)
        if url.scheme or not url.path:continue
        path=(OUT/unquote(url.path)).resolve();assert path.exists(),link;checked.append(link)
    files=['index.html','dashboard.css','viewer.js','catalogue.js','data.js','comparison.csv','calculations.json','validation.json','source-provenance.json','timeline-validation.json','nozzle-catalogue/catalogue.json','nozzle-catalogue/legacy-ranges.json']
    result=dict(cases=len(names),native_frames=len(names)*11,native_bundle_hashes_verified=len(names),verified_pngs=count,local_links_checked=checked,sha256={f:hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in files},status='passed',scope='Artifact integrity and links; physical and continuum accuracy not established')
    (OUT/'delivery-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()

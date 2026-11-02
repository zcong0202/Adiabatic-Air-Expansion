"""Concept of mechanical attachment; no fitted interface dimensions are claimed."""
from pathlib import Path
import json
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch

OUT=Path(__file__).resolve().parents[1]/'results'


def build():
    torque=671.1298844240432/(3000*math.pi/30)
    result=dict(status='Assembly concept; coupling bore and bracket not selected or qualified',
                source_urls=['https://www.amazon.com/dp/B0G4PH83D3',
                             'https://www.cosmostar.net/product/air-motor-and-agitator/255-am0701-0-9-hp-air-operated-vane-type-air-motor'],
                verified_listing_features=['MY1020 has mounting base and 11-tooth sprocket',
                                          'AM0701 manufacturer lists maximum 3 N m and 3000 rpm'],
                application='AM0701 generator-conversion candidate. Not a qualified full-power AM0706 load.',
                connection='Aligned shafts, two correctly bored coupling hubs and elastomer spider, common rigid base, guard',
                shaft_a_bore_mm=None,shaft_generator_bore_mm=None,
                unknown_interfaces=['Both actual shaft diameters and tolerances',
                                    'Straight usable engagement length',
                                    'Keyway, flat, thread and retention details',
                                    'MY1020 sprocket removal method and suitable coupling land',
                                    'AM0701 mounting flange/bracket dimensions'],
                coupling_requirements=['Continuous torque above motor maximum with manufacturer-selected service factor',
                                       'Allowed speed at least 3000 rpm and correct balance',
                                       'Hubs matched to actual shaft profiles and sufficient engagement',
                                       'Correct axial gap and angular/radial alignment per coupling instructions',
                                       'Complete guard and rigid supported mounting'],
                example_only=dict(shaft_w=671.1298844240432,rpm=3000,shaft_torque_nm=torque,
                                  note='Illustration only. Maximum power at 3000 rpm has not been established.'),
                electrical='MY1020 terminals to suitably protected/metered resistor load; verify permanent-magnet construction and generator voltage/current/thermal limits. Open circuit produces little sustained external load.',
                limitation='No coupling SKU selected. Do not force-fit bores or clamp a standard smooth-bore hub onto an unsuitable thread. A compatible hub/adapter or different transmission needs supplier approval.',
                deadline='Last exact-ZIP quote for this MY1020 was Prime Nov 5 to 94107, after required Nov 4. Fixture/coupling assembly is additional.',
                validation='Concept and torque conversion only. No physical fit or load qualification, new CFD or Lean proof.')
    assert 2.13<torque<2.15
    (OUT/'generator-attachment.json').write_text(json.dumps(result,indent=2)+'\n')
    fig,ax=plt.subplots(figsize=(14,5.8));fig.patch.set_facecolor('white')
    ax.set(xlim=(0,14),ylim=(0,5.8));ax.axis('off')
    ink='#172129';shaft='#b27720';air='#087e8b'
    ax.text(.35,5.35,'AM0701 → coupling → MY1020 generator candidate',fontsize=20,weight='bold',color=ink)
    ax.text(.35,4.9,'Concept only · both shaft profiles and mounting dimensions remain unverified',fontsize=11,color='#555')
    ax.add_patch(Rectangle((.65,.65),11.5,.2,facecolor='#c9d0d3',edgecolor=ink))
    ax.text(6.4,.32,'COMMON RIGID BASE · ALIGN SHAFT CENTRES BEFORE TIGHTENING',ha='center',fontsize=10,color=ink)
    for x in (1.35,2.75):ax.add_patch(Rectangle((x,.85),.25,1.05,facecolor='#e2e7e9',edgecolor=ink))
    ax.text(2.25,1.08,'Motor mount / bracket',ha='center',fontsize=9,color=ink)
    ax.add_patch(FancyBboxPatch((1.05,1.9),2.5,1.35,boxstyle='round,pad=.04',facecolor='#f1f4f5',edgecolor=ink,lw=1.6))
    ax.text(2.3,2.6,'AM0701\nAIR MOTOR',ha='center',va='center',fontsize=12,weight='bold',color=ink)
    ax.add_patch(Rectangle((3.55,2.49),.85,.18,facecolor=shaft,edgecolor=ink))
    ax.add_patch(Rectangle((4.25,2.22),.8,.72,facecolor='#edf1f3',edgecolor=ink,lw=1.4))
    ax.add_patch(Rectangle((5.05,2.27),.35,.62,facecolor=shaft,edgecolor=ink))
    ax.add_patch(Rectangle((5.4,2.22),.8,.72,facecolor='#edf1f3',edgecolor=ink,lw=1.4))
    ax.add_patch(Rectangle((6.2,2.49),.9,.18,facecolor=shaft,edgecolor=ink))
    ax.add_patch(FancyBboxPatch((3.95,1.96),2.55,1.25,boxstyle='round,pad=.04',facecolor='none',edgecolor='#777',linestyle='--',lw=1.5))
    ax.text(5.2,3.5,'GUARD',ha='center',fontsize=10,color='#555')
    ax.text(5.2,1.45,'Two hubs + flexible insert\nBore A and bore B: measure first',ha='center',fontsize=10,color=ink)
    ax.add_patch(FancyBboxPatch((7.1,1.9),2.8,1.35,boxstyle='round,pad=.04',facecolor='#f1f4f5',edgecolor=ink,lw=1.6))
    ax.text(8.5,2.6,'MY1020\nDC GENERATOR CANDIDATE',ha='center',va='center',fontsize=11,weight='bold',color=ink)
    for x in (7.35,9.2):ax.add_patch(Rectangle((x,.85),.25,1.05,facecolor='#e2e7e9',edgecolor=ink))
    ax.text(8.5,1.08,'Factory foot mounting',ha='center',fontsize=9,color=ink)
    ax.annotate('',xy=(11.0,2.6),xytext=(9.95,2.6),arrowprops=dict(arrowstyle='-|>',color=shaft,lw=2))
    ax.text(12.1,2.6,'Metering +\nprotected resistor\nload bank',ha='center',va='center',fontsize=11,color=shaft)
    ax.annotate('',xy=(1.7,3.35),xytext=(.65,4.12),arrowprops=dict(arrowstyle='-|>',color=air,lw=2))
    ax.text(.5,4.25,'Regulated air',fontsize=11,color=air)
    ax.annotate('',xy=(5.7,4.1),xytext=(3.0,3.35),arrowprops=dict(arrowstyle='-|>',color=air,lw=2))
    ax.text(5.8,4.15,'Collected motor exhaust → short hose → nozzle',fontsize=11,color=air)
    ax.text(.7,.02,'Shop must confirm shaft land after sprocket removal, hub retention, coupling rating, alignment, guard and generator/load thermal limits.',fontsize=9,color='#555')
    fig.tight_layout(pad=.3);fig.savefig(OUT/'generator-attachment.png',dpi=145)
    fig.savefig(OUT/'generator-attachment.svg',metadata={'Date':None});plt.close(fig)
    section='''<section id="generator-attachment"><h2>How MY1020 attaches</h2><img src="generator-attachment.svg" alt="Two independently mounted machines on a common rigid base, shafts aligned and joined by a guarded two-hub jaw coupling; generator wires connect to load bank"><ol><li>Mount AM0701 using a suitable bracket and MY1020 using its foot on a common rigid base. Support both machines independently.</li><li>If direct coupling is permitted, remove the MY1020 sprocket by its approved method. Verify that the exposed shaft has a suitable coupling land. Do not clamp an ordinary smooth-bore hub onto an unsuitable thread.</li><li>Select two coupling hubs: one for the actual AM0701 shaft, one for the actual MY1020 shaft, plus the matching flexible insert. Confirm diameter, engagement length, key/flat/thread and retention. Both bores remain unverified; no fitted coupling SKU is specified.</li><li>Align shaft centres and angles, set the specified hub gap, tighten per supplier instructions, and install a guard. Check continuous torque, service factor and speed rating. AM0701’s manufacturer maximum is 3 N m / 3000 rpm; 671 W at 3000 rpm would be 2.14 N m, an illustrative point.</li><li>Connect the generator output to a properly protected and metered resistor load. Verify the generator construction, loaded voltage/current and thermal limits. The electrical load creates opposing shaft torque; open circuit supplies little sustained external load.</li></ol><p>This remains a workshop assembly, not a ready-to-attach kit. It is an AM0701 candidate, not a qualified full-power AM0706 load. The last MY1020 delivery quote to 94107 was Prime 5 Nov, after the 4 Nov deadline. <a href="generator-attachment.json">Interface status</a> · <a href="generator-attachment.png">PNG</a> · <a href="generator-attachment.svg">SVG</a>.</p></section>'''
    (OUT/'generator-attachment-section.html').write_text(section)


if __name__=='__main__':build()

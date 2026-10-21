"""Separate cold-core displacement from air warming in completed native fields."""
import json,hashlib,math
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from open_flow import STUDY,CASES
from audit_seat import arr

def field(name):
    p=CASES/name;mesh=np.load(p/'mesh-metadata.npz');idx=mesh['indices'];axes=[(mesh[k][:-1]+mesh[k][1:])/2 for k in ['x','y','z']]
    g=np.full((len(axes[2]),len(axes[1]),len(axes[0])),np.nan);g[idx[:,2],idx[:,1],idx[:,0]]=arr(p/'5/T',len(idx))-273.15
    return RegularGridInterpolator((axes[2],axes[1],axes[0]),g,bounds_error=False,fill_value=np.nan)

def main():
    results=[];fig,ax=plt.subplots(figsize=(7.5,5),layout='constrained')
    for name,d in [('P00_one_d20',.2),('P01_one_d35',.35),('P02_one_d50',.5)]:
        f=field(name);z=np.linspace(.95,1.3,351);t=f(np.column_stack([z,np.full(len(z),-.2),np.full(len(z),-.2)]));i=np.argmin(t)
        row=dict(case=name,standoff_m=d,time_s=5,path_x_m=-.2,side_y_m=-.2,coldest_sampled_height_m=float(z[i]),coldest_point_c=float(t[i]),temperature_at_original_height_c=float(f([[1.15,-.2,-.2]])[0]),
                 downward_offset_m=float(1.15-z[i]),geometric_upward_aim_deg=math.degrees(math.atan2(1.15-z[i],d)),
                 native_temperature_sha256=hashlib.sha256((CASES/name/'5/T').read_bytes()).hexdigest())
        results.append(row);ax.plot(t,z,label=f'{d*100:g} cm; lowest point {t[i]:.1f}°C')
    ax.axhline(1.15,color='#667a85',ls='--',label='Original outlet/target height');ax.set(xlabel='Air temperature at fixed x=-0.2 m,y=-0.2 m (°C)',ylabel='Height z (m)',title='Cold air remains below the original target height');ax.grid(alpha=.2);ax.legend(fontsize=9)
    fig.supxlabel('5 s native CFD; point profiles, not 5 cm area means. Fine plotting interpolation does not add mesh resolution.',fontsize=8)
    fig.savefig(STUDY/'results/cold-core-height.png',dpi=160);plt.close(fig)
    source=json.loads((STUDY/'results/timing-and-energy.json').read_text())['source_budget']
    rho=101325/(287.05*(source['supply_c']+273.15));u=source['mass_kg_s']/(rho*.0448)
    acceleration=9.81*(30-source['supply_c'])/303.15
    scales=[dict(standoff_m=d,constant_speed_flight_s=d/u,ballistic_fall_m=.5*acceleration*(d/u)**2,
                 scale_upward_aim_deg=math.degrees(math.atan2(.5*acceleration*(d/u)**2,d))) for d in [.2,.35,.5]]
    (STUDY/'results/cold-core-diagnostic.json').write_text(json.dumps(dict(results=results,buoyancy_scales=scales,
      scale_caveat='Constant-density/constant-speed parcel scale, not a turbulent jet trajectory or independent validation. The aim test was motivated by the CFD diagnostic.',
      scope='Ideal-source air field without a person. Peak height quantized by coarse mesh; not a measured trajectory.'),indent=2))
    if (CASES/'A00_pitch8_d50/audit.json').exists():
        r,z=np.meshgrid(np.linspace(.005,.65,150),np.linspace(.9,1.4,130));fig,axes=plt.subplots(1,2,figsize=(11.5,4.8),layout='constrained')
        for ax,name,title in zip(axes,['P02_one_d50','A00_pitch8_d50'],['Horizontal prescribed flow','8° upward prescribed flow']):
            f=field(name);t=f(np.column_stack([z.ravel(),(-.7+r).ravel(),np.full(z.size,-.2)])).reshape(z.shape)
            im=ax.pcolormesh(r,z,t,vmin=1,vmax=30,cmap='coolwarm',shading='nearest');ax.axhline(1.15,color='#162f3b',ls='--');ax.axvline(.5,color='#162f3b',ls=':');ax.plot(.5,1.15,'s',mfc='none',mec='#101c24',ms=9)
            ax.set(xlabel='Distance from outlet along y (m)',ylabel='Height z (m)',title=title)
        fig.colorbar(im,ax=axes,fraction=.035,label='Air temperature (°C)');fig.suptitle('Retargeting the cold core / actual native CFD at 5 s',fontsize=15)
        fig.supxlabel('No body. Oblique velocity on vertical slot patch; not resolved tilted-CAD geometry. Actual source mass checked.',fontsize=9)
        fig.savefig(STUDY/'results/pitch-comparison.png',dpi=160);plt.close(fig)
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()

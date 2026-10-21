"""Continuous parametric surface preview of the supplied mount variants."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from milton_mount_reference import OUT,L,THREAD_LENGTH,BLEND_END,bore,outer_radius

fig=plt.figure(figsize=(11,6.5),layout='constrained')
theta=np.linspace(0,2*np.pi,121)
for i,length in enumerate([L,BLEND_END+2]):
 ax=fig.add_subplot(1,2,i+1,projection='3d')
 s=np.unique(np.r_[np.linspace(0,THREAD_LENGTH,200),np.linspace(THREAD_LENGTH+.05,length,90),[THREAD_LENGTH+.025,THREAD_LENGTH+.05,BLEND_END]])
 s=s[s<=length];ss,tt=np.meshgrid(s,theta,indexing='ij')
 rr=outer_radius(ss,tt,0);zz=length-ss
 ax.plot_surface(rr*np.cos(tt),rr*np.sin(tt),zz,color='#508b9f',rstride=1,cstride=1,linewidth=0,antialiased=True,shade=True)
 # Visible end rings and the actual open bore.
 for station in [0,length]:
  inner=float(bore(np.array(station)));outer=outer_radius(np.full_like(theta,station),theta,0)
  r=np.array([np.full_like(theta,inner),outer]);t=np.broadcast_to(theta,r.shape)
  ax.plot_surface(r*np.cos(t),r*np.sin(t),np.full_like(r,length-station),color='#2d5565',linewidth=0,shade=True)
  depth=1.5
  r0=inner
  zt=np.array([length-station,length-station-depth])
  ti,zi=np.meshgrid(theta,zt)
  ax.plot_surface(r0*np.cos(ti),r0*np.sin(ti),zi,color='#355c6c',linewidth=0,shade=True)
 ax.set(xlim=(-15,15),ylim=(-15,15),zlim=(0,length),title=('Full nozzle · 177.65 mm' if i==0 else f'Fit coupon · {length:.2f} mm'))
 ax.set_box_aspect([30,30,length]);ax.view_init(elev=24,azim=35);ax.set_axis_off()
fig.suptitle('Milton-style 3/8-18 NPT male mount\nCommercial tip fit user-confirmed · check printed tolerance with coupon',fontsize=16)
fig.text(.5,.04,'Nominal parametric view. Printable files also include −0.20 mm and −0.40 mm external-diameter variants.',ha='center',fontsize=10)
fig.savefig(OUT/'mount-and-coupon.png',dpi=160);plt.close(fig)
print(OUT/'mount-and-coupon.png')

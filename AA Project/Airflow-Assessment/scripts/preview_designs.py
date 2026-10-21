"""Inspect exported STL topology and render engineering concept views."""
import json
import textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1]
fig=plt.figure(figsize=(14,9),layout="constrained")
models={};checks={}
for idx,path in enumerate(sorted((ROOT/"designs").glob("*/wall.stl"))):
    mesh=trimesh.load_mesh(path,process=True)
    mesh.fix_normals(multibody=True)
    mesh.export(path)
    millimetres=mesh.copy();millimetres.apply_scale(1000);millimetres.export(path.parent/'wall-mm.stl')
    name=path.parent.name
    info=json.loads((path.parent/"design.json").read_text())
    vertices=np.asarray(mesh.vertices)*1000
    triangles=vertices[mesh.faces]
    checks[name]={"stl_watertight":bool(mesh.is_watertight),"winding_consistent":bool(mesh.is_winding_consistent),"triangles":len(mesh.faces),"solid_volume_mm3":abs(float(mesh.volume))*1e9,"bounds_mm":(mesh.bounds*1000).tolist(),"step_exists":(path.parent/"concept.step").exists()}
    models[name]={"label":info["label"],"vertices_mm":np.round(vertices,4).tolist(),"faces":mesh.faces.tolist(),"description":info["description"]}
    ax=fig.add_subplot(2,2,idx+1,projection="3d")
    # Show one longitudinal half to expose the actual generated flow passage.
    visible=triangles[triangles[:,:,1].mean(axis=1)>=-1e-7]
    col=Poly3DCollection(visible,facecolor="#78a8bf",edgecolor="#42708a",linewidth=.12,alpha=.95)
    ax.add_collection3d(col)
    ax.set_xlim(-42,34);ax.set_ylim(-19,19);ax.set_zlim(-19,19)
    ax.set_box_aspect((76,38,38));ax.view_init(elev=24,azim=-62)
    ax.set_xlabel("x (mm)");ax.set_ylabel("y (mm)");ax.set_zlabel("z (mm)")
    ax.set_title(f"{name[:2]}  {info['label']}\n"+textwrap.fill(info['description'],58),loc="left",fontsize=10,pad=10)
    ax.text2D(.02,.03,f"Core exit area: {info['exit_area_mm2']:.1f} mm²",transform=ax.transAxes,fontsize=10)
fig.suptitle("AA concepts · longitudinal half views\nProposed dimensions. Smooth connection passages; threads and shield supports omitted.",fontsize=15)
out=ROOT/"results/design-concepts.png";fig.savefig(out,dpi=170);plt.close(fig)
(ROOT/"results/design-viewer-data.json").write_text(json.dumps(models,separators=(",",":")))
(ROOT/"evidence/geometry-checks.json").write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))

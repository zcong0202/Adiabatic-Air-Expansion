"""Independent small checks for the source, geometry and native-field analysis."""
import unittest,math
import numpy as np,trimesh
from build import spec,geometry,PA,GAS,SOURCE_C
from extract import overlap,voxel_mesh
from patch import patch_metric
from range_metrics import clipped_surface,boxes

class MathChecks(unittest.TestCase):
    def test_all_flow_splits(self):
        for m in [2,27,52,77]:
            for n in [1,2,4]:
                s=spec(m,n);self.assertAlmostEqual(s['per_outlet_g_s']*n,m);self.assertEqual(len(geometry(s)),n)
    def test_equal_area_controls(self):
        a,b=spec(77,4,'base'),spec(77,4,'wide');self.assertAlmostEqual(a['width_m']*a['height_m'],b['width_m']*b['height_m']);self.assertAlmostEqual(a['exit_speed_m_s'],b['exit_speed_m_s']);self.assertNotEqual(a['hydraulic_reynolds'],b['hydraulic_reynolds'])
    def test_adaptive_area_preserves_speed(self):
        for m in [2,27,52,77]:
            for n in [1,2,4]:
                s=spec(m,n,'adaptive');rho=PA/(GAS*(SOURCE_C+273.15));self.assertAlmostEqual(s['exit_speed_m_s'],1.5);self.assertAlmostEqual(s['width_m']/s['height_m'],2);self.assertAlmostEqual(s['width_m']*s['height_m']*n*rho*1.5,m/1000)
    def test_counts_do_not_create_mass(self):
        a,b=spec(77,1),spec(77,4);self.assertAlmostEqual(a['exit_speed_m_s']/b['exit_speed_m_s'],4)
    def test_opposed_and_overhead_directions(self):
        a=geometry(spec(77,4,layout='opposed'));b=geometry(spec(77,4,layout='overhead'));self.assertEqual(sorted(n['direction'] for n in a),[2,2,3,3]);self.assertTrue(all(n['direction']==4 for n in b))
    def test_native_partial_overlap(self):
        mesh=dict(indices=np.array([[0,0,0]]),x=np.array([0,1]),y=np.array([0,1]),z=np.array([0,1]));self.assertAlmostEqual(overlap(mesh,[[.25,.75],[0,.5],[0,1]])[0],.25);self.assertEqual(overlap(mesh,[[2,3],[0,1],[0,1]])[0],0)
    def test_voxel_mesh_conserves_exact_cell_volume(self):
        mesh=dict(indices=np.array([[0,0,0],[1,0,0]]),x=np.array([0,.2,.5]),y=np.array([0,.3]),z=np.array([0,.4]))
        for mask,volume in [(np.array([True,False]),.2*.3*.4),(np.array([True,True]),.5*.3*.4)]:
            v,f=voxel_mesh(mesh,mask);m=trimesh.Trimesh(v,f,process=True);self.assertTrue(m.is_watertight);self.assertAlmostEqual(m.volume,volume)
    def test_range_clipping_preserves_partial_cell_volume(self):
        mesh=dict(indices=np.array([[0,0,0]]),x=np.array([0,1]),y=np.array([0,1]),z=np.array([0,1]));v,f=clipped_surface(mesh,np.array([True]),[[[.25,.75],[.25,.75],[.25,.75]]]);m=trimesh.Trimesh(v,f,process=True);self.assertTrue(m.is_watertight);self.assertAlmostEqual(m.volume,.125)
    def test_declared_range_band_denominators(self):
        for layout,volume in [('side',.336),('opposed',.672),('overhead',.192)]:
            actual=sum(np.prod([hi-lo for lo,hi in b]) for b in boxes({'layout':layout}));self.assertAlmostEqual(actual,volume)
    def test_uniform_patch_average(self):
        a=np.linspace(-.8,.8,161);b=np.linspace(1,1.7,71);s=dict(axis_a=a,axis_b=b,axes=['x','z'],values_c=np.full((70,160),10));r=patch_metric(s);self.assertAlmostEqual(r['best_sampled_5cm_mean_drop_k'],20)
    def test_tiny_cold_cell_does_not_count_as_cold_patch(self):
        a=np.linspace(-.8,.8,161);b=np.linspace(1,1.7,71);t=np.full((70,160),30.);t[34:36,79:81]=0;s=dict(axis_a=a,axis_b=b,axes=['x','z'],values_c=t);r=patch_metric(s);self.assertAlmostEqual(r['best_sampled_5cm_mean_drop_k'],4.8);self.assertLess(r['best_sampled_5cm_mean_drop_k'],6)
    def test_source_energy_upper_bound(self):
        q=.002*1006*(30-SOURCE_C);m=q*10/(1006*6);self.assertAlmostEqual(q,58.429938144329896);self.assertAlmostEqual(m,.02*(30-SOURCE_C)/6)

if __name__=='__main__':unittest.main()

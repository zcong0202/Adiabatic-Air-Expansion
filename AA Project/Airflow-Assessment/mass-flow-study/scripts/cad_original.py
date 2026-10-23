"""Isolated original analytic loft generation. Do not share OCC unit state across models."""
import sys
from build import ROOT,STUDY
sys.path.insert(0,str(ROOT/'pass-by-study/scripts'))
import make_cad
make_cad.STUDY=STUDY
original=make_cad.gmsh.initialize

def initialize(*args,**kwargs):
    original(*args,**kwargs);make_cad.gmsh.option.setNumber('General.NumThreads',1);make_cad.gmsh.option.setString('Geometry.OCCTargetUnit','')
make_cad.gmsh.initialize=initialize
if __name__=='__main__':make_cad.generate(float(sys.argv[1]),float(sys.argv[2]))

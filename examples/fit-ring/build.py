#!/usr/bin/env python3
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cadquery as cq
from common import output_dir, save_part, preview, summary, intersection

# Demonstration parameters in mm; clearance adds to the full diameter.
OUTER_D = 28.0
NOMINAL_D = 18.0
DIAMETER_OFFSETS = (-0.2, 0.0, 0.2)
HEIGHT = 4.0

def main():
    out = output_dir(); checks={}; parts=[]
    for i, delta in enumerate(DIAMETER_OFFSETS):
        inner=NOMINAL_D+delta
        assert 0 < inner < OUTER_D
        ring=cq.Workplane('XY').circle(OUTER_D/2).circle(inner/2).extrude(HEIGHT)
        name=f'ring_{i+1}'
        data=save_part(ring,name,out,[OUTER_D,OUTER_D,HEIGHT])
        probe=cq.Workplane('XY').circle(inner/2-0.01).extrude(HEIGHT)
        assert intersection(ring,probe) < 1e-7
        actual_diameter = 2 * math.sqrt(OUTER_D**2 / 4 - ring.val().Volume() / (math.pi * HEIGHT))
        assert abs(actual_diameter-inner) < 1e-6
        data.update(inner_diameter_mm=actual_diameter, diameter_offset_mm=delta, hole_probe_intersection_mm3=intersection(ring,probe))
        checks[name]=data; parts.append((out/(name+'.stl'),['#6fa8bd','#d8aa66','#8cb391'][i],(i*32,0,0)))
    preview(parts,out/'preview.png'); summary(out,checks)
if __name__=='__main__': main()

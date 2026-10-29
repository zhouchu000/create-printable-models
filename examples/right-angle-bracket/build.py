#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cadquery as cq
from common import output_dir, save_part, preview, summary, intersection

# Demonstration dimensions in mm.
LENGTH, WIDTH, BASE, HEIGHT, WALL = 50.0, 28.0, 4.0, 32.0, 4.0
HOLE_D, HOLE_X = 5.0, 15.0
RIB_THICKNESS, RIB_RUN = 4.0, 18.0

def main():
    out=output_dir()
    base=cq.Workplane('XY').box(LENGTH,WIDTH,BASE,centered=(True,True,False))
    wall=cq.Workplane('XY').box(WALL,WIDTH,HEIGHT,centered=(True,True,False)).translate((-LENGTH/2+WALL/2,0,0))
    # A Y-centred right triangle joining the base and vertical wall.
    x0=-LENGTH/2+WALL-0.5
    rib=(cq.Workplane('XZ').polyline([(x0,BASE-0.5),(x0+RIB_RUN,BASE-0.5),(x0,HEIGHT-3)]).close().extrude(RIB_THICKNESS/2,both=True))
    part=base.union(wall).union(rib)
    holes=[]
    for y in (-7,7):
        cutter=cq.Workplane('XY').center(HOLE_X,y).circle(HOLE_D/2).extrude(BASE+2).translate((0,0,-1))
        part=part.cut(cutter); holes.append(cutter)
    data=save_part(part,'bracket',out,[LENGTH,WIDTH,HEIGHT])
    volumes=[intersection(part,h) for h in holes]
    assert all(v < 1e-7 for v in volumes)
    data.update(hole_diameter_mm=HOLE_D, hole_probe_intersections_mm3=volumes)
    preview([(out/'bracket.stl','#80a8bd',(0,0,0))],out/'preview.png'); summary(out,{'bracket':data})
if __name__=='__main__': main()

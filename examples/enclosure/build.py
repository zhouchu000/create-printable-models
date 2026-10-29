#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cadquery as cq
from common import output_dir, save_part, preview, summary, intersection

# Demonstration dimensions in mm; clearance is per side.
LENGTH, WIDTH, BODY_H, WALL, BOTTOM = 64.0, 44.0, 26.0, 2.4, 2.4
TOP, SKIRT_DEPTH, SKIRT_WALL, CLEARANCE = 2.0, 4.0, 1.6, 0.25
SLOT_W, SLOT_DEPTH = 10.0, 7.0

def block(x,y,z,c):
    return cq.Workplane('XY').box(x,y,z).translate(c)

def main():
    out=output_dir(); il=LENGTH-2*WALL; iw=WIDTH-2*WALL
    outer=block(LENGTH,WIDTH,BODY_H,(0,0,BODY_H/2))
    cavity=block(il,iw,BODY_H,(0,0,BOTTOM+BODY_H/2))
    slot=block(SLOT_W,WALL+2,SLOT_DEPTH+1,(0,-WIDTH/2+WALL/2,BODY_H-SLOT_DEPTH/2+0.5))
    body=outer.cut(cavity).cut(slot)
    plate=block(LENGTH,WIDTH,TOP,(0,0,BODY_H+TOP/2))
    sl=il-2*CLEARANCE; sw=iw-2*CLEARANCE
    ring=block(sl,sw,SKIRT_DEPTH+0.2,(0,0,BODY_H-SKIRT_DEPTH/2+0.1)).cut(block(sl-2*SKIRT_WALL,sw-2*SKIRT_WALL,SKIRT_DEPTH+2,(0,0,BODY_H-SKIRT_DEPTH/2)))
    notch=block(SLOT_W,SKIRT_WALL+2,SKIRT_DEPTH+0.5,(0,-sw/2+SKIRT_WALL/2,BODY_H-SKIRT_DEPTH/2-0.25))
    lid=plate.union(ring.cut(notch))
    data={'body':save_part(body,'body',out,[LENGTH,WIDTH,BODY_H]),'lid':save_part(lid,'lid',out,[LENGTH,WIDTH,TOP+SKIRT_DEPTH], print_shape=lid.rotate((0,0,0),(1,0,0),180))}
    cq.Assembly().add(body,name='body').add(lid,name='lid').save(str(out/'assembly.step'))
    assembly=cq.importers.importStep(str(out/'assembly.step'))
    assert assembly.solids().size()==2
    placeholder=block(45,25,15,(0,0,12))
    corridor=block(SLOT_W,8,SLOT_DEPTH,(0,-WIDTH/2+4,BODY_H-SLOT_DEPTH/2))
    section=block(2,8,1,(15,-WIDTH/2+3, BODY_H-2))
    wall_bounds=body.val().intersect(section.val()).BoundingBox()
    skirt_bounds=lid.val().intersect(section.val()).BoundingBox()
    measured_clearance=skirt_bounds.ymin-wall_bounds.ymax
    assert abs(measured_clearance-CLEARANCE)<1e-6
    measurements={'assembly_intersection_mm3':intersection(body,lid),'placeholder_body_mm3':intersection(placeholder,body),'placeholder_lid_mm3':intersection(placeholder,lid),'channel_body_mm3':intersection(corridor,body),'channel_lid_mm3':intersection(corridor,lid),'clearance_per_side_mm':measured_clearance,'assembly_step_solids':assembly.solids().size()}
    assert all(abs(measurements[k])<1e-7 for k in ('assembly_intersection_mm3','placeholder_body_mm3','placeholder_lid_mm3','channel_body_mm3','channel_lid_mm3'))
    # Undo the print rotation and translation to show the lid in assembly coordinates.
    preview([(out/'body.stl','#88adc0',(0,0,0)),(out/'lid.stl','#dfbc83',(0,0,BODY_H+TOP),True)],out/'preview.png')
    data['assembly']=measurements; summary(out,data)
if __name__=='__main__': main()

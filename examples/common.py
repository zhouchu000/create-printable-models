"""Small shared helpers for the standalone CadQuery examples (millimetres)."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
import cadquery as cq
from cadquery import exporters, importers


def output_dir():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    path = parser.parse_args().output
    path.mkdir(parents=True, exist_ok=True)
    return path


def shape(w):
    return w.val() if isinstance(w, cq.Workplane) else w


def bounds(w):
    b = shape(w).BoundingBox()
    return [b.xlen, b.ylen, b.zlen]


def intersection(a, b):
    # Do not convert Boolean failures into an empty intersection.
    return shape(a).intersect(shape(b)).Volume()


def save_part(w, name, out, expected, print_shape=None):
    s = shape(w)
    assert s.isValid() and len(s.Solids()) == 1
    assert all(abs(a-b) < 1e-6 for a,b in zip(bounds(s), expected)), (name, bounds(s), expected)
    exporters.export(w, str(out / (name + '.step')))
    loaded = importers.importStep(str(out / (name + '.step'))).val()
    assert loaded.isValid() and len(loaded.Solids()) == 1
    assert all(abs(a-b) < 1e-5 for a,b in zip(bounds(loaded), expected))
    printed = shape(print_shape) if print_shape is not None else s
    bed = printed.translate((0, 0, -printed.BoundingBox().zmin))
    exporters.export(bed, str(out / (name + '.stl')), tolerance=0.01, angularTolerance=0.1)
    import trimesh
    mesh = trimesh.load_mesh(out / (name + '.stl'))
    zmin = float(mesh.bounds[0][2])
    assert abs(zmin) < 1e-6
    report_path = out / (name + '-mesh.json')
    inspector = Path(__file__).resolve().parents[1] / 'scripts' / 'inspect_stl.py'
    command = [sys.executable, str(inspector), str(out / (name + '.stl')),
               '--expect-size', *map(str, expected), '--expect-bodies', '1',
               '--on-bed', '--output', str(report_path)]
    checked = subprocess.run(command, capture_output=True, text=True)
    if checked.returncode:
        detail = report_path.read_text() if report_path.exists() else checked.stderr
        raise RuntimeError('Exported mesh check failed: ' + detail)
    report = json.loads(report_path.read_text())
    return {'step_solids': 1, 'size_mm': bounds(loaded), 'stl_zmin_mm': zmin,
            'mesh_status': report['status'], 'mesh_report': report_path.name}


def preview(parts, path):
    import numpy as np
    import trimesh
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(6,5)); ax = fig.add_subplot(111, projection='3d')
    all_bounds=[]
    for item in parts:
        file, color, offset = item[:3]
        m = trimesh.load_mesh(file)
        if len(item) > 3 and item[3]:
            m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
        m.apply_translation(offset)
        all_bounds.append(m.bounds)
        ax.add_collection3d(Poly3DCollection(m.triangles, facecolor=color, edgecolor='#405060', linewidth=0.03, alpha=0.9))
    lo=np.min([b[0] for b in all_bounds],axis=0); hi=np.max([b[1] for b in all_bounds],axis=0)
    center=(lo+hi)/2; span=max(hi-lo)*0.6
    ax.set(xlim=(center[0]-span,center[0]+span), ylim=(center[1]-span,center[1]+span), zlim=(center[2]-span,center[2]+span), xlabel='X mm', ylabel='Y mm', zlabel='Z mm')
    ax.set_box_aspect((1,1,1)); ax.view_init(25,-55)
    fig.savefig(path,dpi=120,bbox_inches='tight'); plt.close(fig)


def summary(out, data):
    (out / 'checks.json').write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')

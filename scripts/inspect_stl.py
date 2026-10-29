#!/usr/bin/env python3
"""Inspect an STL without altering its contents. Coordinates are interpreted as mm."""
import argparse
import json
import math
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model')
    parser.add_argument('--expect-size', nargs=3, type=float, metavar=('X', 'Y', 'Z'))
    parser.add_argument('--size-tol', type=float, default=0.1)
    parser.add_argument('--expect-bodies', type=int)
    parser.add_argument('--on-bed', action='store_true',
                        help='Require minimum Z within size-tol of zero for printing coordinates')
    parser.add_argument('--output')
    args = parser.parse_args()
    report = dict(status='error', bounds_mm=None, size_mm=None, body_count=None,
                  watertight=None, winding_consistent=None, signed_volume_mm3=None,
                  degenerate_faces=None, errors=[])
    code = 2
    try:
        if not math.isfinite(args.size_tol) or args.size_tol < 0:
            raise ValueError('size tolerance must be finite and nonnegative')
        if args.expect_size and any(not math.isfinite(x) or x <= 0 for x in args.expect_size):
            raise ValueError('expected sizes must be finite and positive')
        if args.expect_bodies is not None and args.expect_bodies < 1:
            raise ValueError('expected body count must be positive')
        path = Path(args.model)
        if not path.is_file() or path.suffix.lower() != '.stl':
            raise ValueError('input must be an existing STL file')
        try:
            import numpy as np
            import trimesh
        except ImportError as exc:
            raise ValueError(f'missing dependency: {exc}; install requirements.txt') from exc
        # STL repeats its vertices per triangle; processing joins identical vertices
        # for topology checks in memory. No holes, winding, or faces are repaired.
        mesh = trimesh.load_mesh(path, file_type='stl', process=False)
        if not isinstance(mesh, trimesh.Trimesh) or not len(mesh.faces) or not len(mesh.vertices):
            raise ValueError('STL contains no readable triangle mesh')
        if not np.isfinite(mesh.vertices).all():
            raise ValueError('mesh contains non-finite coordinates')
        mesh.merge_vertices()
        bounds = mesh.bounds
        size = mesh.extents
        report.update(bounds_mm=bounds.tolist(), size_mm=size.tolist(),
                      body_count=int(mesh.body_count), watertight=bool(mesh.is_watertight),
                      winding_consistent=bool(mesh.is_winding_consistent),
                      signed_volume_mm3=float(mesh.volume),
                      degenerate_faces=int((~mesh.nondegenerate_faces()).sum()))
        errors = report['errors']
        if not report['watertight']: errors.append('mesh is not watertight')
        if not report['winding_consistent']: errors.append('face winding is inconsistent')
        if not math.isfinite(report['signed_volume_mm3']) or report['signed_volume_mm3'] <= 0:
            errors.append('signed volume is not positive and finite')
        # A positive aggregate can hide a completely reversed separate part.
        # Negative nested shells can represent a legitimate cavity. Do not
        # silently repair them or label them invalid: require a CAD review.
        components = list(mesh.split(only_watertight=False, repair=False))
        positive = [part for part in components if part.volume > 0]
        volumes = [float(part.volume) for part in components]
        report['component_volumes_mm3'] = [v if math.isfinite(v) else None for v in volumes]
        for part, volume in zip(components, volumes):
            if not math.isfinite(volume):
                errors.append('component volume is not finite')
            elif volume <= 0:
                overlaps = any(np.all(part.bounds[0] <= other.bounds[1]) and
                               np.all(other.bounds[0] <= part.bounds[1]) for other in positive)
                if overlaps:
                    errors.append('negative nested/overlapping shell requires CAD orientation review')
                else:
                    errors.append('independent component has non-positive signed volume')
        if not math.isfinite(report['signed_volume_mm3']):
            report['signed_volume_mm3'] = None
        if report['degenerate_faces']: errors.append('mesh has degenerate faces')
        if args.expect_bodies is not None and report['body_count'] != args.expect_bodies:
            errors.append(f"body count {report['body_count']} does not match {args.expect_bodies}")
        if args.expect_size and any(abs(a-b) > args.size_tol for a,b in zip(size, args.expect_size)):
            errors.append('bounding-box size differs from expected size beyond tolerance')
        if args.on_bed and abs(float(bounds[0, 2])) > args.size_tol:
            errors.append('printing mesh minimum Z is not on the bed within tolerance')
        code = 1 if errors else 0
        report['status'] = 'fail' if errors else 'pass'
    except Exception as exc:
        report['errors'].append(str(exc))
    result = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if args.output:
        try:
            out = Path(args.output)
            if out.resolve() == Path(args.model).resolve() or (out.exists() and Path(args.model).exists() and out.samefile(args.model)):
                raise ValueError('output must not overwrite input')
            out.write_text(result, encoding='utf-8')
        except (OSError, ValueError) as exc:
            print(f'cannot write report: {exc}', file=sys.stderr)
            return 2
    else:
        print(result, end='')
    return code


if __name__ == '__main__':
    sys.exit(main())

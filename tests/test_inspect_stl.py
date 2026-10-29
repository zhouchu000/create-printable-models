import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import trimesh

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'inspect_stl.py'


class InspectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.box = trimesh.creation.box(extents=[10, 20, 30])

    def save(self, mesh, name='model.stl', kind='stl'):
        path = self.root / name
        mesh.export(str(path), file_type=kind)
        return path

    def inspect(self, path, *args):
        run = subprocess.run([sys.executable, str(SCRIPT), str(path), *map(str, args)],
                             capture_output=True, text=True)
        report = json.loads(run.stdout) if run.stdout.strip() else None
        return run, report

    def test_binary_and_ascii(self):
        for kind in ('stl', 'stl_ascii'):
            with self.subTest(kind=kind):
                p = self.save(self.box, kind=kind)
                run, r = self.inspect(p, '--expect-size', 10, 20, 30, '--expect-bodies', 1)
                self.assertEqual(run.returncode, 0)
                self.assertEqual(r['status'], 'pass')
                self.assertEqual(r['size_mm'], [10, 20, 30])
                self.assertEqual(r['body_count'], 1)
                self.assertTrue(r['watertight'] and r['winding_consistent'])
                self.assertEqual(r['degenerate_faces'], 0)
                self.assertAlmostEqual(r['signed_volume_mm3'], 6000)
                self.assertEqual(r['errors'], [])

    def test_open_mesh(self):
        mesh = self.box.copy()
        mesh.update_faces(range(len(mesh.faces) - 1))
        run, r = self.inspect(self.save(mesh))
        self.assertEqual(run.returncode, 1)
        self.assertFalse(r['watertight'])
        self.assertIn('mesh is not watertight', r['errors'])

    def test_separate_bodies(self):
        other = self.box.copy(); other.apply_translation([30, 0, 0])
        p = self.save(trimesh.util.concatenate([self.box, other]))
        run, r = self.inspect(p, '--expect-bodies', 1)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(r['body_count'], 2)
        self.assertIn('body count', ' '.join(r['errors']))
        run, r = self.inspect(p, '--expect-bodies', 2)
        self.assertEqual((run.returncode, r['status']), (0, 'pass'))

    def test_wrong_size(self):
        run, r = self.inspect(self.save(self.box), '--expect-size', 11, 20, 30)
        self.assertEqual((run.returncode, r['status']), (1, 'fail'))
        self.assertIn('size', ' '.join(r['errors']))

    def test_bad_and_missing_input(self):
        bad = self.root / 'bad.stl'; bad.write_text('not an STL')
        for path in (bad, self.root / 'missing.stl'):
            with self.subTest(path=path):
                run, r = self.inspect(path)
                self.assertEqual((run.returncode, r['status']), (2, 'error'))
                self.assertTrue(r['errors'])

    def test_independent_inverted_shell(self):
        # A smaller reversed part leaves the aggregate volume positive, so
        # checking only the total volume cannot detect this regression.
        other = trimesh.creation.box(extents=[2, 2, 2])
        other.apply_translation([30, 0, 0]); other.invert()
        run, r = self.inspect(self.save(trimesh.util.concatenate([self.box, other])))
        self.assertEqual(run.returncode, 1)
        self.assertGreater(r['signed_volume_mm3'], 0)
        self.assertIn('independent component has non-positive signed volume', r['errors'])
        self.assertLess(min(r['component_volumes_mm3']), 0)

    def test_nested_cavity_requires_review(self):
        inner = trimesh.creation.box(extents=[2, 4, 6]); inner.invert()
        run, r = self.inspect(self.save(trimesh.util.concatenate([self.box, inner])))
        self.assertEqual(run.returncode, 1)
        self.assertTrue(r['watertight'])
        self.assertIn('negative nested/overlapping shell requires CAD orientation review', r['errors'])

    def test_bed_positions(self):
        for z, code in ((15, 0), (14, 1), (16, 1)):
            with self.subTest(z=z):
                box = self.box.copy(); box.apply_translation([0, 0, z])
                run, r = self.inspect(self.save(box), '--on-bed')
                self.assertEqual(run.returncode, code)
                self.assertAlmostEqual(r['bounds_mm'][0][2], z - 15)
                if code: self.assertIn('minimum Z', ' '.join(r['errors']))

    def test_input_unchanged_and_json_output(self):
        p = self.save(self.box); before = hashlib.sha256(p.read_bytes()).digest()
        out = self.root / 'report.json'
        run, report = self.inspect(p, '--output', out)
        self.assertEqual(run.returncode, 0)
        self.assertIsNone(report)
        self.assertEqual(json.loads(out.read_text())['status'], 'pass')
        self.assertEqual(hashlib.sha256(p.read_bytes()).digest(), before)
        run, _ = self.inspect(p, '--output', p)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(hashlib.sha256(p.read_bytes()).digest(), before)

    def test_hardlink_output_cannot_overwrite_input(self):
        p = self.save(self.box); link = self.root / 'linked.json'
        try: os.link(p, link)
        except OSError: self.skipTest('hard links not supported')
        before = hashlib.sha256(p.read_bytes()).digest()
        run, _ = self.inspect(p, '--output', link)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(hashlib.sha256(p.read_bytes()).digest(), before)

    def test_invalid_arguments(self):
        p = self.save(self.box)
        for args in (('--size-tol', '-1'), ('--size-tol', 'nan'),
                     ('--expect-bodies', '0'), ('--expect-size', '1', '0', '1')):
            with self.subTest(args=args):
                run, r = self.inspect(p, *args)
                self.assertEqual((run.returncode, r['status']), (2, 'error'))
                self.assertTrue(r['errors'])
        run, _ = self.inspect(p, '--expect-bodies', 'abc')
        self.assertEqual(run.returncode, 2)


if __name__ == '__main__':
    unittest.main()

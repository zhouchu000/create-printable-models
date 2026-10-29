# Right-angle bracket

A one-piece bracket with a base, upright, reinforcing rib and two through holes. Edit the millimetre parameters at the top of `build.py` for the intended application.

From this directory run `python build.py --output ./generated`. The script requires CadQuery, trimesh, NumPy and Matplotlib. It outputs STL and STEP, a preview rendered from the STL, and `checks.json`. The STL is positioned on Z=0. Checks validate the single solid and dimensions, reopen STEP, and probe both holes. Slicing and strength require separate checks.

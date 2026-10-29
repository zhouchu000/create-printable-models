# Fit rings

Three rings test a nominal 18 mm diameter with offsets of -0.2, 0 and +0.2 mm. Offsets change the whole diameter, not the clearance on each side. Dimensions in `build.py` are demonstration values in millimetres; adjust them to the mating part and print process.

From this directory run `python build.py --output ./generated`. The script requires CadQuery, trimesh, NumPy and Matplotlib. It writes three STL/STEP pairs, a preview rendered from the STLs, and `checks.json`. STL is positioned on Z=0; STEP is in model coordinates. The script verifies single valid solids, reopens STEP, measures the bore using solid volume, and checks a probe inside each hole. Slicing and physical fit require separate checks.

# Enclosure with locating lid

An open box and removable locating-skirt lid with a cable notch. Edit the millimetre parameters at the top of `build.py`; `CLEARANCE` is the nominal gap on each side. The lid locates in the box and has no latch. Values are demonstration choices, so confirm actual mating dimensions and print fit for your use.

From this directory run `python build.py --output ./generated`. The script requires CadQuery, trimesh, NumPy and Matplotlib. It outputs separate STL/STEP parts, an assembly STEP, an STL-derived assembly preview, and `checks.json`. Each STL has minimum Z=0; the lid is printed with its outer top face on the bed and its skirt pointing upward. STEP parts use assembly coordinates. The checks reopen STEP, measure the skirt gap at a straight section, and calculate intersections for the assembly, a sample internal envelope, and cable passage. Slicing and physical fit require separate checks.

ASAP7 Technology Library
===========

HAMMER's default demonstration PDK is [ASAP7](http://asap.asu.edu/asap/). There are some special setup and known issues with this open PDK.

Setup and Environment
=====================

In addition to requirements for `hammer-vlsi`, using ASAP7 also requires:
- ASAP7 PDK version 1p5. Note this is not the latest PDK from the ASU website; you will need to contact developers for the older version.
- The PDK tarball must not be pre-extracted, i.e. must specify `technology.asap7.tarball_dir` only.
- `numpy` and `gdspy` must also be installed. This is needed to modify the GDS after place-and-route. \* The gdspy version must be 1.4 as newer versions are incompatible.
- Calibre must be the DRC/LVS tool.

\*At this moment, for BWRC affiliates, the environment needed for a `gdspy` install is setup only on the LSF cluster machines. To install it:
```
scl enable rh-python36 bash
python -m pip install gdspy --user
```
Or, replace the pip installation with installation from source in `hammer/src/tools/gdspy`.

Dummy SRAMs
===========
The ASAP7 plugin comes with a set of dummy SRAMs, which are **NOT** used by default (not included in the default tech.json).

They are **completely blank** (full obstructions on layers M1-M3, will not pass DRC & LVS).
All pins are on M4, with the signal all on the left side and the power stripes running across. The M5 power stripes are able to connect up.

**All SRAMs are scaled up by 4x, so they are subject to the scaling script.**

`sram-cache-gen.py` generates `sram-cache.json` using `srams.txt`, which contains a list of available SRAMs in Hammer IR. `sram-cache.json` memories is used by MacroCompiler to insert these memories into the design.

Finally, the SRAMCompiler in `sram_compiler/__init__.py` is used to generate the ExtraLibrarys (including .lib, .lef, .gds) needed by the particular design.

Known DRC Issues
=================

Due to discrepancies between the technology LEF and DRC decks, these are the most common DRC violations one can expect to encounter:
- V(n).M(n+1).AUX.2 and V(n).M(n).EN.1 due to limited selection of via cuts
- M(4,5,6,7).AUX.(1,2) and FIN.S.1 off-grid due to incorrect technology LEF offset for these layers
- LVT.W.1 due to filler-cells with VT's different from surrounding cells

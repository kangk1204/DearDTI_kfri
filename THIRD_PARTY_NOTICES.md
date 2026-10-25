# Code attribution

## DearDTI

Source: https://github.com/kangk1204/DearDTI

Reference commit: `cc741b8adfa445e45dedfcef884567cb125a819a`.

Copyright (c) 2025 DearDTI contributors. Licensed under MIT. The complete notice is retained in [`src/nutriomics_dti/vendor/DEARDTI_MIT_LICENSE.txt`](src/nutriomics_dti/vendor/DEARDTI_MIT_LICENSE.txt).

| Original file | Adapted component |
|---|---|
| `experiments/plm_model.py` | GINE and amino-acid CNN encoders |
| `dti_sota/models/fusion.py` | Cross-attention and bilinear interaction |

Changes include valid-atom normalization, residue masking, sequence-aware pooling, RDKit atom/bond inputs and a Kd-specific regression layer. Details and source hashes are in [Code origin](docs/DEARDTI_ORIGIN.md).

## Dependencies

PyTorch, RDKit, NumPy, SciPy, pandas, scikit-learn, joblib and Requests are installed as dependencies and retain their respective licenses. MMseqs2 is an external executable used for the protein-similarity split; its GPLv3 license applies to that tool. This repository links to its official installation source in the reproduction guide.

The MIT license covers the software distributed here. Data-provider terms are listed in [DATA_LICENSES.md](DATA_LICENSES.md).

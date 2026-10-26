# DearDTI KFRI

[![한국어](https://img.shields.io/badge/Language-한국어-2457A7)](README.ko.md)

DearDTI KFRI predicts compound-target binding affinity from a molecular structure and a protein sequence. It extends the ingredient recommendation research in the NutriOmics project by adapting the graph, sequence and fusion modules of [DearDTI](https://github.com/kangk1204/DearDTI).

The model takes a compound written as SMILES and a protein written as an amino-acid sequence. It returns **pKd**, a logarithmic measure of binding affinity. Higher pKd corresponds to lower Kd and stronger binding.

[Methods](docs/METHODS.md) | [Reproduction](docs/REPRODUCTION.md) | [Results](results/published_metrics.csv) | [Checks](docs/VALIDATION.md) | [Code origin](docs/DEARDTI_ORIGIN.md)

## Model

| Component | Implementation |
|---|---|
| Molecular structure | Three-layer GINE graph neural network |
| Protein sequence | Amino-acid embedding and three-layer CNN |
| Compound-protein fusion | Bidirectional cross-attention and bilinear interaction |
| Output | One pKd regression value per pair |

This project adds Kd-specific data processing, a regression output layer, source-aware data splits, baseline comparisons and CPU/GPU inference. DearDTI KFRI and the reference models were fitted to the project dataset. [Source attribution](docs/DEARDTI_ORIGIN.md) identifies the reused modules and their changes.

## Data and results

The October 2026 BindingDB archive contained **3,243,660 records**. Processing retained **70,617 exact positive Kd measurements**, covering 27,565 compounds and 3,825 protein sequences. A common molecular-size limit left **69,533 measurements** for splitting and model comparison.

The table presents DearDTI KFRI and Ridge, a regularized linear regression reference, under six data splits. The splits separate pairs, compounds, targets, molecular scaffolds, protein similarity or publication/assay sources within this BindingDB collection. Source and pair overlaps were removed across partitions.

| Split | Test measurements | DearDTI KFRI RMSE | Ridge RMSE |
|---|---:|---:|---:|
| Random pairs | 10,467 | 1.576 | 2.146 |
| New compounds | 11,239 | 1.499 | 1.983 |
| New targets | 11,461 | 1.531 | 1.915 |
| Molecular scaffolds | 9,528 | 1.601 | 1.944 |
| Protein similarity | 11,804 | 1.618 | 1.879 |
| Publication/assay sources | 8,736 | **1.448** | 1.506 |

RMSE measures prediction error in pKd units; lower values indicate smaller errors. On the source split, DearDTI KFRI achieved an RMSE of **1.448 pKd** and a Spearman correlation of **0.413**. Ridge gave **1.506 pKd** and **0.398**, respectively. Model settings were selected using validation data before test evaluation.

The [full results table](results/published_metrics.csv) includes MAE, source-level summaries and uncertainty intervals. [Data preparation counts](results/data_preparation.json), [split sizes](results/split_protocol.json) and [prediction-file hashes](results/prediction_manifest.json) accompany the results.

## Install and check

Use Python 3.11 or 3.12. The following setup runs the checks on a CPU:

```bash
git clone https://github.com/kangk1204/DearDTI_kfri.git
cd DearDTI_kfri
python -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e ".[test]"
python scripts/reproduce_tables.py --check
python -m pytest -q
```

On Windows PowerShell, activate the environment with `.\.venv\Scripts\Activate.ps1`.

The table check recalculates RMSE, MAE and Spearman correlation from the included aggregate statistics. The tests exercise molecular inputs, model gradients, padding, source separation and inference precision. These are separate checks from rerunning the full benchmark.

## Train and predict

The [reproduction guide](docs/REPRODUCTION.md) covers the dated BindingDB inputs, MMseqs2 installation, data splitting, training and evaluation. Raw inputs and trained checkpoints are generated in local data folders.

After training, predict new compound-target pairs:

```bash
deardti-kfri-infer \
  --model-dir data/native_kd_gine_20261003_v1/models/source/deardti_gine_aacnn \
  --input examples/query.csv --out outputs/prediction --device cpu
```

Input columns are `measurement_id`, `smiles` and `protein_sequence`. Outputs include predictions and a manifest recording the input, checkpoint, code and precision settings. Use `--device cuda` in a CUDA environment. The default inference policy uses IEEE FP32 arithmetic.

## License and citation

Software is available under the [MIT license](LICENSE). The original DearDTI copyright and license are retained in the [third-party notice](THIRD_PARTY_NOTICES.md). Data-provider terms and citations are listed in [DATA_LICENSES.md](DATA_LICENSES.md).

For research use, cite this repository and the commit used, together with DearDTI and BindingDB. [CITATION.cff](CITATION.cff) provides the software citation.

# Evaluation data

These files record the 18 Kd evaluations for DearDTI KFRI, ExtraTrees and ridge.

| File | Content |
|---|---|
| `published_metrics.csv` | Full-precision evaluation metrics and source-level summaries |
| `sufficient_statistics.json` | Aggregate error and rank sums used to recalculate RMSE, MAE and Spearman |
| `prediction_manifest.json` | Original prediction-file hashes, row counts and measurement-ID hashes |
| `data_preparation.json` | Dated archive hashes and preprocessing counts |
| `split_protocol.json` | Partition sizes, exclusions and evaluation settings |
| `precision_verification.json` | Recorded CPU/GPU inference comparison panels |
| `training/` | Model, input and source hashes with training settings |

Run `python scripts/reproduce_tables.py --check` from the repository root to verify the primary metrics. See [Reproduction](../docs/REPRODUCTION.md) for checks against original predictions and full training.

Derived evaluation data are provided under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) by kangk1204. Credit BindingDB and ChEMBL for the source measurements, and DearDTI KFRI for the selection, prediction and aggregate analysis. Source citations and provider terms are in [DATA_LICENSES.md](../DATA_LICENSES.md).

# Reproduction

## 1. Recalculate the result table

```bash
python scripts/reproduce_tables.py --check
```

This command recomputes RMSE, MAE and Spearman correlation for all 18 evaluations from `results/sufficient_statistics.json`. That file was calculated from the archived prediction tables. Their SHA256 hashes and row counts are in `results/prediction_manifest.json`.

To recalculate directly from a locally held copy of those prediction tables:

```bash
python scripts/reproduce_tables.py --predictions-root /path/to/benchmark --check
```

The folder must contain `results/<split>/<model>/test_predictions.csv.gz`. The command verifies file hashes before reading the labels and predictions. Both routes compare against the full-precision published CSV.

## 2. Prepare the inputs

Obtain the dated October 2026 archives from the [official BindingDB downloads](https://www.bindingdb.org/rwd/bind/chemsearch/marvin/Download.jsp). Use the exact archive hashes recorded in `results/data_preparation.json`. The download helper checks SHA256 and ZIP integrity:

```bash
python scripts/download_inputs.py --out data/raw
```

Source records retain the terms listed in [DATA_LICENSES.md](../DATA_LICENSES.md).

## 3. Prepare the training environment

The original training used Python 3.11, PyTorch 2.11.0+cu128, RDKit 2026.03.5, scikit-learn 1.9.0 and an RTX 5070 Ti. Full recorded package/runtime values are in [`environment/training_runtime.json`](../environment/training_runtime.json).

Install the matching PyTorch CUDA build for GPU training. Install MMseqs2 release **18-8cc5c** from [its official repository](https://github.com/soedinglab/MMseqs2/releases/tag/18-8cc5c), add `mmseqs` to PATH and compare its version with [`mmseqs_provenance.json`](../environment/mmseqs_provenance.json). The external tool retains its GPLv3 license.

Fixed seeds and recorded environments support numerical comparison. GPU training also records PyTorch deterministic-operation warnings. Saved-checkpoint inference and retraining are distinct reproduction procedures.

## 4. Run the full benchmark

Use a new output folder and a GPU environment. All fitting and validation selection finish before test evaluation.

```bash
python scripts/run_benchmark.py \
  --raw data/raw/BindingDB_All_202610_tsv.zip \
  --assay-map data/raw/BindingDB_rsid_eaids_202610_tsv.zip \
  --root data/native_kd_gine_20261003_v1 \
  --prepared data/native_202610_v1 \
  --out outputs/benchmark --threads 2 --epochs 20
```

The run produces a prepared measurement table, source ledger, six split locks, 18 fitted models, predictions and metrics. Existing completed outputs are retained. A failed or interrupted training attempt requires a fresh model directory.

Compare preprocessing counts with `results/data_preparation.json` and split sizes with `results/split_protocol.json`. The source and model hashes in the individual training records identify the exact executed inputs and code. Published records are in `results/training/`.

## 5. Predict with a trained checkpoint

```bash
deardti-kfri-infer \
  --model-dir data/native_kd_gine_20261003_v1/models/source/deardti_gine_aacnn \
  --input examples/query.csv --out outputs/new_prediction --device cpu
```

`examples/query.csv` is a synthetic input for checking the file format. The CLI requires a trained checkpoint and its training record. It saves predictions and a manifest with input, model, code and precision hashes. A new output directory is required for each run.

Default policy: `ieee-fp32-v1`. Historical CUDA-output reproduction uses `--device cuda --policy legacy-cudnn-tf32-v1`. The two policies are recorded explicitly.

# Validation record

Checks completed on 26 October 2026:

| Check | Result |
|---|---|
| Metrics from included aggregate statistics | All 18 evaluations match the published CSV |
| Metrics from archived prediction tables | File hashes verified; all 18 evaluations match |
| Metric comparison tolerance | Absolute difference at most 1e-8 |
| CPU model and data-protocol tests | 29 passed |
| Training and inference command help | Both entry points execute |
| Local documentation links | All linked files and folders present |
| Original neural training-code hashes | Match the copied model, split and source-ledger files |

The tests cover Kd conversion, molecular stereochemistry and size limits, model gradients, padding invariance, source aliases, partition overlap, training-only data access, frozen-checkpoint verification and precision-state restoration.

Run the numerical and code checks with:

```bash
python scripts/reproduce_tables.py --check
python -m pytest -q
```

`environment/validation_runtime.json` records the software used for these checks. `environment/training_runtime.json` records the original benchmark environment. [Reproduction](REPRODUCTION.md) provides separate instructions for result recalculation, full retraining and checkpoint inference.

# Methods

## Binding affinity

The target is an exact positive Kd measurement. Values are converted with `pKd = 9 - log10(Kd in nM)`. Ki, IC50 and EC50 remain separate endpoints in the source data. The parser records exclusions for censored values, invalid sequences and structures, multi-chain targets, explicitly altered constructs and repeated measurements.

The retained dataset contains 70,617 measurements, 52,375 compound-sequence pairs, 27,565 compounds, 3,825 protein sequences and 4,084 connected source groups. Compounds use the supplied isomeric SMILES. Native full InChIKey agreement was present for 40,656 measurements; the remaining 29,961 retain an identity uncertainty flag in the original ledger. Food-specific structural matching uses the stricter identity condition.

All models share the same maximum molecular size of 128 atoms. This excludes 1,084 measurements and leaves 69,533 for partitioning. Full sequences define target identity and the similarity audit. The CNN processes the first 1,024 residues, pooled to at most 128 tokens.

## Architecture and controls

DearDTI KFRI uses 64 hidden channels, three GINE layers, an amino-acid CNN, four-head bidirectional cross-attention and rank-16 bilinear interaction. A regression head returns standardized pKd; training-set mean and standard deviation restore the original scale.

ExtraTrees and ridge use a chirality-aware Morgan fingerprint and protein composition features. ExtraTrees has 100 trees and searches leaf sizes 2 and 4. Ridge searches alpha values 1, 10 and 100 after training-only standardization.

## Data separation

The six modes are random pairs, cold compounds, cold targets, molecular scaffolds, protein similarity and source groups. Publication, patent and assay aliases are connected before splitting. Measurements that create cross-partition source or pair overlap are quarantined.

The protein audit uses MMseqs2 18-8cc5c with identity 0.4 and bidirectional coverage 0.8. Qualifying connections form components for partitioning. Partition sizes and quarantined counts are retained in [`split_protocol.json`](../results/split_protocol.json).

## Training and selection

The random seed is 20261003. Neural training uses AdamW, learning rate 0.001, weight decay 0.0001, batch size 32, gradient clipping at 5 and up to 20 epochs. Early stopping uses four epochs without validation improvement. Training loads the training and validation files. The final evaluation consumes a separate test attempt for each model and split.

Validation selects hyperparameters, epochs and a preferred model. Test results are then reported for all three models. The preferred model remains the validation choice even when another model has a lower test RMSE.

## Evaluation and precision

RMSE and MAE use pKd units. Spearman correlation uses average ranks for ties. The full result table also contains source-macro RMSE, within-target ranks and source-block bootstrap intervals. Bootstrap intervals are conditional on the recorded predictions.

The benchmark is a source-purged evaluation within the dated BindingDB collection. Food-specific independent evaluation requires its own historical-source exclusion and sufficiently sized test cohort. The current strict food intersection has 33 measurements, 9 compounds, 26 targets and 26 source groups; independent food performance remains unevaluated.

Historical neural results used the recorded CUDA arithmetic. The default portable inference policy uses IEEE FP32. In the recorded RTX 5070 Ti/PyTorch 2.11 environment, CPU/GPU differences were at most 1.9073486e-6 pKd across twelve bounded comparison panels. Training and inference environments are recorded separately.

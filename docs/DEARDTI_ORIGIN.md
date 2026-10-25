# Code origin and project development

Source: https://github.com/kangk1204/DearDTI

Frozen commit: `cc741b8adfa445e45dedfcef884567cb125a819a`.

The selected GINE and amino-acid CNN encoders derive from
`experiments/plm_model.py` (original SHA256
`a989b656447be4f06c50f80779c60b38378153370a0d8dca490dd12ab54f763c`).
Cross-attention and bilinear fusion are copied from
`dti_sota/models/fusion.py` (SHA256
`68743fc5c550828c8a74feccd19487bf2e4db56f29e246fc73bddc73fc9709ee`).

The full MIT notice is preserved in
`src/nutriomics_dti/vendor/DEARDTI_MIT_LICENSE.txt`.

## Changes for the KFRI project

- RDKit atom and bond features for the measured Kd task.
- GINE normalization over valid atoms, including single-atom inputs.
- CNN residue masking and pooling within each sequence's actual length.
- A single pKd regression output and training-only label standardization.
- Native measurement parsing, source alias normalization and six evaluation splits.
- ExtraTrees and scaled-ridge controls trained on the same partitions.
- Checkpoint verification and explicit IEEE FP32 or historical CUDA inference.

The protein encoder is an amino-acid CNN trained from its initialization. The GINE model is also freshly fitted to the project Kd data. [Source-file hashes](source_files.json) and individual [training records](../results/training) identify the executed code and fitted models.

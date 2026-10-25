# Data sources and terms

## BindingDB

The benchmark uses `BindingDB_All_202610_tsv.zip` and the corresponding assay mapping file. File hashes are recorded in [`results/data_preparation.json`](results/data_preparation.json).

BindingDB's [data information page](https://bindingdb.org/rwd/bind/info.jsp) identifies its own curated records under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) and imported ChEMBL records under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Preserve the provider attribution and record origin when redistributing downloaded or processed measurements. Individual releases may provide additional terms in their deposit metadata.

The repository distributes software, aggregate evaluation statistics, source hashes and small synthetic test inputs. Raw BindingDB records, protein sequences from that download and trained checkpoints are acquired or generated in local data folders.

Reference: Liu T et al. BindingDB in 2024: a FAIR knowledgebase of protein-small molecule binding data. *Nucleic Acids Research* 53, D1633–D1644 (2025). https://doi.org/10.1093/nar/gkae1075.

## DearDTI KFRI outputs

| Material | Terms |
|---|---|
| Software | MIT, with the original DearDTI notice retained |
| Aggregate evaluation data in `results/` | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Original documentation and synthetic examples | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Downloaded source data | The terms supplied by each provider |

Evaluation tables were prepared by kangk1204 from project predictions and BindingDB measurements. Processing includes Kd selection, source grouping, data partitioning and aggregate error/rank calculations. BindingDB and ChEMBL attribution is retained for the source measurements. The ShareAlike terms cover these derived evaluation data; software and documentation have the terms shown above.

ChEMBL reference: Zdrazil B et al. The ChEMBL Database in 2023: a drug discovery platform spanning multiple bioactivity data types and time periods. *Nucleic Acids Research* 52, D1180-D1192 (2024). https://doi.org/10.1093/nar/gkad1004.

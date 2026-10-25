"""Freeze current-release native-Kd ledger/splits, refit controls and GINE.

Every configuration is declared before tuning; selection uses validation only.
Existing directories/results are preserved. Run from this repository's root.
"""
import argparse
import os
from pathlib import Path
import pandas as pd
from nutriomics_dti.data import prepare
from nutriomics_dti.source_ledger_v2 import build
from nutriomics_dti.prospective_kd import freeze, MODES, MODELS, SEED
from nutriomics_dti.native_kd_runner import train, evaluate
from nutriomics_dti.io import load_json, write_json, sha256, utc_now


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw",required=True)
    parser.add_argument("--assay-map",required=True)
    parser.add_argument("--root",default="data/native_kd_gine_20261003_v1")
    parser.add_argument("--prepared",default="data/native_202610_v1")
    parser.add_argument("--out",default="reports/native_kd_gine_20261003_v1")
    parser.add_argument("--threads",type=int,default=2)
    parser.add_argument("--epochs",type=int,default=20)
    args = parser.parse_args()
    root,prepared,out = Path(args.root),Path(args.prepared),Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    if not (prepared/"prepare_audit.json").exists():
        prepare(args.raw,prepared,args.assay_map)
    if not (root/"ledger/ledger.json").exists():
        build(prepared/"measurements.csv.gz",root/"ledger",prepared/"prepare_audit.json")
    if not (root/"splits/protocol.json").exists():
        freeze(root/"ledger/measurements.csv.gz",root/"splits",threads=args.threads)
    write_json(out/"run_started.json",{"started_utc":utc_now(),"split_protocol_sha256":sha256(root/"splits/protocol.json"),"epochs_max":args.epochs,"models":list(MODELS),"threads":args.threads,"historical_external_independence":False})
    # Finish all fits and validation selections before opening any final labels.
    for mode in MODES:
        split = root/"splits"/mode/str(SEED)
        selection = []
        for model in MODELS:
            directory = root/"models"/mode/model
            if not (directory/"training.json").exists():
                record = train(split,directory,model,epochs=args.epochs,device="cuda" if model=="deardti_gine_aacnn" else "cpu",threads=args.threads)
            else:
                record = load_json(directory/"training.json")
            selection.append({"model":model,"validation_rmse":record["validation_metrics"]["rmse_pkd"],"training_sha256":sha256(directory/"training.json")})
        choice = sorted(selection,key=lambda value:(value["validation_rmse"],value["model"]))[0]
        write_json(out/f"validation_selection_{mode}.json",{"frozen_utc":utc_now(),"selection":choice,"all_models":selection,"test_consulted":False})
    records = []
    for mode in MODES:
        for model in MODELS:
            destination = out/"results"/mode/model
            if (destination/"metrics.json").exists():
                record = load_json(destination/"metrics.json")
            else:
                record = evaluate(root/"splits"/mode/str(SEED),root/"models"/mode/model,destination,"cuda" if model=="deardti_gine_aacnn" else "cpu")
            records.append({"mode":mode,"model":model,**record["metrics"]})
    pd.DataFrame(records).to_csv(out/"all_runs.csv",index=False)
    write_json(out/"completion.json",{"completed_utc":utc_now(),"runs":records,"complete_runs":len(records),"current_ledger":load_json(root/"ledger/ledger.json"),"protocol_sha256":sha256(root/"splits/protocol.json"),"interpretation":"18 newly fitted internal source-purged tests. Not historical-model external validation and not clinical or food efficacy.","independent_food_status":"unevaluated until historical reference and food-minimum gates pass"})


if __name__=="__main__":
    main()

"""Versioned inference precision for frozen native-Kd GINE checkpoints.

Run this CLI in a dedicated worker process. Backend settings are process-global;
the lock serializes this module's callers, not unrelated PyTorch code. Historical
evaluation files remain valid artifacts under their historical arithmetic policy.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import io
import json
import math
from pathlib import Path
from threading import RLock

import numpy as np
import pandas as pd
import torch

from .deardti_kd import NativeKdGINE, predict
from .io import sha256, utc_now, write_json

IEEE = "ieee-fp32-v1"
LEGACY = "legacy-cudnn-tf32-v1"
_BACKEND_LOCK = RLock()


def _modern_precision_api():
    # PyTorch 2.9+ separates convolution and matrix multiplication precision.
    # Use one API family per process; never mix its old/new setters here.
    version = torch.__version__.split("+")[0].split(".")
    return tuple(int(part) for part in version[:2]) >= (2, 9)


def precision_state():
    if _modern_precision_api():
        state = {"api": "fp32_precision", "matmul": torch.backends.cuda.matmul.fp32_precision,
                 "convolution": torch.backends.cudnn.conv.fp32_precision}
    else:
        state = {"api": "allow_tf32", "matmul": torch.backends.cuda.matmul.allow_tf32,
                 "convolution": torch.backends.cudnn.allow_tf32}
    state["cudnn_benchmark"] = torch.backends.cudnn.benchmark
    return state


@contextmanager
def inference_precision(policy=IEEE, device="cpu"):
    if policy not in (IEEE, LEGACY):
        raise ValueError(f"Unknown precision policy: {policy}")
    if torch.device(device).type not in ("cpu", "cuda"):
        raise ValueError("This precision contract covers CPU/CUDA only")
    if policy == LEGACY and torch.device(device).type != "cuda":
        raise ValueError("Historical cuDNN TF32 replay requires CUDA")
    with _BACKEND_LOCK:
        before = precision_state()
        try:
            if before["api"] == "fp32_precision":
                torch.backends.cuda.matmul.fp32_precision = "ieee"
                torch.backends.cudnn.conv.fp32_precision = "tf32" if policy == LEGACY else "ieee"
            else:
                torch.backends.cuda.matmul.allow_tf32 = False
                torch.backends.cudnn.allow_tf32 = policy == LEGACY
            torch.backends.cudnn.benchmark = False
            yield precision_state()
        finally:
            if before["api"] == "fp32_precision":
                torch.backends.cuda.matmul.fp32_precision = before["matmul"]
                torch.backends.cudnn.conv.fp32_precision = before["convolution"]
            else:
                torch.backends.cuda.matmul.allow_tf32 = before["matmul"]
                torch.backends.cudnn.allow_tf32 = before["convolution"]
            torch.backends.cudnn.benchmark = before["cudnn_benchmark"]


def validate_inputs(frame):
    required = ["measurement_id", "smiles", "protein_sequence"]
    if any(name not in frame for name in required) or frame.empty:
        raise ValueError("Nonempty measurement_id, smiles and protein_sequence columns required")
    clean = frame[required].copy()
    for name in required:
        if clean[name].isna().any() or not clean[name].map(lambda v: isinstance(v, str) and bool(v.strip())).all():
            raise ValueError(f"Missing or non-string input: {name}")
    if clean.measurement_id.duplicated().any():
        raise ValueError("Duplicate measurement_id")
    return clean


def predict_frozen(model_dir, frame, device="cpu", policy=IEEE, batch_size=32):
    frame = validate_inputs(frame)
    if not isinstance(batch_size, int) or not 1 <= batch_size <= 32:
        raise ValueError("Inference batch size must be 1..32")
    if torch.get_default_dtype() != torch.float32:
        raise ValueError("Dedicated float32 worker required")
    directory = Path(model_dir)
    training_path = directory / "training.json"
    training_bytes = training_path.read_bytes()
    training_hash = hashlib.sha256(training_bytes).hexdigest()
    training = json.loads(training_bytes)
    if training["model"] != "deardti_gine_aacnn":
        raise ValueError("This contract only covers native-Kd GINE checkpoints")
    checkpoint_path = directory / "deardti_kd.pt"
    checkpoint_bytes = checkpoint_path.read_bytes()
    if hashlib.sha256(checkpoint_bytes).hexdigest() != training["model_sha256"]:
        raise ValueError("Frozen checkpoint hash mismatch")
    package = Path(__file__).parent
    for relative, expected in training["code_sha256"].items():
        source = (package / relative).resolve()
        if not source.is_relative_to(package.resolve()) or sha256(source) != expected:
            raise ValueError(f"Frozen encoder/source hash mismatch: {relative}")
    checkpoint = torch.load(io.BytesIO(checkpoint_bytes), map_location="cpu", weights_only=True)
    mean, scale = float(checkpoint["mean"]), float(checkpoint["scale"])
    if not math.isfinite(mean) or not math.isfinite(scale) or scale <= 0:
        raise ValueError("Invalid training normalization")
    model = NativeKdGINE().to(device=device, dtype=torch.float32)
    model.load_state_dict(checkpoint["state_dict"])
    with inference_precision(policy, device) as active, torch.autocast(device_type=torch.device(device).type, enabled=False):
        values = predict(model, frame, device, mean, scale, batch_size=batch_size)
        runtime = {"torch": torch.__version__, "cuda_build": torch.version.cuda,
                   "cudnn": torch.backends.cudnn.version(), "device": str(torch.device(device)),
                   "gpu": torch.cuda.get_device_name(device) if torch.device(device).type == "cuda" else None,
                   "threads": torch.get_num_threads(), "dtype": str(next(model.parameters()).dtype),
                   "active_precision": active}
    if not np.isfinite(values).all() or len(values) != len(frame):
        raise ValueError("Nonfinite or incomplete predictions")
    if sha256(checkpoint_path) != training["model_sha256"]:
        raise ValueError("Checkpoint changed during inference")
    if sha256(training_path) != training_hash:
        raise ValueError("Training record changed during inference")
    receipt = {"created_utc": utc_now(), "precision_policy_id": policy,
               "model_sha256": training["model_sha256"], "training_record_sha256": training_hash,
               "frozen_source_sha256": training["code_sha256"], "inference_source_sha256": sha256(__file__),
               "rows": len(frame), "batch_size": batch_size, "runtime": runtime,
               "normalized_input_rows_sha256": hashlib.sha256(frame.to_csv(index=False, lineterminator="\n").encode("utf8")).hexdigest(),
               "autocast_disabled": True,
               "labels_used": False, "retraining": False,
               "evidence_status": "predicted pKd; not a measured interaction or health effect",
               "historical_results_replaced": False}
    return values, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--policy", choices=[IEEE, LEGACY], default=IEEE)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists():
        raise FileExistsError("Choose a new output directory; never replace a frozen result")
    if not 1 <= args.threads <= 4:
        raise ValueError("Threads must be 1..4")
    if Path(args.input).stat().st_size > 256 * 1024 * 1024:
        raise ValueError("CLI input exceeds 256 MiB; partition into separate immutable inference inputs")
    input_bytes = Path(args.input).read_bytes()
    before = hashlib.sha256(input_bytes).hexdigest()
    frame = pd.read_csv(io.BytesIO(input_bytes), usecols=["measurement_id", "smiles", "protein_sequence"], keep_default_na=False)
    validate_inputs(frame)
    if sha256(args.input) != before:
        raise ValueError("Input changed while being parsed")
    torch.set_num_threads(args.threads)
    values, receipt = predict_frozen(args.model_dir, frame, args.device, args.policy)
    if sha256(args.input) != before:
        raise ValueError("Input changed during inference")
    out.mkdir(parents=True, exist_ok=False)
    output = frame[["measurement_id"]].copy()
    output["predicted_pkd"] = values
    output.to_csv(out / "predictions.csv", index=False)
    receipt.update({"input_sha256": before, "predictions_sha256": sha256(out / "predictions.csv")})
    write_json(out / "manifest.json", receipt)
    print(f"{len(frame)} predictions; policy={args.policy}; {out / 'manifest.json'}")


if __name__ == "__main__":
    main()

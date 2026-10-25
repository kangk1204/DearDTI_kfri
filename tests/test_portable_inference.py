import json
from pathlib import Path
import pandas as pd
import pytest

torch = pytest.importorskip("torch")

from nutriomics_dti.portable_inference import (
    IEEE, LEGACY, inference_precision, precision_state, validate_inputs, predict_frozen,
)
from nutriomics_dti.deardti_kd import NativeKdGINE
from nutriomics_dti.io import sha256


def test_precision_restored_after_exception_and_nested_call():
    before = precision_state()
    with pytest.raises(RuntimeError, match="intentional"):
        with inference_precision(IEEE) as active:
            assert active["matmul"] in ("ieee", False)
            assert active["convolution"] in ("ieee", False)
            assert active["cudnn_benchmark"] is False
            with inference_precision(IEEE):
                pass
            assert precision_state() == active
            raise RuntimeError("intentional")
    assert precision_state() == before


@pytest.mark.parametrize("policy,device", [("invalid", "cpu"), (LEGACY, "cpu"), (IEEE, "mps")])
def test_invalid_policy_does_not_mutate_backend(policy, device):
    before = precision_state()
    with pytest.raises(ValueError):
        with inference_precision(policy, device):
            pass
    assert precision_state() == before


def frame():
    return pd.DataFrame({"measurement_id": ["a"], "smiles": ["CCO"], "protein_sequence": ["ACDE"], "pkd": [float("nan")]})


def test_labels_are_not_passed_to_inference():
    clean = validate_inputs(frame())
    assert list(clean) == ["measurement_id", "smiles", "protein_sequence"]


@pytest.mark.parametrize("column,value", [("smiles", ""), ("protein_sequence", None), ("measurement_id", " ")])
def test_missing_identity_rejected(column, value):
    invalid = frame()
    invalid.loc[0, column] = value
    with pytest.raises(ValueError):
        validate_inputs(invalid)


def test_duplicate_identity_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        validate_inputs(pd.concat([frame(), frame()], ignore_index=True))


@pytest.fixture
def frozen(tmp_path):
    torch.set_num_threads(1)
    model = NativeKdGINE()
    path = tmp_path / "deardti_kd.pt"
    torch.save({"state_dict": model.state_dict(), "mean": 5., "scale": 1.}, path)
    import nutriomics_dti
    package = Path(nutriomics_dti.__file__).parent
    sources = ["native_kd_runner.py", "deardti_kd.py", "prospective_kd.py", "source_ledger_v2.py",
               "vendor/deardti_encoders.py", "vendor/deardti_fusion.py"]
    training = {"model": "deardti_gine_aacnn", "model_sha256": sha256(path),
                "code_sha256": {name: sha256(package / name) for name in sources}}
    (tmp_path / "training.json").write_text(json.dumps(training), encoding="utf8")
    return tmp_path


def test_checkpoint_receipt_and_autocast_are_explicit(frozen):
    plain, receipt = predict_frozen(frozen, frame())
    with torch.autocast(device_type="cpu", dtype=torch.bfloat16):
        inside, _ = predict_frozen(frozen, frame())
    assert (plain == inside).all()
    assert receipt["runtime"]["dtype"] == "torch.float32"
    assert receipt["autocast_disabled"] and not receipt["labels_used"]
    assert receipt["model_sha256"] == sha256(frozen / "deardti_kd.pt")


def test_modified_checkpoint_rejected_before_loading(frozen):
    with (frozen / "deardti_kd.pt").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="checkpoint hash"):
        predict_frozen(frozen, frame())


def test_training_record_race_rejected(frozen, monkeypatch):
    import nutriomics_dti.portable_inference as module
    original = module.predict
    def mutate_record(*args, **kwargs):
        path = frozen / "training.json"
        path.write_bytes(path.read_bytes() + b" ")
        return original(*args, **kwargs)
    monkeypatch.setattr(module, "predict", mutate_record)
    before = precision_state()
    with pytest.raises(ValueError, match="Training record changed"):
        predict_frozen(frozen, frame())
    assert precision_state() == before

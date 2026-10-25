import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reproduce_tables',ROOT/'scripts/reproduce_tables.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_all_published_evaluations_recalculate():
    rows=module.reproduce()
    assert len(rows)==18
    assert len({(r['mode'],r['model']) for r in rows})==18

def test_wrong_prediction_bytes_are_rejected(tmp_path):
    path=tmp_path/'results/random/extratrees/test_predictions.csv.gz'
    path.parent.mkdir(parents=True);path.write_bytes(b'changed')
    with pytest.raises(ValueError,match='checksum mismatch'):
        module.reproduce(tmp_path)

"""Metrics shared by the native Kd training and evaluation commands."""
import numpy as np
from scipy.stats import spearmanr

def metrics(actual,predicted):
    actual,predicted = np.asarray(actual),np.asarray(predicted)
    valid = np.isfinite(actual)&np.isfinite(predicted)
    if not valid.all():
        raise ValueError("Nonfinite prediction/label")
    correlation = float(spearmanr(actual,predicted).statistic) if len(actual)>1 and np.std(predicted)>0 and np.std(actual)>0 else None
    return {"n":len(actual),"rmse_pkd":float(np.sqrt(np.mean((actual-predicted)**2))),
            "mae_pkd":float(np.mean(np.abs(actual-predicted))),"spearman":correlation}

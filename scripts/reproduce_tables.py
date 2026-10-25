"""Recalculate the published metrics from aggregate statistics or original predictions."""
from pathlib import Path
import argparse,hashlib,json,math
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT=Path(__file__).resolve().parents[1]

def aggregate_metrics(row):
    n=int(row['n'])
    if n<=1:raise ValueError('At least two observations are required')
    xx=row['rank_x_square_sum']-row['rank_x_sum']**2/n
    yy=row['rank_y_square_sum']-row['rank_y_sum']**2/n
    xy=row['rank_xy_sum']-row['rank_x_sum']*row['rank_y_sum']/n
    return {'n':n,'rmse_pkd':math.sqrt(row['squared_error_sum']/n),'mae_pkd':row['absolute_error_sum']/n,'spearman':xy/math.sqrt(xx*yy)}

def reproduce(predictions_root=None):
    statistics=json.loads((ROOT/'results/sufficient_statistics.json').read_text())['runs']
    manifests=json.loads((ROOT/'results/prediction_manifest.json').read_text())
    reference=pd.read_csv(ROOT/'results/published_metrics.csv')
    actual=[]
    for row in statistics:
        key=(row['mode'],row['model'])
        result=aggregate_metrics(row)
        if predictions_root is not None:
            receipt=next(r for r in manifests if (r['mode'],r['model'])==key)
            file=Path(predictions_root)/receipt['prediction_filename']
            if hashlib.sha256(file.read_bytes()).hexdigest()!=receipt['prediction_sha256']:
                raise ValueError(f'Prediction checksum mismatch: {file}')
            frame=pd.read_csv(file);y=frame.pkd.to_numpy();p=frame.predicted_pkd.to_numpy()
            if not np.isfinite(y).all() or not np.isfinite(p).all():raise ValueError('Nonfinite values')
            result={'n':len(frame),'rmse_pkd':float(np.sqrt(np.mean((y-p)**2))),'mae_pkd':float(np.mean(np.abs(y-p))),'spearman':float(spearmanr(y,p).statistic)}
        expected=reference[(reference['mode']==key[0])&(reference['model']==key[1])]
        if len(expected)!=1:raise ValueError(f'Reference row mismatch: {key}')
        expected=expected.iloc[0]
        if result['n']!=int(expected['n']):raise ValueError(f'Row count mismatch: {key}')
        for metric in ('rmse_pkd','mae_pkd','spearman'):
            if not math.isclose(result[metric],float(expected[metric]),rel_tol=0,abs_tol=1e-8):
                raise ValueError(f'{key} {metric}: {result[metric]} != {expected[metric]}')
        actual.append({'mode':key[0],'model':key[1],**result})
    if len(actual)!=18:raise ValueError('Expected 18 complete evaluations')
    return actual

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true',help='Verify against the published full-precision CSV')
    p.add_argument('--predictions-root',type=Path,help='Folder containing archived results/<split>/<model> prediction files')
    p.add_argument('--out',type=Path,help='Optional new CSV output path')
    a=p.parse_args();rows=reproduce(a.predictions_root)
    if a.out:
        if a.out.exists():raise FileExistsError(a.out)
        a.out.parent.mkdir(parents=True,exist_ok=True);pd.DataFrame(rows).to_csv(a.out,index=False)
    print(json.dumps({'evaluations':len(rows),'metrics_per_evaluation':4,'all_match':True,'absolute_tolerance':1e-8,'source':'original predictions' if a.predictions_root else 'aggregate statistics'},indent=2))

if __name__=='__main__':main()

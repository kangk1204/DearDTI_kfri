"""Download the dated benchmark inputs and verify SHA256 and ZIP integrity."""
from pathlib import Path
import argparse,hashlib,json,zipfile
import requests

ROOT=Path(__file__).resolve().parents[1]
BASE='https://www.bindingdb.org/rwd/bind/downloads/'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    metadata=json.loads((ROOT/'results/data_preparation.json').read_text())
    entries=[('BindingDB_All_202610_tsv.zip',metadata['raw_sha256']),('BindingDB_rsid_eaids_202610_tsv.zip',metadata['assay_map_sha256'])]
    a.out.mkdir(parents=True,exist_ok=True)
    for name,expected in entries:
        target=a.out/name
        if not target.exists():
            temporary=target.with_suffix('.partial')
            with requests.get(BASE+name,stream=True,timeout=(30,180)) as response:
                response.raise_for_status()
                with temporary.open('wb') as f:
                    for chunk in response.iter_content(1024*1024):f.write(chunk)
            with temporary.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
            if actual!=expected:raise ValueError(f'SHA256 mismatch for {name}: {actual}; expected {expected}')
            temporary.replace(target)
        with target.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=expected:raise ValueError(f'SHA256 mismatch for existing {target}')
        with zipfile.ZipFile(target) as z:
            if z.testzip() is not None:raise ValueError(f'ZIP integrity failure: {name}')
        print(json.dumps({'file':name,'bytes':target.stat().st_size,'sha256':actual,'verified':True}))

if __name__=='__main__':main()

# DearDTI KFRI

[![English](https://img.shields.io/badge/Language-English-2457A7)](README.md)

화합물 구조와 단백질 서열을 입력받아 결합력을 예측하는 NutriOmics 과제용 모델. 기존 [DearDTI](https://github.com/kangk1204/DearDTI)의 분자 그래프, 서열 및 융합 모듈을 활용해 Kd 예측에 맞게 개발함.

입력은 SMILES 형식의 화합물 구조와 아미노산 서열이며, 출력은 결합 해리상수 Kd를 로그값으로 변환한 **pKd**임. pKd가 높을수록 Kd가 작고 결합력이 강한 방향에 해당함.

[분석 방법](docs/METHODS.md) | [재현 절차](docs/REPRODUCTION.md) | [전체 결과](results/published_metrics.csv) | [검사 기록](docs/VALIDATION.md) | [코드 출처](docs/DEARDTI_ORIGIN.md)

## 모델 구성

| 구성 | 사용 방법 |
|---|---|
| 화합물 구조 | 3층 GINE 분자 그래프 신경망 |
| 단백질 서열 | 아미노산 임베딩과 3층 CNN |
| 두 정보의 결합 | 양방향 cross-attention과 bilinear interaction |
| 출력 | 화합물과 표적의 pKd 예측값 1개 |

이번 과제에서 Kd 전용 자료 처리, 회귀 출력층, 출처를 반영한 자료 분할, 기준 모델 비교 및 CPU/GPU 추론 기능을 추가함. 세 모델 모두 과제 자료로 새로 학습함. 재사용한 모듈과 수정 내용은 [출처 문서](docs/DEARDTI_ORIGIN.md)에 명시함.

## 자료와 결과

2026년 10월 BindingDB 원자료 **3,243,660행**에서 정확한 양의 Kd 측정 **70,617건**을 정제함. 화합물 27,565개와 단백질 서열 3,825개를 포함하며, 세 모델에 공통 분자 크기 기준을 적용한 **69,533건**으로 자료 분할과 비교를 수행함.

동일 BindingDB 자료 안에서 쌍, 화합물, 표적, 분자 골격, 단백질 서열 유사도 및 논문/assay 출처를 기준으로 분할함. 분할 간 출처와 동일 쌍의 중복을 제거한 뒤 세 모델을 비교하여 **18개 평가**를 확보함.

| 분할 | 시험 측정 수 | ExtraTrees RMSE | DearDTI KFRI RMSE | Ridge RMSE |
|---|---:|---:|---:|---:|
| 무작위 쌍 | 10,467 | 1.561 | 1.576 | 2.146 |
| 새로운 화합물 | 11,239 | 1.471 | 1.499 | 1.983 |
| 새로운 표적 | 11,461 | 1.473 | 1.531 | 1.915 |
| 분자 골격 | 9,528 | 1.545 | 1.601 | 1.944 |
| 단백질 서열 유사도 | 11,804 | 1.589 | 1.618 | 1.879 |
| 논문/assay 출처 | 8,736 | **1.374** | **1.448** | 1.506 |

RMSE는 pKd 단위의 예측 오차이며 낮을수록 측정값에 가까움. 시험 RMSE는 여섯 분할 모두 ExtraTrees에서 가장 낮았음. 출처 분할의 Spearman 상관계수는 ExtraTrees **0.497**, DearDTI KFRI **0.413**임. 모델 설정은 시험 평가 전에 개발 자료에서 선택함.

[전체 결과표](results/published_metrics.csv)에 MAE, 출처별 요약 및 불확실성 구간을 제공함. [정제 건수](results/data_preparation.json), [분할별 표본 수](results/split_protocol.json)와 [예측 파일 해시](results/prediction_manifest.json)를 함께 기록함.

## 설치와 확인

Python 3.11 또는 3.12를 사용하며, 다음 명령으로 CPU 환경 구성 및 기본 검사 수행.

```bash
git clone https://github.com/kangk1204/DearDTI_kfri.git
cd DearDTI_kfri
python -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e ".[test]"
python scripts/reproduce_tables.py --check
python -m pytest -q
```

Windows PowerShell의 환경 활성화 명령은 `.\.venv\Scripts\Activate.ps1`임.

표 검사에서는 저장된 집계 통계로 RMSE, MAE 및 Spearman 상관계수를 재계산함. 코드 검사는 분자 입력, 모델 기울기, 패딩, 출처 분리 및 추론 정밀도를 확인함. 전체 자료의 재학습은 [재현 절차](docs/REPRODUCTION.md)에 따라 별도 수행.

## 학습과 예측

재현 안내에 원자료 확보, MMseqs2 설치, 자료 분할, 학습 및 평가 순서를 제시함. 원자료와 학습 체크포인트는 실행 환경의 data 폴더에 생성됨.

학습 완료 후 다음 명령으로 새 화합물과 표적을 예측함.

```bash
deardti-kfri-infer \
  --model-dir data/native_kd_gine_20261003_v1/models/source/deardti_gine_aacnn \
  --input examples/query.csv --out outputs/prediction --device cpu
```

입력 CSV의 열은 `measurement_id`, `smiles`, `protein_sequence`임. 예측 결과와 입력, 체크포인트, 코드 및 정밀도 설정을 기록한 manifest를 생성함. CUDA 환경에서는 `--device cuda`를 사용하며, 기본 추론은 IEEE FP32 연산을 적용함.

## 라이선스와 인용

코드는 [MIT 라이선스](LICENSE)를 적용하고, 기존 DearDTI의 저작권과 라이선스를 [출처 고지](THIRD_PARTY_NOTICES.md)에 보존함. 원자료의 이용조건과 인용 문헌은 [DATA_LICENSES.md](DATA_LICENSES.md)에 정리함.

연구에 사용한 경우 저장소 주소와 사용한 commit, DearDTI 및 BindingDB를 함께 인용. 소프트웨어 서지는 [CITATION.cff](CITATION.cff)에 제공함.

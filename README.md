# PHQ-9 하이브리드 문항 선택 기법의 전체 척도 재현도 검증

학사학위논문 **「PHQ-9 기반 하이브리드 문항 선택 기법의 전체 척도 재현도 검증: 정신건강
자가진단 서비스 「당신의 하루는」을 중심으로」** <br>(전남대학교 컴퓨터정보통신공학전공)의 실험을
재현하는 코드와 산출물이다.

**핵심 질문**: PHQ-9 9문항 중 **고정 3문항(흥미 상실·우울 기분·수면) + 매 회 무작위 2문항**,<br>
즉 5문항 응답만으로 전체 9문항 PHQ-9의 우울 중증도 분류를 얼마나 충실히 **재현**할 수 있는가?

> 검증하는 것은 임상 진단 정확도가 아니라 **문항 축소에 따른 전체 척도 재현도**다. 공개 데이터에
> 임상 확진(SCID 등)이 동반된 문항 단위 PHQ-9가 없으므로, 정답(ground truth)은 "전체 9문항
> PHQ-9의 총점과 표준 중증도 분류"로 정의한다.

## 추정량 (동일가중)

응답된 5문항 점수 `x_i ∈ {0,1,2,3}` 의 합을 전체 척도로 복원한다.

```
T̂ = 9 · ( Σ_{i∈S} x_i ) / 5        ∈ [0, 27],   S = 고정3 ∪ 랜덤2
```

- 다섯 문항에 **동일 가중(문항당 1/5)** 을 주는 단순 추정량이다.
- 0~27 척도로 복원해 PHQ-9 표준 컷(`≥5 경미 / ≥10 중등도 / ≥15 중등도–심함 / ≥20 심함`)을 그대로 적용한다.
- 동일가중이 타당한지는 **고정 블록에 가중 α를 주는 일반화** `T̂(α) = 9·[(α/3)Σ_F + ((1−α)/2)Σ_R]`
  를 도입해 α를 0.50~0.90으로 **스윕**하여 검증한다(α=0.6이 곧 동일가중). 실험 결과 동일가중이
  일치율 최대점이자 κ 최적 평지 위에 있어, 별도의 가중을 두지 않는 설계가 실증적으로 뒷받침된다.

## 평가 지표

| 지표 | 의미 |
|---|---|
| 분류 일치율(accuracy) | 하이브리드 5문항 분류가 9문항 분류와 일치한 비율 |
| Quadratic weighted κ | 순서형 5등급 분류의 우연 보정 일치도 |
| 상관(Pearson / Spearman) | `T̂` 추정 점수와 9문항 총점의 상관 |
| 민감도 / 특이도 | `≥10`(우울 의심) 컷 기준, 9문항 `≥10`을 참조 |
| 회전 분산(±std) | 랜덤 2문항 조합(C(6,2)=15) 전수에 대한 지표 표준편차 |
| 개인 수준 회전 불안정성 | 같은 응답자의 판정이 회전에 따라 바뀌는 비율 |

## 데이터셋 · 라이선스

| 데이터 | 표본 | 라이선스 | 이 저장소 포함 여부 |
|---|---|---|---|
| **NHANES** DPQ (미 CDC/NCHS) | 미국 성인 N=21,029 | 퍼블릭 도메인 | ✅ `data/processed/nhanes_phq9.csv` |
| **Zenodo** 10423537 (Su et al., 2024) | 중국 대학생 N=24,292 | CC-BY-4.0 | ✅ `data/processed/zenodo_phq9.csv` |
| **KNHANES** (질병관리청) | 한국 성인 N=21,977 | 이용서약 필요(재배포 불가) | ⚠️ **미포함** — 아래 참고 |

**KNHANES 마이크로데이터는 이용약관(제3자 제공 금지)상 재배포할 수 없어 이 저장소에 포함하지
않는다.**<br> KDCA(https://knhanes.kdca.go.kr)에서 직접 원시자료를 내려받아 `src/prep_knhanes.py`
로 동일한 처리 CSV를 재생성할 수 있다.<br> 논문·`results/` 의 KNHANES **집계 결과**(평균·κ 등)는
마이크로데이터가 아니므로 그대로 포함한다. 상세 출처는 [`data/README.md`](data/README.md) 참고.

## 재현 방법

```bash
rye sync                                   # 가상환경 구성 (uv 기반)

# 데이터 준비
rye run python src/download_nhanes.py      # NHANES .xpt 다운로드 → data/processed/
rye run python src/download_zenodo.py      # Zenodo CSV 다운로드 → data/processed/
# KNHANES는 KDCA에서 수동 다운로드 후: rye run python src/prep_knhanes.py

# 실험 실행 (results/ 재생성)
rye run python src/experiment.py           # α 스윕·추정량 비교 (표 4-1·4-2, 그림 4-1·4-2)
rye run python src/crossval.py             # 교차 집단 재현성 (표 4-3, 그림 4-3)
rye run python src/item_importance.py      # 문항 중요도 (표 4-5)
rye run python src/ablation_core_pair.py   # 핵심쌍 28조합 ablation
rye run python src/ablation_fixed_item.py  # 세 번째 고정 문항 비교 (표 4-6, 그림 4-4)
```

`data/processed/` 에 NHANES·Zenodo CSV가 이미 포함되어 있어, 이 둘만으로도 KNHANES를 뺀 대부분의
결과를 바로 재현할 수 있다.

## 디렉토리 구조

```
.
├── README.md                    # (이 파일)
├── pyproject.toml               # rye 프로젝트 정의 / requirements*.lock
├── data/
│   ├── README.md                # 데이터 출처·라이선스
│   └── processed/               # 정제 CSV (NHANES·Zenodo 포함, KNHANES 미포함)
├── src/
│   ├── hybrid.py                # 추정량 T̂ / T̂(α)·분류·지표 정의
│   ├── experiment.py            # α 스윕 + 추정량·베이스라인 비교 (몬테카를로)
│   ├── crossval.py              # 3집단 교차 재현성
│   ├── item_importance.py       # 문항별 중요도(잔여상관·단독AUC·보고율)
│   ├── ablation_core_pair.py    # 핵심 2문항 쌍 교체 ablation
│   ├── ablation_fixed_item.py   # 세 번째 고정 문항 후보 비교
│   ├── replot_alpha.py          # 그림 4-1 재작도
│   ├── replot_comparison.py     # 그림 4-2 재작도
│   ├── download_nhanes.py       # NHANES 수집
│   ├── download_zenodo.py       # Zenodo 수집
│   └── prep_knhanes.py          # KNHANES 정제(수동 다운로드 전제)
└── results/
    ├── RESULTS.md · CROSSVAL.md # 결과 기록(로그)
    ├── figures/                 # 논문 그림 4-1~4-4
    └── tables/                  # 논문 표 4-1~4-6 원자료 CSV
```

## 라이선스

- **코드**(`src/`): MIT License ([`LICENSE`](LICENSE)).
- **데이터**: 각 출처 라이선스를 따른다(NHANES 퍼블릭 도메인, Zenodo CC-BY-4.0, KNHANES 미포함).

# 실험 결과

_생성: 2026-07-02 23:10_

## 데이터
- NHANES DPQ (PHQ-9 item-level), 9문항 완응답자: **N = 21,029**
- 정답 분류 분포 (표준 PHQ-9 컷):

| 중증도 | N | 비율 |
|---|---|---|
| none | 15,250 | 72.5% |
| mild | 3,671 | 17.5% |
| moderate | 1,321 | 6.3% |
| mod-severe | 553 | 2.6% |
| severe | 234 | 1.1% |

- (주의) NHANES 표본가중치 미적용 — 측정 일치도 검증이 목적이라 비가중 분석. 한계에 명시.

## 1) alpha 스윕 (하이브리드 가중평균 추정량, 15개 회전쌍 평균)

- **최적 alpha = 0.60** (분류 일치율 최대)
- 최적점 성능: 일치율 **84.6%** (±3.4), quadratic κ **0.889**, Pearson r **0.955**, 민감도 **0.875**, 특이도 **0.965**
- alpha=0.6(중립) 대비 danjam 초기값 0.7의 위치는 `results/tables/alpha_sweep.csv` 참고
- 그래프: `results/figures/alpha_sweep.png`

## 2) 추정량 비교 (best alpha 기준)

표: `results/tables/estimator_comparison.csv` / 그래프: `results/figures/estimator_comparison.png`

| 방법 | 일치율 | quad κ | Pearson r | 민감도 | 특이도 |
|---|---|---|---|---|---|
| hybrid-weighted (a=0.6, rotating) | 0.846 | 0.889 | 0.955 | 0.875 | 0.965 |
| hybrid-block (rotating) | 0.813 | 0.843 | 0.923 | 0.782 | 0.962 |
| fixed-5 (no rotation) | 0.769 | 0.850 | 0.961 | 0.958 | 0.928 |
| random-5 (no core) | 0.849 | 0.881 | 0.946 | 0.807 | 0.977 |
| PHQ-8 | 0.990 | 0.992 | 0.998 | 0.969 | 1.000 |
| PHQ-2 (screen >=3) | - | - | 0.834 | 0.677 | 0.958 |

## 해석 메모 (초안)
- 하이브리드(회전)가 고정5 대비 얼마나 견고한지, 랜덤5(코어 없음) 대비 고정 코어의 이득이 있는지 위 표에서 확인.
- PHQ-8은 8/9 문항이라 near-ceiling 참조값. PHQ-2는 스크리닝 민감도/특이도만 의미.
- 회전 분산(±std)이 작을수록 "매번 문항이 바뀌어도 결과가 안정적"이라는 근거.

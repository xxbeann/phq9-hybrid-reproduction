# -*- coding: utf-8 -*-
"""문항 중요도 분석: 고정 문항(q1·q2) 선정의 데이터 근거.

교수 피드백 3번("q1·q2 선정 근거 실험값") 대응. 3개 데이터셋(complete만)의
9문항 각각에 대해 아래 세 지표를 계산한다.

- item_rest_r : 해당 문항 점수와 잔여 총점(total - 해당 문항)의 Pearson 상관
                (corrected item-rest correlation)
- auc         : 해당 문항 단독 점수로 total>=10(선별 양성)을 예측하는 ROC AUC
- endorse_rate: 해당 문항 >=1 응답 비율

출력: results/tables/item_importance.csv (그림 없음 — 논문 그림 개수 게이트 9 고정)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "results" / "tables"

Q_COLS = [f"q{i}" for i in range(1, 10)]
LABELS = {0: "q1 흥미상실", 1: "q2 우울기분", 2: "q3 수면", 3: "q4 피로", 4: "q5 식욕",
          5: "q6 자책감", 6: "q7 집중력", 7: "q8 정신운동", 8: "q9 자살사고"}

DATASETS = [("nhanes", "NHANES(미국)"), ("zenodo", "Zenodo(중국)"), ("knhanes", "KNHANES(한국)")]

CUTOFF = 10  # PHQ-9 선별 양성 컷


def load(name):
    df = pd.read_csv(PROCESSED / f"{name}_phq9.csv")
    df = df[df["complete"]].copy()
    return df[Q_COLS].to_numpy(float), df["total"].to_numpy(float)


def main():
    TABLES.mkdir(parents=True, exist_ok=True)

    records = []
    for name, ds_label in DATASETS:
        items, total = load(name)
        positive = (total >= CUTOFF).astype(int)
        for j in range(9):
            item = items[:, j]
            rest = total - item
            r = float(np.corrcoef(item, rest)[0, 1])
            auc = float(roc_auc_score(positive, item))
            endorse = float((item >= 1).mean())
            records.append({
                "dataset": name, "item": f"q{j + 1}", "label": LABELS[j],
                "item_rest_r": round(r, 3), "auc": round(auc, 3),
                "endorse_rate": round(endorse, 3),
            })

    df = pd.DataFrame(records)
    out = TABLES / "item_importance.csv"
    df.to_csv(out, index=False)

    # 3집단 평균 기준 정렬표 (+ 지표별 순위)
    avg = (df.groupby(["item", "label"], sort=False)[["item_rest_r", "auc", "endorse_rate"]]
             .mean().round(3).reset_index())
    for col in ["item_rest_r", "auc", "endorse_rate"]:
        avg[f"rank_{col}"] = avg[col].rank(ascending=False, method="min").astype(int)
    avg = avg.sort_values("item_rest_r", ascending=False).reset_index(drop=True)

    print("=== 문항 중요도: 3집단 평균 (item_rest_r 내림차순) ===")
    print(avg.to_string(index=False))
    print()
    for col, nice in [("item_rest_r", "item-rest r"), ("auc", "AUC(총점>=10)"),
                      ("endorse_rate", "응답률(>=1)")]:
        order = avg.sort_values(col, ascending=False)["label"]
        print(f"{nice:>14s} 순위: " + " > ".join(order))
    for q in ["q1", "q2", "q3"]:
        row = avg[avg["item"] == q].iloc[0]
        print(f"\n{row['label']}: item-rest r {row['item_rest_r']:.3f} ({row['rank_item_rest_r']}위)"
              f" / AUC {row['auc']:.3f} ({row['rank_auc']}위)"
              f" / 응답률 {row['endorse_rate']:.3f} ({row['rank_endorse_rate']}위)")

    print(f"\n저장 -> {out}")


if __name__ == "__main__":
    main()

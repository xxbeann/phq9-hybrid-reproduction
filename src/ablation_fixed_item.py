# -*- coding: utf-8 -*-
"""Ablation: 세 번째 고정 문항 선택의 타당성 검증.

DSM-5 핵심 2문항(q1 흥미상실, q2 우울기분)은 항상 고정하고, 세 번째 고정 문항을
q3(수면)~q9(자살)로 바꿔가며 각 경우의 하이브리드 성능(κ·민감도·특이도·일치율)을
3개 데이터셋에서 비교한다. "왜 수면(q3)을 세 번째로 고정했는가"에 데이터로 답하고,
q9(자살)를 고정 편입했을 때의 성능(5장 향후과제 (1))도 함께 본다.

- 고정 = {q1, q2, X},  랜덤 풀 = 나머지 6문항에서 2개(C(6,2)=15 전수),  α=0.6
- 출력: results/tables/ablation_3rd_fixed.csv, results/figures/ablation_3rd_fixed.png
"""
from __future__ import annotations

import itertools
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = ["AppleGothic", "Apple SD Gothic Neo", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
import numpy as np
import pandas as pd

from experiment import agg, metrics_estimate
from hybrid import t_hat_weighted

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "results" / "tables"
FIGS = ROOT / "results" / "figures"

Q_COLS = [f"q{i}" for i in range(1, 10)]
ALPHA = 0.6
CORE = (0, 1)  # DSM-5 핵심 2문항 고정(항상)
LABELS = {0: "q1 흥미상실", 1: "q2 우울기분", 2: "q3 수면", 3: "q4 피로", 4: "q5 식욕",
          5: "q6 자책감", 6: "q7 집중력", 7: "q8 정신운동", 8: "q9 자살사고"}
CANDIDATES = [2, 3, 4, 5, 6, 7, 8]  # 세 번째 고정 후보

DATASETS = [("nhanes", "NHANES(미국)"), ("zenodo", "Zenodo(중국)"), ("knhanes", "KNHANES(한국)")]


def load(name):
    df = pd.read_csv(PROCESSED / f"{name}_phq9.csv")
    df = df[df["complete"]].copy()
    return df[Q_COLS].to_numpy(float), df["total"].to_numpy(float)


def evaluate(items, total, third):
    """고정={0,1,third}, 나머지 6문항에서 2개 전수 → 15쌍 평균 지표."""
    fixed_idx = list(CORE) + [third]
    pool = [i for i in range(9) if i not in fixed_idx]
    fixed_sum = items[:, fixed_idx].sum(1)
    rows = []
    for pair in itertools.combinations(pool, 2):
        random_sum = items[:, list(pair)].sum(1)
        est = t_hat_weighted(fixed_sum, random_sum, ALPHA)
        rows.append(metrics_estimate(est, total))
    return agg(rows)


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    records = []
    data = {name: load(name) for name, _ in DATASETS}
    for third in CANDIDATES:
        for name, label in DATASETS:
            items, total = data[name]
            m = evaluate(items, total, third)
            records.append({
                "third_item": LABELS[third], "dataset": label,
                "kappa": round(m["kappa_mean"], 3), "sens": round(m["sens_mean"], 3),
                "spec": round(m["spec_mean"], 3), "acc": round(m["acc_mean"], 3),
            })
    df = pd.DataFrame(records)
    df.to_csv(TABLES / "ablation_3rd_fixed.csv", index=False)

    # 3집단 평균으로 랭킹
    avg = df.groupby("third_item")[["kappa", "sens", "spec", "acc"]].mean().round(3)
    avg = avg.reindex([LABELS[c] for c in CANDIDATES])
    print("=== 세 번째 고정 문항별 3집단 평균 ===")
    print(avg.to_string())
    print()
    print("민감도 순위:", " > ".join(avg.sort_values("sens", ascending=False).index))
    print("κ 순위    :", " > ".join(avg.sort_values("kappa", ascending=False).index))
    sleep_sens_rank = avg.sort_values("sens", ascending=False).index.get_loc("q3 수면") + 1
    sleep_kappa_rank = avg.sort_values("kappa", ascending=False).index.get_loc("q3 수면") + 1
    print(f"\nq3 수면: 민감도 {sleep_sens_rank}위 / {len(CANDIDATES)}, κ {sleep_kappa_rank}위 / {len(CANDIDATES)}")

    # 그림: 후보별 민감도·κ (3집단 평균)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(avg))
    ax.bar(x - 0.2, avg["sens"], 0.38, label="민감도(≥10)", color="#8f83ed")
    ax.bar(x + 0.2, avg["kappa"], 0.38, label="quadratic κ", color="#e07a5f")
    ax.set_xticks(x)
    ax.set_xticklabels(avg.index, rotation=30, ha="right", fontsize=8)
    ax.axvspan(-0.5, 0.5, color="gold", alpha=0.15)  # q3 수면 강조
    ax.set_ylim(0.7, 1.0)
    ax.set_ylabel("3집단 평균")
    ax.set_title("세 번째 고정 문항 선택에 따른 성능 (α=0.6)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGS / "ablation_3rd_fixed.png", dpi=150)
    plt.close(fig)
    print(f"\n저장 -> {TABLES/'ablation_3rd_fixed.csv'}, {FIGS/'ablation_3rd_fixed.png'}")


if __name__ == "__main__":
    main()

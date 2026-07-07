# -*- coding: utf-8 -*-
"""Ablation: 코어쌍(고정 2문항) 선택의 타당성 검증 (교수 피드백 3번).

세 번째 고정 문항 q3(수면)은 항상 유지하고, 코어쌍 (X, Y)를 q3를 제외한
8문항에서 C(8,2)=28조합 전수로 바꿔가며 fixed={X, Y, q3}일 때의 하이브리드
성능(κ·민감도·특이도·일치율)을 3개 데이터셋에서 비교한다.
"DSM-5 핵심 2문항(q1 흥미상실, q2 우울기분)을 다른 쌍으로 대체하면 어떻게
되는가"에 데이터로 답한다.

- 고정 = {X, Y, q3},  랜덤 풀 = 나머지 6문항에서 2개(C(6,2)=15 전수),  α=0.6
- 출력: results/tables/ablation_core_pair.csv (컬럼: pair,dataset,kappa,sens,spec,acc)
- 그림 없음. stdout에 3집단 평균 기준 민감도·κ 순위 출력.
"""
from __future__ import annotations

import itertools
from pathlib import Path

import pandas as pd

from experiment import agg, metrics_estimate
from hybrid import t_hat_weighted

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "results" / "tables"

Q_COLS = [f"q{i}" for i in range(1, 10)]
ALPHA = 0.6
THIRD = 2  # q3 수면: 항상 세 번째 고정
CANDIDATES = [i for i in range(9) if i != THIRD]  # 코어쌍 후보 8문항
PAIRS = list(itertools.combinations(CANDIDATES, 2))  # C(8,2)=28

DATASETS = [("nhanes", "NHANES(미국)"), ("zenodo", "Zenodo(중국)"), ("knhanes", "KNHANES(한국)")]


def pair_label(pair) -> str:
    return "+".join(f"q{i + 1}" for i in pair)


def load(name):
    df = pd.read_csv(PROCESSED / f"{name}_phq9.csv")
    df = df[df["complete"]].copy()
    return df[Q_COLS].to_numpy(float), df["total"].to_numpy(float)


def evaluate(items, total, pair):
    """고정={X, Y, q3}, 나머지 6문항에서 2개 전수 → 15쌍 평균 지표."""
    fixed_idx = list(pair) + [THIRD]
    pool = [i for i in range(9) if i not in fixed_idx]
    fixed_sum = items[:, fixed_idx].sum(1)
    rows = []
    for rnd in itertools.combinations(pool, 2):
        random_sum = items[:, list(rnd)].sum(1)
        est = t_hat_weighted(fixed_sum, random_sum, ALPHA)
        rows.append(metrics_estimate(est, total))
    return agg(rows)


def main():
    TABLES.mkdir(parents=True, exist_ok=True)

    records = []
    data = {name: load(name) for name, _ in DATASETS}
    for pair in PAIRS:
        for name, label in DATASETS:
            items, total = data[name]
            m = evaluate(items, total, pair)
            records.append({
                "pair": pair_label(pair), "dataset": label,
                "kappa": round(m["kappa_mean"], 3), "sens": round(m["sens_mean"], 3),
                "spec": round(m["spec_mean"], 3), "acc": round(m["acc_mean"], 3),
            })
    df = pd.DataFrame(records)
    df.to_csv(TABLES / "ablation_core_pair.csv", index=False)

    # 3집단 평균으로 랭킹
    avg = df.groupby("pair")[["kappa", "sens", "spec", "acc"]].mean().round(3)
    avg = avg.reindex([pair_label(p) for p in PAIRS])
    print("=== 코어쌍(고정 2문항)별 3집단 평균 (q3 수면 고정 유지, α=0.6) ===")
    print(avg.to_string())
    print()

    by_sens = avg.sort_values("sens", ascending=False)
    by_kappa = avg.sort_values("kappa", ascending=False)
    print("민감도 순위:")
    for rank, (lab, row) in enumerate(by_sens.iterrows(), 1):
        print(f"  {rank:2d}. {lab:7s} sens={row['sens']:.3f} κ={row['kappa']:.3f} acc={row['acc']:.3f}")
    print()
    print("κ 순위:")
    for rank, (lab, row) in enumerate(by_kappa.iterrows(), 1):
        print(f"  {rank:2d}. {lab:7s} κ={row['kappa']:.3f} sens={row['sens']:.3f} acc={row['acc']:.3f}")

    base = "q1+q2"
    sens_rank = by_sens.index.get_loc(base) + 1
    kappa_rank = by_kappa.index.get_loc(base) + 1
    print(f"\n{base} (DSM-5 핵심쌍): 민감도 {sens_rank}위 / {len(PAIRS)}, κ {kappa_rank}위 / {len(PAIRS)}")
    print(f"\n저장 -> {TABLES / 'ablation_core_pair.csv'}")


if __name__ == "__main__":
    main()

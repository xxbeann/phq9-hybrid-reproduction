"""Monte-Carlo (exhaustive) validation of the PHQ-9 hybrid short-form.

Because the random block draws 2 of 6 items, there are only C(6,2)=15 possible
random pairs. We enumerate ALL of them (exhaustive, deterministic) and report
mean +/- std across pairs -- that spread IS the "rotation variance".

Outputs:
    results/tables/alpha_sweep.csv          metrics vs alpha (0.50..0.90)
    results/tables/estimator_comparison.csv hybrid vs baselines at best alpha
    results/figures/alpha_sweep.png
    results/figures/estimator_comparison.png
    results/RESULTS.md                       human-readable summary
"""
from __future__ import annotations

import itertools
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import cohen_kappa_score

from hybrid import (
    FIXED_IDX,
    PROBABLE_CUT,
    RANDOM_POOL,
    SEVERITY_LABELS,
    classify,
    hybrid_score,
    probable,
    t_hat_block,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "nhanes_phq9.csv"
TABLES = ROOT / "results" / "tables"
FIGS = ROOT / "results" / "figures"
RESULTS_MD = ROOT / "results" / "RESULTS.md"

Q_COLS = [f"q{i}" for i in range(1, 10)]
ALPHAS = np.round(np.arange(0.50, 0.901, 0.05), 2)
RANDOM_PAIRS = list(itertools.combinations(RANDOM_POOL, 2))  # 15 pairs


# --------------------------------------------------------------------------- #
# metrics
# --------------------------------------------------------------------------- #
def sens_spec(pred_pos: np.ndarray, true_pos: np.ndarray) -> tuple[float, float]:
    pred_pos = pred_pos.astype(bool)
    true_pos = true_pos.astype(bool)
    tp = int(np.sum(pred_pos & true_pos))
    fn = int(np.sum(~pred_pos & true_pos))
    tn = int(np.sum(~pred_pos & ~true_pos))
    fp = int(np.sum(pred_pos & ~true_pos))
    sens = tp / (tp + fn) if (tp + fn) else float("nan")
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    return sens, spec


def metrics_estimate(est_total: np.ndarray, gt_total: np.ndarray) -> dict:
    gt_cls = classify(gt_total)
    est_cls = classify(est_total)
    acc = float(np.mean(est_cls == gt_cls))
    kappa = float(cohen_kappa_score(gt_cls, est_cls, weights="quadratic", labels=[0, 1, 2, 3, 4]))
    pear = float(pearsonr(est_total, gt_total)[0])
    spear = float(spearmanr(est_total, gt_total)[0])
    sens, spec = sens_spec(probable(est_total), probable(gt_total))
    return {"acc": acc, "kappa": kappa, "pearson": pear, "spearman": spear, "sens": sens, "spec": spec}


def agg(rows: list[dict]) -> dict:
    """Mean/std across pairs for each metric."""
    out = {}
    for k in rows[0]:
        vals = np.array([r[k] for r in rows], dtype=float)
        out[f"{k}_mean"] = float(np.mean(vals))
        out[f"{k}_std"] = float(np.std(vals))
    return out


# --------------------------------------------------------------------------- #
# experiment steps
# --------------------------------------------------------------------------- #
def load() -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(DATA)
    df = df[df["complete"]].copy()
    items = df[Q_COLS].to_numpy(dtype=float)
    total = df["total"].to_numpy(dtype=float)
    return items, total


def alpha_sweep(items: np.ndarray, total: np.ndarray) -> pd.DataFrame:
    records = []
    for alpha in ALPHAS:
        rows = [metrics_estimate(hybrid_score(items, pair, alpha, "weighted"), total)
                for pair in RANDOM_PAIRS]
        rec = {"alpha": float(alpha), **agg(rows)}
        records.append(rec)
    return pd.DataFrame(records)


def estimator_comparison(items: np.ndarray, total: np.ndarray, best_alpha: float) -> pd.DataFrame:
    fixed = list(FIXED_IDX)
    rows = []

    # 1) hybrid @ best alpha (mean over 15 rotation pairs) — a=0.6 is the equal-weight design
    m = agg([metrics_estimate(hybrid_score(items, p, best_alpha, "weighted"), total) for p in RANDOM_PAIRS])
    name = "hybrid-equal" if abs(best_alpha - 0.6) < 1e-9 else "hybrid-weighted"
    rows.append({"method": f"{name} (a={best_alpha}, rotating)", **m})

    # 2) hybrid block-unbiased (mean over 15 pairs)
    m = agg([metrics_estimate(t_hat_block(items[:, fixed].sum(1), items[:, list(p)].sum(1)), total)
             for p in RANDOM_PAIRS])
    rows.append({"method": "hybrid-block (rotating)", **m})

    # 3) fixed-5 (no rotation): fixed core + items q4,q5 held constant
    m = metrics_estimate(hybrid_score(items, (3, 4), best_alpha, "weighted"), total)
    rows.append({"method": "fixed-5 (no rotation)", **{f"{k}_mean": v for k, v in m.items()},
                 **{f"{k}_std": 0.0 for k in m}})

    # 4) random-5 (no fixed core): any 5 of 9, scaled x9/5 (126 combos)
    r5 = []
    for combo in itertools.combinations(range(9), 5):
        est = items[:, list(combo)].sum(1) * (9.0 / 5.0)
        r5.append(metrics_estimate(est, total))
    rows.append({"method": "random-5 (no core)", **agg(r5)})

    # 5) PHQ-8 (drop item 9), standard reference (near-ceiling)
    est8 = items[:, :8].sum(1)  # 0..24, standard cutoffs
    m = metrics_estimate(est8, total)
    rows.append({"method": "PHQ-8", **{f"{k}_mean": v for k, v in m.items()}, **{f"{k}_std": 0.0 for k in m}})

    # 6) PHQ-2 (items 1-2) -- screener only; report screen sens/spec at >=3 vs full >=10
    phq2 = items[:, :2].sum(1)
    sens, spec = sens_spec((phq2 >= 3).astype(int), probable(total))
    pear = float(pearsonr(phq2, total)[0])
    spear = float(spearmanr(phq2, total)[0])
    row = {"method": "PHQ-2 (screen >=3)", "acc_mean": float("nan"), "acc_std": 0.0,
           "kappa_mean": float("nan"), "kappa_std": 0.0, "pearson_mean": pear, "pearson_std": 0.0,
           "spearman_mean": spear, "spearman_std": 0.0, "sens_mean": sens, "sens_std": 0.0,
           "spec_mean": spec, "spec_std": 0.0}
    rows.append(row)

    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# plots
# --------------------------------------------------------------------------- #
def plot_alpha_sweep(sweep: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for metric, color in [("acc", "#8f83ed"), ("kappa", "#e07a5f"), ("pearson", "#3d9a74")]:
        mean = sweep[f"{metric}_mean"]
        std = sweep[f"{metric}_std"]
        ax.plot(sweep["alpha"], mean, marker="o", label=metric, color=color)
        ax.fill_between(sweep["alpha"], mean - std, mean + std, alpha=0.15, color=color)
    ax.axvline(0.6, ls="--", color="gray", lw=1, label="alpha=0.6 (neutral)")
    ax.set_xlabel("alpha (weight on fixed block)")
    ax.set_ylabel("metric (mean +/- std over 15 rotation pairs)")
    ax.set_title("Hybrid PHQ-9: metric vs alpha")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGS / "alpha_sweep.png", dpi=150)
    plt.close(fig)


def plot_comparison(comp: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    metric = "acc_mean"
    sub = comp.dropna(subset=[metric])
    y = np.arange(len(sub))
    ax.barh(y, sub[metric], xerr=sub["acc_std"], color="#8f83ed")
    ax.set_yticks(y)
    ax.set_yticklabels(sub["method"], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("classification accuracy vs full 9-item PHQ-9")
    ax.set_title("Estimator comparison")
    fig.tight_layout()
    fig.savefig(FIGS / "estimator_comparison.png", dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
def write_results(items, total, sweep, comp, best_alpha) -> None:
    dist = pd.Series(classify(total)).value_counts().sort_index()
    dist_lines = "\n".join(
        f"| {SEVERITY_LABELS[i]} | {int(dist.get(i, 0)):,} | {dist.get(i, 0) / len(total) * 100:.1f}% |"
        for i in range(5)
    )
    best = sweep.loc[sweep["acc_mean"].idxmax()]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    md = f"""# 실험 결과

_생성: {ts}_

## 데이터
- NHANES DPQ (PHQ-9 item-level), 9문항 완응답자: **N = {len(total):,}**
- 정답 분류 분포 (표준 PHQ-9 컷):

| 중증도 | N | 비율 |
|---|---|---|
{dist_lines}

- (주의) NHANES 표본가중치 미적용 — 측정 일치도 검증이 목적이라 비가중 분석. 한계에 명시.

## 1) alpha 스윕 (하이브리드 가중평균 추정량, 15개 회전쌍 평균)

- **최적 alpha = {best['alpha']:.2f}** (분류 일치율 최대)
- 최적점 성능: 일치율 **{best['acc_mean'] * 100:.1f}%** (±{best['acc_std'] * 100:.1f}), quadratic κ **{best['kappa_mean']:.3f}**, Pearson r **{best['pearson_mean']:.3f}**, 민감도 **{best['sens_mean']:.3f}**, 특이도 **{best['spec_mean']:.3f}**
- alpha=0.6(중립) 대비 danjam 초기값 0.7의 위치는 `results/tables/alpha_sweep.csv` 참고
- 그래프: `results/figures/alpha_sweep.png`

## 2) 추정량 비교 (best alpha 기준)

표: `results/tables/estimator_comparison.csv` / 그래프: `results/figures/estimator_comparison.png`

| 방법 | 일치율 | quad κ | Pearson r | 민감도 | 특이도 |
|---|---|---|---|---|---|
"""
    for _, r in comp.iterrows():
        def f(x):
            return "-" if pd.isna(x) else f"{x:.3f}"
        md += (f"| {r['method']} | {f(r['acc_mean'])} | {f(r['kappa_mean'])} | "
               f"{f(r['pearson_mean'])} | {f(r['sens_mean'])} | {f(r['spec_mean'])} |\n")

    md += """
## 해석 메모 (초안)
- 하이브리드(회전)가 고정5 대비 얼마나 견고한지, 랜덤5(코어 없음) 대비 고정 코어의 이득이 있는지 위 표에서 확인.
- PHQ-8은 8/9 문항이라 near-ceiling 참조값. PHQ-2는 스크리닝 민감도/특이도만 의미.
- 회전 분산(±std)이 작을수록 "매번 문항이 바뀌어도 결과가 안정적"이라는 근거.
"""
    RESULTS_MD.write_text(md, encoding="utf-8")


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    items, total = load()
    print(f"Loaded N={len(total):,} complete 9-item responses")

    sweep = alpha_sweep(items, total)
    sweep.to_csv(TABLES / "alpha_sweep.csv", index=False)
    best_alpha = float(sweep.loc[sweep["acc_mean"].idxmax(), "alpha"])
    print(f"Best alpha = {best_alpha} (acc={sweep['acc_mean'].max():.4f})")

    comp = estimator_comparison(items, total, best_alpha)
    comp.to_csv(TABLES / "estimator_comparison.csv", index=False)

    plot_alpha_sweep(sweep)
    plot_comparison(comp)
    write_results(items, total, sweep, comp, best_alpha)

    print("Done. See results/RESULTS.md")


if __name__ == "__main__":
    main()

"""Cross-dataset replication of the hybrid PHQ-9 validation.

Runs the SAME alpha-sweep + estimator comparison on every available dataset
(NHANES / Zenodo / KNHANES) and asks: does the result replicate across
different populations (US adults / Chinese students / Korean adults)?

Reuses the estimator and metric logic from experiment.py.

Outputs:
    results/tables/crossval_summary.csv        one row per dataset (hybrid @ best alpha)
    results/tables/alpha_sweep_<name>.csv      per-dataset sweep
    results/figures/crossval_alpha_kappa.png   kappa-vs-alpha overlaid across datasets
    results/CROSSVAL.md                        summary write-up
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiment import ALPHAS, alpha_sweep, estimator_comparison
from hybrid import SEVERITY_LABELS, classify

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "results" / "tables"
FIGS = ROOT / "results" / "figures"
CROSSVAL_MD = ROOT / "results" / "CROSSVAL.md"

Q_COLS = [f"q{i}" for i in range(1, 10)]

# name -> (processed csv, human label). Missing files are skipped gracefully.
DATASETS = [
    ("nhanes", "nhanes_phq9.csv", "NHANES (US adults)"),
    ("zenodo", "zenodo_phq9.csv", "Zenodo (Chinese students)"),
    ("knhanes", "knhanes_phq9.csv", "KNHANES (Korean adults)"),
]

COLORS = {"nhanes": "#8f83ed", "zenodo": "#e07a5f", "knhanes": "#3d9a74"}


def load(path: Path):
    df = pd.read_csv(path)
    df = df[df["complete"]].copy()
    return df[Q_COLS].to_numpy(float), df["total"].to_numpy(float)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    available = [(n, PROCESSED / f, lbl) for n, f, lbl in DATASETS if (PROCESSED / f).exists()]
    if not available:
        raise SystemExit("No processed datasets found. Run the download scripts first.")

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    summary = []
    prev_lines = []

    for name, path, label in available:
        items, total = load(path)
        n = len(total)
        sweep = alpha_sweep(items, total)
        sweep.to_csv(TABLES / f"alpha_sweep_{name}.csv", index=False)

        best_alpha = float(sweep.loc[sweep["kappa_mean"].idxmax(), "alpha"])  # select by kappa
        best = sweep.loc[sweep["kappa_mean"].idxmax()]
        comp = estimator_comparison(items, total, best_alpha)
        hybrid_row = comp.iloc[0]  # hybrid-weighted @ best alpha

        # prevalence of probable depression (>=10) for context
        prob_rate = float(np.mean(total >= 10))

        summary.append({
            "dataset": label, "N": n, "prob_dep_%": round(prob_rate * 100, 1),
            "best_alpha_by_kappa": best_alpha,
            "acc": round(float(best["acc_mean"]), 3), "acc_std": round(float(best["acc_std"]), 3),
            "kappa": round(float(best["kappa_mean"]), 3),
            "pearson": round(float(best["pearson_mean"]), 3),
            "sens": round(float(best["sens_mean"]), 3),
            "spec": round(float(best["spec_mean"]), 3),
        })

        ax.plot(sweep["alpha"], sweep["kappa_mean"], marker="o",
                label=f"{label} (N={n:,})", color=COLORS.get(name, "gray"))
        ax.fill_between(sweep["alpha"], sweep["kappa_mean"] - sweep["kappa_std"],
                        sweep["kappa_mean"] + sweep["kappa_std"], alpha=0.12,
                        color=COLORS.get(name, "gray"))
        prev_lines.append((label, comp))

    ax.axvline(0.6, ls="--", color="gray", lw=1)
    ax.set_xlabel("alpha (weight on fixed block)")
    ax.set_ylabel("quadratic weighted kappa (mean +/- std)")
    # 제목 생략 — 그림 설명은 논문 캡션(그림 4-3)이 담당
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGS / "crossval_alpha_kappa.png", dpi=150)
    plt.close(fig)

    summ = pd.DataFrame(summary)
    summ.to_csv(TABLES / "crossval_summary.csv", index=False)

    # write-up
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = [f"# 교차검증 결과 (다집단 재현)\n", f"_생성: {ts}_\n",
          "동일한 하이브리드 파이프라인을 서로 다른 집단에 적용해 재현성을 확인한다.\n",
          "## 요약 (하이브리드 가중평균 추정량, α는 κ 최대 기준)\n",
          "| 데이터셋 | N | 우울의심(≥10) | best α | 일치율 | quad κ | Pearson r | 민감도 | 특이도 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in summary:
        md.append(f"| {r['dataset']} | {r['N']:,} | {r['prob_dep_%']}% | {r['best_alpha_by_kappa']:.2f} "
                  f"| {r['acc']:.3f}±{r['acc_std']:.3f} | {r['kappa']:.3f} | {r['pearson']:.3f} "
                  f"| {r['sens']:.3f} | {r['spec']:.3f} |")
    md += ["\n## 해석 메모",
           "- best α가 집단마다 비슷한 값(0.6 근방)으로 수렴하는지 → 파라미터 안정성 근거.",
           "- κ·r이 집단을 넘어 일관되게 높으면 → 특정 표본에 과적합된 결과가 아님(재현성).",
           "- 우울 유병률(≥10)이 집단마다 다른데도 성능이 유지되면 → 분포 강건성.",
           "- 그래프: `results/figures/crossval_alpha_kappa.png`\n"]
    CROSSVAL_MD.write_text("\n".join(md), encoding="utf-8")

    print(summ.to_string(index=False))
    print(f"\nSaved -> {CROSSVAL_MD}")


if __name__ == "__main__":
    main()

"""Re-plot Figure 4-1 (alpha sweep) from the saved CSV — no recomputation.

Professor feedback #2: the legend should explain what "acc" means.
Reads results/tables/alpha_sweep.csv and redraws results/figures/alpha_sweep.png
with Korean metric definitions in the legend. Visual elements (colors, error
bands, markers), figsize (7 x 4.5) and dpi (150) are kept identical to the
original plot_alpha_sweep() in experiment.py, so the PNG stays 1050 x 675 px.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.family"] = ["AppleGothic", "Apple SD Gothic Neo", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "tables" / "alpha_sweep.csv"
OUT = ROOT / "results" / "figures" / "alpha_sweep.png"

# Same series/colors as experiment.py plot_alpha_sweep(); legend now defines
# each metric (professor feedback #2: what does "acc" mean?).
SERIES = [
    ("acc", "#8f83ed", "acc: 5등급 중증도 분류 일치율(전체 9문항 대비)"),
    ("kappa", "#e07a5f", "quadratic κ: 가중 일치도"),
    ("pearson", "#3d9a74", "Pearson r: 총점 상관"),
]


def main() -> None:
    sweep = pd.read_csv(CSV)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for metric, color, label in SERIES:
        mean = sweep[f"{metric}_mean"]
        std = sweep[f"{metric}_std"]
        ax.plot(sweep["alpha"], mean, marker="o", label=label, color=color)
        ax.fill_between(sweep["alpha"], mean - std, mean + std, alpha=0.15, color=color)
    ax.axvline(0.6, ls="--", color="gray", lw=1, label="α=0.6 (5문항 동일가중)")
    ax.set_xlabel("α (고정 블록 가중)")
    ax.set_ylabel("metric (mean +/- std over 15 rotation pairs)")
    ax.set_title("Hybrid PHQ-9: metric vs alpha")
    # Longer Korean labels make loc="best" cover the acc line around
    # alpha 0.75-0.80; pin to the empty lower-left corner instead.
    ax.legend(loc="lower left", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT, dpi=150)
    plt.close(fig)
    print(f"saved: {OUT}")


if __name__ == "__main__":
    main()

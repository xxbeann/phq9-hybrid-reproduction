# -*- coding: utf-8 -*-
"""그림 4-2(estimator comparison) 재작도 — v18.

표 4-2의 행명이 'hybrid-equal (동일가중 α=0.6)'로 개명되었는데 그림 막대 라벨은
구명칭 'hybrid-weighted'로 남아 표-그림 명칭이 어긋났다(레드팀 지적). 결과 수치는
그대로 두고 CSV의 method 라벨만 갱신한 뒤 동일 스타일로 다시 그린다.

실행: cd experiment && rye run python src/replot_comparison.py
산출: results/figures/estimator_comparison.png (논문/media/image7.png로 복사해 사용)
"""
import pandas as pd

from experiment import TABLES, plot_comparison

OLD = "hybrid-weighted (a=0.6, rotating)"
NEW = "hybrid-equal (a=0.6, rotating)"

path = TABLES / "estimator_comparison.csv"
comp = pd.read_csv(path)
assert (comp["method"] == OLD).any() or (comp["method"] == NEW).any(), "대상 행 없음"
comp.loc[comp["method"] == OLD, "method"] = NEW
comp.to_csv(path, index=False)
plot_comparison(comp)
print("figure replotted; methods:", ", ".join(comp["method"].astype(str)))

# -*- coding: utf-8 -*-
"""시스템 성능 실측: 제안 추정량 T̂의 3집단 전수 처리 성능(논문 시스템 성능 평가 절, item 1).

측정 대상 = 세 공개 집단(NHANES·Zenodo·KNHANES)의 complete 응답 전수에 대해
15개 회전쌍(고정3+랜덤2) 전수 하이브리드 추정·중증도 분류를 수행하는 처리량·시간·메모리.
T̂는 사칙연산 7회(O(1))라 모델·서버가 불요함을 정량적으로 보인다.

실행: cd experiment && rye run python src/perf_bench.py
"""
from __future__ import annotations

import itertools
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
Q = [f"q{i}" for i in range(1, 10)]
FIXED = (0, 1, 2)
RANDOM_POOL = (3, 4, 5, 6, 7, 8)
EDGES = [5, 10, 15, 20]


def load_all() -> np.ndarray:
    frames, loaded = [], []
    for name in ["nhanes_phq9.csv", "zenodo_phq9.csv", "knhanes_phq9.csv"]:
        path = PROCESSED / name
        if not path.exists():  # 공개 저장소는 KNHANES 마이크로데이터 제외(이용약관) → 건너뜀
            print(f"(건너뜀: {name} 없음)")
            continue
        df = pd.read_csv(path)
        df = df[df["complete"]].copy()
        frames.append(df)
        loaded.append(name.split("_")[0])
    df = pd.concat(frames, ignore_index=True)
    print(f"로드 집단: {', '.join(loaded)}")
    return df[Q].to_numpy(dtype=np.int16), df["total"].to_numpy(dtype=np.int16)


def main() -> None:
    items, total = load_all()
    n = len(items)
    rotations = list(itertools.combinations(RANDOM_POOL, 2))
    gt_level = np.digitize(total, EDGES)
    fixed_sum = items[:, FIXED].sum(axis=1)

    # --- 전수 처리 시간 측정(15회전 × N 사용자) ---
    tracemalloc.start()
    t0 = time.perf_counter()
    agree_total = 0
    for rot in rotations:
        five_sum = fixed_sum + items[:, list(rot)].sum(axis=1)
        t_hat = 9.0 * five_sum / 5.0
        est_level = np.digitize(t_hat, EDGES)
        agree_total += int((est_level == gt_level).sum())
    elapsed = time.perf_counter() - t0
    cur, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    n_eval = n * len(rotations)
    # --- 단일 추정 지연(O(1) 근거): 벡터화 없이 1건 산술 반복 ---
    t1 = time.perf_counter()
    REP = 200_000
    fs = int(fixed_sum[0]); a = int(items[0, 3]); b = int(items[0, 4])
    for _ in range(REP):
        th = 9.0 * (fs + a + b) / 5.0
        _ = 0 + (th >= 5) + (th >= 10) + (th >= 15) + (th >= 20)
    per_est_ns = (time.perf_counter() - t1) / REP * 1e9

    print(f"집단 3개 complete 전수 N = {n:,}명")
    print(f"전수 평가 = {n:,} × 회전 {len(rotations)} = {n_eval:,} 추정·분류")
    print(f"소요 시간 = {elapsed*1000:.1f} ms  (처리량 {n_eval/elapsed/1e6:.1f}M 추정/s, {n/elapsed/1e6:.2f}M 사용자/s)")
    print(f"피크 추가 메모리(tracemalloc) = {peak/1e6:.2f} MB")
    print(f"단일 추정 지연(비벡터화 산술) ≈ {per_est_ns:.0f} ns  (T̂ 7 사칙연산, O(1))")
    print(f"검증용 평균 등급 일치율 = {agree_total/n_eval:.3f}")


if __name__ == "__main__":
    main()

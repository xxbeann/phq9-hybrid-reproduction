"""KNHANES(국민건강영양조사) 기본DB에서 PHQ-9 문항을 추출·정규화한다.

기본DB(HNYR_ALL) 내 변수:
    BP_PHQ_1 .. BP_PHQ_9  -> PHQ-9 9개 문항 (0~3점; 8=비해당, 9=모름/무응답 -> 결측)
    mh_PHQ_S              -> 총점(검증용, 문항 합과 일치 확인됨)

PHQ-9 수록 연도(만 19세 이상): 2014, 2016, 2018, 2020.
출력: data/processed/knhanes_phq9.csv  (스키마: seqn, cycle, q1..q9, total, complete)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadstat

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

YEARS = {"hn14": "knhanes-2014", "hn16": "knhanes-2016",
         "hn18": "knhanes-2018", "hn20": "knhanes-2020"}
SRC = [f"BP_PHQ_{i}" for i in range(1, 10)]
Q_COLS = [f"q{i}" for i in range(1, 10)]


def load_year(tag: str, label: str) -> pd.DataFrame:
    path = RAW / f"{tag}_all.sas7bdat"
    cols = SRC + ["mh_PHQ_S"]
    id_col = "ID" if False else None  # KNHANES id varies; use running index instead
    df, _ = pyreadstat.read_sas7bdat(str(path), usecols=cols)
    out = df[SRC].rename(columns=dict(zip(SRC, Q_COLS))).copy()
    for c in Q_COLS:
        out[c] = out[c].where(out[c].isin([0, 1, 2, 3]))  # 8/9/NaN -> 결측
    out["cycle"] = label
    out["seqn"] = [f"{tag}-{i}" for i in range(len(out))]
    return out


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    frames = []
    for tag, label in YEARS.items():
        f = RAW / f"{tag}_all.sas7bdat"
        if not f.exists():
            print(f"[warn] 없음: {f.name}")
            continue
        frames.append(load_year(tag, label))
        print(f"[ok ] {label}")

    df = pd.concat(frames, ignore_index=True)
    df["complete"] = df[Q_COLS].notna().all(axis=1)
    df["total"] = df[Q_COLS].sum(axis=1, min_count=9)
    df = df[["seqn", "cycle"] + Q_COLS + ["total", "complete"]]

    out = PROCESSED / "knhanes_phq9.csv"
    df.to_csv(out, index=False)
    print(f"\n전체 {len(df):,}행, 완응답 {int(df['complete'].sum()):,}명")
    print(f"저장 -> {out}")


if __name__ == "__main__":
    main()

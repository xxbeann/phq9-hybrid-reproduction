"""Download the Zenodo (Su et al. 2024) PHQ-9 dataset and normalise it.

Record: https://zenodo.org/records/10423537  (CC-BY-4.0)
phq9.csv columns: export_id, score, question1..question9, time1..time9

Output: data/processed/zenodo_phq9.csv  with columns
    seqn, cycle, q1..q9, total, complete   (schema matches nhanes_phq9.csv)
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
URL = "https://zenodo.org/api/records/10423537/files/phq9.csv/content"

Q_SRC = [f"question{i}" for i in range(1, 10)]
Q_COLS = [f"q{i}" for i in range(1, 10)]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    raw = RAW / "zenodo_phq9.csv"
    if not raw.exists():
        print(f"[get ] {URL}")
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (research)"})
        with urllib.request.urlopen(req, timeout=90) as r:
            raw.write_bytes(r.read())
    df = pd.read_csv(raw)

    out = df[["export_id"] + Q_SRC].rename(
        columns={"export_id": "seqn", **dict(zip(Q_SRC, Q_COLS))}
    )
    for c in Q_COLS:
        out[c] = out[c].where(out[c].isin([0, 1, 2, 3]))
    out["cycle"] = "zenodo-2021"
    out["complete"] = out[Q_COLS].notna().all(axis=1)
    out["total"] = out[Q_COLS].sum(axis=1, min_count=9)

    # sanity check against the provided total
    provided = df["score"].to_numpy()
    mismatch = int((out["total"].to_numpy() != provided).sum())
    print(f"provided-score vs recomputed-total mismatches: {mismatch}")

    dest = PROCESSED / "zenodo_phq9.csv"
    out.to_csv(dest, index=False)
    print(f"Complete 9-item responses: {int(out['complete'].sum()):,}")
    print(f"Saved -> {dest}")


if __name__ == "__main__":
    main()

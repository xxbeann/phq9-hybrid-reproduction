"""Download NHANES DPQ (PHQ-9 item-level) cycles and consolidate to a clean CSV.

NHANES DPQ variables:
    DPQ010..DPQ090  -> the 9 PHQ-9 symptom items (0..3; 7=Refused, 9=Don't know)
    DPQ100          -> functional-impairment item (NOT part of the 0..27 total)

Output: data/processed/nhanes_phq9.csv  with columns
    seqn, cycle, q1..q9, total, complete
"""
from __future__ import annotations

import io
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

# (cycle label, filename, download URL)
CYCLES = [
    ("2013-2014", "DPQ_H", "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2013/DataFiles/DPQ_H.xpt"),
    ("2015-2016", "DPQ_I", "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2015/DataFiles/DPQ_I.xpt"),
    ("2017-2018", "DPQ_J", "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DPQ_J.xpt"),
    ("2021-2023", "DPQ_L", "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DPQ_L.xpt"),
]

ITEM_COLS = [f"DPQ0{i}0" for i in range(1, 10)]  # DPQ010..DPQ090
Q_COLS = [f"q{i}" for i in range(1, 10)]


def download(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"  [skip] {dest.name} already present")
        return
    print(f"  [get ] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    dest.write_bytes(data)
    print(f"        saved {len(data):,} bytes -> {dest}")


def load_cycle(label: str, path: Path) -> pd.DataFrame:
    # NHANES .xpt is SAS transport format; pandas reads it natively.
    df = pd.read_sas(io.BytesIO(path.read_bytes()), format="xport")
    keep = ["SEQN"] + ITEM_COLS
    df = df[[c for c in keep if c in df.columns]].copy()
    df = df.rename(columns={"SEQN": "seqn", **dict(zip(ITEM_COLS, Q_COLS))})
    # NHANES .xpt encodes SAS numeric 0 as a tiny denormalized float (~5.4e-79);
    # round to the nearest integer, then keep only valid 0..3 (7=Refused, 9=Don't know -> NaN).
    for c in Q_COLS:
        v = df[c].round()
        df[c] = v.where(v.isin([0, 1, 2, 3]))
    df["cycle"] = label
    return df


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    frames = []
    print("Downloading NHANES DPQ cycles:")
    for label, name, url in CYCLES:
        dest = RAW / f"{name}.xpt"
        try:
            download(url, dest)
            frames.append(load_cycle(label, dest))
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] {name} failed: {e}")

    if not frames:
        raise SystemExit("No cycles downloaded — check network / URLs.")

    df = pd.concat(frames, ignore_index=True)
    df["complete"] = df[Q_COLS].notna().all(axis=1)
    df["total"] = df[Q_COLS].sum(axis=1, min_count=9)  # NaN unless all 9 present

    out = PROCESSED / "nhanes_phq9.csv"
    df.to_csv(out, index=False)

    n_all = len(df)
    n_complete = int(df["complete"].sum())
    print(f"\nConsolidated {n_all:,} rows across {df['cycle'].nunique()} cycles")
    print(f"Complete 9-item responses: {n_complete:,}")
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()

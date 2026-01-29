import argparse
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail_csv", required=True, help="Path to RQ2_failure_cases.csv")
    ap.add_argument("--out_dir", default="rq2_out", help="Output folder")
    args = ap.parse_args()

    fail_csv = Path(args.fail_csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(fail_csv)

    # failure_type order: by overall frequency (for consistent legend)
    type_order = df["failure_type"].value_counts().index.tolist()

    # model × type counts
    model_type_counts = df.groupby(["model", "failure_type"]).size().unstack(fill_value=0)
    for t in type_order:
        if t not in model_type_counts.columns:
            model_type_counts[t] = 0
    model_type_counts = model_type_counts[type_order]

    # model × type percentage (row sums to 100)
    model_totals = model_type_counts.sum(axis=1)
    model_type_pct = model_type_counts.div(model_totals, axis=0) * 100

    # overall distribution
    overall_counts = df["failure_type"].value_counts().reindex(type_order)
    overall_pct = overall_counts / overall_counts.sum() * 100

    out_counts = out_dir / "RQ2_model_x_type_counts.csv"
    out_pct = out_dir / "RQ2_model_x_type_pct.csv"
    out_overall = out_dir / "RQ2_overall_type_dist.csv"

    model_type_counts.reset_index().to_csv(out_counts, index=False)
    model_type_pct.reset_index().to_csv(out_pct, index=False)

    overall_df = pd.DataFrame({
        "failure_type": overall_counts.index,
        "count": overall_counts.values,
        "pct": overall_pct.round(4).values
    })
    overall_df.to_csv(out_overall, index=False)

    print("Saved:")
    print(" -", out_counts)
    print(" -", out_pct)
    print(" -", out_overall)
    print("Type order:", type_order)


if __name__ == "__main__":
    main()

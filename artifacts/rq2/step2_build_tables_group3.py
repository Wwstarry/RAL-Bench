import argparse
from pathlib import Path
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail_group3_csv", required=True, help="Path to RQ2_failure_cases_group3.csv")
    ap.add_argument("--out_dir", default="rq2_out", help="Output folder")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.fail_group3_csv)

    col = "failure_group3_main"  # 3 classes for main figure
    # Fix ordering for legend / consistent plots
    group_order = [
        "Executability & Environment",
        "Functional Correctness",
        "Runtime Robustness & Efficiency",
    ]

    # model × group counts
    model_group_counts = df.groupby(["model", col]).size().unstack(fill_value=0)
    for g in group_order:
        if g not in model_group_counts.columns:
            model_group_counts[g] = 0
    model_group_counts = model_group_counts[group_order]

    # model × group pct
    model_totals = model_group_counts.sum(axis=1)
    model_group_pct = model_group_counts.div(model_totals, axis=0) * 100

    # overall dist
    overall_counts = df[col].value_counts().reindex(group_order).fillna(0).astype(int)
    overall_pct = overall_counts / overall_counts.sum() * 100

    out_counts = out_dir / "RQ2_model_x_group3_counts.csv"
    out_pct = out_dir / "RQ2_model_x_group3_pct.csv"
    out_overall = out_dir / "RQ2_overall_group3_dist.csv"

    model_group_counts.reset_index().to_csv(out_counts, index=False)
    model_group_pct.round(4).reset_index().to_csv(out_pct, index=False)

    overall_df = pd.DataFrame({
        "failure_group3": overall_counts.index,
        "count": overall_counts.values,
        "pct": overall_pct.round(4).values
    })
    overall_df.to_csv(out_overall, index=False)

    print("Saved:")
    print(" -", out_counts)
    print(" -", out_pct)
    print(" -", out_overall)


if __name__ == "__main__":
    main()

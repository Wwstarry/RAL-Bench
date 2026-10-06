import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pct_csv", required=True, help="RQ2_model_x_type_pct.csv")
    ap.add_argument("--counts_csv", required=True, help="RQ2_model_x_type_counts.csv")
    ap.add_argument("--overall_csv", required=True, help="RQ2_overall_type_dist.csv")
    ap.add_argument("--out_png", default="RQ2_error_breakdown.png", help="Output png path")
    args = ap.parse_args()

    pct_csv = Path(args.pct_csv)
    counts_csv = Path(args.counts_csv)
    overall_csv = Path(args.overall_csv)
    out_png = Path(args.out_png)

    df_pct = pd.read_csv(pct_csv)
    df_counts = pd.read_csv(counts_csv)
    df_overall = pd.read_csv(overall_csv)

    type_cols = [c for c in df_pct.columns if c != "model"]

    # order models by total failures (desc)
    df_counts["total_failures"] = df_counts[type_cols].sum(axis=1)
    model_order = df_counts.sort_values("total_failures", ascending=False)["model"].tolist()

    df_pct["model"] = pd.Categorical(df_pct["model"], categories=model_order, ordered=True)
    df_pct = df_pct.sort_values("model")

    overall_map = dict(zip(df_overall["failure_type"], df_overall["count"]))
    pie_counts = [overall_map.get(t, 0) for t in type_cols]

    fig = plt.figure(figsize=(14, 6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1])

    # Left: stacked horizontal bars
    ax1 = fig.add_subplot(gs[0, 0])
    left_acc = [0.0] * len(df_pct)
    for t in type_cols:
        vals = df_pct[t].values
        ax1.barh(df_pct["model"], vals, left=left_acc, label=t)
        left_acc = [l + v for l, v in zip(left_acc, vals)]

    ax1.set_xlim(0, 100)
    ax1.set_xlabel("Percentage (%)")
    ax1.set_title("Error Breakdown by Model")
    ax1.grid(axis="x", linestyle="--", linewidth=0.5, alpha=0.6)

    # Right: overall pie
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.pie(pie_counts, labels=type_cols, autopct="%1.1f%%", startangle=140)
    ax2.set_title("Overall Error Breakdown")

    # Legend at bottom (like your example)
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.02))

    plt.tight_layout()
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("Saved figure:", out_png)


if __name__ == "__main__":
    main()

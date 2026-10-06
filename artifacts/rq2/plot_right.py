import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


# ---------------------------
# Fonts
# ---------------------------
FONT_EN = "Times New Roman"
NUM_FP = FontProperties(family="Constantia", weight="bold")  # numbers (percentages)


def apply_times_new_roman():
    plt.rcParams["font.family"] = FONT_EN
    plt.rcParams["axes.unicode_minus"] = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="rq2_out", help="Directory containing group3 csv tables")
    ap.add_argument("--save", action="store_true", help="Save figure after showing it")
    ap.add_argument("--out", default="RQ2_group3_overall.png", help="Output filename inside --dir")
    ap.add_argument("--fig_h", type=float, default=7.0, help="Figure height")
    ap.add_argument("--fig_w", type=float, default=7.0, help="Figure width")
    ap.add_argument("--startangle", type=float, default=140.0, help="Pie start angle")
    args = ap.parse_args()

    apply_times_new_roman()

    d = Path(args.dir)
    overall_csv = d / "RQ2_overall_group3_dist.csv"
    df = pd.read_csv(overall_csv)

    # Fixed order + colors (match left plot)
    groups = [
        "Executability & Environment",
        "Functional Correctness",
        "Runtime Robustness & Efficiency",
    ]
    color_map = {
        "Executability & Environment": "#C3E4F5",
        "Functional Correctness": "#D9F3CE",
        "Runtime Robustness & Efficiency": "#FFF0C5",
    }

    # Reindex to ensure consistent slice order across runs
    df = df.set_index("failure_group3").reindex(groups).fillna(0).reset_index()

    labels = df["failure_group3"].tolist()
    counts = df["count"].astype(int).tolist()
    colors = [color_map[g] for g in labels]

    fig, ax = plt.subplots(figsize=(args.fig_w, args.fig_h))

    wedges, texts, autotexts = ax.pie(
        counts,
        labels=labels,
        autopct="%1.1f%%",
        startangle=args.startangle,
        colors=colors,
        wedgeprops={"edgecolor": "black", "linewidth": 0.8},  # outline
        textprops={"fontfamily": FONT_EN},  # ensure labels in Times New Roman
    )

    # Percent numbers: Constantia bold
    for t in autotexts:
        t.set_fontproperties(NUM_FP)

    ax.set_title("Overall Failure Pattern (3-Class Taxonomy)")

    plt.tight_layout()
    plt.show()

    if args.save:
        out_path = d / args.out
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        print("Saved:", out_path)


if __name__ == "__main__":
    main()

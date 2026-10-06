import argparse
from pathlib import Path
import re

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


# ---------------------------
# Fonts (Windows: usually available)
# ---------------------------
FONT_EN = "Times New Roman"
NUM_FP = FontProperties(family="Constantia", weight="bold")  # numbers


# ---------------------------
# Model abbreviation (recognizable, vendor+version oriented)
# ---------------------------
KNOWN_ABBR = {
    # OpenAI
    "gpt-4o-2024-11-20": "GPT-4o",
    "gpt-4o": "GPT-4o",
    "gpt-4-turbo": "GPT-4 Turbo",
    "gpt-4.1": "GPT-4.1",
    "gpt-5": "GPT-5",
    "gpt-5.2": "GPT-5.2",
    "gpt-3.5-turbo": "GPT-3.5 Turbo",
    "o1": "GPT-o1",
    "o3": "GPT-o3",

    # DeepSeek
    "deepseek-r1": "DeepSeek-R1",
    "deepseek-v3": "DeepSeek-V3",
    "deepseek-v3.2": "DeepSeek-V3.2",
    "deepseek-v3-0324": "DeepSeek-V3",

    # Anthropic
    "claude-4.5-sonnet": "Claude-4.5-Sonnet",
    "claude-3.7-sonnet-20250219-thinking": "Claude-3.7-Sonnet (Think)",
    "claude-4.5-haiku": "Claude-4.5-Haiku",
    "claude-3.5-sonnet": "Claude-3.5-Sonnet",
    "claude-3-opus": "Claude-3-Opus",

    # Google
    "gemini-3-pro-preview": "Gemini-3-Pro",
    "gemini-2.5-pro-thinking": "Gemini-2.5-Pro (Think)",
    "gemini-2.5-pro": "Gemini-2.5-Pro",
}


def abbreviate_model(name: str) -> str:
    """
    Produce a short, recognizable abbreviation:
    - Keep vendor + major/minor version
    - Remove dates (YYYY-MM-DD) and long suffixes (e.g., -preview)
    - Normalize casing for common vendors
    """
    if not isinstance(name, str):
        return str(name)

    key = name.strip().lower()
    if key in KNOWN_ABBR:
        return KNOWN_ABBR[key]

    s = name.strip()
    lower = s.lower()

    if lower.startswith("gpt") or lower in ["o1", "o3"]:
        vendor = "GPT"
    elif lower.startswith("claude"):
        vendor = "Claude"
    elif lower.startswith("gemini"):
        vendor = "Gemini"
    elif lower.startswith("deepseek"):
        vendor = "DeepSeek"
    else:
        vendor = s.split("-")[0].title()

    tokens = re.split(r"[-_]", lower)

    # remove vendor token
    if tokens and tokens[0] in ["gpt", "claude", "gemini", "deepseek"]:
        tokens = tokens[1:]

    cleaned = []
    for t in tokens:
        if re.fullmatch(r"\d{4}(\d{2})?(\d{2})?", t):  # 2024 or 202411 or 20241120
            continue
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
            continue
        if re.fullmatch(r"\d{3,4}", t) and ("v3" in lower or "v2" in lower):
            continue
        if t in ["preview", "latest", "stable"]:
            continue
        cleaned.append(t)

    keep = []
    for t in cleaned:
        if t in ["thinking", "think"]:
            keep.append("Think")
        elif t in ["sonnet", "haiku", "opus", "pro", "flash"]:
            keep.append(t.title())
        elif re.fullmatch(r"v\d+(\.\d+)?", t):
            keep.append(t.upper())  # V3, V3.2
        elif re.fullmatch(r"\d+(\.\d+)?", t) or re.fullmatch(r"\d+o", t):
            keep.append(t.upper() if t.endswith("o") else t)
        else:
            pass

    if not keep:
        short = re.sub(r"[-_]\d{3,}", "", name).strip()
        return short

    keep = keep[:3]
    return vendor + "-" + "-".join(keep)


# ---------------------------
# Family + within-family (version/generation) ordering
# ---------------------------
def model_family_rank(raw_name: str, abbr: str) -> int:
    """
    Group order:
      Gemini (0) -> GPT (1) -> Claude (2) -> DeepSeek (3) -> Others (99)
    """
    s = (raw_name or "").strip().lower()
    a = (abbr or "").strip().lower()

    if s.startswith("gemini") or a.startswith("gemini"):
        return 0
    if s.startswith("gpt") or s in ["o1", "o3"] or a.startswith("gpt"):
        return 1
    if s.startswith("claude") or a.startswith("claude"):
        return 2
    if s.startswith("deepseek") or a.startswith("deepseek"):
        return 3
    return 99


def _extract_first_float(text: str):
    m = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(m.group(1)) if m else None


def model_generation_rank(raw_name: str, abbr: str) -> float:
    """
    Return an orderable numeric rank INSIDE each family.
    Smaller rank = earlier/older generation; larger rank = later/newer generation.

    Designed to be stable and "internationally recognizable" without manual per-model lists.

    Rules (by family):
    - Gemini: sort by major version number (2.5 < 3), then Pro/Flash, then Thinking last.
    - GPT:    o1/o3 treated as "o-series" around GPT-4 era (custom), otherwise sort by major (3.5 < 4 < 4.1 < 4o < 5 < 5.2),
              then Turbo/mini variants, then Thinking last.
    - Claude: sort by version (3 < 3.5 < 3.7 < 4.5), then Haiku < Sonnet < Opus, Thinking last.
    - DeepSeek: sort V3 < V3.2 < R1 (R-series after V-series), and add minor if present.
    - Others: fallback by digits found.
    """
    s = (raw_name or "").strip().lower()
    a = (abbr or "").strip().lower()
    fam = model_family_rank(raw_name, abbr)

    # helper flags
    is_think = ("think" in s) or ("think" in a)
    think_bonus = 0.9 if is_think else 0.0  # push thinking variants later within same model

    # ---- Gemini ----
    if fam == 0:
        # base major: 2.5, 3
        v = _extract_first_float(s) or _extract_first_float(a) or 0.0
        # Pro vs Flash ordering: Flash earlier than Pro (often lighter), adjust if needed
        flavor = 0.0
        if "flash" in s or "flash" in a:
            flavor = 0.1
        if "pro" in s or "pro" in a:
            flavor = 0.2
        return v + flavor + think_bonus

    # ---- GPT ----
    if fam == 1:
        # special-case o-series
        if s in ["o1", "o3"] or a.startswith("gpt-o"):
            # put o-series between 4.1 and 4o by default (you can adjust)
            # o1 < o3
            base = 4.15
            if "o3" in s or "o3" in a:
                base = 4.17
            return base + think_bonus

        # detect 3.5, 4, 4.1, 5, 5.2
        v = _extract_first_float(s) or _extract_first_float(a) or 0.0

        # treat "4o" as 4.6 to place after 4.1 and before 5
        if "4o" in s or "4o" in a:
            v = 4.6

        # Turbo / mini: place slightly after base
        variant = 0.0
        if "turbo" in s or "turbo" in a:
            variant += 0.05
        if "mini" in s or "mini" in a:
            variant += 0.03
        return v + variant + think_bonus

    # ---- Claude ----
    if fam == 2:
        v = _extract_first_float(s) or _extract_first_float(a) or 0.0

        # tier ordering: Haiku < Sonnet < Opus (lighter to heavier) within same version
        tier = 0.0
        if "haiku" in s or "haiku" in a:
            tier = 0.10
        elif "sonnet" in s or "sonnet" in a:
            tier = 0.20
        elif "opus" in s or "opus" in a:
            tier = 0.30

        return v + tier + think_bonus

    # ---- DeepSeek ----
    if fam == 3:
        # V-series first, then R-series
        if "r1" in s or "r1" in a:
            return 10.0 + think_bonus  # after V-series
        # V3, V3.2 -> parse
        m = re.search(r"v(\d+(?:\.\d+)?)", s)
        if not m:
            m = re.search(r"v(\d+(?:\.\d+)?)", a)
        v = float(m.group(1)) if m else 0.0
        return v + think_bonus

    # ---- Others ----
    v = _extract_first_float(s) or _extract_first_float(a) or 0.0
    return v + think_bonus


# ---------------------------
# Formatting helpers
# ---------------------------
def apply_times_new_roman():
    plt.rcParams["font.family"] = FONT_EN
    plt.rcParams["axes.unicode_minus"] = False  # avoid minus rendering issues


def set_numeric_ticks_constantia(ax):
    for lbl in ax.get_xticklabels():
        lbl.set_fontproperties(NUM_FP)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="rq2_out", help="Directory containing group3 csv tables")
    ap.add_argument("--save", action="store_true", help="Save figure after showing it")
    ap.add_argument("--out", default="RQ2_group3_by_model.png", help="Output filename inside --dir")
    ap.add_argument("--fig_h", type=float, default=7.0, help="Figure height")
    ap.add_argument("--fig_w", type=float, default=13.0, help="Figure width")
    args = ap.parse_args()

    apply_times_new_roman()

    d = Path(args.dir)
    pct_csv = d / "RQ2_model_x_group3_pct.csv"
    counts_csv = d / "RQ2_model_x_group3_counts.csv"

    df_pct = pd.read_csv(pct_csv)
    df_counts = pd.read_csv(counts_csv)

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

    # Abbreviate model names
    df_pct["model_abbr"] = df_pct["model"].apply(abbreviate_model)
    df_counts["model_abbr"] = df_counts["model"].apply(abbreviate_model)

    # Compute sorting keys
    df_counts["family_rank"] = df_counts.apply(lambda r: model_family_rank(r["model"], r["model_abbr"]), axis=1)
    df_counts["gen_rank"] = df_counts.apply(lambda r: model_generation_rank(r["model"], r["model_abbr"]), axis=1)

    # Sort by:
    #   family order (Gemini -> GPT -> Claude -> DeepSeek)
    #   then generation/version order (older -> newer)
    #   then stable tie-break by name
    df_counts_sorted = df_counts.sort_values(
        ["family_rank", "gen_rank", "model_abbr"],
        ascending=[True, True, True]
    )

    model_order = df_counts_sorted["model_abbr"].tolist()

    df_pct["model_abbr"] = pd.Categorical(df_pct["model_abbr"], categories=model_order, ordered=True)
    df_pct = df_pct.sort_values("model_abbr")

    fig, ax = plt.subplots(figsize=(args.fig_w, args.fig_h))

    left_acc = [0.0] * len(df_pct)
    for g in groups:
        vals = df_pct[g].values
        ax.barh(
            df_pct["model_abbr"],
            vals,
            left=left_acc,
            label=g,
            color=color_map[g],
            edgecolor="black",
            linewidth=0.8,
        )
        left_acc = [l + v for l, v in zip(left_acc, vals)]

    ax.set_xlim(0, 100)
    ax.set_xlabel("Percentage (%)")
    ax.set_title("Failure Pattern by Model (3-Class Taxonomy)")
    ax.grid(axis="x", linestyle="--", linewidth=0.5, alpha=0.6)

    set_numeric_ticks_constantia(ax)

    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.02))

    plt.tight_layout()
    plt.show()

    if args.save:
        out_path = d / args.out
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        print("Saved:", out_path)


if __name__ == "__main__":

    main()

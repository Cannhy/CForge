"""
Reproduce: Decoupling Correctness and Safety: pass@1 vs. MemSafe scatter plot.

Each point = one (model, dataset) pair.
- Shape encodes the model.
- Color encodes the dataset (difficulty level).
- A dashed OLS fit line is drawn across ALL points to illustrate the weak
  correlation between functional correctness and memory safety.

Usage:
    python scripts/plot_correctness_vs_safety.py
Output:
    output/correctness_vs_safety.pdf
    output/correctness_vs_safety.png
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


# ---------------------------------------------------------------------------
# Data: (pass@1, MSC) per (model, dataset)
# Datasets use the CForge difficulty names:
#   Introductory / Easy / Medium / Hard.
# ---------------------------------------------------------------------------
DATA = {
    # model_name: {dataset_name: (pass@1, MSC)}
    "DeepSeek-V3": {
        "Introductory": (0.794, 1.000),
        "Easy":         (0.620, 0.983),
        "Medium":       (0.570, 0.904),
        "Hard":         (0.604, 0.986),
    },
    "DeepSeek-R1": {
        "Introductory": (0.933, 1.000),
        "Easy":         (0.618, 0.900),
        "Medium":       (0.736, 0.874),
        "Hard":         (0.729, 0.839),
    },
    "Qwen3.5-397B-A17B": {
        "Introductory": (0.667, 1.000),
        "Easy":         (0.599, 0.984),
        "Medium":       (0.156, 0.852),
        "Hard":         (0.141, 0.892),
    },
    "Qwen3.5-122B-A10B": {
        "Introductory": (0.490, 1.000),
        "Easy":         (0.600, 0.984),
        "Medium":       (0.152, 0.849),
        "Hard":         (0.133, 0.892),
    },
    "Qwen2.5-Coder-7B-Instruct": {
        "Introductory": (0.634, 1.000),
        "Easy":         (0.521, 0.983),
        "Medium":       (0.147, 0.928),
        "Hard":         (0.132, 0.886),
    },
    "Qwen2.5-Coder-7B-Base": {
        "Introductory": (0.579, 1.000),
        "Easy":         (0.515, 0.977),
        "Medium":       (0.136, 0.857),
        "Hard":         (0.121, 0.907),
    },
    "Qwen2.5-Coder-3B-Instruct": {
        "Introductory": (0.539, 1.000),
        "Easy":         (0.426, 0.978),
        "Medium":       (0.143, 0.874),
        "Hard":         (0.075, 0.843),
    },
}

# Marker shape for each model
MODEL_MARKER = {
    "DeepSeek-V3":               "o",   # circle
    "DeepSeek-R1":               "*",   # star
    "Qwen3.5-397B-A17B":         "P",   # plus-filled
    "Qwen3.5-122B-A10B":         "X",   # x-filled
    "Qwen2.5-Coder-7B-Instruct": "s",   # square
    "Qwen2.5-Coder-7B-Base":     "^",   # triangle up
    "Qwen2.5-Coder-3B-Instruct": "v",   # triangle down
}

# Dataset colors (green / blue / orange / red)
DATASET_COLOR = {
    "Introductory": "#4CAF50",   # green
    "Easy":         "#2F80ED",   # blue
    "Medium":       "#F2A03D",   # orange
    "Hard":         "#E04E4E",   # red
}


def main():
    os.makedirs("output", exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.set_facecolor("#FAFAFA")

    # Collect all points for the regression line
    all_x, all_y = [], []
    for model, per_ds in DATA.items():
        for ds, (p1, msc) in per_ds.items():
            all_x.append(p1)
            all_y.append(msc)

    all_x = np.array(all_x)
    all_y = np.array(all_y)

    # --- Scatter ---
    # Stars need a bit larger visual weight to match the reference figure.
    MARKER_SIZE = {
        "o": 130, "*": 230, "s": 130, "^": 150, "v": 150,
        "P": 150, "X": 150,
    }
    for model, per_ds in DATA.items():
        marker = MODEL_MARKER[model]
        size = MARKER_SIZE[marker]
        for ds, (p1, msc) in per_ds.items():
            ax.scatter(
                p1, msc,
                marker=marker,
                s=size,
                color=DATASET_COLOR[ds],
                edgecolor="black",
                linewidth=0.8,
                alpha=0.95,
                zorder=3,
            )

    # --- Regression dashed line ---
    slope, intercept = np.polyfit(all_x, all_y, 1)
    xs_line = np.linspace(0.0, 1.0, 100)
    ys_line = slope * xs_line + intercept
    ax.plot(xs_line, ys_line, linestyle="--", color="#7A7A7A", linewidth=1.6, zorder=2)

    # --- Axes ---
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.80, 1.05)
    ax.set_xlabel(r"Functional Correctness ($pass@1$)", fontsize=12)
    ax.set_ylabel("MSC Score", fontsize=12)
    ax.set_title(
        r"Decoupling Correctness and Safety: $pass@1$ vs. MSC",
        fontsize=13,
    )

    # Grid
    ax.grid(True, linestyle="-", linewidth=0.6, color="#D6D6D6", zorder=1)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#BDBDBD")

    # --- Legends ---
    # Models (shapes) legend – top-left, black markers
    model_handles = [
        Line2D(
            [0], [0],
            marker=MODEL_MARKER[m], color="white",
            markerfacecolor="#333333", markeredgecolor="black",
            markersize=(9 if MODEL_MARKER[m] == "*" else 7),
            linestyle="none", label=m,
        )
        for m in DATA.keys()
    ]
    leg1 = ax.legend(
        handles=model_handles,
        title="Models (Shapes)",
        loc="upper left",
        frameon=True,
        fancybox=False,
        edgecolor="#BDBDBD",
        fontsize=8,
        title_fontsize=9,
        labelspacing=0.3,
        handletextpad=0.5,
        borderpad=0.4,
    )
    leg1.get_frame().set_facecolor("white")
    ax.add_artist(leg1)

    # Datasets (colors) legend – bottom-right, filled circles
    ds_handles = [
        Line2D(
            [0], [0],
            marker="o", color="white",
            markerfacecolor=DATASET_COLOR[d], markeredgecolor="black",
            markersize=8, linestyle="none", label=d,
        )
        for d in DATASET_COLOR.keys()
    ]
    leg2 = ax.legend(
        handles=ds_handles,
        title="Datasets (Colors)",
        loc="lower right",
        frameon=True,
        fancybox=False,
        edgecolor="#BDBDBD",
        fontsize=8,
        title_fontsize=9,
        labelspacing=0.3,
        handletextpad=0.5,
        borderpad=0.4,
    )
    leg2.get_frame().set_facecolor("white")

    fig.tight_layout()
    fig.savefig("output/correctness_vs_safety.pdf", bbox_inches="tight")
    fig.savefig("output/correctness_vs_safety.png", dpi=200, bbox_inches="tight")
    print("Saved: output/correctness_vs_safety.pdf")
    print("Saved: output/correctness_vs_safety.png")


if __name__ == "__main__":
    main()

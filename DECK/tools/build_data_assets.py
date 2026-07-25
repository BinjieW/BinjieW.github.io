"""Build DECK website figures and machine-readable tables from experiment outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors


MODEL_LABELS = {
    "Claude Opus 4.8": "Claude Opus 4.8",
    "Claude Sonnet 5": "Claude Sonnet 5",
    "GPT-5.5": "GPT-5.5",
    "Claude Sonnet 4.6": "Claude Sonnet 4.6",
    "GPT-5.6 Terra": "GPT-5.6 Terra",
    "Claude Haiku 4.5": "Claude Haiku 4.5",
    "gpt-oss-120b": "GPT-OSS-120B",
    "GPT-5.6 Sol": "GPT-5.6 Sol",
    "Gemma 4 31B": "Gemma 4 31B",
    "GPT-5.6 Luna": "GPT-5.6 Luna",
    "Qwen3-Coder-Next": "Qwen3-Coder-Next",
}

CONDITION_LABELS = {
    "generic": "Global message",
    "checklist": "Checklist",
    "render": "Renders*",
    "checklist_score": "Checklist + score",
    "checklist_items": "Per-item verdicts",
    "checklist_items_render": "Verdicts + renders*",
}

CONDITION_ORDER = list(CONDITION_LABELS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-summary", type=Path, required=True)
    parser.add_argument("--feedback-root", type=Path, required=True)
    parser.add_argument("--error-summary", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": 600,
            "figure.facecolor": "#f7f5ef",
            "axes.facecolor": "#f7f5ef",
            "savefig.facecolor": "#f7f5ef",
            "text.color": "#18201f",
            "axes.labelcolor": "#42504d",
            "xtick.color": "#5e6a67",
            "ytick.color": "#34413e",
        }
    )


def write_benchmark_data(summary: dict, data_dir: Path) -> list[dict]:
    models = sorted(summary["models"], key=lambda item: item["overall"], reverse=True)
    rows = []
    for rank, model in enumerate(models, 1):
        row = {
            "rank": rank,
            "model": MODEL_LABELS.get(model["model"], model["model"]),
            "overall": model["overall"],
            **{f"level_{level}": model["levels"][str(level)] for level in range(1, 7)},
            "render_success_rate": (240 - model["render_fail"]) / 240,
            "render_failures": model["render_fail"],
        }
        rows.append(row)

    fields = [
        "rank",
        "model",
        "overall",
        "level_1",
        "level_2",
        "level_3",
        "level_4",
        "level_5",
        "level_6",
        "render_success_rate",
        "render_failures",
    ]
    with (data_dir / "hardest10-model-results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (data_dir / "hardest10-model-results.json").write_text(
        json.dumps(rows, indent=2) + "\n"
    )
    return rows


def plot_benchmark(rows: list[dict], figure_dir: Path) -> None:
    labels = [row["model"] for row in rows]
    overall = np.array([row["overall"] for row in rows])
    matrix = np.array(
        [[row[f"level_{level}"] for level in range(1, 7)] for row in rows]
    )

    fig = plt.figure(figsize=(14.2, 8.2))
    grid = fig.add_gridspec(1, 2, width_ratios=(1.0, 1.62), wspace=0.35)
    bar_ax = fig.add_subplot(grid[0, 0])
    heat_ax = fig.add_subplot(grid[0, 1])

    y = np.arange(len(rows))
    bar_colors = ["#e85d3f" if index < 2 else "#183f3a" for index in range(len(rows))]
    bar_ax.barh(y, overall, color=bar_colors, height=0.68)
    bar_ax.set_yticks(y, labels)
    bar_ax.invert_yaxis()
    bar_ax.set_xlim(0, 0.86)
    bar_ax.set_xlabel("Mean checklist score")
    bar_ax.set_title("A · Observed overall")
    bar_ax.grid(axis="x", color="#d8d4c9", linewidth=0.8, alpha=0.8)
    bar_ax.set_axisbelow(True)
    for index, value in enumerate(overall):
        bar_ax.text(value + 0.012, index, f"{value:.3f}", va="center", fontsize=9)

    palette = colors.LinearSegmentedColormap.from_list(
        "deck", ["#efe9dc", "#c8d9ca", "#4c8279", "#183f3a"]
    )
    image = heat_ax.imshow(matrix, cmap=palette, vmin=0, vmax=0.9, aspect="auto")
    heat_ax.set_xticks(np.arange(6), [f"L{level}" for level in range(1, 7)])
    heat_ax.set_yticks(y, labels)
    heat_ax.set_title("B · Score by edit difficulty")
    heat_ax.tick_params(length=0)
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            value = matrix[row_index, column_index]
            heat_ax.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if value > 0.58 else "#23312f",
            )
    colorbar = fig.colorbar(image, ax=heat_ax, fraction=0.035, pad=0.035)
    colorbar.set_label("Checklist score", rotation=270, labelpad=16)
    colorbar.outline.set_visible(False)

    fig.suptitle(
        "DECK Hardest-10 model snapshot",
        x=0.06,
        y=0.99,
        ha="left",
        fontsize=20,
        fontweight=650,
    )
    fig.text(
        0.06,
        0.94,
        "10 objects × 6 levels × 4 edits × 11 models · Sonnet 5 checklist judge",
        fontsize=11,
        color="#5d6966",
    )
    fig.text(
        0.06,
        0.012,
        "Observed scores after empty-response repair. These are not human-corrected ground truth; "
        "verifier and execution failures remain part of the measurement.",
        fontsize=9,
        color="#6c6257",
    )
    fig.subplots_adjust(left=0.19, right=0.96, top=0.88, bottom=0.09)
    for suffix in ("svg", "png"):
        fig.savefig(
            figure_dir / f"hardest10-main-figure.{suffix}",
            dpi=210,
            bbox_inches="tight",
        )
    plt.close(fig)


def load_feedback_rows(root: Path) -> list[dict]:
    directory_names = {
        "generic": "quality_feedback_generic_r10",
        "checklist": "quality_feedback_checklist_r10",
        "render": "quality_feedback_render_r10",
        "checklist_score": "quality_feedback_checklist_score_r10",
        "checklist_items": "quality_feedback_checklist_items_r10",
        "checklist_items_render": "quality_feedback_checklist_items_render_r10",
    }
    rows = []
    for condition in CONDITION_ORDER:
        data = json.loads((root / directory_names[condition] / "summary.json").read_text())
        rows.append(
            {
                "condition": condition,
                "label": CONDITION_LABELS[condition],
                "models": data["completed_models"],
                "samples": data["total"],
                "initial": data["round0_mean_score"],
                "final": data["final_mean_score"],
                "delta": data["mean_score_delta"],
            }
        )
    return rows


def write_feedback_data(rows: list[dict], data_dir: Path) -> None:
    fields = ["condition", "label", "models", "samples", "initial", "final", "delta"]
    with (data_dir / "quality-feedback-results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (data_dir / "quality-feedback-results.json").write_text(
        json.dumps(rows, indent=2) + "\n"
    )


def plot_feedback(rows: list[dict], figure_dir: Path) -> None:
    labels = [row["label"] for row in rows]
    initial = np.array([row["initial"] for row in rows])
    final = np.array([row["final"] for row in rows])
    y = np.arange(len(rows))

    fig, ax = plt.subplots(figsize=(11.6, 5.8))
    ax.barh(y + 0.17, initial, height=0.3, color="#c9c4b9", label="Round 0")
    ax.barh(y - 0.17, final, height=0.3, color="#e85d3f", label="After ≤10 rounds")
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0.50, 0.82)
    ax.set_xlabel("Mean checklist score")
    ax.set_title(
        "Quality feedback improves the same Hardest-10 starting outputs",
        loc="left",
        fontsize=17,
        pad=16,
    )
    ax.grid(axis="x", color="#d8d4c9", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="lower right")
    for index, row in enumerate(rows):
        ax.text(
            row["final"] + 0.006,
            index - 0.17,
            f"+{row['delta']:.3f}",
            va="center",
            fontsize=9,
            color="#a33d29",
            fontweight=600,
        )
    fig.text(
        0.125,
        0.015,
        "* Render conditions cover 9 multimodal models; the other four conditions cover all 11. "
        "Aggregate values are therefore not fully apples-to-apples.",
        fontsize=9,
        color="#6c6257",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    for suffix in ("svg", "png"):
        fig.savefig(
            figure_dir / f"feedback-condition-gains.{suffix}",
            dpi=210,
            bbox_inches="tight",
        )
    plt.close(fig)


def plot_error_repair(error_summary: dict, figure_dir: Path, data_dir: Path) -> None:
    repaired_per_round = [227, 126, 28, 7, 2, 3, 3]
    cumulative = np.cumsum(repaired_per_round)
    initial_failures = 402
    rates = cumulative / initial_failures
    rounds = np.arange(1, len(rates) + 1)

    rows = [
        {
            "round": int(round_index),
            "repaired_this_round": repaired_per_round[round_index - 1],
            "cumulative_repaired": int(cumulative[round_index - 1]),
            "cumulative_repair_rate": float(rates[round_index - 1]),
        }
        for round_index in rounds
    ]
    (data_dir / "error-repair-trajectory.json").write_text(
        json.dumps(rows, indent=2) + "\n"
    )

    fig, ax = plt.subplots(figsize=(9.8, 5.1))
    ax.plot(rounds, rates * 100, color="#183f3a", linewidth=3, marker="o", markersize=7)
    ax.fill_between(rounds, rates * 100, color="#98b8ae", alpha=0.24)
    ax.axhline(100, color="#b8b2a8", linestyle="--", linewidth=1)
    ax.set_xlim(1, 7)
    ax.set_ylim(50, 102)
    ax.set_xticks(rounds)
    ax.set_xlabel("Repair round")
    ax.set_ylabel("Initial failures repaired (%)")
    ax.set_title("Most execution failures are fixed within 2–3 rounds", loc="left", fontsize=17)
    ax.grid(axis="y", color="#d8d4c9", linewidth=0.8)
    ax.set_axisbelow(True)
    for x, y_value in zip(rounds, rates * 100):
        ax.text(x, y_value + 2.1, f"{y_value:.1f}%", ha="center", fontsize=9)
    fig.text(
        0.125,
        0.01,
        f"Hardest-10: 402 initial render failures; "
        f"{error_summary['final_render_success']} / {error_summary['total']} final renders succeed.",
        fontsize=9,
        color="#6c6257",
    )
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    for suffix in ("svg", "png"):
        fig.savefig(
            figure_dir / f"error-repair-trajectory.{suffix}",
            dpi=210,
            bbox_inches="tight",
        )
    plt.close(fig)


def main() -> None:
    args = parse_args()
    configure_style()
    figure_dir = args.output_root / "assets" / "figures"
    data_dir = args.output_root / "assets" / "data"
    figure_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    summary = json.loads(args.benchmark_summary.read_text())
    benchmark_rows = write_benchmark_data(summary, data_dir)
    plot_benchmark(benchmark_rows, figure_dir)

    feedback_rows = load_feedback_rows(args.feedback_root)
    write_feedback_data(feedback_rows, data_dir)
    plot_feedback(feedback_rows, figure_dir)

    error_summary = json.loads(args.error_summary.read_text())
    plot_error_repair(error_summary, figure_dir, data_dir)


if __name__ == "__main__":
    main()

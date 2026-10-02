"""Static chart exports for the match-prediction article."""

from __future__ import annotations

import html
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]


def export_match_article_charts(
    *,
    table_dir: Path = Path("outputs/tables"),
    output_dir: Path = Path("outputs/charts/article"),
) -> list[Path]:
    """Export static SVG charts and a caption file from aggregate article tables."""

    output_dir.mkdir(parents=True, exist_ok=True)
    baseline = pd.read_csv(table_dir / "match_baseline_evaluation.csv")
    walk_forward = pd.read_csv(table_dir / "match_walk_forward_evaluation.csv")
    source_composition = pd.read_csv(table_dir / "match_source_composition_diagnostics.csv")

    paths = [
        _write_holdout_log_loss_chart(
            baseline,
            output_dir / "match_holdout_log_loss.svg",
        ),
        _write_walk_forward_log_loss_chart(
            walk_forward,
            output_dir / "match_walk_forward_log_loss.svg",
        ),
        _write_source_guardrail_chart(
            source_composition,
            output_dir / "match_source_guardrail.svg",
        ),
    ]
    paths.append(_write_captions(output_dir / "captions.md"))
    return paths


def _write_holdout_log_loss_chart(frame: pd.DataFrame, path: Path) -> Path:
    test = frame[frame["split"] == "test"].sort_values("log_loss")
    labels = [str(value) for value in test["model_name"]]
    values = [float(value) for value in test["log_loss"]]
    _write_svg(
        path,
        _horizontal_bar_svg(
            title="2022+ Held-Out Log Loss",
            subtitle="Lower is better; calibrated models are fit on validation rows only.",
            labels=labels,
            values=values,
            value_label="log loss",
            width=1080,
            row_height=34,
        ),
    )
    return path


def _write_walk_forward_log_loss_chart(frame: pd.DataFrame, path: Path) -> Path:
    core_models = [
        "ranking_log_difference",
        "overall_elo",
        "surface_elo",
        "logistic_baseline",
    ]
    filtered = frame[frame["model_name"].isin(core_models)].copy()
    filtered["window_label"] = filtered["window_label"].astype(str)
    years = sorted(filtered["window_label"].unique())
    series = {
        model_name: [
            float(
                filtered[
                    (filtered["model_name"] == model_name)
                    & (filtered["window_label"] == year)
                ]["log_loss"].iloc[0]
            )
            for year in years
        ]
        for model_name in core_models
    }
    _write_svg(
        path,
        _line_svg(
            title="Annual Walk-Forward Test Log Loss",
            subtitle="Expanding train windows, three-year validation windows, one-year tests.",
            x_labels=years,
            series=series,
            width=1080,
            height=620,
        ),
    )
    return path


def _write_source_guardrail_chart(frame: pd.DataFrame, path: Path) -> Path:
    subset = (
        frame[
            (frame["split"] == "test")
            & (frame["ranking_coverage"] == "missing_rank")
            & (frame["era"] == "2020s")
        ]
        .sort_values("logistic_roc_auc", ascending=False)
        .head(8)
        .copy()
    )
    labels = [
        " | ".join(
            [
                str(row.tour).upper(),
                str(row.surface),
                str(row.event_level),
                str(row.draw_stage),
            ]
        )
        for row in subset.itertuples(index=False)
    ]
    values = [float(value) for value in subset["logistic_roc_auc"]]
    _write_svg(
        path,
        _horizontal_bar_svg(
            title="Missing-Rank Source Guardrail",
            subtitle="Top 2020s test segments by ROC-AUC; diagnostic, not a model claim.",
            labels=labels,
            values=values,
            value_label="ROC-AUC",
            width=1080,
            row_height=40,
            lower_bound=0.5,
        ),
    )
    return path


def _write_captions(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "# Match Article Chart Captions",
                "",
                "## match_holdout_log_loss.svg",
                "",
                "Caption/alt text: horizontal bar chart of 2022-onward held-out log loss by model. Lower bars are better; the logistic baseline remains strongest, while Platt and isotonic variants are calibration checks fit only on validation rows.",
                "",
                "## match_walk_forward_log_loss.svg",
                "",
                "Caption/alt text: line chart of annual test log loss from 2016 through 2025 for ranking difference, overall Elo, blended surface Elo, and logistic baseline. The logistic baseline is consistently the lowest line.",
                "",
                "## match_source_guardrail.svg",
                "",
                "Caption/alt text: horizontal bar chart of the top 2020s missing-rank test segments by logistic ROC-AUC. Segments are labeled by tour, surface, event level, and draw stage; these results are source-composition diagnostics, not broad model claims.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _horizontal_bar_svg(
    *,
    title: str,
    subtitle: str,
    labels: list[str],
    values: list[float],
    value_label: str,
    width: int,
    row_height: int,
    lower_bound: float | None = None,
) -> str:
    left = 300
    right = 130
    top = 92
    bottom = 54
    height = top + bottom + len(values) * row_height
    plot_width = width - left - right
    minimum = min(values) if lower_bound is None else lower_bound
    maximum = max(values)
    span = max(maximum - minimum, 1e-9)
    palette = ["#2563eb", "#0891b2", "#16a34a", "#ca8a04", "#dc2626", "#7c3aed"]

    elements = _svg_header(width, height, title, subtitle)
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        y = top + index * row_height
        bar_width = max(2.0, (value - minimum) / span * plot_width)
        color = palette[index % len(palette)]
        elements.append(
            f'<text x="{left - 14}" y="{y + 21}" text-anchor="end" '
            f'class="label">{_escape(label)}</text>'
        )
        elements.append(
            f'<rect x="{left}" y="{y + 7}" width="{bar_width:.2f}" '
            f'height="18" fill="{color}" rx="3" />'
        )
        elements.append(
            f'<text x="{left + bar_width + 8:.2f}" y="{y + 21}" '
            f'class="value">{value:.4f}</text>'
        )
    elements.append(
        f'<text x="{left}" y="{height - 18}" class="axis">'
        f'{_escape(value_label)} scale starts at {minimum:.3f}</text>'
    )
    elements.append("</svg>")
    return "\n".join(elements)


def _line_svg(
    *,
    title: str,
    subtitle: str,
    x_labels: list[str],
    series: dict[str, list[float]],
    width: int,
    height: int,
) -> str:
    left = 72
    right = 280
    top = 92
    bottom = 70
    plot_width = width - left - right
    plot_height = height - top - bottom
    values = [value for points in series.values() for value in points]
    minimum = min(values)
    maximum = max(values)
    span = max(maximum - minimum, 1e-9)
    palette = {
        "ranking_log_difference": "#dc2626",
        "overall_elo": "#2563eb",
        "surface_elo": "#0891b2",
        "logistic_baseline": "#16a34a",
    }
    elements = _svg_header(width, height, title, subtitle)
    elements.append(
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" '
        f'y2="{top + plot_height}" stroke="#9ca3af" />'
    )
    elements.append(
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" '
        f'stroke="#9ca3af" />'
    )
    for index, label in enumerate(x_labels):
        x = left + index / max(len(x_labels) - 1, 1) * plot_width
        elements.append(
            f'<text x="{x:.2f}" y="{height - 34}" text-anchor="middle" '
            f'class="axis">{_escape(label)}</text>'
        )
    for tick in range(5):
        value = minimum + tick / 4 * span
        y = top + plot_height - (value - minimum) / span * plot_height
        elements.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" '
            f'y2="{y:.2f}" stroke="#e5e7eb" />'
        )
        elements.append(
            f'<text x="{left - 12}" y="{y + 4:.2f}" text-anchor="end" '
            f'class="axis">{value:.3f}</text>'
        )
    for model_name, points in series.items():
        color = palette.get(model_name, "#4b5563")
        coordinates = []
        for index, value in enumerate(points):
            x = left + index / max(len(points) - 1, 1) * plot_width
            y = top + plot_height - (value - minimum) / span * plot_height
            coordinates.append(f"{x:.2f},{y:.2f}")
            elements.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}" />')
        elements.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="3" '
            f'points="{" ".join(coordinates)}" />'
        )
    legend_x = left + plot_width + 36
    for index, model_name in enumerate(series):
        y = top + index * 30
        color = palette.get(model_name, "#4b5563")
        elements.append(f'<rect x="{legend_x}" y="{y}" width="16" height="16" fill="{color}" />')
        elements.append(
            f'<text x="{legend_x + 24}" y="{y + 13}" class="label">'
            f'{_escape(model_name)}</text>'
        )
    elements.append("</svg>")
    return "\n".join(elements)


def _svg_header(width: int, height: int, title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{_escape(title)}">',
        "<style>",
        "text { font-family: Arial, sans-serif; fill: #111827; }",
        ".title { font-size: 28px; font-weight: 700; }",
        ".subtitle { font-size: 15px; fill: #4b5563; }",
        ".label { font-size: 14px; }",
        ".value { font-size: 13px; font-weight: 700; }",
        ".axis { font-size: 12px; fill: #6b7280; }",
        "</style>",
        '<rect width="100%" height="100%" fill="#ffffff" />',
        f'<text x="32" y="42" class="title">{_escape(title)}</text>',
        f'<text x="32" y="66" class="subtitle">{_escape(subtitle)}</text>',
    ]


def _write_svg(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)

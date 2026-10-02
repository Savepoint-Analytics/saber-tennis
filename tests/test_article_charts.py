from pathlib import Path

import pandas as pd

from tennis_sabermetrics.evaluation.article_charts import export_match_article_charts


def test_export_match_article_charts_writes_static_svgs(tmp_path: Path) -> None:
    table_dir = tmp_path / "tables"
    output_dir = tmp_path / "charts"
    table_dir.mkdir()
    pd.DataFrame(
        [
            {
                "model_name": "ranking_log_difference",
                "split": "test",
                "log_loss": 0.65,
                "brier_score": 0.22,
                "roc_auc": 0.67,
                "accuracy": 0.61,
                "sample_size": 100,
            },
            {
                "model_name": "logistic_baseline",
                "split": "test",
                "log_loss": 0.58,
                "brier_score": 0.20,
                "roc_auc": 0.75,
                "accuracy": 0.68,
                "sample_size": 100,
            },
        ]
    ).to_csv(table_dir / "match_baseline_evaluation.csv", index=False)
    pd.DataFrame(
        [
            {
                "window_label": year,
                "model_name": model_name,
                "log_loss": log_loss,
                "brier_score": 0.2,
                "roc_auc": 0.7,
                "accuracy": 0.65,
                "sample_size": 100,
            }
            for year in ("2019", "2020")
            for model_name, log_loss in [
                ("ranking_log_difference", 0.65),
                ("overall_elo", 0.60),
                ("surface_elo", 0.61),
                ("logistic_baseline", 0.58),
            ]
        ]
    ).to_csv(table_dir / "match_walk_forward_evaluation.csv", index=False)
    pd.DataFrame(
        [
            {
                "split": "test",
                "ranking_coverage": "missing_rank",
                "era": "2020s",
                "tour": "atp",
                "surface": "clay",
                "event_level": "challenger_level",
                "draw_stage": "qualifying",
                "source_sample_size": 120,
                "source_share": 1.0,
                "serve_return_available_rate": 0.5,
                "logistic_log_loss": 0.4,
                "logistic_roc_auc": 0.9,
            }
        ]
    ).to_csv(table_dir / "match_source_composition_diagnostics.csv", index=False)

    paths = export_match_article_charts(table_dir=table_dir, output_dir=output_dir)

    assert {path.name for path in paths} == {
        "match_holdout_log_loss.svg",
        "match_walk_forward_log_loss.svg",
        "match_source_guardrail.svg",
        "captions.md",
    }
    assert (output_dir / "match_holdout_log_loss.svg").read_text(encoding="utf-8").startswith("<svg")
    assert "Caption/alt text" in (output_dir / "captions.md").read_text(encoding="utf-8")

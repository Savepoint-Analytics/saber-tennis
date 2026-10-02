# Publication Review: Match Prediction Baseline Article

Review date: 2026-09-28.

Reviewed artifacts:

- [docs/articles/why-elo-serve-return-beat-rankings.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/articles/why-elo-serve-return-beat-rankings.md)
- [notebooks/why_elo_serve_return_beat_rankings.ipynb](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/notebooks/why_elo_serve_return_beat_rankings.ipynb)
- [docs/model-cards/match-outcome-baseline.md](/Users/alexoswald/Projects/Sabermetrics/Tennis/saber-tennis/docs/model-cards/match-outcome-baseline.md)

## Verdict

The article is suitable as a non-commercial research/portfolio artifact after retaining the attribution, snapshot, missingness, source-composition, and no-betting-advice caveats.

It is not suitable for paid Savepoint Analytics deliverables without written permission from the data rights holder or replacement with a commercial-use data source.

## License Position

The current data remains treated as Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International because it is derived from Jeff Sackmann / Tennis Abstract data through the reviewed fallback archive source.

Required public attribution:

> Data derived from Jeff Sackmann / Tennis Abstract repositories and/or The Tennis Abstract Match Charting Project. Original sources are licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International unless otherwise stated. This project is non-commercial research/portfolio work and does not redistribute raw third-party data.

## Redistribution Review

Current public tables are aggregate model metrics, calibration summaries, missingness rates, and source-composition diagnostics. They do not redistribute bulk raw third-party match rows.

Do not publish:

- Raw ATP/WTA source files.
- Row-level match exports that recreate a substantial portion of the source dataset.
- Paid reports, dashboards, or forecasts derived from the CC BY-NC-SA data without permission.
- Betting picks or wagering advice.

## Publication Requirements

Keep these in any public article, notebook, chart, or dashboard:

- Source attribution.
- Snapshot date: 2026-08-25.
- Match coverage: 1990-01-01 to 2026-06-02.
- Test period: 2022-01-01 onward.
- Walk-forward window definition when walk-forward metrics are shown.
- Sample sizes.
- Missing-rank and serve/return missingness caveats.
- Non-commercial-use caveat.
- Clear statement that outputs are not betting advice.
- Captions or alt text for exported static charts.

## Residual Risk

The top missing-rank test segments remain 100% fallback-archive sourced. Event/source flags now separate ITF-level, challenger-level, tour-level, qualifying, main-draw, incomplete-ranking, and source-coverage populations, but high-performing missing-rank findings should be described as diagnostics rather than general model claims.

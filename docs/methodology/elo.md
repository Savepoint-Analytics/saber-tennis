# Elo Methodology

Elo is the first transparent baseline for match prediction because it updates from opponent-adjusted results and can be computed strictly as of match date.

## Initial Implementation

The scaffold includes simple overall Elo and independent surface Elo baselines in `src/tennis_sabermetrics/models/elo.py`.

Rules:

- Sort matches by match date and stable within-day order.
- Emit pre-match prediction before updating ratings.
- Persist split definitions and model parameters with evaluation outputs.
- Keep surface Elo ratings independent by surface until there is enough data to justify blending.

## Next Extensions

- Blended overall/surface ratings with shrinkage for sparse surfaces.
- Tour-specific and level-specific calibration.
- Time decay or inactivity adjustments.

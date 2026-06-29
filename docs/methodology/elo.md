# Elo Methodology

Elo is the first transparent baseline for match prediction because it updates from opponent-adjusted results and can be computed strictly as of match date.

## Initial Implementation

The scaffold includes a simple overall Elo baseline in `src/tennis_sabermetrics/models/elo.py`.

Rules:

- Sort matches by match date and stable within-day order.
- Emit pre-match prediction before updating ratings.
- Persist split definitions and model parameters with evaluation outputs.
- Extend to surface Elo only after the overall no-lookahead tests are stable.

## Next Extensions

- Surface-specific Elo.
- Blended overall/surface ratings with shrinkage for sparse surfaces.
- Tour-specific and level-specific calibration.
- Time decay or inactivity adjustments.


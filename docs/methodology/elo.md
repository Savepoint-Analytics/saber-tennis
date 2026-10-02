# Elo Methodology

Elo is the first transparent baseline for match prediction because it updates from opponent-adjusted results and can be computed strictly as of match date.

## Current Implementation

The scaffold includes simple overall Elo, independent surface Elo, and blended surface Elo baselines in `src/tennis_sabermetrics/models/elo.py`.

Rules:

- Sort matches by match date and stable within-day order.
- Emit pre-match prediction before updating ratings.
- Persist split definitions and model parameters with evaluation outputs.
- Keep the independent surface Elo implementation available for comparison tests.
- Use blended surface Elo for production gold features: raw surface ratings are shrunk toward each player's overall Elo when the player has few prior matches on that surface.

The blended surface rating is:

```text
surface_weight = surface_matches / (surface_matches + min_surface_matches)
blended_rating = surface_weight * raw_surface_elo + (1 - surface_weight) * overall_elo
```

The current `min_surface_matches` default is 12. A player with no prior matches on the match surface uses their overall Elo as the blended surface rating; as surface-specific history accumulates, the raw surface rating receives more weight.

## Next Extensions

- Tune `min_surface_matches` on validation windows.
- Tour-specific and level-specific Elo parameters.
- Time decay or inactivity adjustments.

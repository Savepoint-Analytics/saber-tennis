# Win Probability

Win probability models should respect tennis structure:

```text
points -> games -> sets -> matches
```

Point-state models should be calibrated by:

- Score state.
- Surface.
- Server/returner strength bucket.
- Match format.
- Tiebreak versus regular game.

The first implementation should favor transparent Markov-style baselines before complex in-match models.


# COMPANY_CONTEXT.md — Savepoint Analytics Tennis Sabermetrics Context

_Last updated: 2026-06-28_

## Purpose

This document is the business source of truth for the Tennis Empirical Analysis project under Alex Oswald / Savepoint Analytics.

Use it when AI tools need context for strategy, positioning, portfolio decisions, sales collateral, public research framing, licensing decisions, or business-level reasoning.

---

## Executive Snapshot

**Founder:** Alex Oswald  
**Company:** Savepoint Analytics  
**Core business:** Founder-led analytics consultancy and reusable analytics platform, with the primary commercial focus still rooted in video game analytics.  
**Project vertical:** Sports Sabermetrics / Tennis Analytics  
**Project name:** Tennis Empirical Analysis  
**Home base:** Langford / Victoria, British Columbia, Canada  
**Infrastructure:** Savepoint-Lab headless Ubuntu Server with Docker, PostgreSQL, MinIO, Prefect, and MLflow.

### Why Tennis

Alex is an avid tennis player and wants to understand tennis empirically from coaching, player-analysis, and prediction perspectives. This project is intended to explain how points, games, sets, and matches are won; predict match outcomes; and simulate counterfactual player improvements.

### Business Role of the Project

This project should help Savepoint Analytics:

- Demonstrate rigorous domain knowledge outside video games.
- Diversify the public research portfolio.
- Show end-to-end analytics capability: data acquisition, warehousing, feature engineering, prediction, simulation, dashboards, and narrative communication.
- Build public credibility with sports analytics audiences.
- Eventually support affordable tennis analysis offerings, while respecting data licenses.

---

## Relationship to Savepoint Analytics

Savepoint Analytics remains the umbrella brand. The core commercial focus is still senior analytics services and reusable analytics infrastructure, especially for game studios. Tennis sabermetrics is a public research and domain-expansion vertical, not a replacement for the core Savepoint business.

The tennis project should borrow Savepoint’s strongest capabilities:

- Data engineering and reproducible pipelines.
- Analytics engineering and dbt-style warehouse modeling.
- Predictive modeling and careful validation.
- Experimentation/counterfactual thinking.
- Dashboarding and plain-language explanation.
- Practical product thinking: useful outputs over decorative charts.

---

## Strategic Positioning

### External Positioning

Savepoint Analytics can present this project as:

> A rigorous public tennis analytics project that applies professional-grade data engineering, predictive modeling, and counterfactual simulation to tennis performance analysis.

### What Makes It Credible

- It does not simply scrape data and train a black-box model.
- It models the structure of tennis: points → games → sets → matches.
- It separates serve, return, surface, form, and matchup components.
- It uses strict temporal validation to avoid look-ahead bias.
- It reports uncertainty and sample size.
- It explains tactical and coaching implications.
- It documents licensing constraints instead of pretending all public GitHub data is free for commercial use.

### Potential Audience Segments

| Audience | What they care about | Possible outputs |
|---|---|---|
| Tennis coaches | Actionable player improvement | Serve/return breakdowns, pressure-point diagnostics, tactical counterfactuals |
| Competitive players | How to improve match outcomes | Personalized or archetype-based recommendations |
| Tennis fans | Better understanding of players and matchups | Articles, leaderboards, dashboards |
| Sports analytics community | Methodology and reproducibility | GitHub repo, notebooks, methodology docs |
| Hiring managers / clients | Demonstrated analytical breadth | Portfolio artifacts and technical write-ups |
| Future paid clients | Affordable analysis | Must use licensed, client-supplied, permissioned, or original data |

---

## Commercialization Constraints

The most important business constraint is licensing.

Many of the best public tennis datasets, especially Jeff Sackmann / Tennis Abstract datasets, are licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0. That means:

- Attribution is required.
- Non-commercial use only unless separate permission is obtained.
- Derivative datasets and analysis artifacts may trigger share-alike obligations.
- Public portfolio research is acceptable when properly attributed and non-commercial.
- Paid client deliverables, commercial dashboards, subscription products, or betting tools based directly on these datasets are not acceptable without permission or a separate commercial license.

### Commercial Pathways That Respect Licenses

To eventually offer affordable tennis analysis commercially, use one or more of these paths:

1. **Get written permission or a commercial license** from the relevant data owner.
2. **Use client-supplied data** from players, clubs, academies, or teams.
3. **Collect original charting data** through Savepoint-owned workflows and consented contributors.
4. **Use officially licensed feeds** from commercial providers if economics make sense.
5. **Sell methodology, code, and consulting** while requiring clients to provide their own licensed data.
6. **Build tools for recreational players** where users enter their own match data.

### Commercial Non-Goals

Do not:

- Resell or package non-commercial public datasets.
- Build a paid prediction/betting product on CC BY-NC-SA data without permission.
- Copy unlicensed GitHub code into Savepoint-owned code.
- Present third-party data as Savepoint-owned data.
- Hide license limitations in public or client-facing materials.

---

## Product / Service Ideas

### Public Portfolio Outputs

- “Elo vs Ranking: What Official Rankings Miss.”
- “Serve and Return Archetypes by Surface.”
- “How Much Does Second-Serve Improvement Matter?”
- “The Point-to-Match Simulator: Why One Percentage Point Matters.”
- “Tennis Counterfactuals: What If Player X Held Serve 2% More Often?”
- Interactive Dash app showing surface-adjusted player profiles.

### Future Commercial Offers

Only after licensing/data-source questions are solved:

- Affordable match report for competitive players using their own entered/charted match data.
- Coach dashboard for serve/return tendencies, pressure points, and tactical patterns.
- Club analytics package for ladder/team match records.
- Tournament preview model using licensed or permissioned data.
- Custom analytics for tennis academies.

---

## Brand Voice and Standards

The project should sound:

- Empirical but accessible.
- Practical for players and coaches.
- Transparent about uncertainty.
- Respectful of existing tennis data contributors.
- Clear that predictions are probabilistic, not certainties.

Avoid:

- Betting tout language.
- Overclaiming causal conclusions from observational data.
- “AI magic” framing.
- Generic sports punditry unsupported by data.
- Unlicensed commercial implications.

---

## Founder Background to Emphasize

Alex brings:

- Deep experience in game analytics, where player behavior, state transitions, progression systems, and counterfactual simulation are central.
- Strong Python, SQL, R, dbt, PostgreSQL, AWS, dashboarding, and data platform skills.
- Experience with telemetry systems, product analytics, A/B testing, forecasting, recommender systems, and simulation.
- The ability to translate data into practical product/coaching decisions.
- A personal connection to tennis as an avid player.

Relevant bridge from games to tennis:

- Tennis points are sequential events with state transitions, similar to game telemetry.
- Player styles can be clustered like player segments.
- Tactical changes can be modeled as counterfactual interventions.
- Match prediction needs leakage-resistant validation, like live game forecasting.
- Dashboards must guide decisions, not merely display metrics.

---

## AI Usage Guidance

When using AI tools with this document:

- Reason from this context, not generic sports-business advice.
- Treat licensing as a first-class requirement.
- Produce implementation-ready artifacts.
- Recommend, do not override Alex’s decision authority.
- Keep tennis outputs useful for both coaching and analytics credibility.
- Prefer Python-centric implementations with R used selectively.
- Use Savepoint-Lab infrastructure where practical.
- Preserve public/private boundaries between code, raw data, derived data, and commercial outputs.

Standard prompt pattern for new sessions:

> Load `CLAUDE.md`, `COMPANY_CONTEXT.md`, `PROJECT_CONTEXT.md`, `registry.md`, `public-data-sources.md`, and `AGENTS.md` for the Tennis Empirical Analysis project. Act as a senior collaborator who already knows this context. Give practical, implementation-ready answers specific to this project, and respect all licensing constraints.

---

## Update Log

| Date | Update |
|---|---|
| 2026-06-28 | Created tennis-specific Savepoint Analytics business context, including portfolio rationale, commercialization constraints, and license-respecting pathways. |

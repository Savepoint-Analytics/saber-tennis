# Commercial Data Path

Last updated: 2026-09-09.

The current warehouse is built from CC BY-NC-SA tennis data and is suitable for non-commercial research only. Paid Savepoint Analytics deliverables need a separate commercial-use data path.

## Recommended Path

1. Keep the existing Sackmann-derived warehouse for non-commercial research, portfolio articles, and methodology development.
2. For ATP commercial work, contact Tennis Data Innovations and/or its licensed distributors. TDI says it manages and commercialises ATP data across betting, media, and performance, and its Tennis Data Platform includes live professional-tennis sources, historical archive, and a sandbox environment.
3. For WTA commercial work, contact Stats Perform/Opta. WTA announced that Stats Perform extended its exclusive agreement to collect and distribute official WTA data and live streams to licensed sportsbooks through the end of the decade.
4. Evaluate Sportradar Tennis API v3 as an integration candidate where contract scope supports the intended use. The current Tennis API docs list authenticated access, historical results, rankings, match statistics, point-by-point scoring where available, and probability feeds with add-on entitlements.
5. Treat SportsDataIO as a lower-priority broad sports API candidate unless a sales/legal review confirms tennis coverage and the exact commercial rights needed. Its public licensing FAQ says commercial licenses can permit caching, model building, and display of derived analytics, but final rights depend on the contracted feeds and use case.

## Contract Questions

Before using a paid feed, get written answers for:

- Can Savepoint store raw API responses in PostgreSQL/MinIO?
- Can Savepoint train statistical models, Elo ratings, and derived analytics from the feed?
- Can derived predictions or dashboards be shown to paying customers?
- Are betting-adjacent analytics allowed, prohibited, or subject to extra integrity obligations?
- Are ATP, WTA, Challenger, ITF, qualifying, doubles, and historical seasons included?
- Are odds/probabilities included, and are they licensed separately?
- Can official data be combined with unofficial or historical research data? Stats Perform's WTA terms include restrictions on combining WTA data with unofficial data, so this needs explicit review.
- What attribution, deletion, retention, and post-termination rules apply?
- Are there sublicensing, redistribution, or customer access restrictions?

## Candidate Sources

| Source | Best fit | Current status | Notes |
|---|---|---|---|
| Tennis Data Innovations | ATP official/commercial data, performance, media, betting, historical archive/sandbox | Contact required | Likely first ATP route because TDI manages ATP data commercialisation. |
| Sportradar Tennis API v3 | API integration for tennis scores, schedules, rankings, historical results, stats, probabilities | Contract/trial required | Good technical candidate; confirm ATP/WTA rights, historical depth, and probabilities entitlements. |
| Stats Perform / Opta WTA | Official WTA data, deep data, shot-level/live products, betting/media packages | Contact required | First WTA route because WTA describes Stats Perform as exclusive official data distributor. |
| SportsDataIO Global/Commercial APIs | Broad sports API or commercial license model reference | Verify tennis coverage | Useful licensing model reference; do not assume tennis coverage or rights until confirmed. |

## Source Links

- [Tennis Data Innovations home](https://www.tennisdata.com/home/)
- [Tennis Data Platform](https://www.tennisdata.com/tennis-data-platform)
- [Sportradar Tennis API overview](https://developer.sportradar.com/tennis/reference/overview)
- [Sportradar Tennis v3 API basics](https://developer.sportradar.com/tennis/docs/tennis-ig-api-basics)
- [Stats Perform WTA official feed](https://www.statsperform.com/wta/)
- [WTA announcement: Stats Perform extends official rights partnership](https://www.wtatennis.com/news/3812740/stats-perform-extends-exclusive-official-rights-partnership-with-the-wta)
- [Stats Perform WTA terms](https://www.statsperform.com/legal/wta-terms-conditions/)
- [SportsDataIO data rights and licensing FAQ](https://sportsdata.io/help/data-rights-and-licensing-questions)

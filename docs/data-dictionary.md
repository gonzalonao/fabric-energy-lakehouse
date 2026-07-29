# Data dictionary

Confirmed against the loaded Silver tables (Track A, dev), 2026-07-19. Units are recorded
only where the data confirms them — the REE payload does not state units, so magnitudes
were profiled before asserting.

## Units (confirmed by C4 profiling)

| Quantity | Unit | Evidence |
|---|---|---|
| Demand | **MWh** (per day) | `silver.demand_daily.value` ranges 403,297 – 866,733 → 403–867 GWh/day, the correct scale for peninsular Spain |
| Generation | **MWh** (per day, per technology) | `silver.generation_daily.value` up to 457,441; the composite `Generación total` is excluded so this is a single technology's daily total |
| Price | **€/MWh** | `silver.price_hourly.value` ranges −15 – 423; negative spot prices are real (oversupply) |

## Silver tables

### `silver.demand_daily` — one row per day
| Column | Type | Notes |
|---|---|---|
| `date` | date | Local (Europe/Madrid) civil date; **not** UTC-shifted (a daily bucket UTC-converted lands on the wrong day) |
| `value` | double | Daily demand, MWh. DQ: must be **> 0** |

### `silver.generation_daily` — one row per (day, technology)
| Column | Type | Notes |
|---|---|---|
| `date` | date | Local civil date |
| `technology` | string | REE technology name (e.g. `Eólica`). The composite `Generación total` is excluded — see the note below; getting this wrong doubles every daily total |
| `is_renewable` | boolean | From the payload's own classification (`attributes.type == "Renovable"`), not a hardcoded map |
| `value` | double | Daily generation for the technology, MWh. **DQ policy:** renewables must be `>= 0`; thermal (non-renewable) may be slightly negative — see note below |

**The composite exclusion, and why it is defended three ways.** REE's generation payload
carries `Generación total` alongside the technologies — the sum of them, not one of
them. Included, it lands as an extra row per day, doubles the daily total and **halves
the renewables share**, while every individual value stays perfectly plausible.

A series is treated as an aggregate if **any** of three signals fires: a truthy
`composite` flag (in any encoding), the title `Generación total`, or the type `total`
(formerly `Generación total`). They are OR'd, and deliberately so — REE has changed two
of them mid-project. As of 2026-07-28 `composite` reads `False` on *every* series and no
longer distinguishes anything, and the aggregate's type was renamed. Only the title
survived both changes, and an earlier version that consulted the flag first let the dead
signal answer on behalf of the live ones.

On top of that, `type` acts as a **whitelist**: a real technology is `Renovable` or
`No-Renovable`, and anything else is **quarantined rather than dropped**, so the next
upstream rename surfaces as a row in `silver.quarantine` instead of a quietly changed
total. And `ratio_band` in the DQ gate bounds generation ÷ demand to `[0.8, 1.6]`, so a
recurrence fails the pipeline rather than reaching a report — as it did, on the first run
after the second attempt at this fix.

**Negative generation (real data, not corruption).** REE reports small negative daily values
for **thermal** technologies on near-idle days — station self-consumption net of output.
Observed across 2023-01 → 2026-07 **only for `Carbón`** (coal): 8 days, min −120 MWh, avg
−107, against a typical scale of 10⁴–10⁵. Renewables never go negative physically, so the DQ
gate flags any negative renewable value **and** any generation below −1000 MWh (gross
corruption), while tolerating the small thermal negatives. Rule:
`(is_renewable AND value < 0) OR value < -1000`.

### `silver.price_hourly` — one row per (instant, series)
| Column | Type | Notes |
|---|---|---|
| `datetime_utc` | timestamp | The instant in **UTC** (tz-naive). UTC normalization keeps the key unique across DST |
| `series` | string | `PVPC` or `Precio mercado spot` |
| `value` | double | Price, €/MWh. DQ: must be within **[−500, 4000]** |
| `period_minutes` | int | Observation grain, **derived per series**. Confirmed split: PVPC is 60-min throughout; spot is 60-min until 2024-12-31 and **15-min from 2025-01-01** (a single hardcoded grain would be wrong for half the spot history) |

### `silver.quarantine` — structurally-unparseable records (never dropped)
| Column | Type | Notes |
|---|---|---|
| `raw` | string | The offending record, re-serialized to JSON |
| `indicator` | string | Which indicator it came from |
| `reason` | string | Why parsing failed (missing field, non-numeric value, bad datetime) |
| `loaded_at` | timestamp | When it was quarantined (UTC) |

## Gold star schema

Full atomic rebuild by `nb_gold_build` (runs only downstream of a green DQ gate); natural
keys throughout — facts join dims on `date` / `technology` / `indicator` directly.

### `gold.dim_date` — generated calendar, one row per day, spanning exactly the loaded data

Gapless between its bounds, but the bounds themselves are **derived from the facts** on every
run (`MIN`/`MAX` across demand, generation and price), not hardcoded. It previously ran to a
fixed `2027-12-31`, which leaked empty future years into every consumer — an unselectable 2027
in report slicers, and rolling-window measures averaging over days holding no data.

The end bound takes the **MAX** across all three indicators, which is the opposite aggregation
to the `Data Through` measure's **MIN** of the same three dates. A calendar that falls short of
any fact orphans rows; a freshness figure that takes the max hides a lagging indicator behind
two current ones. Same three numbers, two different jobs.

| Column | Type | Notes |
|---|---|---|
| `date` | date | Key |
| `year`, `month`, `quarter` | int | Calendar parts |
| `month_name` | string | `date_format(d,'MMMM')` |
| `day_of_week` | int | `weekday()`: 0 = Monday … 6 = Sunday |
| `is_weekend` | boolean | `day_of_week >= 5` |

### `gold.dim_technology` — one row per technology (16 rows)
| Column | Type | Notes |
|---|---|---|
| `technology` | string | Key. 16 distinct non-composite series across 2023–2026 (a single month shows fewer; verified no duplicate names, so fact joins cannot fan out) |
| `is_renewable` | boolean | Carried from Silver = the API's own classification |
| `renewable_label` | string | `Renewable` / `Non-renewable` — the display form of `is_renewable`, for report legends and slicers where a raw boolean renders as "True"/"False". Derived in `nb_gold_build`, not in DAX, because Direct Lake supports no calculated columns |

### `gold.dim_indicator` — one row per ingested series (3 rows)
| Column | Type | Notes |
|---|---|---|
| `indicator` | string | Key (`demanda_evolucion`, …) — from the wheel's canonical `INDICATORS` |
| `source_path` | string | REE URL path segment |
| `silver_table` | string | Where the parsed rows live |
| `grain` | string | Human-readable grain statement |
| `unit` | string | C4-confirmed unit (`MWh` / `EUR/MWh`) |

### Facts — 1:1 projections of Silver with unit-suffixed measures
| Table | Grain | Columns |
|---|---|---|
| `gold.fact_demand_daily` (1295) | civil day | `date`, `demand_mwh` |
| `gold.fact_generation_daily` (19412) | civil day × technology | `date`, `technology`, `generation_mwh` |
| `gold.fact_price_hourly` (102763) | UTC instant × series | `datetime_utc`, `date`, `series`, `period_minutes`, `price_eur_mwh` |

**`fact_price_hourly.date` is the Madrid civil day**, computed as
`to_date(from_utc_timestamp(datetime_utc,'Europe/Madrid'))` — `to_date(datetime_utc)` would
put the first 1–2 hours of every Madrid day on the previous day and break joins against the
civil-date daily facts. `datetime_utc` remains the row identity (unique across DST);
`is_renewable` deliberately lives only on `dim_technology` (star schema: attributes on the
dimension).

### Materialized lake views (engine-refreshed)
| View | Grain | Columns |
|---|---|---|
| `gold.mlv_monthly_renewables_share` (43) | year × month | `year`, `month`, `renewable_mwh`, `total_mwh`, `renewables_share_pct` |
| `gold.mlv_monthly_avg_price` (86) | year × month × series | `year`, `month`, `series`, `avg_price_eur_mwh`, `n_observations` |

The price MLV's plain `AVG` is grain-safe: PVPC is hourly throughout and spot switched to
15-min exactly at 2025-01-01, so no (series, month) group mixes row weights.

## Control tables

- `bronze.ctl_watermark` — per-indicator ingestion watermark (Phase B).
- `ops.dq_results` — one row per DQ check per gate run (`run_ts, stage, check, table, column,
  status, observed, threshold, details`); the write-then-raise gate populates it.

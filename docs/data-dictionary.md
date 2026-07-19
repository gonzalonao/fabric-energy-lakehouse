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
| `technology` | string | REE technology name (e.g. `Eólica`). The composite `Generación total` is excluded |
| `is_renewable` | boolean | From the payload's own classification (`attributes.type == "Renovable"`), not a hardcoded map |
| `value` | double | Daily generation for the technology, MWh. **DQ policy:** renewables must be `>= 0`; thermal (non-renewable) may be slightly negative — see note below |

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

## Control tables

- `bronze.ctl_watermark` — per-indicator ingestion watermark (Phase B).
- `ops.dq_results` — one row per DQ check per gate run (`run_ts, stage, check, table, column,
  status, observed, threshold, details`); the write-then-raise gate populates it.

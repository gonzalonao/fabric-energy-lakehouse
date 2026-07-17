"""The canonical description of every REE series this project ingests.

This mirrors the ``INDICATORS`` tuple in the ``nb_gen_chunks`` ingestion notebook, but
carries the extra metadata Silver and Gold need (grain, target table, natural key). The
notebook keeps its own lightweight copy for now because it runs in Phase B pipelines
predating this wheel; once ``env_energy`` is the workspace default (C3) the notebook can
import from here and the duplication collapses. Until then, keep the two in step.
"""

from __future__ import annotations

from dataclasses import dataclass

TIME_TRUNC_DAY = "day"
TIME_TRUNC_HOUR = "hour"


@dataclass(frozen=True)
class Indicator:
    """One REE series and how it maps through the medallion layers.

    Attributes:
        path: URL path segment under ``/es/datos/`` used to fetch the series.
        name: Our name for the series; drives the Bronze path and the watermark key.
        time_trunc: API granularity requested, ``day`` or ``hour``.
        silver_table: Fully-qualified Silver Delta table the parsed rows land in.
        natural_key: Columns that uniquely identify a Silver row (dedup key).
        unit: Physical unit, or ``None`` until confirmed by profiling at C4. The REE
            payload does not state units, so this stays unasserted rather than guessed.
    """

    path: str
    name: str
    time_trunc: str
    silver_table: str
    natural_key: tuple[str, ...]
    unit: str | None


INDICATORS: tuple[Indicator, ...] = (
    Indicator(
        path="demanda/evolucion",
        name="demanda_evolucion",
        time_trunc=TIME_TRUNC_DAY,
        silver_table="silver.demand_daily",
        natural_key=("date",),
        unit=None,
    ),
    Indicator(
        path="generacion/estructura-generacion",
        name="generacion_estructura",
        time_trunc=TIME_TRUNC_DAY,
        silver_table="silver.generation_daily",
        natural_key=("date", "technology"),
        unit=None,
    ),
    Indicator(
        path="mercados/precios-mercados-tiempo-real",
        name="precios_mercados",
        time_trunc=TIME_TRUNC_HOUR,
        silver_table="silver.price_hourly",
        natural_key=("datetime_utc", "series"),
        unit=None,
    ),
)

INDICATORS_BY_NAME: dict[str, Indicator] = {ind.name: ind for ind in INDICATORS}

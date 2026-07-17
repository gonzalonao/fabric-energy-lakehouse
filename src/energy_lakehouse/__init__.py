"""Typed REE parsers and data-quality checks for the Fabric energy lakehouse.

The package is deliberately Spark-free in its core: :mod:`energy_lakehouse.parsers`
turns raw REE JSON into typed rows, and :mod:`energy_lakehouse.dq.checks` evaluates
plain numeric inputs into :class:`~energy_lakehouse.models.DQResult` verdicts. Only
:mod:`energy_lakehouse.dq.gate` touches Spark, and only to feed those pure functions.
This keeps the transformation and DQ logic unit-testable locally, off the cluster.
"""

__version__ = "0.1.0"

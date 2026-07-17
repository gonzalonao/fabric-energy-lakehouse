# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "6cabfc1b-836e-43ad-9379-94fa8bdb6c16",
# META       "default_lakehouse_name": "lh_energy",
# META       "default_lakehouse_workspace_id": "476b58fd-19e3-4c0d-bde7-c3f16d2a6fcf",
# META       "known_lakehouses": [
# META         {
# META           "id": "6cabfc1b-836e-43ad-9379-94fa8bdb6c16"
# META         }
# META       ]
# META     }
# META   }
# META }

# PARAMETERS CELL ********************

# The stage to gate (currently "silver"). Empty fails validation inside run_gate on
# purpose: an unparameterized run must error rather than gate an unintended stage.
p_stage = ""


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""Run the data-quality gate for a stage — a thin wrapper over ``energy_lakehouse``.

All the logic lives in ``energy_lakehouse.dq.gate.run_gate``: it runs every check for the
stage, writes every result to ``ops.dq_results``, then raises ``DQGateError`` if any
failed. Raising propagates as a notebook-activity failure, so the pipeline stops — but
only after the results table is written, so the failure is diagnosable from a query.
"""

import logging

from energy_lakehouse.dq.gate import run_gate

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nb_dq_gate")

logger.info("running DQ gate for stage=%r", p_stage)
run_gate(p_stage, spark)
logger.info("DQ gate passed for stage=%r", p_stage)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

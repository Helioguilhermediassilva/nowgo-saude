"""AI Workers subsystem (PRD 003).

Houses the ORM models, deterministic guards, prompts, LangGraph workflows,
and worker entrypoints for the autonomous-AI layer. The package is **import-
safe**: nothing here triggers a network call at import time — workers are
spun up explicitly by their entrypoints in ``workers/src/workers/``.

Submodule map:

* ``models``    — SQLAlchemy ORM (AnomalySignal, Recommendation, DailyBrief,
                  WorkerRun, HumanDecision).
* ``guards``    — pure-function safety filters (intent, clinical, prompt
                  injection, output sanitisation).
* ``prompts``   — versioned prompt templates (``<task>_v<n>.md``).
* ``workers``   — LangGraph state machines (lazy-imported by entrypoints).
* ``graphs``    — reusable LangGraph nodes/edges.
* ``feedback``  — HumanDecision → training signal loop.
* ``api``       — FastAPI routers for HITL endpoints.
"""

from __future__ import annotations

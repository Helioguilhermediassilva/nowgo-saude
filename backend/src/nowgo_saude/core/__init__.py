"""Cross-cutting infrastructure (observability, LLM provider, auth).

Modules under ``core/`` MUST stay free of domain logic: they expose plug-points
that ingestion, dashboard and AI features compose against.
"""

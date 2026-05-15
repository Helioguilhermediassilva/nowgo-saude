"""Cross-cutting infrastructure (auth, observability, LLM provider).

Modules under ``core/`` are deliberately framework-agnostic and free of domain
logic: they expose plug-points that ingestion, dashboard and AI features
compose against. Production swaps the default adapter via Settings without
touching call sites.
"""

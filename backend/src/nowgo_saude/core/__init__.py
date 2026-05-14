"""Cross-cutting infrastructure (LLM provider, egress guard, auth, observability).

Modules under ``core/`` MUST stay free of domain logic: they expose plug-points
that the ingestion, dashboard and AI features compose against. This isolation
is what lets the MVP swap Grok for on-prem NVIDIA NIMs (Principle I) without
touching ingestion code.
"""

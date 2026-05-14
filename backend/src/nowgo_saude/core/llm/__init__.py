"""LLM plug-point: provider interface, egress guard, concrete adapters.

The interface (``LLMProvider``) is the single contract domain code depends on.
Concrete adapters (Grok today, NVIDIA NIM tomorrow) implement it. Every
outbound call passes through :mod:`egress_guard` so Principle I (sovereignty)
and Principle II (LGPD by design) are enforced at the boundary, not at the
caller.
"""

from .grok_provider import GrokProvider
from .null_provider import NullProvider
from .provider import (
    LLMProvider,
    LLMResponse,
    LLMUnavailableError,
)

__all__ = [
    "GrokProvider",
    "LLMProvider",
    "LLMResponse",
    "LLMUnavailableError",
    "NullProvider",
]

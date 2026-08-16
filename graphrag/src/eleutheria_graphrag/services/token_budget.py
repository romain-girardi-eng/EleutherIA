"""One conservative token estimator, shared by prompt budgeting and LLM routing.

Prompt-size decisions used to be made with three different ratios: ``len // 4``
(``RetrievalBudget.estimate_tokens``, the pack packer), ``len // 3``
(``LLMService._estimate_input_tokens``, the provider-window routing gate), and
nothing at all for the sections assembled outside the pack. The result was a
"250k" pack budget sitting under an ~800k-token prompt.

This module holds the ONE estimator any prompt-budget decision must use: the
conservative (over-estimating) ``len // 3`` with a word count as the floor. It
matches what the routing gate prices, so a prompt that budgeting says fits is a
prompt the gate also says fits.

Dense polytonic Greek, Latin and citation apparatus run ~3-4 chars/token through
our proxies — hence ``len // 3``. Over-estimating is the cheap direction: it
costs a little unused context, whereas under-estimating costs a 400 and a
minutes-long fallback cascade.
"""

from __future__ import annotations


def estimate_tokens(*texts: str | None) -> int:
    """Conservative token estimate for one or more prompt fragments.

    ``max(len(text) // 3, len(text.split()))`` per fragment, summed. ``None``
    and empty fragments contribute 0.
    """
    total = 0
    for text in texts:
        if not text:
            continue
        total += max(len(text) // 3, len(text.split()))
    return total


def format_tokens(value: int) -> str:
    """Compact token count for log lines: 120000 -> '120k', 1000000 -> '1M'."""
    if value >= 1_000_000 and value % 1_000_000 == 0:
        return f"{value // 1_000_000}M"
    if value >= 1000:
        return f"{value // 1000}k"
    return str(value)

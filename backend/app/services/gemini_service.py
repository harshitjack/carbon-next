"""
OpenRouter AI service for personalised carbon reduction insights.

Replaces the former Vertex AI / Gemini SDK integration.
Calls the OpenRouter OpenAI-compatible REST API via httpx (async).

Security checkpoint (per global security rule):
  1. Scrubs SSNs and credit-card numbers from any string fields before they
     reach the model or logs.
  2. Detects prompt-injection patterns â€” if found, raises
     GeminiUnavailableError and the route falls back to the rule engine
     without the payload ever reaching the LLM.

Identical external contract to the previous gemini_service:
  generate_insights_gemini(ranked_categories, breakdown, total_kg) â†’ list[InsightItem]
  GeminiUnavailableError
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.core.config import get_settings
from app.models.insights import InsightItem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security checkpoint patterns
# ---------------------------------------------------------------------------

# SSN: 123-45-6789 or 123 45 6789 or 123456789
_SSN_RE = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b")

# Credit-card numbers: 13â€“19 digit groups (optionally separated by spaces/dashes)
_CC_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")

# Prompt-injection: phrases attempting to override model instructions
_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+(all\s+)?previous\s+instructions?",
        r"disregard\s+(all\s+)?previous",
        r"you\s+are\s+now\s+(?:a\s+)?(?:DAN|jailbreak|uncensored)",
        r"auto[_-]?approve",
        r"bypass\s+(?:rules?|checks?|security)",
        r"forget\s+(?:all\s+)?(?:your\s+)?(?:previous\s+)?instructions?",
        r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions?",
    ]
]

_REDACTED = "[REDACTED]"


def _scrub_pii(text: str) -> tuple[str, list[str]]:
    """
    Remove SSNs and credit-card numbers from *text*.

    Returns:
        (scrubbed_text, list_of_redacted_categories)
    """
    redacted: list[str] = []

    if _SSN_RE.search(text):
        text = _SSN_RE.sub(_REDACTED, text)
        redacted.append("SSN")

    if _CC_RE.search(text):
        text = _CC_RE.sub(_REDACTED, text)
        redacted.append("credit-card")

    return text, redacted


def _detect_injection(text: str) -> bool:
    """Return True if *text* contains prompt-injection patterns."""
    return any(p.search(text) for p in _INJECTION_PATTERNS)


def _security_check_prompt(prompt: str) -> str:
    """
    Apply security checkpoint to the prompt before it reaches the LLM.

    1. Scrubs PII (SSNs, CC numbers).
    2. Raises GeminiUnavailableError (routes to human review) if
       prompt-injection is detected.

    Returns:
        Sanitised prompt string.

    Raises:
        GeminiUnavailableError: On injection detection (bypasses LLM entirely).
    """
    # Injection check on raw text first (before PII scrubbing)
    if _detect_injection(prompt):
        logger.warning(
            "SECURITY: Prompt-injection attempt detected â€” routing to fallback without LLM call"
        )
        raise GeminiUnavailableError(
            "Prompt injection detected; request routed to rule-based fallback for human review."
        )

    # PII scrub
    clean_prompt, redacted_categories = _scrub_pii(prompt)
    if redacted_categories:
        logger.info(
            "SECURITY: Redacted PII categories from prompt: %s",
            ", ".join(redacted_categories),
        )

    return clean_prompt


# ---------------------------------------------------------------------------
# Public error type (preserved from original gemini_service)
# ---------------------------------------------------------------------------


class GeminiUnavailableError(Exception):
    """Raised when the AI service cannot produce a valid response (network, parse, timeout)."""


# ---------------------------------------------------------------------------
# Prompt builder (unchanged logic from original)
# ---------------------------------------------------------------------------


def _build_prompt(
    ranked_categories: list[dict[str, Any]],
    breakdown: dict[str, float],
    total_kg: float,
) -> str:
    """Construct the structured prompt for the AI model."""
    category_lines = "\n".join(
        f"  {i + 1}. {item['category'].title()}: {item['kg']} kg CO2e/year "
        f"({item['percentage']}% of total)"
        for i, item in enumerate(ranked_categories)
    )

    return f"""\
You are a carbon footprint reduction expert helping a user reduce their personal CO2e emissions.

USER'S CARBON FOOTPRINT PROFILE:
- Total annual footprint: {total_kg} kg CO2e/year
- Breakdown by category (ranked largest first):
{category_lines}

TASK:
Generate exactly 3 highly personalized, quantified carbon reduction actions for this user.

REQUIREMENTS for each action:
1. Target this user's ACTUAL biggest emission sources (use the ranked list above)
2. Include a SPECIFIC estimated annual CO2e saving in kg (be realistic, not exaggerated)
3. Be ACTIONABLE within 30 days â€” no vague advice like "be more conscious"
4. Be SPECIFIC â€” e.g., "Switch daily 15 km petrol commute to train" not just "use less transit"
5. The saving estimate must reflect user's actual numbers (e.g., drive 20k km/year)

RESPONSE FORMAT:
Return ONLY a valid JSON array. No markdown, no explanation, no code fences. Example:
[
  {{
    "category": "transport",
    "action": "Replace daily petrol car commute with transit 4 days per week.",
    "estimated_saving_kg": 1200.0,
    "timeframe": "Achievable within 30 days",
    "priority": 1
  }},
  ...
]

Valid category values: transport, home, diet, consumption
Priority must be 1, 2, or 3 (1 = highest impact)
"""


# ---------------------------------------------------------------------------
# Main service function (identical signature to original)
# ---------------------------------------------------------------------------


async def generate_insights_gemini(
    ranked_categories: list[dict[str, Any]],
    breakdown: dict[str, float],
    total_kg: float,
) -> list[InsightItem]:
    """
    Call OpenRouter (google/gemini-flash-1.5) to generate personalised carbon insights.

    Security checkpoint is applied before the prompt reaches the model:
      - PII (SSNs, credit-card numbers) is scrubbed.
      - Prompt-injection attempts bypass the LLM entirely and raise
        GeminiUnavailableError so the route falls back to the rule engine.

    Args:
        ranked_categories: Sorted list of {category, kg, percentage} dicts (biggest first).
        breakdown: Per-category kg CO2e dict.
        total_kg: Total annual footprint in kg CO2e.

    Returns:
        List of exactly 3 InsightItem instances.

    Raises:
        GeminiUnavailableError: If the API returns an error, invalid JSON, or times out.
    """
    settings = get_settings()

    if not settings.OPENROUTER_API_KEY:
        raise GeminiUnavailableError("OPENROUTER_API_KEY is not configured")

    raw_prompt = _build_prompt(ranked_categories, breakdown, total_kg)

    # ── Security checkpoint ───────────────────────────────────────────
    clean_prompt = _security_check_prompt(raw_prompt)
    # ──────────────────────────────────────────────────────────────────

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": clean_prompt}],
        "temperature": 0.4,
        "top_p": 0.8,
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/climate-iq",
        "X-Title": "EcoTracker",
    }

    try:
        async with httpx.AsyncClient(
            base_url=settings.OPENROUTER_BASE_URL,
            timeout=httpx.Timeout(15.0),  # 15-second hard timeout (matches original)
        ) as client:
            response = await client.post(
                "/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()
        raw_text: str = data["choices"][0]["message"]["content"].strip()

        # Strip potential markdown code fences the model sometimes adds
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
            raw_text = raw_text.rsplit("```", 1)[0].strip()

        raw_insights: list[dict[str, Any]] = json.loads(raw_text)

        if not isinstance(raw_insights, list) or len(raw_insights) == 0:
            raise ValueError("AI returned empty or non-list JSON")

        # Parse and validate each insight through Pydantic
        items: list[InsightItem] = []
        for idx, raw in enumerate(raw_insights[:3], start=1):
            raw["priority"] = idx  # Normalise priority to 1â€“3 sequence
            items.append(InsightItem(**raw))

        logger.info("OpenRouter generated %d insights successfully", len(items))
        return items

    except GeminiUnavailableError:
        raise
    except Exception as exc:
        logger.warning("OpenRouter unavailable: %s â€” %s", type(exc).__name__, exc)
        raise GeminiUnavailableError(f"OpenRouter call failed: {exc}") from exc

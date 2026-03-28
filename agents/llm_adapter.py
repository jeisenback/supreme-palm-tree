from __future__ import annotations

import logging
import os
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class APIKeyError(Exception):
    """Raised when ANTHROPIC_API_KEY is not set and a live adapter is required."""


class ContentGenerationError(Exception):
    """Raised when the API call succeeds but returns an unusable response."""


# ---------------------------------------------------------------------------
# Adapter interface + no-op
# ---------------------------------------------------------------------------

class LLMAdapter:
    """Provider interface for LLMs."""

    def summarize(self, text: str, **params: Any) -> str:
        raise NotImplementedError()

    def generate(self, prompt: str, **params: Any) -> str:
        raise NotImplementedError()


class NoOpAdapter(LLMAdapter):
    """Safe no-op adapter used when no provider key is configured.

    Returns deterministic canned responses so callers can continue without
    requiring network access.
    """

    def summarize(self, text: str, **params: Any) -> str:
        return "[LLM disabled] summary unavailable."

    def generate(self, prompt: str, **params: Any) -> str:
        return "[LLM disabled] generation unavailable."


# ---------------------------------------------------------------------------
# Legacy adapter (v1/complete — kept for backwards compatibility)
# ---------------------------------------------------------------------------

class AnthropicAdapter(LLMAdapter):
    """Minimal Anthropic REST API adapter using `requests`.

    This adapter is intentionally small and defensive: it performs an HTTP
    POST to the Anthropic completion endpoint and returns the textual output.
    It will never raise on network/API errors — instead it returns a helpful
    error string so callers can continue.
    """

    DEFAULT_URL = "https://api.anthropic.com/v1/complete"

    def __init__(self, api_key: str, api_url: Optional[str] = None, model: str = "claude-2") -> None:
        self.api_key = api_key
        self.api_url = api_url or os.environ.get("ANTHROPIC_API_URL") or self.DEFAULT_URL
        self.model = model

    def _call_api(self, prompt: str, max_tokens: int = 512, **kwargs: Any) -> str:
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        body = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens_to_sample": int(max_tokens),
        }
        try:
            resp = requests.post(self.api_url, json=body, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                for key in ("completion", "completion_text", "output", "response", "text"):
                    if key in data and isinstance(data[key], str):
                        return data[key]
                if "completion" in data and isinstance(data["completion"], dict):
                    comp = data["completion"]
                    return str(comp.get("response") or comp.get("text") or comp).strip()
            return str(data)
        except Exception as e:
            return f"[anthropic-error] {e}"

    def summarize(self, text: str, **params: Any) -> str:
        prompt = f"Summarize the following text in one concise paragraph:\n\n{text}\n\nSummary:\n"
        return self._call_api(prompt, max_tokens=params.get("max_tokens", 200))

    def generate(self, prompt: str, **params: Any) -> str:
        return self._call_api(prompt, max_tokens=params.get("max_tokens", 512))


# ---------------------------------------------------------------------------
# Messages API adapter (v1/messages — current)
# ---------------------------------------------------------------------------

_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"
_DEFAULT_DRAFT_MODEL = "claude-haiku-4-5-20251001"

# Approximate token budget for grounding context.
# 1 token ≈ 4 characters (conservative estimate for English prose).
_TOKEN_BUDGET_CHARS = 9_000 * 4  # 9K tokens → ~36K chars


class AnthropicMessagesAdapter(LLMAdapter):
    """Anthropic Messages API adapter (v1/messages).

    Uses the current messages format with system + user roles.
    Raises ContentGenerationError on API or parsing failures so callers
    can decide how to surface the error (e.g. preserve editor content).
    """

    def __init__(
        self,
        api_key: str,
        model: str = _DEFAULT_DRAFT_MODEL,
        max_tokens: int = 2048,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout

    def _call_messages(
        self,
        user_message: str,
        system_message: str = "",
        max_tokens: Optional[int] = None,
    ) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "messages": [{"role": "user", "content": user_message}],
        }
        if system_message:
            body["system"] = system_message

        try:
            resp = requests.post(_MESSAGES_URL, json=body, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise ContentGenerationError(f"API request failed: {exc}") from exc

        try:
            data = resp.json()
            content_blocks = data.get("content", [])
            text_parts = [b["text"] for b in content_blocks if b.get("type") == "text"]
            result = "\n".join(text_parts).strip()
        except Exception as exc:
            raise ContentGenerationError(f"Failed to parse API response: {exc}") from exc

        if not result:
            raise ContentGenerationError("API returned an empty response.")

        return result

    def summarize(self, text: str, **params: Any) -> str:
        system = "You are a concise summarizer. Return one paragraph only."
        user = f"Summarize:\n\n{text}"
        try:
            return self._call_messages(user, system_message=system, max_tokens=params.get("max_tokens", 300))
        except ContentGenerationError as exc:
            return f"[anthropic-error] {exc}"

    def generate(self, prompt: str, **params: Any) -> str:
        try:
            return self._call_messages(prompt, max_tokens=params.get("max_tokens", self.max_tokens))
        except ContentGenerationError as exc:
            return f"[anthropic-error] {exc}"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_adapter_from_env() -> LLMAdapter:
    """Return an adapter instance based on environment variables.

    - If ANTHROPIC_API_KEY is set → AnthropicMessagesAdapter (v1/messages).
    - Otherwise → NoOpAdapter.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return NoOpAdapter()

    model = os.environ.get("ANTHROPIC_MODEL", _DEFAULT_DRAFT_MODEL)
    return AnthropicMessagesAdapter(api_key=api_key, model=model)


# ---------------------------------------------------------------------------
# High-level content draft generator (used by Content Studio)
# ---------------------------------------------------------------------------

_SLOT_PROMPTS = {
    "slides": (
        "Generate a slide deck for this IIBA ETN session. "
        "Use '## Slide N — Title' headers. Each slide: title, 3–5 bullet points, "
        "one [FACILITATOR: cue] note. Include a '## Learning Objective' slide first. "
        "Target 8–12 slides total."
    ),
    "handout": (
        "Generate a participant handout for this IIBA ETN session. "
        "Include: Learning Objectives, Key Concepts, guided exercises, homework instructions."
    ),
    "facilitator_script": (
        "Generate a facilitator script with exact talking points, timing notes, "
        "and [FACILITATOR: cue] annotations for each section."
    ),
    "facilitator_guide": (
        "Generate a facilitator guide with session overview, learning objectives, "
        "step-by-step facilitation instructions, and debrief questions."
    ),
    "participant_handout": (
        "Generate a participant handout with pre-work instructions, "
        "in-session activities, and reflection prompts."
    ),
    "moderator_script": (
        "Generate a panel moderator script with opening remarks, "
        "question sequence, transition phrases, and closing."
    ),
    "panel_agenda": (
        "Generate a panel event agenda with time slots, segment descriptions, "
        "and logistics notes."
    ),
}

_DEFAULT_SLOT_PROMPT = (
    "Generate high-quality IIBA ETN curriculum content for this session slot. "
    "Follow the style guide and maintain professional, educational tone."
)


def generate_content_draft(
    content_type: str,
    slot: str,
    context: dict,
) -> str:
    """Generate a first-draft content string for a given content type + slot.

    Args:
        content_type: e.g. 'ecba_session', 'career_accelerator', 'panel_event'
        slot:         e.g. 'slides', 'handout', 'facilitator_guide'
        context:      dict with optional keys:
                        master_context  str  — TrailBlaze_MasterContext.md text
                        style_guide     str  — ECBA_Style_Guide.md text
                        example_slides  str  — Session1_Slides.md text (few-shot)
                        session_n       int  — ECBA session number (1–5)
                        topic           str  — human-readable session topic
                        subtype         str  — career_accelerator subtype name

    Returns:
        Generated markdown string (first draft — not auto-saved).

    Raises:
        APIKeyError            if ANTHROPIC_API_KEY is not set.
        ContentGenerationError on API failure or empty response.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise APIKeyError(
            "ANTHROPIC_API_KEY is not set. "
            "Set the environment variable to enable AI generation."
        )

    adapter = AnthropicMessagesAdapter(api_key=api_key)

    # Build grounding context — apply token budget
    style_guide = context.get("style_guide", "")
    master_context = context.get("master_context", "")
    example_slides = context.get("example_slides", "")

    grounding_parts = [style_guide, master_context, example_slides]
    total_chars = sum(len(p) for p in grounding_parts)

    if total_chars > _TOKEN_BUDGET_CHARS:
        logger.warning(
            "Grounding context exceeds 9K token budget (%d chars). "
            "Falling back to style guide only.",
            total_chars,
        )
        grounding = style_guide
    else:
        grounding = "\n\n---\n\n".join(p for p in grounding_parts if p)

    # Build system message from grounding docs
    system_parts = ["You are an expert curriculum designer for the IIBA East Tennessee Chapter."]
    if grounding:
        system_parts.append(
            "Use the following reference materials to inform the content:\n\n" + grounding
        )
    system_message = "\n\n".join(system_parts)

    # Build user message
    slot_instruction = _SLOT_PROMPTS.get(slot, _DEFAULT_SLOT_PROMPT)
    topic = context.get("topic", "")
    session_n = context.get("session_n")
    subtype = context.get("subtype", "")

    label_parts = [f"Content type: {content_type}", f"Slot: {slot}"]
    if session_n:
        label_parts.append(f"Session: {session_n}")
    if topic:
        label_parts.append(f"Topic: {topic}")
    if subtype:
        label_parts.append(f"Subtype: {subtype}")

    user_message = "\n".join(label_parts) + "\n\n" + slot_instruction

    result = adapter._call_messages(user_message, system_message=system_message)

    # Warn if output looks truncated (no closing slide separator)
    if slot == "slides" and not result.rstrip().endswith(("---", "##")):
        logger.warning("Generated slide deck may be incomplete — no closing separator found.")

    return result

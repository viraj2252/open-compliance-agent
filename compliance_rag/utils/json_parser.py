"""
Robust JSON parser that handles common LLM output quirks.
Strips markdown code fences, extracts JSON from mixed text, and retries parsing.
"""
import json
import re
import logging

logger = logging.getLogger(__name__)


def parse_llm_json(raw: str) -> dict:
    """
    Robustly parse JSON from LLM output.
    Handles:
    - Markdown ```json ... ``` blocks
    - Leading/trailing whitespace
    - Partial JSON embedded in prose
    """
    if not raw or not raw.strip():
        logger.warning("Received empty string for JSON parsing.")
        return {}

    text = raw.strip()

    # 1. Strip markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # 2. Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Try to extract first JSON object from mixed text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # 4. Try to extract first JSON array from mixed text
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    logger.error(f"Failed to parse JSON from LLM output: {text[:200]}...")
    return {}

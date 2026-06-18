import json
import logging
import random
import re
import asyncio
from groq import Groq, RateLimitError

logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 3
RETRY_BASE_SECONDS = 5

_FALLBACK = {"level": "NA", "summary": "Could not parse analysis."}
_NO_README = {"level": "NA", "summary": "This repository has no README."}

_client: Groq | None = None

# To switch back to Gemini:
# 1. Comment out the Groq lines and uncomment the Gemini lines in requirements.txt
# 2. Replace this file with the Gemini version (use google.genai.Client + asyncio.to_thread)


def configure(api_key: str) -> None:
    global _client
    _client = Groq(api_key=api_key)


async def analyze_readme(readme: str | None) -> dict:
    if not readme:
        return _NO_README

    prompt = (
        'Analyze this README and return ONLY a JSON object with no extra text:\n'
        '{"level": "Basic" | "Intermediate" | "Advanced", '
        '"summary": "<2-3 sentences: what the project does, its complexity, and the experience level required>"}\n\n'
        f"README:\n{readme}"
    )

    for attempt in range(MAX_RETRIES):
        try:
            response = await asyncio.to_thread(
                _client.chat.completions.create,
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            text = response.choices[0].message.content.strip()

            # Strip markdown code fences if present
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

            parsed = json.loads(text)
            if parsed.get("level") not in ("Basic", "Intermediate", "Advanced"):
                parsed["level"] = "NA"
            if not isinstance(parsed.get("summary"), str):
                parsed["summary"] = _FALLBACK["summary"]
            return parsed

        except RateLimitError as e:
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BASE_SECONDS * (attempt + 1) + random.uniform(0, 2)
                logger.warning(
                    "Groq rate limited, retrying in %.1fs (attempt %d/%d)",
                    wait, attempt + 1, MAX_RETRIES,
                )
                await asyncio.sleep(wait)
            else:
                logger.error("Groq rate limit reached, giving up: %s", e)
                return _FALLBACK

        except Exception as e:
            logger.error("analyze_readme failed: %s", e)
            return _FALLBACK

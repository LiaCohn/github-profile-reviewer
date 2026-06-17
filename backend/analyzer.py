import json
import re
import asyncio
from groq import Groq, RateLimitError

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

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                _client.chat.completions.create,
                model="llama-3.3-70b-versatile",
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
            if attempt < max_retries - 1:
                wait = 5 * (attempt + 1)  # 5s, 10s, 15s
                print(f"Rate limited, retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait)
            else:
                print("analyze_readme error (rate limit, giving up):", e)
                return _FALLBACK

        except Exception as e:
            print("analyze_readme error:", e)
            return _FALLBACK

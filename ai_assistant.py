# ai_assistant.py
"""
Generates a draft "Outlook & Analyst Notes" paragraph for the quarterly
market report using an external AI text-generation API.

The provider is intentionally not named anywhere in the UI — the app only
ever refers to this as "the AI assistant" — but is documented here in code
for anyone maintaining this module: it calls the DeepSeek chat completions
API (OpenAI-compatible schema), configured entirely via the API key saved
on the Settings tab (stored in the local app_settings table, never checked
into source control or logged).
"""
import requests

_API_URL = "https://api.deepseek.com/chat/completions"
_MODEL = "deepseek-chat"
_TIMEOUT_SECONDS = 45


class AIAssistantError(Exception):
    """Raised for any failure calling the AI assistant, with a message
    that's safe to show directly in the UI (no key/vendor leakage)."""
    pass


def _build_prompt(quarter: str, year: int, benchmark_stats, product_stats, developments) -> str:
    lines = [
        f"Draft a concise, professional 'Outlook & Analyst Notes' section for a {quarter} {year} "
        f"oil market intelligence report prepared for a refiner's Marketing Operations Group. "
        f"Write 2-3 short paragraphs. Do not invent numbers beyond what is given below; if data "
        f"is sparse, focus commentary on the developments listed instead.",
        "",
        "Benchmark price movement this quarter:",
    ]
    if benchmark_stats is not None and not benchmark_stats.empty:
        for _, row in benchmark_stats.iterrows():
            lines.append(
                f"- {row['Benchmark']}: opened {row['Open']}, closed {row['Close']}, "
                f"change {row['Change']} ({row['Change %']}%)"
            )
    else:
        lines.append("- No benchmark readings recorded for this quarter.")

    lines.append("")
    lines.append("Refined product movement this quarter:")
    if product_stats is not None and not product_stats.empty:
        for _, row in product_stats.iterrows():
            lines.append(
                f"- {row['Product']}: opened {row['Open']}, closed {row['Close']}, "
                f"change {row['Change']} ({row['Change %']}%)"
            )
    else:
        lines.append("- No product readings recorded for this quarter.")

    lines.append("")
    lines.append("Key market developments logged this quarter:")
    if developments is not None and not developments.empty:
        for _, row in developments.iterrows():
            lines.append(f"- [{row.get('category', '')}, {row.get('impact', '')} impact] {row.get('headline', '')}")
    else:
        lines.append("- No developments logged for this quarter.")

    return "\n".join(lines)


def generate_ai_outlook(api_key: str, quarter: str, year: int, benchmark_stats, product_stats, developments) -> str:
    """Calls the configured AI assistant and returns a draft outlook paragraph.
    Raises AIAssistantError with a UI-safe message on any failure."""
    if not api_key:
        raise AIAssistantError("No AI assistant API key is configured. Add one on the Settings tab.")

    prompt = _build_prompt(quarter, year, benchmark_stats, product_stats, developments)

    try:
        response = requests.post(
            _API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": _MODEL,
                "messages": [
                    {"role": "system", "content": "You are a senior oil markets analyst writing internal reports."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
                "max_tokens": 500,
                "stream": False,
            },
            timeout=_TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as ex:
        raise AIAssistantError(f"Could not reach the AI assistant service: {str(ex)}") from ex

    if response.status_code == 401:
        raise AIAssistantError("The AI assistant API key was rejected. Check the key on the Settings tab.")
    if response.status_code != 200:
        raise AIAssistantError(f"The AI assistant service returned an error (status {response.status_code}).")

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, ValueError) as ex:
        raise AIAssistantError("The AI assistant returned an unexpected response format.") from ex

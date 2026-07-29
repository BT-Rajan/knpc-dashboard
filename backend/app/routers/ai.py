import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.schemas import AIAskRequest, AIAskResponse
from app.services import get_item_by_code_or_404, trend_fields, recent_news, resolve_ai_key
from app.config import DEEPSEEK_API_URL, DEEPSEEK_MODEL, CLAUDE_API_URL, CLAUDE_MODEL

router = APIRouter(prefix="/api/ai", tags=["ai"], dependencies=[Depends(get_current_user)])


def _build_context(db: Session, item_code: str | None) -> str:
    if not item_code:
        return ""
    item = get_item_by_code_or_404(db, item_code)
    fields = trend_fields(db, item.id)
    news = recent_news(db, item.id, limit=5)
    lines = [
        f"Item: {item.name} ({item.category}, {item.unit})",
        f"Current price: {fields['current_price']}, previous: {fields['previous_price']}, "
        f"daily change: {fields['daily_change']} ({fields['daily_change_pct']}%), as of {fields['as_of']}",
        "Recent headlines:",
    ]
    lines += [f"- {n.headline}" for n in news] or ["- (none collected yet)"]
    return "\n".join(lines)


def _ask_deepseek(prompt: str, api_key: str) -> str:
    if not api_key:
        raise HTTPException(status_code=503, detail="DeepSeek API key is not configured. Add it under Admin -> AI Settings.")
    try:
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": DEEPSEEK_MODEL, "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except requests.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"DeepSeek API error: {exc.response.status_code} {exc.response.text[:200]}")
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"DeepSeek request failed: {exc}")


def _ask_claude(prompt: str, api_key: str) -> str:
    if not api_key:
        raise HTTPException(status_code=503, detail="Claude API key is not configured. Add it under Admin -> AI Settings.")
    try:
        resp = requests.post(
            CLAUDE_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": 800,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        blocks = resp.json().get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    except requests.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Claude API error: {exc.response.status_code} {exc.response.text[:200]}")
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Claude request failed: {exc}")


@router.post("/ask", response_model=AIAskResponse)
def ask(body: AIAskRequest, db: Session = Depends(get_db)):
    context = _build_context(db, body.item_code)
    prompt = (
        f"You are a market intelligence assistant for a petroleum pricing dashboard.\n"
        f"{('Context:\\n' + context) if context else ''}\n\n"
        f"Question: {body.question}\n"
        f"Answer concisely, and note explicitly if the available data is insufficient."
    )

    if body.provider == "deepseek":
        answer = _ask_deepseek(prompt, resolve_ai_key(db, "deepseek"))
    elif body.provider == "claude":
        answer = _ask_claude(prompt, resolve_ai_key(db, "claude"))
    else:
        raise HTTPException(status_code=422, detail="provider must be 'deepseek' or 'claude'")

    return AIAskResponse(provider=body.provider, answer=answer)

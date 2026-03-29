import json
import os
from openai import OpenAI

MODEL = "openai/gpt-oss-120b:free"

SYSTEM_PROMPT = """You are a Kanban board assistant. The user's current board state is provided at the start of each message as JSON.

You must ALWAYS respond with valid JSON matching this exact schema — no markdown, no extra text:
{{
  "reply": "<your conversational response to the user>",
  "board_update": {{
    "cards_to_create": [{{"column_title": "<exact column title>", "title": "<card title>", "details": "<card details>"}}],
    "cards_to_update": [{{"card_id": "<card-N>", "title": "<new title>", "details": "<new details>"}}],
    "cards_to_delete": [{{"card_id": "<card-N>"}}],
    "cards_to_move":   [{{"card_id": "<card-N>", "column_title": "<exact column title>"}}]
  }}
}}

All four arrays in board_update are required and can be empty.
For cards_to_update, include only the fields you want to change (title and/or details).
Use the exact column titles from the board. Use the exact card IDs (e.g. "card-5") from the board."""


def _board_to_context(board: dict) -> str:
    """Render board as compact text for the system message."""
    lines = []
    for col in board["columns"]:
        lines.append(f"Column: {col['title']}")
        for cid in col["cardIds"]:
            card = board["cards"].get(cid, {})
            lines.append(f"  - [{cid}] {card.get('title', '')} | {card.get('details', '')}")
    return "\n".join(lines)


def get_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


def chat(messages: list[dict]) -> str:
    """Low-level chat call. Returns raw text content."""
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    return response.choices[0].message.content or ""


def board_chat(board: dict, history: list[dict], user_message: str) -> dict:
    """
    Call the AI with full board context.

    Returns a dict with keys:
      reply        str
      board_update dict with cards_to_create/update/delete/move
    """
    board_context = _board_to_context(board)
    system = SYSTEM_PROMPT + f"\n\nCurrent board:\n{board_context}"

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    client = get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {}

    # Ensure schema is always complete
    update = result.get("board_update", {})
    return {
        "reply": result.get("reply", ""),
        "board_update": {
            "cards_to_create": update.get("cards_to_create", []),
            "cards_to_update": update.get("cards_to_update", []),
            "cards_to_delete": update.get("cards_to_delete", []),
            "cards_to_move":   update.get("cards_to_move", []),
        },
    }

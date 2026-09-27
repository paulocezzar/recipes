"""Turn recipe photos and/or pasted text into structured recipe data with Claude."""
import base64
import json
import os
import re

from django.conf import settings

PROMPT = """You are turning a recipe into clean structured data for a personal recipe collection. The recipe is in the attached photo(s) and/or the pasted text below. Photos may be cookbook pages, handwritten cards or screenshots; if there are several they are consecutive pages of ONE recipe.

Reply with only a JSON object of exactly this shape:
{"title": string, "description": string, "servings": string, "prep": string, "cook": string,
 "ingredients": [{"heading": string, "items": [{"qty": string, "item": string}]}],
 "method": [{"heading": string, "steps": [string]}],
 "notes": string, "source": string}

Rules:
- Transcribe faithfully. Never invent quantities, steps or times. Use "" for anything not given.
- qty holds the amount and unit exactly as written ("200 g", "1 tbsp", "2", "½ cup"). For "salt, to taste" put "" in qty and keep the words in item. item holds the ingredient plus any prep note ("onion, finely chopped").
- Only use ingredient/method headings if the recipe itself groups them (e.g. "For the icing"); otherwise one group with heading "".
- One step per instruction paragraph or numbered step, without the step number. Fix obvious OCR or typing errors only.
- description: the recipe's own intro in one or two sentences if it has one, else "".
- servings like "4" or "12 buns"; prep/cook like "20 min", "1 hr 10 min".
- notes: tips, storage, variations from the source. source: book/website/author name if visible.
- If there is no recipe at all, reply {"error": "short reason"}."""


class ReaderError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.message = message
        self.status = status


def _parse_json(text):
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def read_recipe(images, text):
    """images: list of (bytes, media_type). text: str. Returns dict."""
    import anthropic

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise ReaderError("Photo reading isn't set up yet: add ANTHROPIC_API_KEY in Render's settings.", 503)
    client = anthropic.Anthropic(timeout=100, max_retries=1)

    content = []
    for data, media_type in images:
        content.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": base64.b64encode(data).decode()},
            }
        )
    prompt = PROMPT + ("\n\nPasted text:\n" + text[:20000] if text else "\n\n(No pasted text; read the photos.)")
    content.append({"type": "text", "text": prompt})

    try:
        msg = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": content}],
        )
    except anthropic.AuthenticationError as exc:
        raise ReaderError("The Anthropic API key was rejected. Check ANTHROPIC_API_KEY in Render.", 503) from exc
    except anthropic.RateLimitError as exc:
        raise ReaderError("Too many requests just now. Wait a minute and try again.", 429) from exc
    except anthropic.BadRequestError as exc:
        raise ReaderError("That photo couldn't be read. Try a clearer or smaller photo.", 400) from exc
    except anthropic.APIError as exc:
        raise ReaderError("The recipe reader isn't responding. Try again in a moment.", 502) from exc

    reply = "".join(getattr(block, "text", "") for block in msg.content)
    try:
        data = _parse_json(reply)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ReaderError("The recipe came back in an unexpected shape. Try again, or crop the photo to just the recipe.") from exc
    if not isinstance(data, dict):
        raise ReaderError("The recipe came back in an unexpected shape. Try again.")
    return data

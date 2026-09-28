def strip_code_fences(content: str) -> str:
    """Strip a ```/```json code fence some models wrap JSON responses in."""
    text = content.strip()
    if not text.startswith("```"):
        return text
    text = text[3:]
    if text.startswith("json"):
        text = text[4:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

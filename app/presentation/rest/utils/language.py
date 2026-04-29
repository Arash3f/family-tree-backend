def detect_language(request) -> str:
    """
    Detect user's language from Accept-Language header.

    Returns:
        'fa' if the header contains a Persian language preference (fa, fa-IR, etc.),
        otherwise 'en'.
    """
    raw = request.headers.get("accept-language", "en")
    value = raw.lower().strip()

    # Common case: "fa", "fa-IR"
    if value.startswith("fa"):
        return "fa"

    # More realistic: "fa-IR, en;q=0.9"
    if "fa" in [part.strip() for part in value.split(",")][0] or "fa" in value:
        return "fa"

    return "en"

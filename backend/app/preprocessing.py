import re


HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
WHITESPACE_PATTERN = re.compile(r"\s+")


# Normalizes enterprise ticket text before classification and retrieval.
def clean_text(text: str) -> str:
    without_html = HTML_TAG_PATTERN.sub(" ", text)
    without_urls = URL_PATTERN.sub(" ", without_html)
    normalized = WHITESPACE_PATTERN.sub(" ", without_urls)
    return normalized.strip().lower()

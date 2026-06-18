from urllib.parse import quote_plus


BRAVE_SUBMIT_URL = "https://search.brave.com/submit-url"
BRAVE_SEARCH_URL = "https://search.brave.com/search"


def submit_url() -> str:
    return BRAVE_SUBMIT_URL


def site_search_url(url: str) -> str:
    query = f"site:{url}"
    return f"{BRAVE_SEARCH_URL}?q={quote_plus(query)}"


def domain_search_url(domain: str) -> str:
    query = f"site:{domain}"
    return f"{BRAVE_SEARCH_URL}?q={quote_plus(query)}"

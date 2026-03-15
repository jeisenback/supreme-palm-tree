"""Registry for scraper source configurations (PoC)."""

_REGISTRY: dict[str, dict] = {}


def register_source(source_id: str, url: str, parser: str, selectors: dict) -> None:
    _REGISTRY[source_id] = {
        "id": source_id,
        "url": url,
        "parser": parser,
        "selectors": selectors,
    }


def get_source(source_id: str) -> dict | None:
    return _REGISTRY.get(source_id)


def list_sources() -> list[dict]:
    return list(_REGISTRY.values())

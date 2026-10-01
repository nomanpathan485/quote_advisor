from langchain_tavily import TavilySearch
import re


def search_web(query: str) -> dict:
    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    search_tool = TavilySearch(
        max_results=3,
        topic="general",
        search_depth="basic",
        include_answer=False,
        include_raw_content=False,
    )

    response = search_tool.invoke({"query": query})

    if not isinstance(response, dict):
        raise RuntimeError("Search returned an unexpected response.")

    if response.get("error"):
        raise RuntimeError(f"Search failed: {response['error']}")

    if not isinstance(response.get("results"), list):
        raise RuntimeError("Search response is missing its results list.")

    return response

def filter_hotel_candidates(
    hotel_name: str,
    results: list[dict],
) -> list[dict]:
    if not hotel_name.strip():
        raise ValueError("Hotel name cannot be empty.")

    pattern = re.compile(
        rf"(?<!\w){re.escape(hotel_name.strip())}(?!\w)",
        flags=re.IGNORECASE,
    )

    candidates = []

    for result in results:
        title = result.get("title") or ""

        if pattern.search(title):
            candidates.append(result)

    return candidates
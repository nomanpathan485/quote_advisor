from langchain_tavily import TavilyExtract


def extract_pages(urls: list[str]) -> dict:
    """Retrieve page text while retaining source URLs and failures."""
    if not urls:
        raise ValueError("No URLs provided for extraction.")

    tool = TavilyExtract(
        extract_depth="basic",
        include_images=False,
        format="markdown",
    )

    response = tool.invoke({"urls": urls})

    if not isinstance(response, dict):
        raise RuntimeError("Page extraction returned an unexpected response.")

    if response.get("error"):
        raise RuntimeError(f"Page extraction failed: {response['error']}")

    if not isinstance(response.get("results"), list):
        raise RuntimeError("Page extraction response is missing results.")

    return response
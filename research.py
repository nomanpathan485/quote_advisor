from pathlib import Path
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from schemas.quote import Quote
from services.query_service import generate_search_query
from services.search_service import search_web


def main():
    project_dir = Path(__file__).resolve().parent
    load_dotenv(project_dir / ".env")

    saved_path = project_dir / "output" / "doha_quote.json"
    quote = Quote.model_validate_json(
        saved_path.read_text(encoding="utf-8")
    )

    hotel = quote.hotels[0]
    if not hotel.name or not hotel.name.strip():
        raise ValueError("A hotel name is required for research.")

    model = ChatGroq(
        model="qwen/qwen3.8-27b",
        temperature=0,
        max_tokens=1024,
    )

    query = generate_search_query(hotel.name, hotel.address, model)
    print("Generated search query:")
    print(query)
    
    search_response = search_web(query)

    result_path = project_dir / "output" / "first_hotel_search.json"
    result_path.write_text(
        json.dumps(search_response, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    results = search_response["results"]

    if not results:
        print("No search results found.")

    for number, result in enumerate(results, start=1):
        print(f"\nResult {number}")
        print("Title:", result.get("title"))
        print("URL:", result.get("url"))
        print("Excerpt:", (result.get("content") or "")[:600])

    print(f"\nSaved search results: {result_path}")


if __name__ == "__main__":
    main()
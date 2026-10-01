import json
from pathlib import Path

from dotenv import load_dotenv

from schemas.quote import Quote
from services.search_service import search_web

project_dir = Path(__file__).resolve().parent
load_dotenv(project_dir / ".env")

output_dir = project_dir / "output"

quote = Quote.model_validate_json(
    (output_dir / "doha_quote.json").read_text(encoding="utf-8")
)

research_dir = output_dir / "hotel_research"
research_dir.mkdir(parents=True, exist_ok=True)

manifest = []


for index, hotel in enumerate(quote.hotels, start=1):
    hotel_id = f"hotel_{index:02d}"
    hotel_dir = research_dir / hotel_id
    hotel_dir.mkdir(parents=True, exist_ok=True)

    entry = {
        "hotel_id": hotel_id,
        "quote_index": index - 1,
        "name": hotel.name,
        "address": hotel.address,
    }

    if not hotel.name:
        entry["status"] = "missing_name"
        manifest.append(entry)
        print(f"\n{hotel_id}: skipped because the hotel name is missing.")
        continue

    search_path = hotel_dir / "search.json"

    # This query is simple enough to build without an LLM call.
    query = " ".join(
        part for part in [
            hotel.name,
            hotel.address,
            "official website location facilities",
        ]
        if part
    )

    print(f"\nHotel: {hotel.name}")

    try:
        if search_path.is_file():
            saved = json.loads(
                search_path.read_text(encoding="utf-8")
            )

            # Avoid reusing another hotel's results if the quote changed.
            if (
                saved.get("hotel_name") != hotel.name
                or saved.get("hotel_address") != hotel.address
                or saved.get("query") != query
            ):
                raise ValueError(
                    f"Saved search does not match this hotel/query: "
                    f"{search_path}. Move that file before rerunning."
                )

            response = saved["response"]
            print("Using saved search results.")

        else:
            print(f"Searching: {query}")
            response = search_web(query)

            saved = {
                "hotel_name": hotel.name,
                "hotel_address": hotel.address,
                "query": query,
                "response": response,
            }

            search_path.write_text(
                json.dumps(saved, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        results = response["results"]

        entry["status"] = "searched" if results else "no_results"
        entry["search_file"] = str(
            search_path.relative_to(output_dir)
        )

        for number, result in enumerate(results, start=1):
            print(f"\n  Result {number}: {result.get('title', '')}")
            print(f"  {result.get('url', '')}")

    except Exception as exc:
        entry["status"] = "search_failed"
        entry["error"] = str(exc)
        print(f"Search failed for {hotel.name}: {exc}")

    manifest.append(entry)


manifest_path = research_dir / "manifest.json"
manifest_path.write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(f"\nSaved research manifest: {manifest_path}")
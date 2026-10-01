import json
from pathlib import Path
from dotenv import load_dotenv
from services.page_service import extract_pages
from schemas.quote import Quote
from services.search_service import filter_hotel_candidates

project_dir = Path(__file__).resolve().parent
load_dotenv(project_dir / ".env")
quote = Quote.model_validate_json(
    (project_dir / "output" / "doha_quote.json").read_text(
        encoding="utf-8"
    )
)

search_response = json.loads(
    (project_dir / "output" / "first_hotel_search.json").read_text(
        encoding="utf-8"
    )
)

hotel = quote.hotels[0]
if not hotel.name:
    raise ValueError("Hotel name is missing.")

candidates = filter_hotel_candidates(
    hotel.name,
    search_response["results"],
)

for candidate in candidates:
    print(candidate["title"])
    print(candidate["url"])
    print()

urls = [candidate["url"] for candidate in candidates]
pages = extract_pages(urls)

output_path = project_dir / "output" / "first_hotel_pages.json"
output_path.write_text(
    json.dumps(pages, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

for page in pages["results"]:
    content = page.get("raw_content") or ""

    print(f"\nSource: {page['url']}")
    print(f"Characters retrieved: {len(content)}")
    print(f"Preview:\n{content[:800]}")

for failure in pages.get("failed_results", []):
    print(f"\nFailed extraction: {failure}")

print(f"\nSaved page content: {output_path}")
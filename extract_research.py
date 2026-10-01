import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from urllib.parse import urlparse
from services.content_service import clean_travelweekly_page
from schemas.quote import Quote
from services.research_extractor import extract_research


project_dir = Path(__file__).resolve().parent
load_dotenv(project_dir / ".env")

quote = Quote.model_validate_json(
    (project_dir / "output" / "doha_quote.json").read_text(
        encoding="utf-8"
    )
)

pages = json.loads(
    (project_dir / "output" / "first_hotel_pages.json").read_text(
        encoding="utf-8"
    )
)

hotel = quote.hotels[0]
if not hotel.name:
    raise ValueError("Hotel name is missing.")

model = ChatGroq(
    model="qwen/qwen3.8-27b",
    temperature=0,
    max_tokens=4000,
)

sources = []

for page in pages["results"]:
    raw_text = page.get("raw_content") or ""
    hostname = urlparse(page["url"]).hostname

    if hostname not in {"travelweekly.com", "www.travelweekly.com"}:
        raise ValueError(f"No page cleaner configured for: {hostname}")

    page_text = clean_travelweekly_page(raw_text, hotel.name)

    print(f"Original characters: {len(raw_text)}")
    print(f"Cleaned characters: {len(page_text)}")

    research = extract_research(
        hotel_name=hotel.name,
        address=hotel.address,
        page_text=page_text,
        model=model,
    )

    sources.append(
        {
            "source_url": page["url"],
            "research": research.model_dump(),
        }
    )

result = {
    "hotel_name": hotel.name,
    "sources": sources,
    "failed_sources": pages.get("failed_results", []),
}

output_path = project_dir / "output" / "first_hotel_research.json"
output_path.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps(result, indent=2, ensure_ascii=False))
print(f"\nSaved research: {output_path}")
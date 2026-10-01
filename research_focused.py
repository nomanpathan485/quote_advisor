import json
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from services.research_extractor import extract_research


project_dir = Path(__file__).resolve().parent
load_dotenv(project_dir / ".env")

research_dir = project_dir / "output" / "hotel_research"

model = ChatGroq(
    model="qwen/qwen3.8-27b",
    temperature=0,
    max_tokens=800,
    max_retries=0,
)


def section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start == -1:
        raise ValueError(f"Missing start heading: {start_marker}")

    end = text.find(end_marker, start + len(start_marker))
    if end == -1:
        raise ValueError(f"Missing end heading: {end_marker}")

    return text[start:end].strip()


# Source choices based on inspection of this saved quotation's pages.
jobs = [
    (
        "hotel_02",
        "https://www.dusit.com/dusitdoha-hotel",
    ),
    (
        "hotel_03",
        "https://www.pullman-doha-westbay.com",
    ),
]

last_finished = None

for hotel_id, source_url in jobs:
    hotel_dir = research_dir / hotel_id
    result_path = hotel_dir / "focused_research.json"

    if result_path.is_file():
        print(f"{hotel_id}: focused result already saved; skipping.")
        continue

    prepared = json.loads(
        (hotel_dir / "prepared_pages.json").read_text(encoding="utf-8")
    )

    source = next(
        item for item in prepared["sources"]
        if item["source_url"] == source_url
    )

    page_text = source["text"]

    if hotel_id == "hotel_02":
        introduction = section(
            page_text,
            "# Dusit Doha Hotel\n",
            "Best Rate Guarantee",
        )
        location = section(
            page_text,
            "## In the Heart of West Bay",
            "## Elegant Rooms and Suites",
        )

        # Separate source excerpts visibly; do not join their sentences.
        page_text = (
            introduction
            + "\n\n--- Separate source section ---\n\n"
            + location
        )

    (hotel_dir / "focused_input.txt").write_text(
        page_text, encoding="utf-8"
    )

    if last_finished is not None:
        remaining = max(0, 60 - (time.monotonic() - last_finished))
        if remaining:
            print(f"Waiting {remaining:.0f}s for rate allowance...")
            time.sleep(remaining)

    rejected = []
    print(f"Extracting: {prepared['hotel_name']}")

    try:
        research = extract_research(
            hotel_name=prepared["hotel_name"],
            address=prepared["hotel_address"],
            page_text=page_text,
            model=model,
            rejected_items=rejected,
        )

        result = {
            "hotel_name": prepared["hotel_name"],
            "source_url": source_url,
            "scope": "Selected source text; not exhaustive hotel research.",
            "research": research.model_dump(),
            "rejected_items": rejected,
        }

        result_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as exc:
        print(f"Failed: {exc}")

    finally:
        last_finished = time.monotonic()
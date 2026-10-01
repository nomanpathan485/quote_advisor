import json
from pathlib import Path
from urllib.parse import urlparse

from services.content_service import (
    clean_travelweekly_page,
    clean_web_page,
)


project_dir = Path(__file__).resolve().parent
research_dir = project_dir / "output" / "hotel_research"

manifest = json.loads(
    (research_dir / "manifest.json").read_text(encoding="utf-8")
)


for entry in manifest:
    hotel_dir = research_dir / entry["hotel_id"]
    pages_path = hotel_dir / "pages.json"

    if not pages_path.is_file():
        print(f"\nSkipping {entry['name']}: no saved pages.")
        continue

    saved = json.loads(pages_path.read_text(encoding="utf-8"))

    if (
        saved["hotel_name"] != entry["name"]
        or saved["hotel_address"] != entry["address"]
    ):
        raise ValueError(f"Saved pages do not match {entry['name']}.")

    prepared_sources = []

    print(f"\nHotel: {entry['name']}")

    for index, page in enumerate(
        saved["response"]["results"], start=1
    ):
        raw_text = page.get("raw_content") or ""
        url = page["url"]
        hostname = urlparse(url).hostname
        preparation_notes = []

        if hostname in {"travelweekly.com", "www.travelweekly.com"}:
            try:
                cleaned = clean_travelweekly_page(
                    raw_text, entry["name"]
                )
                cleaner = "travelweekly"
            except ValueError as exc:
                cleaned = clean_web_page(raw_text)
                cleaner = "generic"
                preparation_notes.append(
                    f"Hotel-section boundaries not found: {exc}"
                )
        else:
            cleaned = clean_web_page(raw_text)
            cleaner = "generic"

        source_id = f"source_{index:02d}"

        prepared_sources.append(
            {
                "source_id": source_id,
                "source_url": url,
                "cleaner": cleaner,
                "original_characters": len(raw_text),
                "cleaned_characters": len(cleaned),
                "text": cleaned,
                "preparation_notes": preparation_notes,
            }
        )

        # A readable copy for inspecting the exact model input later.
        text_path = hotel_dir / f"{source_id}_cleaned.txt"
        text_path.write_text(cleaned, encoding="utf-8")

        print(f"  {source_id}: {url}")
        print(f"  Characters: {len(raw_text)} -> {len(cleaned)}")

    prepared = {
        "hotel_name": entry["name"],
        "hotel_address": entry["address"],
        "sources": prepared_sources,
        "failed_sources": saved["response"].get("failed_results", []),
    }

    (hotel_dir / "prepared_pages.json").write_text(
        json.dumps(prepared, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
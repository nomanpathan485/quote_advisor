import json
from pathlib import Path

from dotenv import load_dotenv

from services.page_service import extract_pages
from services.search_service import filter_hotel_candidates


project_dir = Path(__file__).resolve().parent
load_dotenv(project_dir / ".env")

output_dir = project_dir / "output"
research_dir = output_dir / "hotel_research"

manifest = json.loads(
    (research_dir / "manifest.json").read_text(encoding="utf-8")
)


for entry in manifest:
    name = entry["name"]

    if entry["status"] != "searched":
        print(f"\nSkipping {name}: {entry['status']}")
        continue

    hotel_dir = research_dir / entry["hotel_id"]
    pages_path = hotel_dir / "pages.json"

    try:
        search_path = output_dir / entry["search_file"]
        saved_search = json.loads(
            search_path.read_text(encoding="utf-8")
        )

        if (
            saved_search["hotel_name"] != name
            or saved_search["hotel_address"] != entry["address"]
        ):
            raise ValueError("Saved search does not match the manifest.")

        candidates = filter_hotel_candidates(
            name,
            saved_search["response"]["results"],
        )

        # Remove duplicate URLs while preserving their order.
        urls = list(dict.fromkeys(
            candidate["url"]
            for candidate in candidates
            if candidate.get("url")
        ))

        print(f"\nHotel: {name}")
        print(f"Candidate pages: {len(urls)}")

        if not urls:
            print("No exact-name candidates. A broader search is needed.")
            continue

        if pages_path.is_file():
            saved_pages = json.loads(
                pages_path.read_text(encoding="utf-8")
            )

            if (
                saved_pages.get("hotel_name") != name
                or saved_pages.get("hotel_address") != entry["address"]
                or saved_pages.get("requested_urls") != urls
            ):
                raise ValueError(
                    f"Saved pages do not match this request. "
                    f"Move {pages_path} before rerunning."
                )

            response = saved_pages["response"]
            print("Using saved pages.")

        else:
            response = extract_pages(urls)

            saved_pages = {
                "hotel_name": name,
                "hotel_address": entry["address"],
                "requested_urls": urls,
                "response": response,
            }

            pages_path.write_text(
                json.dumps(saved_pages, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        for page in response["results"]:
            content = page.get("raw_content") or ""
            print(f"  Retrieved: {page['url']}")
            print(f"  Characters: {len(content)}")

        for failure in response.get("failed_results", []):
            print(f"  Failed: {failure.get('url', 'Unknown URL')}")
            print(f"  Reason: {failure.get('error', 'Unknown error')}")

    except Exception as exc:
        print(f"Page collection failed for {name}: {exc}")
import hashlib
import json
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from services.research_extractor import extract_research


project_dir = Path(__file__).resolve().parent
load_dotenv(project_dir / ".env")

research_dir = project_dir / "output" / "hotel_research"

manifest = json.loads(
    (research_dir / "manifest.json").read_text(encoding="utf-8")
)

model = ChatGroq(
    model="qwen/qwen3.8-27b",
    temperature=0,
    max_tokens=800,
    max_retries=0,
)

# Conservative spacing for the current free-tier allowance.
MIN_REQUEST_INTERVAL = 60
last_request_finished = None

# Change this when you change the extraction prompt or schema.
EXTRACTION_VERSION = "chunked-v1"


def make_chunks(page_text: str) -> list[str]:
    """Split long text with overlap and surrounding section context."""
    size = 5000
    overlap = 500

    if len(page_text) <= size:
        return [page_text] if page_text.strip() else []

    chunks = []
    start = 0

    while start < len(page_text):
        end = min(start + size, len(page_text))

        # Prefer ending at a line boundary.
        if end < len(page_text):
            boundary = page_text.rfind("\n", start + size // 2, end)
            if boundary != -1:
                end = boundary

        # Track the active Markdown heading hierarchy.
        headings = {}
        for line in page_text[:start].splitlines():
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                headings = {
                    depth: heading
                    for depth, heading in headings.items()
                    if depth < level
                }
                headings[level] = line

        heading_context = "\n".join(headings.values())

        chunk = (
            "PAGE OPENING CONTEXT:\n"
            + page_text[:1200]
            + "\n\nSECTION CONTEXT:\n"
            + heading_context
            + "\n\nPAGE EXCERPT:\n"
            + page_text[start:end]
        )
        chunks.append(chunk)

        if end == len(page_text):
            break

        start = end - overlap

    return chunks


for entry in manifest:
    hotel_dir = research_dir / entry["hotel_id"]
    prepared_path = hotel_dir / "prepared_pages.json"

    if not prepared_path.is_file():
        print(f"\nSkipping {entry['name']}: no prepared pages.")
        continue

    prepared = json.loads(
        prepared_path.read_text(encoding="utf-8")
    )

    if (
        prepared["hotel_name"] != entry["name"]
        or prepared["hotel_address"] != entry["address"]
    ):
        raise ValueError("Prepared pages do not match the hotel.")

    chunks_dir = hotel_dir / "research_chunks"
    chunks_dir.mkdir(exist_ok=True)

    hotel_result = {
        "hotel_name": entry["name"],
        "hotel_address": entry["address"],
        "sources": [],
        "failed_sources": prepared.get("failed_sources", []),
    }

    print(f"\nHotel: {entry['name']}")

    for source in prepared["sources"]:
        chunks = make_chunks(source["text"])

        source_result = {
            "source_id": source["source_id"],
            "source_url": source["source_url"],
            "preparation_notes": source["preparation_notes"],
            "chunks": [],
            "errors": [],
        }

        print(f"  {source['source_id']}: {len(chunks)} chunk(s)")

        if not chunks:
            source_result["errors"].append(
                {"error": "No usable page text."}
            )

        for number, chunk in enumerate(chunks, start=1):
            cache_input = {
                "version": EXTRACTION_VERSION,
                "hotel": entry["name"],
                "address": entry["address"],
                "url": source["source_url"],
                "text": chunk,
            }

            fingerprint = hashlib.sha256(
                json.dumps(
                    cache_input, ensure_ascii=False, sort_keys=True
                ).encode("utf-8")
            ).hexdigest()

            cache_path = chunks_dir / f"{fingerprint}.json"

            try:
                if cache_path.is_file():
                    saved = json.loads(
                        cache_path.read_text(encoding="utf-8")
                    )
                    print(f"    Chunk {number}: cached")

                else:
                    if last_request_finished is not None:
                        elapsed = time.monotonic() - last_request_finished
                        wait = max(0, MIN_REQUEST_INTERVAL - elapsed)

                        if wait:
                            print(f"    Waiting {wait:.0f}s for rate allowance...")
                            time.sleep(wait)
                    
                    print(f"    Chunk {number}: extracting")

                    try:
                        research = extract_research(
                            hotel_name=entry["name"],
                            address=entry["address"],
                            page_text=chunk,
                            model=model,
                        )
                    finally:
                        last_request_finished = time.monotonic()

                    saved = {
                        "chunk_number": number,
                        "research": research.model_dump(),
                    }

                    cache_path.write_text(
                        json.dumps(saved, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )

                source_result["chunks"].append(saved)

            except Exception as exc:
                source_result["errors"].append(
                    {
                        "chunk_number": number,
                        "error": str(exc),
                    }
                )
                print(f"    Chunk {number} failed: {exc}")

        source_result["status"] = (
            "complete" if not source_result["errors"] else "incomplete"
        )
        hotel_result["sources"].append(source_result)

        # Save after every source, including any failures.
        (hotel_dir / "facts.json").write_text(
            json.dumps(hotel_result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(f"  Saved: {hotel_dir / 'facts.json'}")
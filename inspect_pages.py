import json
from pathlib import Path

project_dir = Path(__file__).resolve().parent
pages_path = project_dir / "output" / "first_hotel_pages.json"

pages = json.loads(pages_path.read_text(encoding="utf-8"))

for page in pages["results"]:
    content = page.get("raw_content") or ""
    lines = content.splitlines()

    print(f"\nSource: {page['url']}")

    # Find hotel-name mentions beyond the page title.
    # Markdown headings identify sections such as location and amenities.
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            print(f"\n--- Section at line {index + 1} ---")
            print("\n".join(lines[index:index + 16]))
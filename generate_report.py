import json
from pathlib import Path

from schemas.quote import Quote
from services.report_service import build_hotel_report


project_dir = Path(__file__).resolve().parent
output_dir = project_dir / "output"

quote = Quote.model_validate_json(
    (output_dir / "doha_quote.json").read_text(encoding="utf-8")
)

research_data = json.loads(
    (output_dir / "first_hotel_research.json").read_text(
        encoding="utf-8"
    )
)

matches = [
    hotel
    for hotel in quote.hotels
    if hotel.name == research_data["hotel_name"]
]

if len(matches) != 1:
    raise ValueError("Expected exactly one matching hotel in the quotation.")

html = build_hotel_report(matches[0], research_data)

report_path = output_dir / "hotel_report.html"
report_path.write_text(html, encoding="utf-8")

print(f"Report generated: {report_path}")
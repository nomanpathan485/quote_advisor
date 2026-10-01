import json
from html import escape
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from schemas.quote import Quote
from schemas.research import SourceResearch
from services.comparison_service import recommend_hotels


project_dir = Path(__file__).resolve().parent
load_dotenv(project_dir / ".env")

output_dir = project_dir / "output"
research_dir = output_dir / "hotel_research"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def h(value) -> str:
    return escape(str(value)) if value is not None else "Not provided"


def source_link(url: str) -> str:
    if urlparse(url).scheme not in {"https", "http"}:
        return h(url)
    return f'<a href="{h(url)}">{h(url)}</a>'


quote = Quote.model_validate_json(
    (output_dir / "doha_quote.json").read_text(encoding="utf-8")
)
manifest = read_json(research_dir / "manifest.json")

packet = {"hotels": []}
evidence_records = {}
review_notes = [
    "Research coverage differs between hotels and is incomplete.",
    "Missing amenities must not be interpreted as unavailable amenities.",
    "Saved quotation sample; availability and prices have not been refreshed.",
]
excluded_items = []


for entry in manifest:
    hotel_id = entry["hotel_id"]
    offer = quote.hotels[entry["quote_index"]]

    if offer.name != entry["name"] or offer.address != entry["address"]:
        raise ValueError("Quotation does not match the research manifest.")

    hotel_dir = research_dir / hotel_id

    if hotel_id == "hotel_01":
        saved = read_json(hotel_dir / "facts.json")

        # Use the previously inspected Travel Weekly source for this demo.
        source = next(
            item for item in saved["sources"]
            if item["source_url"]
            == "https://www.travelweekly.com/Hotels/Doha-Qatar/W-Doha-p55149919"
        )
        source_url = source["source_url"]
        researches = [
            SourceResearch.model_validate(chunk["research"])
            for chunk in source["chunks"]
        ]

        if source.get("errors"):
            review_notes.append(f"{offer.name}: source processing is incomplete.")

    else:
        saved = read_json(hotel_dir / "focused_research.json")

        if saved["hotel_name"] != offer.name:
            raise ValueError("Focused research belongs to another hotel.")

        source_url = saved["source_url"]
        researches = [
            SourceResearch.model_validate(saved["research"])
        ]

        if saved.get("rejected_items"):
            review_notes.append(f"{offer.name}: some evidence was rejected.")

    quote_reference = f"{hotel_id}_quote"
    evidence_records[quote_reference] = {
        "label": f"{offer.name}: quotation",
        "quote": offer.model_dump(),
    }

    facts = []
    warnings = []

    for research in researches:
        if research.identity_status != "matched":
            review_notes.append(
                f"{offer.name}: a source identity remains unconfirmed."
            )
            continue

        warnings.extend(w.model_dump() for w in research.warnings)

        for fact in research.facts:
            # Explicit review correction for the known cached demo error.
            if "four onsite dining options" in fact.claim.casefold():
                excluded_items.append({
                    "hotel_name": offer.name,
                    "claim": fact.claim,
                    "reason": "Evidence lists three restaurants, not four.",
                })
                continue

            reference = f"{hotel_id}_fact_{len(facts) + 1}"

            facts.append({
                "reference": reference,
                "category": fact.category,
                "claim": fact.claim,
                "caveats": fact.caveats,
            })

            evidence_records[reference] = {
                "label": offer.name,
                "source_url": source_url,
                **fact.model_dump(),
            }

    packet["hotels"].append({
        "hotel_id": hotel_id,
        "quote_reference": quote_reference,
        "quotation": offer.model_dump(),
        "facts": facts,
        "warnings": warnings,
    })


if len(packet["hotels"]) != len(quote.hotels):
    raise ValueError("Research manifest does not cover every quoted hotel.")

model = ChatGroq(
    model="qwen/qwen3.8-27b",
    temperature=0,
    max_tokens=800,
    max_retries=0,
)

recommendation = recommend_hotels(packet, model)

result = {
    "comparison": packet,
    "recommendation": recommendation.model_dump(),
    "evidence": evidence_records,
    "review_notes": review_notes,
    "excluded_items": excluded_items,
}

(output_dir / "comparison.json").write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8",
)


def render_statement(statement) -> str:
    links = " ".join(
        f'<a href="#{h(ref)}">[{h(ref)}]</a>'
        for ref in statement.references
    )
    return f"{h(statement.text)} {links}"


hotels = packet["hotels"]

names = {
    hotel["hotel_id"]: hotel["quotation"]["name"]
    for hotel in hotels
}
selected_name = names.get(
    recommendation.recommended_hotel_id,
    "No supported choice yet",
)

fields = [
    ("Displayed price", "price_display"),
    ("Date shown", "date_display"),
    ("Nights", "nights"),
    ("Room", "room_description"),
    ("Meal plan", "meal_plan"),
    ("Cancellation", "cancellation_wording"),
]

table_header = "<tr><th>Quotation</th>" + "".join(
    f"<th>{h(hotel['quotation']['name'])}</th>"
    for hotel in hotels
) + "</tr>"

table_rows = "".join(
    f"<tr><th>{h(label)}</th>"
    + "".join(
        f"<td>{h(hotel['quotation'][field])}</td>"
        for hotel in hotels
    )
    + "</tr>"
    for label, field in fields
)

hotel_sections = []

for hotel in hotels:
    items = "".join(
        f"<li>{h(fact['claim'])}"
        + (
            "<ul>"
            + "".join(f"<li>{h(note)}</li>" for note in fact["caveats"])
            + "</ul>"
            if fact["caveats"] else ""
        )
        + f' <a href="#{h(fact["reference"])}">[Evidence]</a></li>'
        for fact in hotel["facts"]
    )

    warning_items = "".join(
        f"<li>{h(warning['issue'])}</li>"
        for warning in hotel["warnings"]
    )

    hotel_sections.append(
        f"<section><h2>{h(hotel['quotation']['name'])}</h2>"
        f"<p>Source-reported findings; research is partial.</p>"
        f"<ul>{items or '<li>No accepted research facts.</li>'}</ul>"
        + (
            f"<h3>Unresolved source issues</h3><ul>{warning_items}</ul>"
            if warning_items else ""
        )
        + "</section>"
    )

evidence_html = []

for reference, record in evidence_records.items():
    if "quote" in record:
        body = f"<pre>{h(json.dumps(record['quote'], indent=2, ensure_ascii=False))}</pre>"
    else:
        body = (
            f"<p>{source_link(record['source_url'])}</p>"
            f"<p>Section: {h(record['section'])}</p>"
            f"<blockquote>{h(record['evidence'])}</blockquote>"
        )

    evidence_html.append(
        f'<details id="{h(reference)}">'
        f"<summary>{h(reference)} — {h(record['label'])}</summary>"
        f"{body}</details>"
    )

reasons_html = "".join(
    f"<li>{render_statement(reason)}</li>"
    for reason in recommendation.reasons
)

notes = [
    *recommendation.assumptions,
    *recommendation.limitations,
    *review_notes,
]
notes_html = "".join(f"<li>{h(note)}</li>" for note in notes)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RateLoc Hotel Comparison</title>
<style>
body {{ font-family: Arial, sans-serif; background:#f2f5f9;
       color:#19324b; line-height:1.6; margin:0; }}
main {{ max-width:1100px; margin:30px auto; padding:20px; }}
header {{ background:#14324f; color:white; padding:28px; border-radius:12px; }}
section {{ background:white; padding:24px; margin:20px 0; border-radius:12px; }}
.pick {{ border-left:6px solid #168087; }}
table {{ width:100%; border-collapse:collapse; }}
th,td {{ text-align:left; padding:12px; border:1px solid #dce3eb;
         vertical-align:top; }}
.table-wrap {{ overflow-x:auto; }}
a {{ color:#086b91; overflow-wrap:anywhere; }}
li {{ margin-bottom:8px; }}
details {{ margin:12px 0; padding:12px; border:1px solid #dce3eb; }}
blockquote,pre {{ white-space:pre-wrap; overflow-wrap:anywhere; }}
button {{ padding:10px 16px; margin-top:16px; cursor:pointer; }}
@media print {{
    body {{ background:white; }}
    main {{ margin:0; padding:0; }}
    button {{ display:none; }}
    tr {{ break-inside:avoid; }}
}}
</style>
</head>
<body><main>
<header>
<h1>RateLoc Hotel Comparison</h1>
<p>Prototype · Provisional recommendation · Manager review</p>
</header>
<button onclick="window.print()">Print / Save as PDF</button>

<section class="pick">
<h2>Suggested choice: {h(selected_name)}</h2>
<ul>{reasons_html}</ul>
<h3>Trade-off</h3>
<p>{render_statement(recommendation.tradeoff)}</p>
</section>

<section>
<h2>Quoted offers</h2>
<p>Prices and booking wording are copied from the saved quotation.
Full room descriptions, occupancy, taxes and pricing basis require confirmation.</p>
<div class="table-wrap">
<table>{table_header}{table_rows}</table>
</div>
</section>

{"".join(hotel_sections)}

<section>
<h2>Assumptions and limitations</h2>
<ul>{notes_html}</ul>
</section>

<section>
<h2>Sources and supporting evidence</h2>
{"".join(evidence_html)}
</section>
</main></body></html>"""

report_path = output_dir / "comparison_report.html"
report_path.write_text(html, encoding="utf-8")

print(json.dumps(recommendation.model_dump(), indent=2, ensure_ascii=False))
print(f"Report saved: {report_path}")
from html import escape
from urllib.parse import urlparse

from schemas.quote import HotelOffer
from schemas.research import SourceResearch


def text(value) -> str:
    """Escape text so document content cannot become HTML code."""
    return escape(str(value)) if value is not None else "Not provided"


def source_link(url: str) -> str:
    if urlparse(url).scheme not in {"https", "http"}:
        return text(url)

    return (
        f'<a href="{escape(url, quote=True)}" '
        f'target="_blank" rel="noopener noreferrer">'
        f"{text(url)}</a>"
    )


def build_hotel_report(offer: HotelOffer, research_data: dict) -> str:
    if research_data.get("hotel_name") != offer.name:
        raise ValueError("Research hotel does not match the quotation.")

    quote_fields = [
        ("Hotel", offer.name),
        ("Area shown", offer.address),
        ("Displayed price", offer.price_display),
        ("Date shown", offer.date_display),
        ("Nights", offer.nights),
        ("Room", offer.room_description),
        ("Meal plan", offer.meal_plan),
        ("Cancellation wording", offer.cancellation_wording),
    ]

    rows = "".join(
        f"<tr><th>{text(label)}</th><td>{text(value)}</td></tr>"
        for label, value in quote_fields
    )

    categories = {
        "location": "Location",
        "transport": "Transport",
        "hotel_facility": "Hotel facilities",
        "room_amenity": "Room amenities",
        "nearby_attraction": "Nearby attractions",
        "policy": "Hotel policies",
    }

    sections = []
    research_warnings = []

    for source in research_data.get("sources", []):
        research = SourceResearch.model_validate(source["research"])
        link = source_link(source["source_url"])

        if research.identity_status != "matched":
            sections.append(
                '<section class="card">'
                "<h2>Source awaiting identity confirmation</h2>"
                f"<p>{text(research.identity_reason)}</p>"
                f"<p>{link}</p></section>"
            )
            continue

        groups = []

        for category, heading in categories.items():
            facts = [
                fact for fact in research.facts
                if fact.category == category
            ]

            if not facts:
                continue

            items = []

            for fact in facts:
                caveats = ""

                if fact.caveats:
                    caveats = (
                        '<ul class="caveats">'
                        + "".join(
                            f"<li>{text(note)}</li>"
                            for note in fact.caveats
                        )
                        + "</ul>"
                    )

                items.append(
                    '<li class="fact">'
                    f"<p>{text(fact.claim)}</p>"
                    f"{caveats}"
                    "<details><summary>View supporting evidence</summary>"
                    f"<p><strong>Section:</strong> {text(fact.section)}</p>"
                    f"<blockquote>{text(fact.evidence)}</blockquote>"
                    "</details></li>"
                )

            groups.append(
                f"<h3>{text(heading)}</h3>"
                f'<ul class="facts">{"".join(items)}</ul>'
            )

        sections.append(
            '<section class="card">'
            "<h2>Source-reported hotel information</h2>"
            f'<p class="source">Source: {link}</p>'
            + "".join(groups)
            + "</section>"
        )

        for warning in research.warnings:
            evidence = "".join(
                f"<li>{text(excerpt)}</li>"
                for excerpt in warning.evidence
            )

            research_warnings.append(
                f"<li><strong>{text(warning.issue)}</strong>"
                f"<ul>{evidence}</ul>"
                f'<p class="source">{link}</p></li>'
            )

    checks = [
        "This is a one-hotel prototype, not a comparison or final recommendation.",
        "Web information has not been independently verified.",
        "Hotel facilities do not establish inclusion in the quoted room or price.",
        "Displayed price is copied from the quotation; its pricing basis "
        "and tax inclusions need confirmation.",
    ]

    if offer.room_description_truncated:
        checks.append(
            "The quoted room description is truncated. Confirm the full description."
        )

    for failure in research_data.get("failed_sources", []):
        checks.append(
            f"Source retrieval failed: {failure.get('url', 'Unknown URL')}. "
            "Its page content was not used."
        )

    check_items = "".join(f"<li>{text(item)}</li>" for item in checks)
    warning_items = "".join(research_warnings)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{text(offer.name)} — RateLoc Quote Advisor</title>
<style>
    * {{ box-sizing: border-box; }}
    body {{
        margin: 0;
        background: #f1f5f9;
        color: #172b46;
        font-family: Arial, sans-serif;
        line-height: 1.6;
    }}
    main {{ max-width: 960px; margin: 36px auto; padding: 0 20px; }}
    header {{
        background: #102a43;
        color: white;
        padding: 32px;
        border-radius: 14px;
    }}
    header p {{ margin: 4px 0; }}
    h1 {{ margin: 12px 0; font-size: 34px; }}
    h2 {{ margin-top: 0; font-size: 23px; }}
    h3 {{ margin-bottom: 8px; }}
    .badge {{
        display: inline-block;
        background: #dbeafe;
        color: #163e75;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
    }}
    .card {{
        background: white;
        margin: 22px 0;
        padding: 28px;
        border: 1px solid #dce5ee;
        border-radius: 12px;
    }}
    .review {{ border-left: 5px solid #d69e2e; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{
        text-align: left;
        vertical-align: top;
        padding: 12px;
        border-bottom: 1px solid #e5eaf0;
    }}
    th {{ width: 30%; background: #f8fafc; }}
    .facts {{ padding-left: 22px; }}
    .fact {{ margin-bottom: 18px; }}
    .fact p {{ margin: 5px 0; }}
    .caveats {{ color: #805500; }}
    .source {{ font-size: 13px; overflow-wrap: anywhere; }}
    a {{ color: #126b96; }}
    details {{ font-size: 14px; color: #486078; }}
    summary {{ cursor: pointer; }}
    blockquote {{
        margin: 10px 0;
        padding: 12px;
        background: #f1f5f9;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
    }}
    button {{
        margin: 18px 0 0;
        padding: 10px 18px;
        border: 0;
        border-radius: 6px;
        background: #0e7490;
        color: white;
        cursor: pointer;
    }}
    @media print {{
        body {{ background: white; }}
        main {{ margin: 0; max-width: none; padding: 0; }}
        button {{ display: none; }}
        .card {{ border-radius: 0; }}
        .fact, tr {{ break-inside: avoid; }}
    }}
</style>
</head>
<body>
<main>
    <header>
        <p>RATELOC QUOTE ADVISOR</p>
        <h1>{text(offer.name)}</h1>
        <p>Quotation and hotel research</p>
        <span class="badge">Prototype · Manager review</span>
    </header>

    <button onclick="window.print()">Print / Save as PDF</button>

    <section class="card">
        <h2>Your quotation</h2>
        <table>{rows}</table>
    </section>

    <section class="card review">
        <h2>Review notes</h2>
        <ul>{check_items}</ul>
        {"<h3>Source discrepancies</h3><ul>" + warning_items + "</ul>"
         if warning_items else ""}
    </section>

    {"".join(sections)}
</main>
</body>
</html>"""
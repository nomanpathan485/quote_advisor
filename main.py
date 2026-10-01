import os
from pathlib import Path
import json
from dotenv import load_dotenv
from groq import Groq

from services.pdf_service import render_first_page
from services.quote_extractor import extract_quote


def main():
    project_dir = Path(__file__).resolve().parent
    load_dotenv(project_dir / ".env")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing.")

    pdf_path = project_dir / "samples" / "doha_quote.pdf"
    image_path = project_dir / "output" / "doha_page_1.png"

    render_first_page(pdf_path, image_path)
    print(f"Rendered: {image_path.name}")

    with Groq(api_key=api_key) as client:
        quote_data = extract_quote(image_path, client)

        json_text = json.dumps(
        quote_data,
        indent=2,
        ensure_ascii=False,
    )

    result_path = project_dir / "output" / "doha_quote.json"
    result_path.write_text(json_text, encoding="utf-8")

    print(json_text)
    print(f"Saved extraction: {result_path}")


if __name__ == "__main__":
    main()
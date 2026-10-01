from pathlib import Path
import pypdfium2 as pdfium


def render_first_page(pdf_path: Path, output_path: Path) -> Path:
    """Render the first PDF page and return the saved image path."""

    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pdfium.PdfDocument(pdf_path) as pdf:
        page = pdf[0]
        bitmap = page.render(scale=4)
        image = bitmap.to_pil()

        try:
            image.save(output_path)
        finally:
            image.close()
            bitmap.close()
            page.close()

    return output_path
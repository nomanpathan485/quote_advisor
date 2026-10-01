from pathlib import Path
import pypdfium2 as pdfium

# Folder where this script is located
BASE_DIR = Path(__file__).resolve().parent

# Input PDF
PDF_PATH = BASE_DIR / "comp.pdf"

# Output folder
OUTPUT_DIR = BASE_DIR / "output_pages"

# Create output folder if it does not exist
OUTPUT_DIR.mkdir(exist_ok=True)

# Check PDF exists
if not PDF_PATH.exists():
    raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

print(f"Reading PDF: {PDF_PATH}")

# Open PDF
pdf = pdfium.PdfDocument(str(PDF_PATH))

print(f"Total pages: {len(pdf)}")

# Convert every PDF page to PNG
for page_number in range(len(pdf)):
    page = pdf[page_number]

    # Higher scale = better image quality
    bitmap = page.render(scale=3)

    image = bitmap.to_pil()

    output_path = OUTPUT_DIR / f"comp_page_{page_number + 1}.png"

    image.save(output_path)

    print(f"Created: {output_path}")

print("\nConversion complete!")
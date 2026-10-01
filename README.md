# RateLoc Quote Advisor

RateLoc Quote Advisor is a tool designed to automate the extraction of hotel offer data from quotation documents (PDFs/images) using Vision LLMs via the Groq API.

## 🚀 Features

- **PDF to Image Rendering**: Converts hotel quotation PDFs into images for processing.
- **Vision-Based Extraction**: Uses high-performance Vision models (e.g., Qwen) to transcribe complex hotel offer details.
- **Structured Data Output**: Extracts information into a validated JSON schema, including:
  - Hotel name and address
  - Price and currency symbols
  - Room descriptions (preserving truncations)
  - Dates and number of nights
  - Meal plans and cancellation policies
- **Strict Fidelity**: Designed to copy digits and wording exactly as they appear, avoiding AI hallucinations or inferences.

## 🛠️ Tech Stack

- **Language**: Python 3.13
- **LLM API**: [Groq](https://groq.com/)
- **Data Validation**: Pydantic (via schemas)
- **PDF Processing**: Custom service for page rendering

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rateloc_quote_advisor
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

## 🏃 Usage

### Basic Extraction
Place your hotel quotation PDF in the `samples/` directory and run the main script:

```bash
python main.py
```

**Workflow**:
1. `main.py` triggers `pdf_service` to render the first page of the PDF to `output/doha_page_1.png`.
2. The image is sent to the `quote_extractor` service.
3. The extracted data is validated against the `Quote` schema.
4. The final result is saved to `output/doha_quote.json`.

### Generating the Hotel Report (`hotel_report.html`)
To generate the final HTML report, you must run the full research pipeline in the following order:

1. **Extract Quote**:
   ```bash
   python main.py
   ```
   *Generates `output/doha_quote.json`*

2. **Web Research**:
   ```bash
   python research.py
   ```
   *Generates `output/first_hotel_search.json`*

3. **Extract Research Details**:
   ```bash
   python extract_research.py
   ```
   *Generates `output/first_hotel_research.json` (Requires page content in `first_hotel_pages.json`)*

4. **Build Report**:
   ```bash
   python generate_report.py
   ```
   *Generates the final `output/hotel_report.html`*


## 📂 Project Structure

- `main.py`: Entry point for the extraction pipeline.
- `services/`: Business logic for PDF rendering, LLM interaction, and reporting.
- `schemas/`: Pydantic models ensuring the extracted JSON follows a strict format.
- `samples/`: Input PDF files for testing.
- `output/`: Rendered images and resulting JSON extractions.



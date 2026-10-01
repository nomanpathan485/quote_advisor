# Quote Advisor
Quote Advisor is a tool designed to automate the extraction of hotel offer data from quotation documents (PDFs/images) using Vision LLMs via the Groq API.
=======
RateLoc Quote Advisor is an intelligent automation system designed to streamline the extraction of hotel offer data from quotation documents (PDFs/Images) and enhance that data thro
ugh automated web research to generate professional comparison reports.
>>>>>>> 69f6766 (feat: add hotel research and comparison pipeline)

By leveraging state-of-the-art Vision LLMs and structured data extraction, the tool eliminates manual data entry and reduces the risk of human error in processing complex hotel quotations.

## 🚀 Key Features

- **Vision-Based Extraction**: Utilizes high-performance Vision models (via Groq API) to transcribe complex hotel offer details from images and PDFs with high fidelity.
- **Automated PDF Processing**: Converts PDF quotations into high-resolution images optimized for LLM vision processing.
- **Structured Data Validation**: Employs strict Pydantic schemas to ensure extracted data (prices, room types, meal plans, policies) is validated and consistent.
- **Intelligent Web Research**: Automatically searches for and extracts additional hotel details to enrich the basic quote data.
- **Professional Reporting**: Generates comprehensive HTML reports and comparison summaries for stakeholders.
- **Strict Fidelity**: Engineered to copy digits and wording exactly as they appear, preventing AI hallucinations.

## 🛠️ Technology Stack

### Core Backend
- **Language**: Python 3.13
- **Orchestration**: Custom service-oriented architecture for modularity.

### AI & LLM Integration
- **LLM Gateway**: [Groq](https://groq.com/) (providing ultra-fast inference).
- **Models**: Vision-capable LLMs (e.g., Qwen-VL) for document transcription and analysis.

### Data & Validation
- **Validation**: [Pydantic](https://docs.pydantic.dev/) for rigorous type checking and JSON schema enforcement.
- **Data Format**: JSON for intermediate storage and exchange.

### Document Processing
- **PDF Rendering**: Specialized service for converting PDF pages to images.
- **Reporting**: HTML/CSS for the final professional output.

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rateloc_quote_advisor
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
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

## 🏃 Usage Guide

### 1. Basic Data Extraction
Extract structured data from a hotel quotation PDF:
```bash
python main.py
```
- **Input**: PDF in `samples/`
- **Output**: `output/doha_quote.json` (Validated JSON data)

### 2. Full Research & Reporting Pipeline
To generate a professional `hotel_report.html`, execute the following sequence:

| Step | Command | Description | Output |
| :--- | :--- | :--- | :--- |
| **1** | `python main.py` | Extracts basic quote data | `doha_quote.json` |
| **2** | `python research.py` | Performs web research on the hotel | `first_hotel_search.json` |
| **3** | `python extract_research.py` | Parses research pages into structured facts | `first_hotel_research.json` |
| **4** | `python generate_report.py` | Compiles all data into a final report | `hotel_report.html` |

## 📂 Project Architecture

```text
rateloc_quote_advisor/
├── main.py                 # Entry point for the extraction pipeline
├── research.py              # Web research orchestration
├── extract_research.py      # Research data extraction logic
├── generate_report.py      # Final HTML report generator
├── services/               # Core Business Logic
│   ├── pdf_service.py      # PDF to Image conversion
│   ├── quote_extractor.py  # LLM Vision integration for quotes
│   ├── search_service.py   # Web search capabilities
│   ├── research_extractor.py # LLM integration for research facts
│   └── report_service.py   # HTML template rendering
├── schemas/                # Pydantic Data Models
│   ├── quote.py            # Schema for hotel quotes
│   └── research.py         # Schema for hotel research facts
├── samples/                # Input PDF files
└── output/                 # Resulting images, JSONs, and HTML
```

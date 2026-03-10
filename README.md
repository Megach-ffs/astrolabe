# AI-Assisted Data Wrangler & Visualizer 

![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat&logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python)

An interactive Streamlit application for data preparation, cleaning, transformation, and visualization. Upload a dataset and take it through a complete data wrangling pipeline — all from a user-friendly web interface.

## ✨ Features

- **📤 Upload & Profile** — CSV, Excel, JSON upload with instant data profiling
- **🧹 Cleaning Studio** — Missing values, duplicates, outliers, type conversion, and more
- **📊 Visualization Builder** — 6+ chart types with interactive filtering and aggregation
- **📥 Export & Report** — Download cleaned data, reproducible recipes, and transformation reports (JSON, Markdown, DOCX)
- **🤖 AI Assistant** — Data Dictionary, Intelligent Chart Suggestions, and Context-Aware AI Chat (Gemini)
- **🧠 Smart State Management** — Seamless UI persistence across page navigation
- **🔄 Undo & Replay** — Full transformation log with undo support

## 🚀 Quick Start

### Prerequisites

- Python 3.10+

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd Astrolabe

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Setup AI API Key (Optional)

To enable the AI Assistant features, you must provide a Gemini API key. Create a `.streamlit` folder at the root of the project and add a `secrets.toml` file inside of it:

```bash
mkdir .streamlit
echo 'GEMINI_API_KEY = "your_api_key_here"' > .streamlit/secrets.toml
```

*(Alternatively, you can manually create `.streamlit/secrets.toml` using your code editor and paste in the key).*

### Generate Sample Data

```bash
python utils/generate_sample_data.py
```

### Run the App

```bash
streamlit run app.py
```

## 📁 Project Structure

```
Astrolabe/
├── app.py                          # Main Streamlit entrypoint
├── pages/
│   ├── home.py                     # Landing page & navigation
│   ├── upload_overview.py          # Page A — Upload & data profiling
│   ├── cleaning_studio.py          # Page B — Data cleaning & prep
│   ├── visualization.py            # Page C — Chart builder
│   ├── ai_chat.py                  # Page E — AI Chat & Snippets
│   └── export_report.py            # Page D — Export & reports
├── utils/
│   ├── __init__.py
│   ├── data_loader.py              # File upload & parsing
│   ├── profiler.py                 # Data profiling
│   ├── cleaning.py                 # Cleaning operations
│   ├── validation.py               # Data validation rules
│   ├── chart_builder.py            # Visualization helpers
│   ├── export.py                   # Export & recipe generation
│   ├── transform_log.py            # Transformation log & undo
│   ├── ai_assistant.py             # Optional AI integration
│   └── generate_sample_data.py     # Sample data generator
├── sample_data/
│   ├── ecommerce_orders.csv        # ~1,500 rows, 10 columns
│   └── weather_stations.xlsx       # ~1,200 rows, 9 columns
├── tests/
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_profiler.py
│   ├── test_transform_log.py
│   └── ...                         # 25+ other tests
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI
├── .streamlit/
│   ├── config.toml                 # App theme
│   └── secrets.toml                # AI API Keys (Not committed)
├── requirements.txt
├── AI_USAGE.md
└── README.md
```

## 📊 Sample Datasets

| Dataset | Rows | Columns | Issues |
|---------|------|---------|--------|
| `ecommerce_orders.csv` | ~1,500 | 10 | Dirty prices, mixed case, missing values, duplicates, outlier discounts |
| `weather_stations.xlsx` | ~1,200 | 9 | Sentinel outliers (999), missing values, blank strings, negative wind speeds |

## 👥 Authors

- Megach-FFs
- Tako030303

## 📄 License

This project was created for the Data Wrangling & Visualization (5COSC038C) coursework.

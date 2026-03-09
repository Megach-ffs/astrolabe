# AI-Assisted Data Wrangler & Visualizer

![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat&logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python)

An interactive Streamlit application for data preparation, cleaning, transformation, and visualization. Upload a dataset and take it through a complete data wrangling pipeline — all from a user-friendly web interface.

## ✨ Features

- **📤 Upload & Profile** — CSV, Excel, JSON upload with instant data profiling
- **🧹 Cleaning Studio** — Missing values, duplicates, outliers, type conversion, and more
- **📊 Visualization Builder** — 6+ chart types with interactive filtering and aggregation
- **📥 Export & Report** — Download cleaned data, transformation reports, and reproducible recipes
- **🤖 AI Assistant** — Optional LLM-powered suggestions (Gemini / Claude)
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
│   ├── 1_Upload_Overview.py        # Page A — Upload & data profiling
│   ├── 2_Cleaning_Studio.py        # Page B — Data cleaning & prep
│   ├── 3_Visualization.py          # Page C — Chart builder
│   ├── 4_AI_Chat.py                # Page E — AI Chat & Snippets
│   └── 5_Export_Report.py          # Page D — Export & reports
├── utils/
│   ├── __init__.py
│   ├── data_loader.py             # File upload & parsing
│   ├── profiler.py                # Data profiling
│   ├── cleaning.py                # Cleaning operations
│   ├── validation.py              # Data validation rules
│   ├── viz.py                     # Visualization helpers
│   ├── export.py                  # Export & recipe generation
│   ├── transform_log.py          # Transformation log & undo
│   ├── ai_assistant.py           # Optional AI integration
│   └── generate_sample_data.py   # Sample data generator
├── sample_data/
│   ├── ecommerce_orders.csv       # ~1,500 rows, 10 columns
│   └── weather_stations.xlsx      # ~1,200 rows, 9 columns
├── tests/
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_profiler.py
│   └── test_transform_log.py
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI
├── .streamlit/
│   └── config.toml               # App theme
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

- Student 1
- Student 2

## 📄 License

This project was created for the Data Wrangling & Visualization (5COSC038C) coursework.

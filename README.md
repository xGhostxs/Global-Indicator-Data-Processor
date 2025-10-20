# 🌍 Global Indicator Data Processor

This Python tool reads, cleans, and reshapes **World Development Indicator (WDI)**–style datasets.  
It preserves **all countries, all indicators, and all years**, without filtering, averaging, or aggregation.  
Large datasets are automatically split across multiple Excel sheets to avoid Excel row limits.

---

## 🚀 Features

- Reads main WDI CSV and optional country metadata CSV
- Converts wide format data into long format (`country-year-indicator-value`)
- Converts year columns to numeric, cleans missing or invalid values
- Merges country metadata (e.g., income group) if provided
- Exports all data into Excel:
  - Large datasets are automatically split into multiple sheets
  - Each indicator can be saved to a separate sheet
  - Sheet names are automatically truncated to Excel limits
- Provides a preview of the first 15 rows in the console

---

## 📁 Folder Structure

project_root/
├─ data/
│ ├─ data_main.csv # Main WDI-style CSV
│ └─ data_country.csv # Optional country metadata
├─ output/
│ └─ global_indicator_output.xlsx
├─ main.py
├─ requirements.txt
└─ README.md

---

## ⚙️ Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/global-indicator-processor.git
cd global-indicator-processor
pip install -r requirements.txt
python main.py
output/global_indicator_output.xlsx

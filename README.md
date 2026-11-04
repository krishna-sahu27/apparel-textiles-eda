# Apparel & Textiles – Exploratory Data Analysis

**Internship:** YuvaIntern – Week 2  
**Project:** Exploratory Data Analysis of Fashion Retail Sales  
**Tools:** Python, Pandas, NumPy, Matplotlib, Seaborn

## Dataset
Use the public Fashion Retail Sales CSV:
- Source page: https://github.com/aakinwande/Fashion-Retail-Sales-Analysis/blob/main/Fashion_Retail_Sales.csv
- Dataset file: `Fashion_Retail_Sales.csv`
- Expected columns: Customer Reference ID, Item Purchased, Purchase Amount (USD), Date Purchase, Review Rating, Payment Method.
- The source preview reports approximately 3,400 records. Confirm the exact row count after downloading.

Download the CSV and place it at `data/Fashion_Retail_Sales.csv`. Do not upload the raw dataset to GitHub unless its license/redistribution terms permit it; linking to the source is sufficient.

## Run in VS Code (Windows)
```powershell
py -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python eda_analysis.py
```

## Outputs
The script creates a cleaned CSV, item/monthly summaries, an EDA summary, and six PNG charts under `outputs/`.

## Analysis workflow
1. Inspect dataset shape, columns, data types, missing values and duplicates.
2. Standardize column names and convert amount, rating and date fields.
3. Remove duplicates; exclude rows without usable date, item or payment category.
4. Impute missing purchase amount with the median and missing rating with the mean.
5. Flag purchase-amount outliers using the 1.5×IQR rule; do not automatically delete them.
6. Explore item performance, monthly revenue, payment methods, ratings and amount-rating relationship.
7. Interpret the charts in business context.

## Limitations
This transaction sample does not include inventory, cost, profit margin, marketing spend, store-level or demographic information. Purchase amount is not profit; correlation does not establish causation. Avoid claiming long-term industry-wide seasonality from a limited date range.

## Repository structure
`data/` stores the downloaded CSV locally (ignored by Git); `outputs/` stores generated analysis outputs; `eda_analysis.py` contains the reproducible analysis.

# Apparel and Textiles EDA


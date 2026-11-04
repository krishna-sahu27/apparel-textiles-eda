# Week 3 — Apparel & Textiles Data Integration and Transformation

**Internship:** YuvaIntern — Junior Data Analyst (Apparel & Textiles)  
**Author:** Krishna Sahu  
**Repository:** [apparel-textiles-eda](https://github.com/krishna-sahu27/apparel-textiles-eda)

## Objective

Combine retail transaction data with a separate fashion article catalogue, standardize the fields, reconcile category labels, and produce a validated integrated dataset. The workflow demonstrates profiling, cleaning, transformation, mapping, joining, exception reporting, and quality assurance.

## Data sources

1. **Fashion Retail Sales** — customer reference, purchased item, sales amount (USD), purchase date, review rating, and payment method. Public dataset page: https://www.kaggle.com/datasets/atharvasoundankar/fashion-retail-sales
2. **H&M Personalized Fashion Recommendations — Articles** — product/article identifiers and product metadata such as product type, product group, colour group, and product name. Source: https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations

Download the retail CSV as `Fashion_Retail_Sales.csv` and H&M's `articles.csv`. Put both in this folder's `data/` directory. The H&M competition may require a Kaggle account and acceptance of its rules.

**Important matching limitation:** The retail sample does not provide H&M article IDs. Therefore this project reconciles at a normalized category level, not at exact SKU/article level. Category matching is approximate and is labelled as such. Unmatched records are retained. The small `sample_*.csv` files are synthetic examples for testing and are not real customer or H&M data.

## Folder structure

```
Week_3_Data_Integration/
├── data/
│   ├── sample_fashion_retail_sales.csv
│   └── sample_hm_articles.csv
├── output/                 # generated outputs; not committed
├── data_integration.py
├── requirements.txt
└── README.md
```

## Run in VS Code (Windows PowerShell)

From this folder:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python data_integration.py
```

For a quick demo, run without downloading anything: the script automatically uses the two synthetic sample files if the real files are absent. If you have real datasets, place them in `data/`; the real filenames take priority.

## Outputs

The script creates:

- `output/integrated_apparel_transactions.csv` — one row per retained retail transaction, enriched with category-level catalogue metadata.
- `output/category_catalog.csv` — one unique row per normalized category, with article counts and example metadata.
- `output/product_mapping.csv` — source product labels mapped to canonical categories.
- `output/data_quality_report.csv` and `data_quality_report.json` — validation results and exception counts.

## Transformation and reconciliation

- Standardizes column names and trims text.
- Parses dates and converts sales and ratings to numeric values.
- Normalizes product descriptions into a controlled category taxonomy.
- Removes exact duplicate rows only; does not silently delete unusual but potentially valid purchases.
- Flags missing/invalid amounts, negative amounts, invalid ratings, and dates.
- Aggregates article metadata to one row per canonical category before joining. This prevents a many-to-many join from multiplying transactions.
- Uses a left join so all retail transactions remain in the output.
- Flags each transaction as `matched_category` or `unmatched_category`.

## Validation rules

The pipeline asserts that the integrated row count equals the cleaned retail row count, integration IDs are unique, and the category dimension has unique keys. It also reports duplicate removal, missing values, negative sales, invalid ratings/dates, and category match coverage. Quality exceptions are visible in reports rather than hidden through arbitrary imputation.

## Limitations and responsible use

Category-level similarity is not proof that two products are identical. For exact product-level reconciliation, both sources need a shared SKU/article identifier or an approved crosswalk. Currency conversion, taxes, discounts, and differing date conventions must be resolved before combining financial totals across sources. Use original dataset licences and Kaggle competition terms; do not publish restricted raw data or personal information.

## Reference

The structure and learning approach were informed by the public example repository [its-Kunal-fr/Apparel-Textiles-Data-Integration](https://github.com/its-Kunal-fr/Apparel-Textiles-Data-Integration). This implementation is independently written and includes a category-level join with explicit match limitations and synthetic test data.

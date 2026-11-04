# YuvaIntern Week 3 — Data Integration and Transformation Report

**Project:** Apparel & Textiles Data Integration and Transformation  
**Prepared by:** Krishna Sahu  
**Role:** Junior Data Analyst — Apparel & Textiles  
**Tools:** Python, Pandas, NumPy, VS Code, GitHub  
**Report type:** Technical project report and reproducible workflow

## 1. Executive summary

This project demonstrates how two independently maintained apparel datasets can be prepared for combined analysis. A retail transaction source contains customer references, purchased-item labels, purchase amounts, dates, ratings, and payment methods. A separate H&M article catalogue contains article identifiers and product metadata such as product names, product types, product groups, and colours. These sources differ in purpose, schema, granularity, and identifier systems.

The workflow profiles both inputs, standardizes field names and data types, creates a common product-category taxonomy, removes exact duplicate records, preserves exceptions, and joins transaction records to a category-level catalogue. It produces a unified transaction file, a category catalogue, a product mapping table, and a data-quality report.

A key design decision is that the retail transaction data does not contain H&M article identifiers. Consequently, a defensible exact SKU-to-article join is not possible. This implementation uses conservative category-level reconciliation and labels it clearly. It does not claim that a retail item is the same physical H&M article. Unmatched records are retained for review.

## 2. Business problem and objectives

Apparel retailers often store point-of-sale transactions, product catalogues, inventory records, and customer feedback in separate systems. Different teams may use different names for the same category, date formats, identifiers, or data types. If these sources are analysed independently, decision-makers may miss useful relationships between sales and product assortment.

The objectives are to:
1. Identify two public sources relevant to apparel retail.
2. Explain their different formats and levels of detail.
3. Profile the inputs before transformation.
4. Standardize names, types, text, and product categories.
5. Reconcile category labels without fabricating exact product matches.
6. Integrate the data while preserving transaction rows.
7. validate the result with programmatic checks.
8. Produce reproducible outputs and document limitations.

## 3. Data sources and selection

### 3.1 Fashion Retail Sales

Source: https://www.kaggle.com/datasets/atharvasoundankar/fashion-retail-sales

The dataset is a transaction-oriented CSV. Typical fields include Customer Reference ID, Item Purchased, Purchase Amount (USD), Date Purchase, Review Rating, and Payment Method. It is useful because it represents a simplified retail sales event and contains both numeric and categorical attributes.

### 3.2 H&M Personalized Fashion Recommendations — Articles

Source: https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations

The articles file is a product-master CSV. Typical fields include article_id, prod_name, product_type_name, product_group_name, colour_group_name, department_name, and garment_group_name. It describes products rather than individual retail purchases. Kaggle access may require account registration and acceptance of competition rules.

### 3.3 Differences between the sources

| Aspect | Retail sales | H&M articles |
|---|---|---|
| Business purpose | Record purchases | Describe products |
| Grain | Transaction row | Article/product row |
| Identifiers | Customer reference; no H&M article ID | Article ID |
| Measures | Purchase amount and rating | Product attributes |
| Dates | Purchase date | Usually no transaction date |
| Categories | Item Purchased text | Product type/group |
| Typical format | CSV | CSV |

These differences make direct row concatenation inappropriate. The correct conceptual model is to enrich transaction rows with a product dimension through a documented mapping key.

## 4. Data acquisition and project organization

The downloaded source files should be stored locally in the `data/` folder. The project includes small synthetic sample CSVs to allow a reproducible demonstration without redistributing the full public datasets. The sample records are illustrative and must not be described as real observations.

Expected input filenames:
- `data/Fashion_Retail_Sales.csv`
- `data/articles.csv`

The script automatically falls back to `sample_fashion_retail_sales.csv` and `sample_hm_articles.csv` when real source files are absent. Real files take priority when present.

## 5. Data profiling

Before transformation, the script reports:
- number of rows and columns;
- exact duplicate row count;
- total missing cells;
- available field names and schema compatibility.

Profiling identifies structural issues before the merge. It also helps distinguish a missing value from a value that merely uses a different spelling or format.

## 6. Transformation strategy

### 6.1 Column-name standardization

Column labels are converted to lowercase snake_case. Punctuation and repeated separators are removed. This makes source fields easier to reference consistently in code.

### 6.2 Data-type conversion

Sales amounts and ratings are converted to numeric values using safe coercion. Currency symbols and thousands separators are removed from amount strings before conversion. Purchase dates are parsed into a datetime type. Unparseable values become missing and are counted in the quality report.

### 6.3 Text cleaning

Text values are trimmed to remove leading and trailing spaces. Payment methods are converted to lowercase to reduce superficial category differences. Original product labels are retained in the output so the transformation remains traceable.

### 6.4 Category normalization

A common taxonomy is applied to both source datasets. Rule-based mappings group similar terms into categories such as tops, bottoms, one_piece, outerwear, footwear, accessories, and innerwear. The rules are intentionally conservative and can be extended after reviewing source-specific labels.

### 6.5 Missing values and outliers

The pipeline does not invent missing sales amounts or dates. Such values are retained and flagged. Negative amounts are flagged because they may represent returns, corrections, or errors; they are not automatically removed. Ratings outside the expected 1–5 range are flagged. This approach preserves evidence for business review instead of silently changing source facts.

### 6.6 Duplicate handling

Exact duplicate rows are removed from each input. The number removed is reported. The script does not drop records merely because two customers bought the same item on the same date; those can be legitimate separate transactions.

## 7. Data integration workflow

The integration proceeds as follows:

1. Load the retail transaction CSV and H&M article CSV.
2. Profile row counts, columns, missing values, and exact duplicates.
3. Standardize source column names.
4. Convert dates and numeric fields safely.
5. Normalize retail item labels and H&M product descriptions into the shared category taxonomy.
6. Remove exact duplicate rows.
7. Build a category catalogue from article metadata.
8. Aggregate the catalogue to one row per canonical category.
9. Perform a left join from retail transactions to the category catalogue.
10. Assign an integration record ID and a category-match status.
11. Run validation checks and export all outputs.

### Why aggregate the article catalogue first?

A category can contain many articles. Joining raw articles directly to transactions on category could multiply each transaction into several rows. Aggregating article metadata to one row per category creates a many-to-one relationship and prevents accidental inflation of transaction counts. The output article_count communicates how many catalogue records contributed to each category.

## 8. Reconciliation conflicts and resolutions

| Potential conflict | Resolution |
|---|---|
| Different column names | Standardize to a common schema |
| Upper/lowercase differences | Normalize text case |
| Extra spaces and punctuation | Trim and normalize labels |
| Different product category terms | Apply controlled category mapping |
| Multiple articles in one category | Aggregate to one category record before joining |
| No shared product ID | Use category-level matching and disclose limitation |
| Unmatched categories | Retain row and flag for review |
| Missing amount/date | Retain and report; do not fabricate |
| Negative amount | Flag for return/adjustment investigation |
| Invalid rating | Flag values outside 1–5 |
| Duplicate records | Remove exact duplicates and report count |

## 9. Validation and quality assurance

Validation is performed both before and after integration.

### 9.1 Structural validation

- The integrated transaction row count must equal the cleaned retail transaction row count.
- Integration record IDs must be unique.
- Category catalogue keys must be unique.
- A many-to-one merge validation prevents unexpected multiplication.

### 9.2 Field-level validation

- Count missing or invalid sales amounts.
- Count negative sales amounts.
- Count ratings outside the 1–5 range.
- Count missing or invalid dates.
- Count records matched and unmatched at category level.

### 9.3 Reconciliation validation

The left join preserves all cleaned retail transactions. A row-count assertion catches accidental row multiplication or loss. Category match coverage is reported as matched and unmatched counts. A match means category compatibility only, not proof of SKU identity.

### 9.4 Output audit trail

The generated quality report is saved in CSV and JSON formats. The product mapping file records original labels and normalized categories. These artifacts support review, debugging, and repeatable execution.

## 10. Outputs and interpretation

The pipeline generates:
- `integrated_apparel_transactions.csv`
- `category_catalog.csv`
- `product_mapping.csv`
- `data_quality_report.csv`
- `data_quality_report.json`

The integrated table is suitable for exploratory analysis at transaction and broad category level. Analysts can compare sales amounts by normalized category and inspect which categories have catalogue coverage. It should not be used to claim exact H&M product sales because the retail source lacks a shared article ID.

## 11. Business applications

A reconciled dataset can support:
- category-level sales summaries;
- product assortment coverage checks;
- customer purchase pattern analysis;
- identification of categories requiring better product metadata;
- preparation of a downstream Power BI dashboard;
- data-quality monitoring across source systems.

Sales amount is not profit. Margin, inventory availability, discounts, returns, and tax treatment would be required for profitability analysis.

## 12. Challenges, limitations, and improvements

The largest challenge is the absence of a common product identifier across the two selected sources. Category matching is useful for demonstrating integration, but it is less precise than SKU matching. Future work should use an approved crosswalk, barcode, SKU, or article identifier.

The category mapping rules may not cover every label and should be reviewed with a domain expert. A production pipeline should include versioned mapping tables, logging, schema contracts, automated tests, source checksums, and a quarantine process for invalid records.

The datasets may use different geographic markets, currencies, collection periods, and definitions. Financial comparisons should not be made until currency, tax, returns, and date semantics are harmonized. Dataset licensing and Kaggle competition terms must be respected; raw restricted data should not be committed to a public repository.

## 13. Conclusion

This project demonstrates a structured and reproducible data integration process for apparel retail. It combines transaction information with product catalogue metadata using a transparent category-level reconciliation strategy. Cleaning, normalization, deduplication, controlled joins, exception handling, and validation are documented and automated. Most importantly, the implementation preserves unmatched records and clearly distinguishes category-level similarity from exact product identity. This is essential for trustworthy analysis in a real business environment.

## 14. References

1. Fashion Retail Sales dataset: https://www.kaggle.com/datasets/atharvasoundankar/fashion-retail-sales
2. H&M Personalized Fashion Recommendations: https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations
3. Reference learning repository: https://github.com/its-Kunal-fr/Apparel-Textiles-Data-Integration
4. Pandas documentation: https://pandas.pydata.org/docs/

## Appendix A — Execution commands

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python data_integration.py
```

## Appendix B — Reproducibility note

The included demo CSVs are synthetic and intentionally small. Run the pipeline with them first to verify the code and output structure. For internship analysis using public data, download the source files from their official dataset pages, place them in `data/`, and rerun the same script. Record the actual input filenames, row counts, run date, and validation results in the final submitted report.

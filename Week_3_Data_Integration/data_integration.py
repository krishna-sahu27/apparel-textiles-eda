"""
YuvaIntern Week 3 - Apparel & Textiles Data Integration
Author: Krishna Sahu
Purpose: Integrate retail transactions with H&M article metadata.

The integration is performed at a normalized product-category level because
the Fashion Retail Sales sample does not contain H&M article IDs/SKUs.
Unmatched categories are retained and clearly flagged; no SKU-level match
is fabricated.
"""
from pathlib import Path
import re
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(exist_ok=True)

RETAIL_CANDIDATES = [DATA / "Fashion_Retail_Sales.csv",
                     DATA / "sample_fashion_retail_sales.csv"]
ARTICLES_CANDIDATES = [DATA / "articles.csv",
                       DATA / "HnM_Articles.csv",
                       DATA / "sample_hm_articles.csv"]

def choose_file(candidates, label):
    for path in candidates:
        if path.exists():
            print(f"[LOAD] {label}: {path.name}")
            return path
    raise FileNotFoundError(
        f"{label} not found. Place it in {DATA}. Tried: "
        + ", ".join(p.name for p in candidates)
    )

def read_csv_safely(path):
    # utf-8-sig handles common Excel-exported CSV files.
    try:
        return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1", low_memory=False)

def clean_column_names(df):
    df = df.copy()
    df.columns = [re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_")
                  for c in df.columns]
    return df

def first_existing(df, names, required=True):
    for name in names:
        if name in df.columns:
            return name
    if required:
        raise ValueError(f"Required column not found. Expected one of: {names}. "
                         f"Available: {list(df.columns)}")
    return None

def normalize_category(value):
    """Map related category labels to a conservative common taxonomy."""
    if pd.isna(value):
        return "unknown"
    text = re.sub(r"[^a-z0-9 ]", " ", str(value).lower())
    text = re.sub(r"\s+", " ", text).strip()
    rules = [
        (r"t.?shirt|tee shirt|vest top|top", "tops"),
        (r"shirt|blouse|sweatshirt|hoodie|sweater|cardigan|jumper|knitwear", "tops"),
        (r"trouser|pants|jean|legging|shorts", "bottoms"),
        (r"skirt", "bottoms"),
        (r"dress|gown|jumpsuit|playsuit", "one_piece"),
        (r"coat|jacket|blazer|parka|outerwear", "outerwear"),
        (r"shoe|boot|sandal|sneaker|trainer", "footwear"),
        (r"bag|backpack|purse", "accessories"),
        (r"hat|cap|scarf|belt|glove|sock|tights", "accessories"),
        (r"underwear|bra|brief|lingerie|swimwear|bikini", "innerwear"),
    ]
    for pattern, canonical in rules:
        if re.search(pattern, text):
            return canonical
    return text.replace(" ", "_") if text else "unknown"

def prepare_retail(raw):
    df = clean_column_names(raw)
    customer = first_existing(df, ["customer_reference_id", "customer_id"], False)
    product = first_existing(df, ["item_purchased", "product_name", "product"])
    amount = first_existing(df, ["purchase_amount_usd", "sales_amount_usd",
                                 "purchase_amount", "amount"])
    date = first_existing(df, ["date_purchase", "transaction_date", "date"], False)
    rating = first_existing(df, ["review_rating", "rating"], False)
    payment = first_existing(df, ["payment_method", "payment_type"], False)
    out = pd.DataFrame()
    out["source_customer_id"] = df[customer].astype("string").str.strip() if customer else pd.NA
    out["source_product_name"] = df[product].astype("string").str.strip()
    out["sales_amount_usd"] = pd.to_numeric(
        df[amount].astype("string").str.replace(r"[$,]", "", regex=True),
        errors="coerce")
    out["transaction_date"] = pd.to_datetime(df[date], errors="coerce") if date else pd.NaT
    out["review_rating"] = pd.to_numeric(df[rating], errors="coerce") if rating else pd.NA
    out["payment_method"] = (df[payment].astype("string").str.strip().str.lower()
                             if payment else "not_provided")
    out["canonical_category"] = out["source_product_name"].map(normalize_category)
    out["source_row_number"] = range(2, len(out) + 2)
    return out

def prepare_articles(raw):
    df = clean_column_names(raw)
    article_id = first_existing(df, ["article_id", "product_id", "sku"], False)
    product_type = first_existing(df, ["product_type_name", "product_type"], False)
    product_group = first_existing(df, ["product_group_name", "product_group"], False)
    name = first_existing(df, ["prod_name", "product_name", "product"], False)
    if not any([product_type, product_group, name]):
        raise ValueError("H&M articles file needs product_type_name, "
                         "product_group_name, or prod_name.")
    out = pd.DataFrame()
    out["source_article_id"] = df[article_id].astype("string") if article_id else pd.NA
    out["article_name"] = df[name].astype("string").str.strip() if name else pd.NA
    out["product_type"] = df[product_type].astype("string").str.strip() if product_type else pd.NA
    out["product_group"] = df[product_group].astype("string").str.strip() if product_group else pd.NA
    # Prefer the more granular product type, then product name, then group.
    basis = out["product_type"].fillna(out["article_name"]).fillna(out["product_group"])
    out["canonical_category"] = basis.map(normalize_category)
    return out

def profile(name, df):
    print(f"\n--- {name} PROFILE ---")
    print("Rows:", len(df), "| Columns:", len(df.columns))
    print("Missing values:", int(df.isna().sum().sum()))
    print("Exact duplicate rows:", int(df.duplicated().sum()))

def main():
    retail_path = choose_file(RETAIL_CANDIDATES, "Retail transactions")
    article_path = choose_file(ARTICLES_CANDIDATES, "H&M article catalogue")
    retail_raw, articles_raw = read_csv_safely(retail_path), read_csv_safely(article_path)
    profile("Retail raw", retail_raw)
    profile("Articles raw", articles_raw)

    retail = prepare_retail(retail_raw)
    articles = prepare_articles(articles_raw)

    retail_before = len(retail)
    retail = retail.drop_duplicates().copy()
    # Invalid monetary values are retained for audit but flagged; they are not
    # silently imputed because a fabricated sales amount harms reconciliation.
    retail["sales_amount_status"] = retail["sales_amount_usd"].apply(
        lambda x: "missing_or_invalid" if pd.isna(x) else
        ("negative_review" if x < 0 else "valid"))
    retail["rating_status"] = retail["review_rating"].apply(
        lambda x: "not_available" if pd.isna(x) else
        ("valid" if 1 <= x <= 5 else "out_of_range"))
    retail["date_status"] = retail["transaction_date"].apply(
        lambda x: "missing_or_invalid" if pd.isna(x) else "valid")
    articles = articles.drop_duplicates().copy()

    # Build one metadata record per canonical category to prevent a many-to-many
    # join from multiplying transaction rows.
    valid_articles = articles[articles["canonical_category"] != "unknown"].copy()
    category_catalog = (valid_articles.groupby("canonical_category", as_index=False)
        .agg(article_count=("canonical_category", "size"),
             example_article=("article_name", "first"),
             example_product_type=("product_type", "first"),
             example_product_group=("product_group", "first")))
    category_catalog["catalog_match"] = "matched_category"

    integrated = retail.merge(category_catalog, on="canonical_category",
                              how="left", validate="many_to_one")
    integrated["catalog_match"] = integrated["catalog_match"].fillna("unmatched_category")
    integrated.insert(0, "integration_record_id",
                      [f"INT_{i:07d}" for i in range(1, len(integrated) + 1)])

    # Stable source mappings for traceability.
    product_mapping = (retail[["source_product_name", "canonical_category"]]
                       .drop_duplicates().sort_values("source_product_name"))
    product_mapping.insert(0, "master_category_id",
                           [f"CAT_{i:04d}" for i in range(1, len(product_mapping) + 1)])

    checks = {
        "retail_input_rows": int(len(retail_raw)),
        "retail_rows_after_exact_deduplication": int(len(retail)),
        "retail_exact_duplicates_removed": int(retail_before - len(retail)),
        "article_input_rows": int(len(articles_raw)),
        "article_rows_after_exact_deduplication": int(len(articles)),
        "integrated_rows": int(len(integrated)),
        "row_count_preserved": bool(len(integrated) == len(retail)),
        "duplicate_integration_ids": int(integrated["integration_record_id"].duplicated().sum()),
        "missing_sales_amounts": int(integrated["sales_amount_usd"].isna().sum()),
        "negative_sales_amounts": int((integrated["sales_amount_usd"] < 0).sum()),
        "invalid_ratings": int((integrated["rating_status"] == "out_of_range").sum()),
        "missing_or_invalid_dates": int(integrated["transaction_date"].isna().sum()),
        "matched_category_rows": int((integrated["catalog_match"] == "matched_category").sum()),
        "unmatched_category_rows": int((integrated["catalog_match"] == "unmatched_category").sum()),
        "duplicate_category_keys": int(category_catalog["canonical_category"].duplicated().sum()),
    }

    # Fail fast on structural errors; data-quality exceptions are reported.
    assert checks["row_count_preserved"], "Join changed transaction row count."
    assert checks["duplicate_integration_ids"] == 0, "Integration IDs are not unique."
    assert checks["duplicate_category_keys"] == 0, "Category dimension is not unique."

    integrated.to_csv(OUTPUT / "integrated_apparel_transactions.csv", index=False)
    category_catalog.to_csv(OUTPUT / "category_catalog.csv", index=False)
    product_mapping.to_csv(OUTPUT / "product_mapping.csv", index=False)
    pd.DataFrame([{"check": k, "result": v} for k, v in checks.items()]).to_csv(
        OUTPUT / "data_quality_report.csv", index=False)
    (OUTPUT / "data_quality_report.json").write_text(
        json.dumps(checks, indent=2, default=str), encoding="utf-8")

    print("\n--- VALIDATION SUMMARY ---")
    for key, value in checks.items():
        print(f"{key}: {value}")
    print("\nPipeline completed. Files saved in:", OUTPUT)
    print("Note: category-level reconciliation is not an exact SKU-level match.")

if __name__ == "__main__":
    main()

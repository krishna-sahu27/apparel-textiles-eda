"""
Apparel & Textiles Retail: Exploratory Data Analysis
YuvaIntern Week 2 internship project

Input:
    data/Fashion_Retail_Sales.csv

Run:
    pip install -r requirements.txt
    python eda_analysis.py

Outputs are written to outputs/ and outputs/charts/.
"""

from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "Fashion_Retail_Sales.csv"
OUTPUT_DIR = ROOT / "outputs"
CHART_DIR = OUTPUT_DIR / "charts"

sns.set_theme(style="whitegrid")


def standardize_column_name(name: str) -> str:
    """Convert source column names into predictable snake_case names."""
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def find_column(data: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first matching column from a list of possible names."""
    for candidate in candidates:
        if candidate in data.columns:
            return candidate
    return None


def save_chart(filename: str) -> None:
    """Save the current Matplotlib figure and close it."""
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(CHART_DIR / filename, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_PATH.exists():
        print("Dataset not found.")
        print(f"Please download Fashion_Retail_Sales.csv and place it here:\n{DATA_PATH}")
        sys.exit(1)

    # 1. Load and inspect the dataset
    df = pd.read_csv(DATA_PATH)
    original_rows, original_columns = df.shape

    print("\n========== INITIAL DATASET OVERVIEW ==========")
    print(f"Rows: {original_rows:,}")
    print(f"Columns: {original_columns}")
    print("\nColumn names:")
    print(df.columns.tolist())
    print("\nData types:")
    print(df.dtypes)
    print("\nMissing values:")
    print(df.isna().sum())
    print(f"\nDuplicate rows: {df.duplicated().sum():,}")

    # 2. Standardize column names and identify required fields
    df.columns = [standardize_column_name(col) for col in df.columns]

    item_col = find_column(df, ["item_purchased", "item", "product", "product_name"])
    amount_col = find_column(
        df, ["purchase_amount_usd", "purchase_amount", "amount", "sales"]
    )
    date_col = find_column(
        df, ["date_purchase", "purchase_date", "date", "transaction_date"]
    )
    rating_col = find_column(df, ["review_rating", "rating", "customer_rating"])
    payment_col = find_column(
        df, ["payment_method", "payment_type", "payment"]
    )

    required = {
        "item/product": item_col,
        "purchase amount": amount_col,
        "purchase date": date_col,
        "review rating": rating_col,
        "payment method": payment_col,
    }
    missing_required = [name for name, col in required.items() if col is None]
    if missing_required:
        print("\nCould not identify these required fields:", ", ".join(missing_required))
        print("Available standardized columns:", df.columns.tolist())
        print("Update the candidate names in eda_analysis.py to match your CSV.")
        sys.exit(1)

    # 3. Convert columns to appropriate data types
    df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")
    df[rating_col] = pd.to_numeric(df[rating_col], errors="coerce")
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # 4. Clean duplicate and unusable records
    before_duplicates = len(df)
    df = df.drop_duplicates().copy()
    duplicates_removed = before_duplicates - len(df)

    before_required = len(df)
    df = df.dropna(subset=[item_col, date_col, payment_col]).copy()
    rows_missing_key_fields_removed = before_required - len(df)

    # Impute numeric missing values using robust/simple central measures.
    amount_median = df[amount_col].median()
    rating_mean = df[rating_col].mean()

    if pd.isna(amount_median):
        raise ValueError("Purchase amount column contains no valid numeric values.")
    df[amount_col] = df[amount_col].fillna(amount_median)

    if not pd.isna(rating_mean):
        df[rating_col] = df[rating_col].fillna(rating_mean)

    # 5. Add date and outlier-analysis fields
    df["purchase_month"] = df[date_col].dt.to_period("M").astype(str)
    q1 = df[amount_col].quantile(0.25)
    q3 = df[amount_col].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    df["amount_outlier_flag"] = (
        (df[amount_col] < lower_bound) | (df[amount_col] > upper_bound)
    )

    # 6. Generate summary tables
    item_summary = (
        df.groupby(item_col)
        .agg(
            transactions=(amount_col, "size"),
            total_revenue=(amount_col, "sum"),
            average_purchase_amount=(amount_col, "mean"),
            average_rating=(rating_col, "mean"),
        )
        .sort_values("total_revenue", ascending=False)
        .reset_index()
    )

    monthly_summary = (
        df.groupby("purchase_month")
        .agg(
            transactions=(amount_col, "size"),
            total_revenue=(amount_col, "sum"),
            average_purchase_amount=(amount_col, "mean"),
        )
        .reset_index()
        .sort_values("purchase_month")
    )

    payment_summary = (
        df[payment_col].value_counts(dropna=False)
        .rename_axis("payment_method")
        .reset_index(name="transactions")
    )

    # 7. Create visualizations
    top_items_count = df[item_col].value_counts().head(10).sort_values()
    plt.figure(figsize=(10, 6))
    top_items_count.plot(kind="barh")
    plt.title("Top 10 Items by Number of Transactions")
    plt.xlabel("Number of transactions")
    plt.ylabel("Item purchased")
    save_chart("01_top_items_by_transactions.png")

    top_revenue = item_summary.head(10).sort_values("total_revenue")
    plt.figure(figsize=(10, 6))
    plt.barh(top_revenue[item_col].astype(str), top_revenue["total_revenue"])
    plt.title("Top 10 Items by Total Purchase Amount")
    plt.xlabel("Total purchase amount (USD)")
    plt.ylabel("Item purchased")
    save_chart("02_revenue_by_item.png")

    plt.figure(figsize=(11, 5))
    plt.plot(
        monthly_summary["purchase_month"],
        monthly_summary["total_revenue"],
        marker="o",
    )
    plt.title("Monthly Purchase Amount Trend")
    plt.xlabel("Purchase month")
    plt.ylabel("Total purchase amount (USD)")
    plt.xticks(rotation=45, ha="right")
    save_chart("03_monthly_sales_trend.png")

    payment_counts = df[payment_col].value_counts()
    plt.figure(figsize=(8, 6))
    plt.pie(
        payment_counts.values,
        labels=payment_counts.index.astype(str),
        autopct="%1.1f%%",
        startangle=90,
    )
    plt.title("Payment Method Distribution")
    save_chart("04_payment_method_distribution.png")

    rating_data = df[[rating_col, amount_col]].dropna()
    plt.figure(figsize=(9, 6))
    sns.scatterplot(data=rating_data, x=rating_col, y=amount_col, alpha=0.65)
    plt.title("Review Rating vs Purchase Amount")
    plt.xlabel("Review rating")
    plt.ylabel("Purchase amount (USD)")
    save_chart("05_rating_vs_purchase_amount.png")

    plt.figure(figsize=(9, 5))
    sns.boxplot(x=df[amount_col])
    plt.title("Distribution of Purchase Amounts")
    plt.xlabel("Purchase amount (USD)")
    save_chart("06_purchase_amount_boxplot.png")

    # 8. Export cleaned data and analytical tables
    df.to_csv(OUTPUT_DIR / "cleaned_fashion_retail_sales.csv", index=False)
    item_summary.to_csv(OUTPUT_DIR / "item_performance_summary.csv", index=False)
    monthly_summary.to_csv(OUTPUT_DIR / "monthly_sales_summary.csv", index=False)
    payment_summary.to_csv(OUTPUT_DIR / "payment_method_summary.csv", index=False)

    correlation = df[[amount_col, rating_col]].corr().iloc[0, 1]
    outlier_count = int(df["amount_outlier_flag"].sum())

    # 9. Write a plain-text summary with dataset-specific values
    summary_lines = [
        "APPAREL & TEXTILES RETAIL – EDA SUMMARY",
        "=" * 48,
        f"Input file: {DATA_PATH.name}",
        f"Original rows: {original_rows}",
        f"Original columns: {original_columns}",
        f"Duplicate rows removed: {duplicates_removed}",
        f"Rows removed for missing item/date/payment: {rows_missing_key_fields_removed}",
        f"Rows after cleaning: {len(df)}",
        f"Missing purchase amounts filled with median: {amount_median:.2f}",
        f"Missing review ratings filled with mean: "
        f"{rating_mean:.2f}" if not pd.isna(rating_mean) else "No valid ratings available",
        f"Purchase amount outliers flagged (not removed): {outlier_count}",
        f"Outlier lower bound: {lower_bound:.2f}",
        f"Outlier upper bound: {upper_bound:.2f}",
        f"Total purchase amount (USD): {df[amount_col].sum():.2f}",
        f"Average purchase amount (USD): {df[amount_col].mean():.2f}",
        f"Average review rating: {df[rating_col].mean():.2f}",
        f"Amount-rating correlation: {correlation:.4f}",
        "",
        "Top 5 items by total purchase amount:",
        item_summary.head(5).to_string(index=False),
        "",
        "Monthly summary:",
        monthly_summary.to_string(index=False),
        "",
        "Payment method summary:",
        payment_summary.to_string(index=False),
        "",
        "Charts saved in: outputs/charts/",
        "Note: purchase amount is revenue-like transaction value, not profit.",
        "Correlation does not establish causation.",
    ]
    (OUTPUT_DIR / "eda_summary.txt").write_text(
        "\n".join(summary_lines), encoding="utf-8"
    )

    print("\n========== CLEANING SUMMARY ==========")
    print(f"Original rows: {original_rows:,}")
    print(f"Rows after cleaning: {len(df):,}")
    print(f"Duplicates removed: {duplicates_removed:,}")
    print(f"Outliers flagged (not removed): {outlier_count:,}")
    print("\nTop 5 items by total purchase amount:")
    print(item_summary.head(5).to_string(index=False))
    print("\nMonthly sales summary:")
    print(monthly_summary.to_string(index=False))
    print("\nPayment method summary:")
    print(payment_summary.to_string(index=False))
    print(f"\nAnalysis complete. Check the folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

"""Profile the nine immutable Olist source CSV files.

The large geolocation table is processed in chunks. Duplicate counts represent
fully duplicated rows after the first occurrence. Row hashes keep memory usage
bounded compared with loading the complete table as Python objects.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


EXPECTED_SCHEMAS: dict[str, list[str]] = {
    "olist_customers_dataset.csv": [
        "customer_id", "customer_unique_id", "customer_zip_code_prefix",
        "customer_city", "customer_state",
    ],
    "olist_geolocation_dataset.csv": [
        "geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng",
        "geolocation_city", "geolocation_state",
    ],
    "olist_order_items_dataset.csv": [
        "order_id", "order_item_id", "product_id", "seller_id",
        "shipping_limit_date", "price", "freight_value",
    ],
    "olist_order_payments_dataset.csv": [
        "order_id", "payment_sequential", "payment_type",
        "payment_installments", "payment_value",
    ],
    "olist_order_reviews_dataset.csv": [
        "review_id", "order_id", "review_score", "review_comment_title",
        "review_comment_message", "review_creation_date", "review_answer_timestamp",
    ],
    "olist_orders_dataset.csv": [
        "order_id", "customer_id", "order_status", "order_purchase_timestamp",
        "order_approved_at", "order_delivered_carrier_date",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    ],
    "olist_products_dataset.csv": [
        "product_id", "product_category_name", "product_name_lenght",
        "product_description_lenght", "product_photos_qty", "product_weight_g",
        "product_length_cm", "product_height_cm", "product_width_cm",
    ],
    "olist_sellers_dataset.csv": [
        "seller_id", "seller_zip_code_prefix", "seller_city", "seller_state",
    ],
    "product_category_name_translation.csv": [
        "product_category_name", "product_category_name_english",
    ],
}

# No independently verified reference row counts are embedded. Empty values in
# the comparison output deliberately distinguish validation from guesswork.
REFERENCE_ROWS: dict[str, int] = {}


def find_project_root(start: Path | None = None) -> Path:
    """Find the nearest parent containing both .git and data/raw."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() and (candidate / "data" / "raw").is_dir():
            return candidate
    raise FileNotFoundError("Could not locate project root containing .git and data/raw")


def profile_csv(path: Path, expected_columns: list[str], chunk_size: int) -> tuple[dict, list[dict]]:
    """Return file-level metrics and per-column missing-value metrics."""
    actual_rows = 0
    missing = pd.Series(0, index=expected_columns, dtype="int64")
    unique_row_hashes: set[int] = set()
    actual_columns: list[str] | None = None

    for chunk in pd.read_csv(path, chunksize=chunk_size, low_memory=False):
        if actual_columns is None:
            actual_columns = chunk.columns.tolist()
            missing = pd.Series(0, index=actual_columns, dtype="int64")
        actual_rows += len(chunk)
        missing = missing.add(chunk.isna().sum(), fill_value=0).astype("int64")
        unique_row_hashes.update(pd.util.hash_pandas_object(chunk, index=False).astype("uint64").tolist())

    actual_columns = actual_columns or pd.read_csv(path, nrows=0).columns.tolist()
    duplicate_rows = actual_rows - len(unique_row_hashes)
    schema_matches = actual_columns == expected_columns
    reference = REFERENCE_ROWS.get(path.name)
    difference = actual_rows - reference if reference is not None else pd.NA
    status = "PASS" if schema_matches else "FAIL"
    notes = "Schema and CSV readability validated; reference row count not independently verified."
    if not schema_matches:
        notes = f"Column mismatch. Expected {expected_columns}; found {actual_columns}."

    summary = {
        "file_name": path.name,
        "actual_rows": actual_rows,
        "reference_rows": reference if reference is not None else pd.NA,
        "difference": difference,
        "column_count": len(actual_columns),
        "size_mb": round(path.stat().st_size / (1024 * 1024), 3),
        "status": status,
        "duplicate_rows": duplicate_rows,
        "notes": notes,
    }
    missing_rows = [
        {"file_name": path.name, "column_name": column, "missing_values": int(count)}
        for column, count in missing.items()
    ]
    return summary, missing_rows


def run(project_root: Path, chunk_size: int = 100_000) -> pd.DataFrame:
    raw_dir = project_root / "data" / "raw"
    output_dir = project_root / "data" / "profiling"
    output_dir.mkdir(parents=True, exist_ok=True)

    missing_files = [name for name in EXPECTED_SCHEMAS if not (raw_dir / name).is_file()]
    if missing_files:
        raise FileNotFoundError(f"Missing required Olist CSV files: {missing_files}")

    summaries: list[dict] = []
    missing_details: list[dict] = []
    for file_name, expected_columns in EXPECTED_SCHEMAS.items():
        summary, missing_rows = profile_csv(raw_dir / file_name, expected_columns, chunk_size)
        summaries.append(summary)
        missing_details.extend(missing_rows)

    summary_df = pd.DataFrame(summaries)
    summary_df.to_csv(output_dir / "doi_chieu_so_dong.csv", index=False)
    pd.DataFrame(missing_details).to_csv(output_dir / "missing_values.csv", index=False)
    summary_df[["file_name", "duplicate_rows"]].to_csv(
        output_dir / "duplicate_rows.csv", index=False
    )
    return summary_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, help="Repository root; auto-detected by default")
    parser.add_argument("--chunk-size", type=int, default=100_000)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    root = args.project_root.resolve() if args.project_root else find_project_root(Path(__file__).parent)
    result = run(root, args.chunk_size)
    print(result.to_string(index=False))
    if (result["status"] == "FAIL").any():
        raise SystemExit(1)

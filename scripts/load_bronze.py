"""Nạp 10 bảng bronze_* vào commerceflow.duckdb từ data/raw/*.csv.

Dùng đúng logic TAO_BRONZE_TAM trong notebooks/03_Silver_Transformation.ipynb
(all_varchar=true, kèm _ingested_at, _source_file) để Silver/Gold có thể build độc lập
trong lúc chờ 02_Bronze_Ingestion.ipynb chính thức.
"""
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DUCKDB_PATH = PROJECT_ROOT / "commerceflow.duckdb"

RAW_FILES = {
    "bronze_customers": "olist_customers_dataset.csv",
    "bronze_geolocation": "olist_geolocation_dataset.csv",
    "bronze_order_items": "olist_order_items_dataset.csv",
    "bronze_order_payments": "olist_order_payments_dataset.csv",
    "bronze_order_reviews": "olist_order_reviews_dataset.csv",
    "bronze_orders": "olist_orders_dataset.csv",
    "bronze_products": "olist_products_dataset.csv",
    "bronze_sellers": "olist_sellers_dataset.csv",
    "bronze_product_category_name_translation": "product_category_name_translation.csv",
    "bronze_holidays": "holidays_brazil.csv",
}

if __name__ == "__main__":
    with duckdb.connect(str(DUCKDB_PATH)) as con:
        for table, filename in RAW_FILES.items():
            src = (RAW_DIR / filename).as_posix()
            con.execute(f"""
                create or replace table {table} as
                select *, current_timestamp as _ingested_at, '{filename}' as _source_file
                from read_csv('{src}', all_varchar = true, header = true)
            """)
            count = con.execute(f"select count(*) from {table}").fetchone()[0]
            print(f"{table}: {count} dòng")
    print("Xong. DuckDB:", DUCKDB_PATH)

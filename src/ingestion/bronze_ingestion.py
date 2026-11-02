"""B01 - Nạp dữ liệu nguồn vào tầng Bronze (DuckDB).

Nạp 9 CSV Olist + holidays_brazil.csv thành 10 bảng bronze_*:
  * giữ nguyên dữ liệu nguồn: mọi cột đọc dạng VARCHAR (all_varchar), không đổi tên cột, không xóa dòng;
  * bổ sung 2 cột metadata: _ingested_at (thời điểm nạp) và _source_file (tên file nguồn);
  * ghi nhật ký vào bảng ingestion_log: số dòng trong CSV (đếm độc lập bằng module csv),
    số dòng đã nạp, trạng thái khớp/không khớp, thời điểm nạp.

Quy tắc tên bảng: bronze_<tên bảng gốc>, bỏ tiền tố olist_ và hậu tố _dataset.
Silver đọc các bảng này qua source('bronze', ...) trong dbt_project/models/sources.yml.

Chạy từ thư mục gốc repository:
    python -m src.ingestion.bronze_ingestion
"""
from __future__ import annotations

import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

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


def count_csv_rows(path: Path) -> int:
    """Đếm số bản ghi bằng module csv (xử lý đúng ô có xuống dòng trong review)."""
    csv.field_size_limit(sys.maxsize if sys.maxsize < 2**31 else 2**31 - 1)
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # bỏ dòng tiêu đề
        return sum(1 for _ in reader)


def run(project_root: Path | str, duckdb_path: Path | str | None = None) -> pd.DataFrame:
    project_root = Path(project_root)
    raw_dir = project_root / "data" / "raw"
    duckdb_path = Path(duckdb_path or os.environ.get("DUCKDB_PATH", project_root / "commerceflow.duckdb"))

    missing = [f for f in RAW_FILES.values() if not (raw_dir / f).is_file()]
    if missing:
        raise FileNotFoundError(f"Thiếu file nguồn trong data/raw: {missing}")

    batch_ts = datetime.now(timezone.utc).replace(tzinfo=None)
    logs = []
    with duckdb.connect(str(duckdb_path)) as con:
        con.execute("""
            create table if not exists ingestion_log (
                table_name     varchar,
                source_file    varchar,
                csv_rows       bigint,
                loaded_rows    bigint,
                column_count   integer,
                status         varchar,
                ingested_at    timestamp
            )
        """)
        for table, filename in RAW_FILES.items():
            src = (raw_dir / filename).as_posix()
            con.execute(
                f"""
                create or replace table {table} as
                select *,
                       cast(? as timestamp) as _ingested_at,
                       cast(? as varchar)   as _source_file
                from read_csv(?, all_varchar = true, header = true)
                """,
                [batch_ts, filename, src],
            )
            loaded = con.execute(f"select count(*) from {table}").fetchone()[0]
            n_cols = len(con.execute(f"select * from {table} limit 0").description) - 2
            csv_rows = count_csv_rows(raw_dir / filename)
            status = "PASS" if loaded == csv_rows else "FAIL"
            logs.append((table, filename, csv_rows, loaded, n_cols, status, batch_ts))

        con.executemany("insert into ingestion_log values (?, ?, ?, ?, ?, ?, ?)", logs)

    result = pd.DataFrame(
        logs,
        columns=["table_name", "source_file", "csv_rows", "loaded_rows", "column_count", "status", "ingested_at"],
    )
    if (result["status"] != "PASS").any():
        raise RuntimeError("Số dòng nạp vào Bronze không khớp CSV:\n" + result.to_string(index=False))
    return result


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    print(run(root).to_string(index=False))

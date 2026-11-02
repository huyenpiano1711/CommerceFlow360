"""E05 - Xuất Parquet cho dashboard (Task E05, Quỳnh Kha).

Chạy `dbt build` toàn bộ để tầng Gold/Mart mới nhất và run_results.json phản ánh đúng lần chạy,
sau đó xuất 3 mart + bảng kết quả kiểm thử (quality_results) sang Parquet trong data/exports/,
phục vụ dashboard đọc trực tiếp không cần DuckDB.
Dừng ngay, KHÔNG xuất Parquet, nếu dbt có model lỗi hoặc test FAIL (test WARN vẫn cho qua).
"""
from __future__ import annotations

import duckdb
import pandas as pd

from src.utils.project import DUCKDB_PATH, EXPORT_DIR, load_test_results, run_dbt

MARTS = ["mart_sales", "mart_delivery", "mart_customer"]


def build_and_export() -> pd.DataFrame:
    """dbt build + xuất Parquet; trả về bảng quality_results."""
    run_dbt("build", tail=3000)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as con:
        for mart in MARTS:
            df = con.execute(f"select * from {mart}").df()
            df.to_parquet(EXPORT_DIR / f"{mart}.parquet", index=False)
            print(f"{mart}: {len(df)} dong -> data/exports/{mart}.parquet")

    quality_df = (load_test_results()
                  .sort_values(["status", "test_name"], ascending=[False, True])
                  .reset_index(drop=True))
    quality_df.to_parquet(EXPORT_DIR / "quality_results.parquet", index=False)
    print(f"quality_results: {len(quality_df)} test -> data/exports/quality_results.parquet")
    print(quality_df["status"].value_counts().to_string())
    return quality_df

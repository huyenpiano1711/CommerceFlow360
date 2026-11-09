"""E05 - Xuất Parquet cho dashboard (Task E05, Quỳnh Kha).

Chạy `dbt build` toàn bộ để tầng Gold/Mart mới nhất và run_results.json phản ánh đúng lần chạy,
sau đó xuất 3 mart + bảng kết quả kiểm thử (quality_results) sang Parquet trong data/exports/,
phục vụ dashboard đọc trực tiếp không cần DuckDB.
Dừng ngay, KHÔNG xuất Parquet, nếu dbt có model lỗi hoặc test FAIL (test WARN vẫn cho qua).

Các file được ghi ra file tạm rồi mới thay thế file cũ, sau khi đã đọc xong toàn bộ dữ liệu:
nếu lỗi giữa chừng, data/exports/ vẫn là bộ file nhất quán của lần xuất trước.
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from src.utils.project import DUCKDB_PATH, EXPORT_DIR, load_test_results, run_dbt

MARTS = ["mart_sales", "mart_delivery", "mart_customer"]

# Thứ tự hiển thị trạng thái test: vấn đề lên đầu, PASS cuối cùng
STATUS_ORDER = {"fail": 0, "error": 1, "warn": 2, "skipped": 3, "pass": 4}


def _sorted_quality(df: pd.DataFrame) -> pd.DataFrame:
    return (df.sort_values(["status", "test_name"],
                           key=lambda col: col.map(STATUS_ORDER).fillna(len(STATUS_ORDER)) if col.name == "status" else col)
              .reset_index(drop=True))


def build_and_export() -> pd.DataFrame:
    """dbt build + xuất Parquet; trả về bảng quality_results."""
    run_dbt("build", tail=3000)

    frames: dict[str, pd.DataFrame] = {}
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as con:
        for mart in MARTS:  # tên bảng lấy từ hằng MARTS nên ghép f-string an toàn
            frames[mart] = con.execute(f"select * from {mart}").df()
    frames["quality_results"] = _sorted_quality(load_test_results())

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    temp_files: dict[Path, Path] = {}
    try:
        for name, df in frames.items():
            target = EXPORT_DIR / f"{name}.parquet"
            tmp = target.with_suffix(".parquet.tmp")
            df.to_parquet(tmp, index=False)
            temp_files[tmp] = target
        for tmp, target in temp_files.items():
            tmp.replace(target)
    finally:
        for tmp in temp_files:
            tmp.unlink(missing_ok=True)

    for mart in MARTS:
        print(f"{mart}: {len(frames[mart])} dòng -> data/exports/{mart}.parquet")
    quality_df = frames["quality_results"]
    print(f"quality_results: {len(quality_df)} test -> data/exports/quality_results.parquet")
    print(quality_df["status"].value_counts().to_string())
    return quality_df

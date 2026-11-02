"""E05 - Xuất Parquet cho dashboard (Task E05, Quỳnh Kha).

`dbt build` toàn bộ (Silver -> Gold -> Mart + mọi test), rồi xuất data/exports/mart_*.parquet
và quality_results.parquet. Dừng, KHÔNG xuất Parquet, nếu có model lỗi hoặc test FAIL.
Logic nằm ở src/reporting/exports.py, dùng chung với notebooks/06_Business_Analytics.ipynb.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.reporting.exports import build_and_export  # noqa: E402

if __name__ == "__main__":
    build_and_export()

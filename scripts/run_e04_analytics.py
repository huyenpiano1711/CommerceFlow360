"""E04 - Truy vấn phân tích KPI (Task E04, Quỳnh Kha).

Chạy 10 file analytics/sql/analysis_<mart>_<nội dung>.sql trên commerceflow.duckdb, lưu bảng vào
reports/tables/Bang_4.x_*.csv và biểu đồ vào reports/figures/Hinh_4.x_*.png; kèm Bảng 4.1.1
tóm tắt kiểm thử từ data/exports/quality_results.parquet (chạy sau scripts/export_parquet.py).
Logic nằm ở src/reporting/kpi_report.py, dùng chung với notebooks/06_Business_Analytics.ipynb.
"""
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.reporting.kpi_report import run_all  # noqa: E402

if __name__ == "__main__":
    run_all()
    print("\nHoan tat E04.")

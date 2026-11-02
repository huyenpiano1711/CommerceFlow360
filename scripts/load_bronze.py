"""Nạp 10 bảng bronze_* vào commerceflow.duckdb từ data/raw/*.csv.

[Sửa] Gọi logic Bronze chính thức trong src/ingestion/bronze_ingestion.py (Task B01,
cũng được dùng bởi notebooks/02_Bronze_Ingestion.ipynb) để chỉ còn MỘT cách nạp Bronze,
có ghi bảng ingestion_log và đối chiếu số dòng với CSV.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.bronze_ingestion import run  # noqa: E402

if __name__ == "__main__":
    print(run(PROJECT_ROOT).to_string(index=False))

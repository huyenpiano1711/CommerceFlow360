"""E05 - Xuất Parquet cho dashboard (Task E05, Quỳnh Kha).

Chạy `dbt build` để tầng Gold/Mart mới nhất và run_results.json phản ánh đúng lần chạy,
sau đó xuất 3 mart + bảng tổng hợp kết quả kiểm thử (quality_results) sang Parquet
trong data/exports/, phục vụ dashboard (Streamlit/Power BI...) đọc trực tiếp không cần DuckDB.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = PROJECT_ROOT / "dbt_project"
DUCKDB_PATH = Path(os.environ.get("DUCKDB_PATH", PROJECT_ROOT / "commerceflow.duckdb")).resolve()
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# [Sửa] Không gắn cứng đường dẫn dbt của một máy (.venv312/Scripts/dbt.exe chỉ có trên máy Windows
# của một thành viên, Colab/máy khác sẽ lỗi). Tìm dbt trong PATH, hoặc đặt biến môi trường DBT_EXECUTABLE.
DBT_EXE = os.environ.get("DBT_EXECUTABLE") or shutil.which("dbt")
if DBT_EXE is None:
    sys.exit("Không tìm thấy lệnh dbt. Cài dbt-duckdb hoặc đặt biến môi trường DBT_EXECUTABLE.")

env = os.environ.copy()
env["DUCKDB_PATH"] = str(DUCKDB_PATH)
proc = subprocess.run(
    [str(DBT_EXE), "build", "--no-use-colors"],
    cwd=DBT_DIR, env=env, capture_output=True, text=True,
)
print(proc.stdout[-3000:])
# [Sửa logic] dbt trả exit 0 khi chỉ có test WARN; exit 1 nghĩa là có model lỗi hoặc test FAIL
# (kể cả test đối soát doanh thu). Trước đây exit 1 vẫn được chấp nhận nên Parquet có thể xuất ra
# từ dữ liệu đã hỏng. Nay dừng ngay nếu dbt build không thành công.
if proc.returncode != 0:
    raise SystemExit(f"dbt build loi (exit {proc.returncode}) - KHONG xuat Parquet:\n{proc.stdout[-3000:]}\n{proc.stderr}")

con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
for mart in ["mart_sales", "mart_delivery", "mart_customer"]:
    df = con.execute(f"select * from {mart}").df()
    out = EXPORT_DIR / f"{mart}.parquet"
    df.to_parquet(out, index=False)
    print(f"{mart}: {len(df)} dong -> {out}")

with open(DBT_DIR / "target" / "run_results.json", encoding="utf-8") as f:
    run_results = json.load(f)

rows = []
for r in run_results["results"]:
    if not r["unique_id"].startswith("test."):
        continue
    rows.append({
        "test_name": r["unique_id"].split(".")[-2],
        "status": r["status"],
        "execution_time_sec": round(r["execution_time"], 4),
        "failing_rows": (r.get("failures") or 0),
        "message": r.get("message"),
    })
quality_df = pd.DataFrame(rows).sort_values(["status", "test_name"], ascending=[False, True])
out = EXPORT_DIR / "quality_results.parquet"
quality_df.to_parquet(out, index=False)
print(f"quality_results: {len(quality_df)} test -> {out}")
print(quality_df["status"].value_counts().to_string())

"""E05 - Xuất Parquet cho dashboard (Task E05, Quỳnh Kha).

Chạy `dbt build` để tầng Gold/Mart mới nhất và run_results.json phản ánh đúng lần chạy,
sau đó xuất 3 mart + bảng tổng hợp kết quả kiểm thử (quality_results) sang Parquet
trong data/exports/, phục vụ dashboard (Streamlit/Power BI...) đọc trực tiếp không cần DuckDB.
"""
import json
import os
import subprocess
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = PROJECT_ROOT / "dbt_project"
DUCKDB_PATH = PROJECT_ROOT / "commerceflow.duckdb"
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

DBT_EXE = PROJECT_ROOT / ".venv312" / "Scripts" / "dbt.exe"

env = os.environ.copy()
env["DUCKDB_PATH"] = str(DUCKDB_PATH)
proc = subprocess.run(
    [str(DBT_EXE), "build", "--no-use-colors"],
    cwd=DBT_DIR, env=env, capture_output=True, text=True,
)
print(proc.stdout[-3000:])
if proc.returncode not in (0, 1):  # 1 = có test WARN (severity warn), vẫn tiếp tục
    raise SystemExit(f"dbt build loi (exit {proc.returncode}):\n{proc.stderr}")

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

"""Tiện ích dùng chung cho script và notebook CommerceFlow 360.

Gom một chỗ những việc trước đây mỗi notebook tự viết lại: xác định thư mục gốc,
đường dẫn DuckDB, chép profile dbt, chạy lệnh dbt, truy vấn chỉ đọc và đọc kết quả kiểm thử dbt.

Khi import, module đặt biến môi trường DUCKDB_PATH để mọi lệnh dbt (profiles.yml đọc
env_var('DUCKDB_PATH')) và mọi kết nối DuckDB dùng chung một file.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DBT_DIR = PROJECT_ROOT / "dbt_project"
DUCKDB_PATH = Path(os.environ.get("DUCKDB_PATH", PROJECT_ROOT / "commerceflow.duckdb")).resolve()
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"
TABLE_DIR = PROJECT_ROOT / "reports" / "tables"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures"

os.environ["DUCKDB_PATH"] = str(DUCKDB_PATH)


def ensure_dbt_profile() -> Path:
    """Chép profiles.yml.example vào ~/.dbt/profiles.yml nếu máy chưa có profile."""
    target = Path.home() / ".dbt" / "profiles.yml"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(DBT_DIR / "profiles.yml.example", target)
    return target


def dbt_executable() -> str:
    """Tìm lệnh dbt: biến DBT_EXECUTABLE, PATH, rồi thư mục Scripts/bin của Python đang chạy
    (kernel Jupyter thường không có .venv/Scripts trong PATH)."""
    found = os.environ.get("DBT_EXECUTABLE") or shutil.which("dbt")
    if found:
        return found
    for name in ("dbt.exe", "dbt"):
        candidate = Path(sys.executable).parent / name
        if candidate.is_file():
            return str(candidate)
    raise FileNotFoundError("Không tìm thấy lệnh dbt. Cài dbt-duckdb hoặc đặt biến môi trường DBT_EXECUTABLE.")


def run_dbt(*args: str, check: bool = True, tail: int = 6000) -> subprocess.CompletedProcess:
    """Chạy một lệnh dbt trong dbt_project/, in phần cuối log.

    dbt trả exit 0 khi chỉ có test WARN; exit khác 0 nghĩa là có model lỗi hoặc test FAIL.
    check=True thì dừng ngay trong trường hợp đó.
    """
    ensure_dbt_profile()
    cmd = [dbt_executable(), *args, "--no-use-colors"]
    print("$ dbt", " ".join(args))
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        cmd, cwd=DBT_DIR, env=env, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )
    print(proc.stdout[-tail:])
    if proc.returncode != 0:
        print(proc.stderr[-tail:])
        if check:
            raise RuntimeError(f"dbt {args[0]} thất bại (exit {proc.returncode}) - xem log ở trên.")
    return proc


def query(sql: str) -> pd.DataFrame:
    """Truy vấn chỉ đọc; đóng kết nối ngay để không khóa file khi dbt ghi."""
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as con:
        return con.sql(sql).df()


def load_test_results() -> pd.DataFrame:
    """Kết quả các test trong lần chạy dbt gần nhất (target/run_results.json).

    unique_id của test có dạng test.<project>.<tên test>[.<hash>] nên tên test luôn ở vị trí 2
    (lấy vị trí -2 sẽ sai với test tùy chỉnh, vốn không có hash).
    """
    run_results = json.loads((DBT_DIR / "target" / "run_results.json").read_text(encoding="utf-8"))
    rows = [
        {
            "test_name": r["unique_id"].split(".")[2],
            "status": r["status"],
            "execution_time_sec": round(r["execution_time"], 4),
            "failing_rows": r.get("failures") or 0,
            "message": r.get("message"),
        }
        for r in run_results["results"]
        if r["unique_id"].startswith("test.")
    ]
    frame = pd.DataFrame(rows, columns=["test_name", "status", "execution_time_sec", "failing_rows", "message"])
    frame.attrs["generated_at"] = run_results["metadata"]["generated_at"]
    return frame

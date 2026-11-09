"""Tiện ích dùng chung cho script và notebook CommerceFlow 360.

Gom một chỗ những việc trước đây mỗi notebook tự viết lại: xác định thư mục gốc,
đường dẫn DuckDB, chuẩn bị profile dbt, chạy lệnh dbt, truy vấn chỉ đọc và đọc kết quả kiểm thử dbt.

Khi import, module đặt biến môi trường DUCKDB_PATH để mọi lệnh dbt (profiles.yml đọc
env_var('DUCKDB_PATH')) và mọi kết nối DuckDB dùng chung một file.
"""
from __future__ import annotations

import json
import os
import re
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

DBT_PROFILE_NAME = "commerceflow360"  # trùng khóa `profile:` trong dbt_project/dbt_project.yml
PROFILE_TEMPLATE = DBT_DIR / "profiles.yml.example"
LOCAL_PROFILE = DBT_DIR / "profiles.yml"  # bản dự phòng trong repo, đã khai báo trong .gitignore

os.environ["DUCKDB_PATH"] = str(DUCKDB_PATH)


def _has_profile(path: Path) -> bool:
    """File profiles.yml có khai báo profile commerceflow360 ở cấp ngoài cùng hay không."""
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return re.search(rf"^{DBT_PROFILE_NAME}\s*:", text, flags=re.MULTILINE) is not None


def ensure_dbt_profile() -> Path:
    """Bảo đảm dbt tìm được profile commerceflow360; trả về file profiles.yml dbt sẽ dùng.

    * Đã đặt DBT_PROFILES_DIR và file ở đó có profile -> dùng nguyên.
    * Máy chưa có ~/.dbt/profiles.yml -> chép profiles.yml.example vào đó (đúng hướng dẫn README).
    * ~/.dbt/profiles.yml đã có nhưng thiếu profile commerceflow360 (máy dùng dbt cho dự án khác)
      -> KHÔNG sửa file của người dùng; chép mẫu thành dbt_project/profiles.yml và đặt
      DBT_PROFILES_DIR trỏ tới dbt_project/ cho các lệnh dbt chạy từ tiến trình này.
    """
    env_dir = os.environ.get("DBT_PROFILES_DIR")
    if env_dir and _has_profile(Path(env_dir) / "profiles.yml"):
        return Path(env_dir) / "profiles.yml"

    home_profile = Path.home() / ".dbt" / "profiles.yml"
    if not home_profile.exists():
        home_profile.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(PROFILE_TEMPLATE, home_profile)
        return home_profile
    if _has_profile(home_profile):
        return home_profile

    if not _has_profile(LOCAL_PROFILE):
        shutil.copy(PROFILE_TEMPLATE, LOCAL_PROFILE)
    os.environ["DBT_PROFILES_DIR"] = str(DBT_DIR)
    return LOCAL_PROFILE


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
    if not args:
        raise ValueError("Cần truyền lệnh dbt, ví dụ run_dbt('build').")
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
    """Kết quả các test trong lần chạy dbt GẦN NHẤT (target/run_results.json).

    run_results.json bị ghi đè sau mỗi lệnh dbt, nên kết quả chỉ gồm các test của lệnh đó:
    sau `dbt test -s silver` là test Silver, sau `dbt build` là toàn bộ test.

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

"""Kiểm thử logic profiling và đọc kết quả dbt (không cần chạy dbt)."""
import json
from pathlib import Path

import pytest

from src.utils import project
from src.validation.profile_raw_data import profile_csv


def test_duplicates_detected_across_chunks_with_missing_values(tmp_path: Path) -> None:
    # Chunk 1 có ô trống ở cột số (pandas suy kiểu float), chunk 2 thì không (suy kiểu int):
    # nếu không đọc dtype=str, dòng "a,1" ở hai chunk cho hash khác nhau và không bị tính trùng.
    path = tmp_path / "t.csv"
    path.write_text("k,v\na,1\nb,\na,1\n", encoding="utf-8")
    summary, missing = profile_csv(path, ["k", "v"], chunk_size=2)
    assert summary["duplicate_rows"] == 1
    assert summary["actual_rows"] == 3
    assert {m["column_name"]: m["missing_values"] for m in missing} == {"k": 0, "v": 1}


def test_schema_mismatch_fails(tmp_path: Path) -> None:
    path = tmp_path / "t.csv"
    path.write_text("x,y\n1,2\n", encoding="utf-8")
    summary, _ = profile_csv(path, ["k", "v"], chunk_size=10)
    assert summary["status"] == "FAIL"


def test_load_test_results_parses_test_names(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    (target / "run_results.json").write_text(json.dumps({
        "metadata": {"generated_at": "2026-11-09T00:00:00Z"},
        "results": [
            {"unique_id": "test.commerceflow360.not_null_silver_orders_order_id.abc123",
             "status": "pass", "execution_time": 0.12345, "failures": 0, "message": None},
            {"unique_id": "test.commerceflow360.assert_revenue_reconciles",
             "status": "warn", "execution_time": 0.5, "failures": 3, "message": "Got 3 results"},
            {"unique_id": "model.commerceflow360.silver_orders",
             "status": "success", "execution_time": 1.0, "failures": None, "message": "OK"},
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(project, "DBT_DIR", tmp_path)

    frame = project.load_test_results()
    assert frame["test_name"].tolist() == ["not_null_silver_orders_order_id", "assert_revenue_reconciles"]
    assert frame["failing_rows"].tolist() == [0, 3]
    assert frame.attrs["generated_at"] == "2026-11-09T00:00:00Z"


def test_ensure_dbt_profile_does_not_touch_foreign_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    (home / ".dbt").mkdir(parents=True)
    foreign = home / ".dbt" / "profiles.yml"
    foreign.write_text("other_project:\n  target: dev\n", encoding="utf-8")
    dbt_dir = tmp_path / "dbt_project"
    dbt_dir.mkdir()
    (dbt_dir / "profiles.yml.example").write_text("commerceflow360:\n  target: dev\n", encoding="utf-8")

    monkeypatch.setattr(project.Path, "home", lambda: home)
    monkeypatch.setattr(project, "DBT_DIR", dbt_dir)
    monkeypatch.setattr(project, "PROFILE_TEMPLATE", dbt_dir / "profiles.yml.example")
    monkeypatch.setattr(project, "LOCAL_PROFILE", dbt_dir / "profiles.yml")
    monkeypatch.setenv("DBT_PROFILES_DIR", "")  # ghi nhận giá trị gốc để khôi phục sau test
    monkeypatch.delenv("DBT_PROFILES_DIR")

    used = project.ensure_dbt_profile()
    assert used == dbt_dir / "profiles.yml"
    assert foreign.read_text(encoding="utf-8") == "other_project:\n  target: dev\n"
    assert project.os.environ["DBT_PROFILES_DIR"] == str(dbt_dir)

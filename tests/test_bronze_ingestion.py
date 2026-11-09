"""Kiểm thử nạp Bronze trên bộ CSV nhỏ trong thư mục tạm (không đụng commerceflow.duckdb thật)."""
from pathlib import Path

import duckdb
import pytest

from src.ingestion import bronze_ingestion
from src.ingestion.bronze_ingestion import RAW_FILES, count_csv_rows, run


def _make_raw(root: Path, rows: int = 2) -> None:
    raw = root / "data" / "raw"
    raw.mkdir(parents=True)
    for filename in RAW_FILES.values():
        lines = ["id,text"] + [f'{i},"dòng {i}\nxuống dòng trong ô"' for i in range(rows)]
        (raw / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_count_csv_rows_handles_multiline_cells(tmp_path: Path) -> None:
    _make_raw(tmp_path, rows=3)
    assert count_csv_rows(tmp_path / "data" / "raw" / "olist_orders_dataset.csv") == 3


def test_run_loads_all_tables_and_log_is_not_cumulative(tmp_path: Path) -> None:
    _make_raw(tmp_path)
    db = tmp_path / "test.duckdb"
    run(tmp_path, db)
    result = run(tmp_path, db)  # chạy lại: log không được cộng dồn

    assert result["status"].eq("PASS").all()
    assert len(result) == len(RAW_FILES)
    with duckdb.connect(str(db), read_only=True) as con:
        assert con.execute("select count(*) from ingestion_log").fetchone()[0] == len(RAW_FILES)
        cols = [d[0] for d in con.execute("select * from bronze_orders limit 0").description]
        assert cols == ["id", "text", "_ingested_at", "_source_file"]
        assert con.execute("select count(*) from bronze_orders").fetchone()[0] == 2


def test_row_mismatch_rolls_back_everything(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_raw(tmp_path)
    db = tmp_path / "test.duckdb"
    first = run(tmp_path, db)

    # Lần nạp sau có thêm dòng, nhưng giả lập bộ đếm CSV trả sai -> phải rollback toàn bộ
    _make_raw(tmp_path / "v2", rows=5)
    for filename in RAW_FILES.values():
        (tmp_path / "data" / "raw" / filename).write_bytes((tmp_path / "v2" / "data" / "raw" / filename).read_bytes())
    monkeypatch.setattr(bronze_ingestion, "count_csv_rows", lambda path: 999)

    with pytest.raises(RuntimeError, match="không khớp"):
        run(tmp_path, db)

    with duckdb.connect(str(db), read_only=True) as con:
        assert con.execute("select count(*) from bronze_orders").fetchone()[0] == 2  # dữ liệu cũ còn nguyên
        logged = con.execute("select distinct ingested_at from ingestion_log").fetchall()
        assert len(logged) == 1 and logged[0][0] == first["ingested_at"].iloc[0]


def test_missing_source_file_raises(tmp_path: Path) -> None:
    _make_raw(tmp_path)
    (tmp_path / "data" / "raw" / "holidays_brazil.csv").unlink()
    with pytest.raises(FileNotFoundError, match="holidays_brazil.csv"):
        run(tmp_path, tmp_path / "test.duckdb")

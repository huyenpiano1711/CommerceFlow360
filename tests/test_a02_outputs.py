from pathlib import Path

import pandas as pd

from src.validation.profile_raw_data import EXPECTED_SCHEMAS


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROFILING_DIR = ROOT / "data" / "profiling"


def test_nine_olist_files_are_readable_with_expected_columns() -> None:
    assert len(EXPECTED_SCHEMAS) == 9
    for file_name, expected_columns in EXPECTED_SCHEMAS.items():
        path = RAW_DIR / file_name
        assert path.is_file(), file_name
        assert pd.read_csv(path, nrows=5).columns.tolist() == expected_columns


def test_profiling_outputs_pass() -> None:
    comparison = pd.read_csv(PROFILING_DIR / "doi_chieu_so_dong.csv")
    assert comparison["file_name"].tolist() == list(EXPECTED_SCHEMAS)
    assert comparison["status"].eq("PASS").all()
    assert comparison["actual_rows"].gt(0).all()
    assert comparison["column_count"].gt(0).all()
    assert (PROFILING_DIR / "missing_values.csv").is_file()
    assert (PROFILING_DIR / "duplicate_rows.csv").is_file()


def test_brazil_holidays_output() -> None:
    frame = pd.read_csv(RAW_DIR / "holidays_brazil.csv")
    assert frame.columns.tolist() == ["date", "holiday_name", "country_code", "is_holiday"]
    assert not frame.isna().any().any()
    assert not frame["date"].duplicated().any()
    assert frame["date"].tolist() == sorted(frame["date"])
    assert set(pd.to_datetime(frame["date"]).dt.year) == {2016, 2017, 2018}
    assert frame["country_code"].eq("BR").all()
    assert frame["is_holiday"].eq(1).all()

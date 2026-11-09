"""A02 - Sinh danh sách ngày lễ quốc gia Brazil 2016–2018 bằng thư viện python-holidays.

Ghi data/raw/holidays_brazil.csv (nguồn thứ 10 của Bronze) và data/reference/holidays_brazil_metadata.json
(phiên bản thư viện, để tái lập kết quả). Đây là file DUY NHẤT trong data/raw do code sinh ra;
9 CSV Olist còn lại là dữ liệu gốc, chỉ đọc.

Chạy từ thư mục gốc repository:
    python -m src.ingestion.generate_brazil_holidays
"""

from __future__ import annotations

import argparse
import json
from importlib.metadata import version
from pathlib import Path

import holidays
import pandas as pd


YEARS = (2016, 2017, 2018)


# Thư mục gốc suy ra từ vị trí file (src/ingestion/...), không phụ thuộc .git
# nên vẫn chạy được khi tải repository dạng ZIP.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def generate(project_root: Path = PROJECT_ROOT) -> pd.DataFrame:
    """Sinh, kiểm tra và ghi danh sách ngày lễ; trả về DataFrame đã ghi."""
    brazil_holidays = holidays.Brazil(years=YEARS, language="en_US")
    frame = pd.DataFrame(
        (
            {
                "date": day.isoformat(),
                "holiday_name": name,
                "country_code": "BR",
                "is_holiday": 1,
            }
            for day, name in sorted(brazil_holidays.items())
        )
    )
    if frame.empty:
        raise RuntimeError("Thư viện holidays không trả về ngày lễ Brazil nào")
    if frame["date"].duplicated().any():
        raise ValueError("Có ngày lễ bị trùng")
    if frame.isna().any().any():
        raise ValueError("Có giá trị NULL trong cột bắt buộc")
    if set(pd.to_datetime(frame["date"]).dt.year) != set(YEARS):
        raise ValueError("Kết quả thiếu năm hoặc có năm ngoài phạm vi 2016–2018")

    raw_dir = project_root / "data" / "raw"
    reference_dir = project_root / "data" / "reference"
    raw_dir.mkdir(parents=True, exist_ok=True)
    reference_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(raw_dir / "holidays_brazil.csv", index=False, lineterminator="\n")
    metadata = {
        "generator": "python-holidays",
        "holidays_version": version("holidays"),
        "country": "BR",
        "scope": "national holidays provided by the library",
        "years": list(YEARS),
    }
    (reference_dir / "holidays_brazil_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, help="Thư mục gốc repository; mặc định tự suy ra")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    root = args.project_root.resolve() if args.project_root else PROJECT_ROOT
    result = generate(root)
    print(result.to_string(index=False))
    print(f"Đã sinh {len(result)} ngày lễ quốc gia bằng holidays {version('holidays')}.")

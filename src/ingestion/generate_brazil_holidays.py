"""Generate national Brazil holidays for 2016–2018 using python-holidays."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import version
from pathlib import Path

import holidays
import pandas as pd


YEARS = (2016, 2017, 2018)


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() and (candidate / "data" / "raw").is_dir():
            return candidate
    raise FileNotFoundError("Could not locate project root containing .git and data/raw")


def generate(project_root: Path) -> pd.DataFrame:
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
        raise RuntimeError("The holidays library returned no Brazil holidays")
    if frame["date"].duplicated().any():
        raise ValueError("Duplicate holiday dates detected")
    if frame.isna().any().any():
        raise ValueError("NULL found in required holiday fields")
    if set(pd.to_datetime(frame["date"]).dt.year) != set(YEARS):
        raise ValueError("Holiday output contains unexpected or missing years")

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
    parser.add_argument("--project-root", type=Path, help="Repository root; auto-detected by default")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    root = args.project_root.resolve() if args.project_root else find_project_root(Path(__file__).parent)
    result = generate(root)
    print(result.to_string(index=False))
    print(f"Generated {len(result)} national holiday rows with holidays {version('holidays')}.")

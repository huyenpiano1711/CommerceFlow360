"""A02 - Kiểm tra (profiling) 9 file CSV Olist nguồn, chỉ đọc.

Với mỗi file: số dòng, số cột, dung lượng, khớp schema mong đợi, số giá trị thiếu theo cột
và số dòng trùng hoàn toàn (tính từ lần xuất hiện thứ hai). Kết quả ghi vào data/profiling/.

* Bảng geolocation (~1 triệu dòng) được đọc theo chunk; dòng trùng được phát hiện bằng hash
  64 bit của từng dòng để bộ nhớ không phụ thuộc kích thước bảng.
* Mọi cột đọc dạng chuỗi (dtype=str), giống Bronze (all_varchar): giữ số 0 đầu của mã zip
  ("01037") và bảo đảm cùng một dòng luôn cho cùng một hash dù nằm ở chunk nào
  (nếu để pandas tự suy kiểu, một cột có thể là int ở chunk này và float ở chunk khác).

Chạy từ thư mục gốc repository:
    python -m src.validation.profile_raw_data
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


# Thư mục gốc suy ra từ vị trí file (src/validation/...), không phụ thuộc .git.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_SCHEMAS: dict[str, list[str]] = {
    "olist_customers_dataset.csv": [
        "customer_id", "customer_unique_id", "customer_zip_code_prefix",
        "customer_city", "customer_state",
    ],
    "olist_geolocation_dataset.csv": [
        "geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng",
        "geolocation_city", "geolocation_state",
    ],
    "olist_order_items_dataset.csv": [
        "order_id", "order_item_id", "product_id", "seller_id",
        "shipping_limit_date", "price", "freight_value",
    ],
    "olist_order_payments_dataset.csv": [
        "order_id", "payment_sequential", "payment_type",
        "payment_installments", "payment_value",
    ],
    "olist_order_reviews_dataset.csv": [
        "review_id", "order_id", "review_score", "review_comment_title",
        "review_comment_message", "review_creation_date", "review_answer_timestamp",
    ],
    "olist_orders_dataset.csv": [
        "order_id", "customer_id", "order_status", "order_purchase_timestamp",
        "order_approved_at", "order_delivered_carrier_date",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    ],
    "olist_products_dataset.csv": [
        "product_id", "product_category_name", "product_name_lenght",
        "product_description_lenght", "product_photos_qty", "product_weight_g",
        "product_length_cm", "product_height_cm", "product_width_cm",
    ],
    "olist_sellers_dataset.csv": [
        "seller_id", "seller_zip_code_prefix", "seller_city", "seller_state",
    ],
    "product_category_name_translation.csv": [
        "product_category_name", "product_category_name_english",
    ],
}

# Cố ý để trống: chưa có số dòng tham chiếu được xác minh độc lập từ nguồn chính thức.
# Cột reference_rows/difference để trống thay vì điền số phỏng đoán; khi có số đã xác minh,
# thêm vào đây ({"olist_orders_dataset.csv": <số dòng>, ...}) thì status sẽ so cả số dòng.
REFERENCE_ROWS: dict[str, int] = {}


def profile_csv(path: Path, expected_columns: list[str], chunk_size: int) -> tuple[dict, list[dict]]:
    """Trả về chỉ số cấp file và số giá trị thiếu theo từng cột."""
    actual_rows = 0
    missing: pd.Series | None = None
    unique_row_hashes: set[int] = set()
    actual_columns: list[str] | None = None

    for chunk in pd.read_csv(path, chunksize=chunk_size, dtype=str):
        if actual_columns is None:
            actual_columns = chunk.columns.tolist()
            missing = pd.Series(0, index=actual_columns, dtype="int64")
        actual_rows += len(chunk)
        missing = missing.add(chunk.isna().sum(), fill_value=0).astype("int64")
        unique_row_hashes.update(pd.util.hash_pandas_object(chunk, index=False).astype("uint64").tolist())

    if actual_columns is None:  # file chỉ có dòng tiêu đề
        actual_columns = pd.read_csv(path, nrows=0).columns.tolist()
        missing = pd.Series(0, index=actual_columns, dtype="int64")

    duplicate_rows = actual_rows - len(unique_row_hashes)
    schema_matches = actual_columns == expected_columns
    reference = REFERENCE_ROWS.get(path.name)
    rows_match = reference is None or actual_rows == reference
    status = "PASS" if schema_matches and rows_match else "FAIL"

    if not schema_matches:
        notes = f"Lệch schema. Mong đợi {expected_columns}; thực tế {actual_columns}."
    elif not rows_match:
        notes = f"Lệch số dòng: thực tế {actual_rows}, tham chiếu {reference}."
    elif reference is None:
        notes = "Đã kiểm tra schema và đọc được CSV; chưa có số dòng tham chiếu được xác minh độc lập."
    else:
        notes = "Khớp schema và số dòng tham chiếu."

    summary = {
        "file_name": path.name,
        "actual_rows": actual_rows,
        "reference_rows": reference if reference is not None else pd.NA,
        "difference": actual_rows - reference if reference is not None else pd.NA,
        "column_count": len(actual_columns),
        "size_mb": round(path.stat().st_size / (1024 * 1024), 3),
        "status": status,
        "duplicate_rows": duplicate_rows,
        "notes": notes,
    }
    missing_rows = [
        {"file_name": path.name, "column_name": column, "missing_values": int(count)}
        for column, count in missing.items()
    ]
    return summary, missing_rows


def run(project_root: Path = PROJECT_ROOT, chunk_size: int = 100_000) -> pd.DataFrame:
    """Profiling 9 file Olist, ghi 3 file CSV vào data/profiling/; trả về bảng đối chiếu."""
    raw_dir = project_root / "data" / "raw"
    output_dir = project_root / "data" / "profiling"
    output_dir.mkdir(parents=True, exist_ok=True)

    missing_files = [name for name in EXPECTED_SCHEMAS if not (raw_dir / name).is_file()]
    if missing_files:
        raise FileNotFoundError(f"Thiếu file CSV Olist bắt buộc: {missing_files}")

    summaries: list[dict] = []
    missing_details: list[dict] = []
    for file_name, expected_columns in EXPECTED_SCHEMAS.items():
        summary, missing_rows = profile_csv(raw_dir / file_name, expected_columns, chunk_size)
        summaries.append(summary)
        missing_details.extend(missing_rows)

    summary_df = pd.DataFrame(summaries)
    summary_df.to_csv(output_dir / "doi_chieu_so_dong.csv", index=False)
    pd.DataFrame(missing_details).to_csv(output_dir / "missing_values.csv", index=False)
    summary_df[["file_name", "duplicate_rows"]].to_csv(
        output_dir / "duplicate_rows.csv", index=False
    )
    return summary_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, help="Thư mục gốc repository; mặc định tự suy ra")
    parser.add_argument("--chunk-size", type=int, default=100_000)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    root = args.project_root.resolve() if args.project_root else PROJECT_ROOT
    result = run(root, args.chunk_size)
    print(result.to_string(index=False))
    if (result["status"] == "FAIL").any():
        raise SystemExit(1)

"""F01 - Đọc dữ liệu cho dashboard CommerceFlow 360 (Task F01, Phương Anh).

Dashboard CHỈ đọc 4 file Parquet trong data/exports/ do E05 xuất ra
(mart_sales, mart_delivery, mart_customer, quality_results). Không nối lại CSV gốc,
không mở commerceflow.duckdb. DuckDB chỉ được dùng như bộ đọc Parquet trong bộ nhớ.

Quy tắc KPI bám theo AGENTS.md mục 9 (không tự định nghĩa lại):
- Đơn hợp lệ = mart_sales.is_valid_sale (loại canceled, unavailable).
- Doanh thu = sum(revenue) trên đơn hợp lệ; freight_value là measure riêng.
- Số đơn = nunique(order_id), không cộng số đơn giữa các nhóm.
- Giao trễ: chỉ đơn delivered có is_delivered_late khác NULL.
- mart_delivery có grain (order_id, seller_id) -> khử trùng theo order_id khi tính chỉ số cấp đơn.
- Khách hàng: customer_unique_id, chỉ tính khách có has_valid_order.
- Chi tiêu khách (total_spend) = payment_value khách trả, gồm phí vận chuyển; KHÔNG gọi là doanh thu.
- Review trong mart_delivery là điểm của ĐƠN, gán chung cho mọi người bán của đơn.

Cache: mỗi hàm load_* nhận thời điểm sửa file (mtime) làm khóa cache, nên khi chạy lại
scripts/export_parquet.py trong lúc dashboard đang mở, lần tải trang kế tiếp đọc dữ liệu mới
thay vì giữ bản cũ đến khi khởi động lại Streamlit.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = Path(os.environ.get("COMMERCEFLOW_EXPORT_DIR", PROJECT_ROOT / "data" / "exports"))
TABLE_DIR = PROJECT_ROOT / "reports" / "tables"

REQUIRED_FILES = ["mart_sales", "mart_delivery", "mart_customer", "quality_results"]

# Các tháng không đầy đủ của Olist (báo cáo mục 4.2 yêu cầu loại khỏi so sánh theo tháng):
# 09-12/2016 mới khởi động và 09/2018 bị cắt tại thời điểm trích xuất.
FULL_MONTH_START = "2017-01"
FULL_MONTH_END = "2018-08"


class MissingExportError(FileNotFoundError):
    """Thiếu file Parquet - cần chạy lại pipeline."""


def _parquet_path(name: str) -> Path:
    path = EXPORT_DIR / f"{name}.parquet"
    if not path.exists():
        raise MissingExportError(
            f"Không tìm thấy {path}. Chạy `python scripts/export_parquet.py` ở thư mục gốc repo "
            "(sau `python scripts/load_bronze.py`) để tạo các file Parquet."
        )
    return path


def _version(path: Path) -> int:
    """Khóa cache theo thời điểm sửa file (đổi khi file Parquet được xuất lại)."""
    return path.stat().st_mtime_ns


def _read(name: str, columns: list[str]) -> pd.DataFrame:
    path = _parquet_path(name)
    cols = ", ".join(columns)  # tên cột là hằng trong module này, không lấy từ người dùng
    with duckdb.connect(":memory:") as con:
        return con.execute(f"select {cols} from read_parquet(?)", [str(path)]).df()


def check_exports() -> None:
    """Ném MissingExportError nếu thiếu file Parquet nào."""
    for name in REQUIRED_FILES:
        _parquet_path(name)


def load_sales() -> pd.DataFrame:
    return _load_sales(_version(_parquet_path("mart_sales")))


# Tham số version KHÔNG đặt tên bắt đầu bằng "_": st.cache_data bỏ qua các tham số đó khi tạo khóa cache
@st.cache_data(show_spinner="Đang đọc mart_sales...")
def _load_sales(version: int) -> pd.DataFrame:
    df = _read("mart_sales", [
        "order_id", "order_item_id", "order_purchase_date", "year", "month", "is_holiday",
        "product_category", "customer_state", "seller_id", "order_status",
        "is_valid_sale", "revenue", "freight_value", "item_count",
    ])
    df["year_month"] = df["order_purchase_date"].dt.strftime("%Y-%m")
    df["product_category"] = df["product_category"].fillna("unknown")
    df["customer_state"] = df["customer_state"].fillna("unknown")
    return df


def load_delivery() -> pd.DataFrame:
    return _load_delivery(_version(_parquet_path("mart_delivery")))


@st.cache_data(show_spinner="Đang đọc mart_delivery...")
def _load_delivery(version: int) -> pd.DataFrame:
    df = _read("mart_delivery", [
        "order_id", "seller_id", "seller_state", "customer_state", "year", "month",
        "order_status", "delivery_days", "days_late", "is_delivered_late", "review_score",
    ])
    df["year_month"] = df["year"].astype("Int64").astype(str) + "-" + df["month"].astype("Int64").astype(str).str.zfill(2)
    df["customer_state"] = df["customer_state"].fillna("unknown")
    return df


def load_customer() -> pd.DataFrame:
    return _load_customer(_version(_parquet_path("mart_customer")))


@st.cache_data(show_spinner="Đang đọc mart_customer...")
def _load_customer(version: int) -> pd.DataFrame:
    return _read("mart_customer", [
        "customer_key", "customer_unique_id", "order_count", "order_count_all_status",
        "total_spend", "first_order_date", "last_order_date", "days_since_last_order",
        "has_valid_order", "is_repeat_customer",
    ])


def load_quality() -> pd.DataFrame:
    return _load_quality(_version(_parquet_path("quality_results")))


@st.cache_data(show_spinner="Đang đọc quality_results...")
def _load_quality(version: int) -> pd.DataFrame:
    return _read("quality_results", ["test_name", "status", "execution_time_sec", "failing_rows", "message"])


def load_reconciliation_reference() -> pd.DataFrame | None:
    """Bảng 3.7.1 (đối soát Bronze -> Silver -> Gold, task D04) nếu có trong repo; None nếu không."""
    path = TABLE_DIR / "Bang_3.7.1_DoiSoatGold.csv"
    if not path.exists():
        return None
    return _load_reconciliation(str(path), _version(path))


@st.cache_data
def _load_reconciliation(path: str, version: int) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


# ----------------------------------------------------------------------------
# Bộ lọc chung
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Filters:
    start_month: str            # "YYYY-MM"
    end_month: str
    states: tuple[str, ...]     # rỗng = tất cả bang
    categories: tuple[str, ...]  # rỗng = tất cả danh mục (chỉ áp dụng cho Sales)


def month_options() -> list[str]:
    """Danh sách tháng có trong mart_sales, theo thứ tự thời gian."""
    return sorted(load_sales()["year_month"].dropna().unique().tolist())


def state_options() -> list[str]:
    return sorted(load_sales()["customer_state"].dropna().unique().tolist())


def category_options() -> list[str]:
    return sorted(load_sales()["product_category"].dropna().unique().tolist())


def partial_month_summary(sales: pd.DataFrame) -> str:
    """Các tháng ngoài giai đoạn đầy đủ kèm số đơn, vd. "2016-09 (4 đơn), 2016-10 (324 đơn)"; rỗng nếu không có."""
    orders = sales.groupby("year_month")["order_id"].nunique()
    partial = orders[(orders.index < FULL_MONTH_START) | (orders.index > FULL_MONTH_END)]
    return ", ".join(f"{month} ({n:,} đơn)".replace(",", ".") for month, n in partial.items())


def filter_sales(df: pd.DataFrame, f: Filters) -> pd.DataFrame:
    mask = (df["year_month"] >= f.start_month) & (df["year_month"] <= f.end_month)
    if f.states:
        mask &= df["customer_state"].isin(f.states)
    if f.categories:
        mask &= df["product_category"].isin(f.categories)
    return df[mask]


def filter_delivery(df: pd.DataFrame, f: Filters) -> pd.DataFrame:
    """Bộ lọc danh mục không áp dụng cho mart_delivery (grain đơn/người bán, không có danh mục)."""
    mask = (df["year_month"] >= f.start_month) & (df["year_month"] <= f.end_month)
    if f.states:
        mask &= df["customer_state"].isin(f.states)
    return df[mask]


# ----------------------------------------------------------------------------
# KPI dùng chung - một nơi duy nhất để Home và các trang cho cùng một con số
# ----------------------------------------------------------------------------
def sales_kpis(sales: pd.DataFrame) -> dict[str, float]:
    """Doanh thu, số đơn, AOV, phí vận chuyển trên đơn hợp lệ."""
    valid = sales[sales["is_valid_sale"]]
    orders = valid["order_id"].nunique()
    revenue = float(valid["revenue"].sum())
    return {
        "revenue": revenue,
        "freight": float(valid["freight_value"].sum()),
        "orders": int(orders),
        "items": int(valid["item_count"].sum()),
        "aov": revenue / orders if orders else float("nan"),
    }


def orders_dedup(delivery: pd.DataFrame) -> pd.DataFrame:
    """Về grain một dòng/đơn (mart_delivery lặp dòng khi đơn có nhiều người bán)."""
    return delivery.drop_duplicates("order_id")


def eligible_delivered(delivery: pd.DataFrame) -> pd.DataFrame:
    """Đơn delivered có đủ mốc thời gian để xác định giao trễ, mỗi đơn một dòng."""
    d = orders_dedup(delivery)
    return d[(d["order_status"] == "delivered") & d["is_delivered_late"].notna()]


def delivery_kpis(delivery: pd.DataFrame) -> dict[str, float]:
    el = eligible_delivered(delivery)
    n = len(el)
    late = int(el["is_delivered_late"].astype(int).sum()) if n else 0
    rated = el.dropna(subset=["review_score"])
    return {
        "eligible_orders": n,
        "late_orders": late,
        "late_rate": late / n if n else float("nan"),
        "avg_delivery_days": float(el["delivery_days"].astype(float).mean()) if n else float("nan"),
        "avg_days_late": float(el["days_late"].astype(float).mean()) if n else float("nan"),
        "avg_review": float(rated["review_score"].astype(float).mean()) if len(rated) else float("nan"),
    }


def customer_kpis(customer: pd.DataFrame) -> dict[str, float]:
    valid = customer[customer["has_valid_order"]]
    n = len(valid)
    repeat = int(valid["is_repeat_customer"].sum())
    return {
        "customers": n,
        "repeat_customers": repeat,
        "repeat_rate": repeat / n if n else float("nan"),
        "avg_spend_repeat": float(valid.loc[valid["is_repeat_customer"], "total_spend"].mean()) if repeat else float("nan"),
        "avg_spend_single": float(valid.loc[~valid["is_repeat_customer"], "total_spend"].mean()) if n - repeat else float("nan"),
        "total_spend": float(valid["total_spend"].sum()),
    }


def spend_quartiles(customer: pd.DataFrame) -> pd.DataFrame:
    """Phân khúc chi tiêu 4 nhóm bằng nhau về số khách (giống ntile(4) trong analysis_customer_spend_segments.sql).

    total_spend là payment_value khách trả (gồm phí vận chuyển), không phải doanh thu price.
    Sắp theo (total_spend, customer_unique_id) để khách bằng điểm chi tiêu luôn rơi vào cùng một nhóm.
    """
    spend = (customer.loc[customer["total_spend"] > 0, ["total_spend", "customer_unique_id"]]
                     .sort_values(["total_spend", "customer_unique_id"])["total_spend"].reset_index(drop=True))
    n = len(spend)
    base, extra = divmod(n, 4)
    sizes = [base + (1 if i < extra else 0) for i in range(4)]
    labels: list[int] = []
    for q, size in enumerate(sizes, start=1):
        labels += [q] * size
    seg = pd.DataFrame({"total_spend": spend, "spend_quartile": labels})
    out = (seg.groupby("spend_quartile")["total_spend"]
              .agg(customer_count="count", min_spend="min", max_spend="max", total_spend_segment="sum")
              .reset_index())
    out["pct_total_spend"] = 100 * out["total_spend_segment"] / out["total_spend_segment"].sum()
    return out


RECENCY_ORDER = ["0-90 ngày", "91-180 ngày", "181-365 ngày", "> 365 ngày"]


def recency_distribution(customer: pd.DataFrame) -> pd.DataFrame:
    """Phân bố recency; mốc = ngày đặt hàng lớn nhất trong dữ liệu (đã tính sẵn ở mart_customer)."""
    valid = customer[customer["has_valid_order"]].dropna(subset=["days_since_last_order"])
    days = valid["days_since_last_order"].astype(int)
    group = pd.cut(days, bins=[-1, 90, 180, 365, 10**9], labels=RECENCY_ORDER)
    out = group.value_counts().reindex(RECENCY_ORDER).rename_axis("nhom_recency").reset_index(name="customer_count")
    out["pct_customers"] = 100 * out["customer_count"] / out["customer_count"].sum()
    return out

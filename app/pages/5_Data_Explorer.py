"""Trang Khám phá dữ liệu: xem, lọc và tải trực tiếp 4 bảng Data Mart mà dashboard đang dùng.

Không tính KPI mới; chỉ cho phép xem dữ liệu gốc của từng mart (đã áp bộ lọc chung nếu mart có chiều tương ứng),
tìm theo từ khóa, chọn cột và tải ra CSV.
"""
import streamlit as st

from components.ui import (
    STRETCH, download_csv, filter_summary, fmt_int, kpi, page_header, section, setup_page, sidebar_filters,
)
from services.data_loader import (
    filter_delivery, filter_sales, load_customer, load_delivery, load_quality, load_sales,
)

setup_page("Khám phá dữ liệu", "🔎")
page_header("Khám phá dữ liệu Data Mart",
            "Xem trực tiếp từng bảng Data Mart mà dashboard sử dụng, lọc theo từ khóa, chọn cột và tải về CSV.",
            chips=["mart_sales", "mart_delivery", "mart_customer", "quality_results"])

filters = sidebar_filters(use_category=True, use_state=True)

MARTS = {
    "mart_sales · doanh thu": ("sales", "Dòng hàng", "khóa: order_id, order_item_id"),
    "mart_delivery · giao hàng": ("delivery", "Đơn × người bán", "khóa: order_id, seller_id"),
    "mart_customer · khách hàng": ("customer", "Khách hàng", "khóa: customer_unique_id"),
    "quality_results · kiểm thử": ("quality", "Kiểm thử dbt", "khóa: test_name"),
}
choice = st.radio("Chọn bảng", list(MARTS), horizontal=True, label_visibility="collapsed")
kind, grain, grain_key = MARTS[choice]

if kind == "sales":
    df = filter_sales(load_sales(), filters)
    scope = filter_summary(filters)
elif kind == "delivery":
    df = filter_delivery(load_delivery(), filters)
    scope = filter_summary(filters, use_category=False) + " (mart_delivery không có chiều danh mục)"
elif kind == "customer":
    df = load_customer()
    scope = "Toàn bộ dữ liệu (mart_customer không có chiều tháng/bang/danh mục)"
else:
    df = load_quality()
    scope = "Toàn bộ 91 kiểm thử của lần dbt build gần nhất"

st.caption(scope)

c1, c2, c3 = st.columns(3)
kpi(c1, "Số dòng sau bộ lọc", fmt_int(len(df)), icon="layers")
kpi(c2, "Số cột", fmt_int(df.shape[1]), icon="database")
kpi(c3, "Mỗi dòng là (grain)", grain, icon="box", note=grain_key)

section("Lọc và chọn cột", "Tìm theo từ khóa trên mọi cột dạng chữ; bỏ chọn cột không cần xem.")
f1, f2 = st.columns([1, 2])
keyword = f1.text_input("Từ khóa", placeholder="vd. SP, health_beauty, delivered…")
cols = f2.multiselect("Cột hiển thị", list(df.columns), default=list(df.columns)[:10])

view = df
if keyword:
    text_cols = [c for c in df.columns if df[c].dtype == object or str(df[c].dtype).startswith("string")]
    mask = False
    for c in text_cols:
        mask = mask | df[c].astype(str).str.contains(keyword, case=False, na=False, regex=False)
    view = df[mask] if text_cols else df.iloc[0:0]
view = view[cols] if cols else view

tab_data, tab_stats = st.tabs(["Dữ liệu", "Thống kê nhanh"])
with tab_data:
    st.caption(f"Hiển thị {fmt_int(min(len(view), 2000))} / {fmt_int(len(view))} dòng khớp (giới hạn 2.000 dòng để trang nhẹ; tải CSV để lấy đủ).")
    st.dataframe(view.head(2000), hide_index=True, **STRETCH)
with tab_stats:
    numeric = view.select_dtypes("number")
    if numeric.empty:
        st.info("Các cột đang chọn không có cột số.")
    else:
        stats = numeric.describe().T.rename(columns={
            "count": "Số giá trị", "mean": "Trung bình", "std": "Độ lệch chuẩn", "min": "Nhỏ nhất",
            "25%": "Q1", "50%": "Trung vị", "75%": "Q3", "max": "Lớn nhất"})
        st.dataframe(stats.round(2), **STRETCH)

section("Tải dữ liệu", "Tải toàn bộ các dòng khớp từ khóa và cột đã chọn.", icon="download")
download_csv(view, f"commerceflow_{kind}.csv", "Tải bảng đang xem (CSV)")

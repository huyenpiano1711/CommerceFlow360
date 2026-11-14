"""Trang Kiến trúc pipeline: giới thiệu luồng dữ liệu Medallion, các tầng, kiểm thử và cách chạy lại.

Số dòng của Data Mart và kết quả kiểm thử đọc trực tiếp từ Parquet; số liệu tầng Bronze/Silver/Gold lấy từ
lần chạy pipeline gần nhất (README, mục Kết quả đúng).
"""
import html

import streamlit as st

from components.ui import fmt_int, icon_svg, kpi, page_header, section, setup_page, sidebar_brand
from services.data_loader import load_customer, load_delivery, load_quality, load_sales

setup_page("Kiến trúc pipeline", "🏗️")
page_header("Kiến trúc pipeline CommerceFlow 360",
            "Từ 9 tệp CSV Olist đến dashboard: dữ liệu đi qua 4 tầng Medallion, được kiểm thử tự động ở mỗi bước.",
            chips=["Python", "DuckDB", "dbt Core", "Streamlit", "Google Colab", "GitHub"])
sidebar_brand()
st.sidebar.info("Trang giới thiệu kiến trúc, không dùng bộ lọc.")

sales, delivery, customer, quality = load_sales(), load_delivery(), load_customer(), load_quality()
status = quality["status"].value_counts()

st.markdown(
    '<div class="cf-flow">' + '<span class="arrow">›</span>'.join(
        f'<span class="step">{s}</span>' for s in
        ["9 CSV Olist + ngày lễ", "Bronze", "Silver", "Gold", "Data Mart", "Parquet", "Dashboard"]) + "</div>",
    unsafe_allow_html=True,
)

section("Bốn tầng dữ liệu", "Mỗi tầng một trách nhiệm, nên lỗi được khoanh vùng và truy vết ngược được.", icon="layers")
LAYERS = [
    ("database", "Bronze", "10 bảng bronze_*", "1.550.949 dòng",
     "Nạp nguyên trạng 9 CSV + bảng ngày lễ, mọi cột dạng chữ, thêm thời điểm nạp và tên file. Lệch số dòng là hủy toàn bộ lần nạp."),
    ("check", "Silver", "10 model silver_*", "70 kiểm thử",
     "Ép kiểu, chuẩn hóa chuỗi bằng macro dùng chung, khử trùng theo khóa, gắn cờ dòng bất thường thay vì xóa."),
    ("layers", "Gold", "5 dimension · 4 fact", "Star Schema",
     "Mỗi fact một grain: đơn hàng, dòng hàng, thanh toán, đánh giá. Định nghĩa đơn hợp lệ đặt một lần ở fact_orders."),
    ("chart", "Data Mart", "3 mart", f"{fmt_int(len(sales) + len(delivery) + len(customer))} dòng",
     "mart_sales, mart_delivery, mart_customer phục vụ ba chủ đề phân tích; xuất ra Parquet cho dashboard."),
]
cols = st.columns(4)
for col, (ic, name, what, badge, desc) in zip(cols, LAYERS):
    col.markdown(
        f'<div class="cf-card"><div class="cf-kpi-icon" style="background:linear-gradient(135deg,#4d9bff,#1f5eea)">{icon_svg(ic)}</div>'
        f'<h4>{name}</h4><span class="cf-pill">{html.escape(what)}</span><span class="cf-pill">{html.escape(badge)}</span>'
        f'<p style="margin-top:.5rem">{html.escape(desc)}</p></div>',
        unsafe_allow_html=True,
    )

section("Dữ liệu dashboard đang đọc", "Đọc trực tiếp từ 4 file Parquet trong data/exports/.", icon="database")
d1, d2, d3, d4 = st.columns(4)
kpi(d1, "mart_sales (dòng hàng)", fmt_int(len(sales)), icon="money")
kpi(d2, "mart_delivery (đơn × người bán)", fmt_int(len(delivery)), icon="truck")
kpi(d3, "mart_customer (khách thật)", fmt_int(len(customer)), icon="users")
kpi(d4, "Kiểm thử dbt", fmt_int(len(quality)), icon="check",
    note=f"{fmt_int(status.get('pass', 0))} pass · {fmt_int(status.get('warn', 0))} warn · "
         f"{fmt_int(status.get('fail', 0) + status.get('error', 0))} fail")

section("Chạy lại toàn bộ hệ thống", "Ba lệnh từ thư mục gốc repository, hoặc 6 notebook trên Google Colab.", icon="repeat")
left, right = st.columns([1.1, 1])
with left:
    st.code(
        "python scripts/load_bronze.py        # 1. Nạp 10 bảng Bronze\n"
        "python scripts/export_parquet.py     # 2. dbt build Silver → Gold → Mart + 91 test, xuất Parquet\n"
        "python scripts/run_e04_analytics.py  # 3. 10 truy vấn phân tích, bảng và hình báo cáo\n"
        "streamlit run app/Home.py            # Mở dashboard",
        language="bash",
    )
with right:
    NOTEBOOKS = [("01", "Data_Source_Setup", "Kiểm tra 9 CSV, sinh ngày lễ"), ("02", "Bronze_Ingestion", "Nạp Bronze"),
                 ("03", "Silver_Transformation", "Làm sạch + 70 test"), ("04", "Gold_Data_Warehouse", "5 dim, 4 fact"),
                 ("05", "Data_Quality", "Đối soát 3 tầng"), ("06", "Business_Analytics", "dbt build, Parquet, phân tích")]
    st.markdown(
        '<div class="cf-card">' + "".join(
            f'<p style="margin:.25rem 0"><span class="cf-pill">Notebook {n}</span> <b>{name}</b> · {desc}</p>'
            for n, name, desc in NOTEBOOKS) + "</div>",
        unsafe_allow_html=True,
    )

section("Nguyên tắc chất lượng", icon="check")
q1, q2, q3 = st.columns(3)
for col, (title, desc) in zip((q1, q2, q3), [
    ("Không xóa dữ liệu gốc", "Dòng bất thường được gắn cờ ở Silver, nên tổng số luôn đối soát được với Bronze."),
    ("Kiểm thử chặn dữ liệu sai", "Test ở mức error làm dừng pipeline: dashboard không bao giờ hiển thị số liệu chưa qua kiểm thử."),
    ("Một định nghĩa cho mỗi chỉ số", "Đơn hợp lệ, doanh thu, giao trễ được định nghĩa một lần và dùng chung cho mọi mart."),
]):
    col.markdown(f'<div class="cf-card"><h4>{title}</h4><p>{desc}</p></div>', unsafe_allow_html=True)

st.caption("Nhóm 08 · Đồ án Nhà kho dữ liệu và Tích hợp · Dữ liệu: Brazilian E-Commerce Public Dataset by Olist (Kaggle).")

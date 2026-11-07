"""F01 - Trang chủ / tổng quan KPI của dashboard CommerceFlow 360 (Task F01, Phương Anh).

Chạy từ thư mục gốc repo:  streamlit run app/Home.py
Chỉ đọc data/exports/*.parquet (xem app/services/data_loader.py).
"""
import plotly.graph_objects as go
import streamlit as st

from components.ui import (
    STRETCH,
    AMBER, BLUE, GREEN, RED, empty_guard, filter_summary, fmt_int, fmt_money, fmt_num, fmt_pct,
    fmt_pct_points, page_header, setup_page, sidebar_filters, style_fig,
)
from services.data_loader import (
    customer_kpis, delivery_kpis, filter_delivery, filter_sales, load_customer, load_delivery,
    load_quality, load_sales, sales_kpis,
)

setup_page("Tổng quan", "📦")
page_header(
    "CommerceFlow 360 – Tổng quan KPI",
    "Kho dữ liệu thương mại điện tử Olist (Brazil, 2016–2018) theo kiến trúc Medallion: "
    "Bronze → Silver → Gold → Data Mart → Dashboard.",
)

filters = sidebar_filters(use_category=True, use_state=True)

sales_all, delivery_all, customer_all, quality = load_sales(), load_delivery(), load_customer(), load_quality()
sales = filter_sales(sales_all, filters)
delivery = filter_delivery(delivery_all, filters)
empty_guard(sales)

sk, dk, ck = sales_kpis(sales), delivery_kpis(delivery), customer_kpis(customer_all)

st.caption(filter_summary(filters))

# --------------------------------------------------------------------- KPI chính
st.subheader("Kinh doanh")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Doanh thu (đơn hợp lệ)", fmt_money(sk["revenue"], 0), help="Tổng price của dòng hàng thuộc đơn không bị canceled/unavailable. Không gồm phí vận chuyển.")
c2.metric("Số đơn hợp lệ", fmt_int(sk["orders"]), help="count(distinct order_id) trên đơn hợp lệ.")
c3.metric("Giá trị đơn trung bình (AOV)", fmt_money(sk["aov"]), help="Doanh thu / số đơn hợp lệ.")
c4.metric("Phí vận chuyển (đơn hợp lệ)", fmt_money(sk["freight"], 0), help="Measure riêng, không cộng vào doanh thu.")

st.subheader("Vận hành giao hàng")
d1, d2, d3, d4 = st.columns(4)
d1.metric("Tỷ lệ giao trễ", fmt_pct(dk["late_rate"]), help="Số đơn delivered giao trễ / số đơn delivered có đủ mốc thời gian.")
d2.metric("Số ngày giao TB", fmt_num(dk["avg_delivery_days"], 1), help="Từ ngày đặt đến ngày khách nhận, đơn delivered đủ điều kiện.")
d3.metric("Điểm đánh giá TB", fmt_num(dk["avg_review"]), help="Đánh giá mới nhất của mỗi đơn (thang 1–5).")
d4.metric("Đơn đủ điều kiện", fmt_int(dk["eligible_orders"]))

st.subheader("Khách hàng (toàn bộ dữ liệu)")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Khách hàng (customer_unique_id)", fmt_int(ck["customers"]), help="Khách có ít nhất 1 đơn hợp lệ.")
k2.metric("Khách mua lại (≥ 2 đơn)", fmt_int(ck["repeat_customers"]))
k3.metric("Tỷ lệ mua lại", fmt_pct(ck["repeat_rate"]))
k4.metric("Chi tiêu TB: mua lại vs 1 lần", f'{fmt_num(ck["avg_spend_repeat"], 0)} vs {fmt_num(ck["avg_spend_single"], 0)}',
          help="Tổng payment_value trung bình mỗi khách (R$), đơn hợp lệ.")
st.caption("Chỉ số khách hàng tính theo customer_unique_id trên toàn bộ dữ liệu; mart_customer không có chiều bang/danh mục/tháng "
           "nên không chịu tác động của bộ lọc chung.")

# --------------------------------------------------------------------- xu hướng
st.subheader("Doanh thu và số đơn theo tháng")
valid = sales[sales["is_valid_sale"]]
monthly = (valid.groupby("year_month")
                .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique")).reset_index())
fig = go.Figure()
fig.add_bar(x=monthly["year_month"], y=monthly["orders"], name="Số đơn", marker_color="#cbd5e1", yaxis="y2")
fig.add_scatter(x=monthly["year_month"], y=monthly["revenue"], name="Doanh thu (R$)", mode="lines+markers", line=dict(color=BLUE))
fig.update_layout(
    yaxis=dict(title="Doanh thu (R$)", tickformat=",.0f"),
    yaxis2=dict(title="Số đơn", overlaying="y", side="right", showgrid=False),
    xaxis=dict(tickangle=-60),
)
st.plotly_chart(style_fig(fig, 360), **STRETCH)
st.caption("Lưu ý: 09–12/2016 (giai đoạn khởi động) và 09/2018 (chỉ 1 đơn do dữ liệu bị cắt) không phản ánh kinh doanh thực; "
           "bật “Chỉ các tháng đầy đủ” ở thanh bên để loại khỏi so sánh.")

# --------------------------------------------------------------------- tình trạng dữ liệu
st.subheader("Tình trạng kiểm thử dữ liệu")
counts = quality["status"].value_counts()
q1, q2, q3, q4 = st.columns(4)
q1.metric("Tổng test dbt", fmt_int(len(quality)))
q2.metric("Pass", fmt_int(counts.get("pass", 0)))
q3.metric("Warn", fmt_int(counts.get("warn", 0)), help="Bất thường có thật của dữ liệu nguồn, đã gắn cờ ở Silver; không chặn pipeline.")
q4.metric("Fail / Error", fmt_int(counts.get("fail", 0) + counts.get("error", 0)))
st.caption("Chi tiết ở trang Data Quality.")

with st.expander("Định nghĩa KPI dùng trong dashboard"):
    st.markdown(
        """
        - **Đơn hợp lệ**: trạng thái không phải `canceled`, `unavailable` (cờ `is_valid_sale` của `mart_sales`).
        - **Doanh thu** = tổng `price` của dòng hàng thuộc đơn hợp lệ; **phí vận chuyển** và **giá trị thanh toán** là measure riêng, không cộng lẫn.
        - **Số đơn** = `count(distinct order_id)`; không cộng số đơn giữa các danh mục hoặc người bán.
        - **AOV** = doanh thu / số đơn hợp lệ.
        - **Tỷ lệ giao trễ** = đơn `delivered` giao sau ngày dự kiến / đơn `delivered` có đủ hai mốc thời gian (so sánh theo ngày). `mart_delivery` có grain (đơn, người bán) nên được khử trùng theo `order_id` trước khi tính.
        - **Đánh giá**: lấy đánh giá mới nhất của mỗi đơn.
        - **Khách hàng**: dùng `customer_unique_id`; chỉ tính khách có đơn hợp lệ. Recency tính đến ngày đặt hàng lớn nhất trong dữ liệu (không phải ngày hiện tại).
        """
    )

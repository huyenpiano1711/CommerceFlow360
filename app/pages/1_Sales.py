"""F02 - Trang Sales (Task F02, Phương Anh). Nguồn: mart_sales.parquet, grain (order_id, order_item_id).

Câu hỏi kinh doanh: doanh thu biến động thế nào theo tháng, danh mục và bang nào đóng góp nhiều nhất,
và ngày lễ Brazil có làm giá trị đơn hàng khác đi không (mục 4.2 báo cáo).
"""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.ui import (
    STRETCH,
    AMBER, BLUE, GREY, empty_guard, filter_summary, fmt_int, fmt_money, fmt_num, page_header,
    setup_page, sidebar_filters, style_fig,
)
from services.data_loader import filter_sales, load_sales, sales_kpis

setup_page("Sales", "💰")
page_header("Phân tích doanh thu (mart_sales)",
            "Doanh thu = giá sản phẩm (price) của đơn hợp lệ; phí vận chuyển là measure riêng.")

filters = sidebar_filters(use_category=True, use_state=True)
sales = filter_sales(load_sales(), filters)
empty_guard(sales)
st.caption(filter_summary(filters))

valid = sales[sales["is_valid_sale"]]
empty_guard(valid, "Không có đơn hợp lệ nào khớp bộ lọc hiện tại.")
k = sales_kpis(sales)
excluded_orders = sales.loc[~sales["is_valid_sale"], "order_id"].nunique()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Doanh thu", fmt_money(k["revenue"], 0))
c2.metric("Số đơn hợp lệ", fmt_int(k["orders"]))
c3.metric("AOV", fmt_money(k["aov"]))
c4.metric("Số dòng hàng", fmt_int(k["items"]), help="Tổng item_count; đếm dòng sản phẩm, không phải số đơn.")
c5.metric("Phí vận chuyển", fmt_money(k["freight"], 0), help="Không cộng vào doanh thu.")
st.caption(f"Đã loại {fmt_int(excluded_orders)} đơn canceled/unavailable khỏi các KPI trên.")

# ------------------------------------------------------------------ theo tháng
st.subheader("Doanh thu theo tháng")
monthly = (valid.groupby("year_month")
                .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique")).reset_index())
monthly["aov"] = monthly["revenue"] / monthly["orders"]
metric = st.radio("Chỉ số", ["Doanh thu", "Số đơn", "AOV"], horizontal=True, label_visibility="collapsed")
col, label = {"Doanh thu": ("revenue", "Doanh thu (R$)"), "Số đơn": ("orders", "Số đơn"), "AOV": ("aov", "AOV (R$)")}[metric]
fig = go.Figure(go.Scatter(x=monthly["year_month"], y=monthly[col], mode="lines+markers", line=dict(color=BLUE)))
fig.update_layout(yaxis_title=label, xaxis=dict(tickangle=-60))
st.plotly_chart(style_fig(fig, 340), **STRETCH)
st.caption("09–12/2016 gần như chưa có doanh thu và 09/2018 chỉ có 1 đơn do dữ liệu bị cắt khi trích xuất; không dùng để kết luận tăng/giảm.")

# ------------------------------------------------------------------ danh mục và bang
left, right = st.columns(2)
with left:
    st.subheader("Top 10 danh mục theo doanh thu")
    cat = (valid.groupby("product_category")
                .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"))
                .sort_values("revenue", ascending=False).head(10).reset_index())
    fig = px.bar(cat.iloc[::-1], x="revenue", y="product_category", orientation="h",
                 hover_data={"orders": ":,.0f", "revenue": ":,.2f"}, labels={"revenue": "Doanh thu (R$)", "product_category": ""})
    fig.update_traces(marker_color=BLUE)
    st.plotly_chart(style_fig(fig, 400), **STRETCH)
with right:
    st.subheader("Top 10 bang khách hàng theo doanh thu")
    st_rev = (valid.groupby("customer_state")
                   .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique")).reset_index())
    st_rev["aov"] = st_rev["revenue"] / st_rev["orders"]
    st_rev = st_rev.sort_values("revenue", ascending=False).head(10)
    fig = px.bar(st_rev, x="customer_state", y="revenue", hover_data={"orders": ":,.0f", "aov": ":,.2f", "revenue": ":,.2f"},
                 labels={"revenue": "Doanh thu (R$)", "customer_state": "Bang"})
    fig.update_traces(marker_color=BLUE)
    st.plotly_chart(style_fig(fig, 400), **STRETCH)
st.caption("Số đơn theo danh mục/bang là số đơn riêng của từng nhóm; một đơn nhiều danh mục được tính ở mỗi danh mục nên không cộng các nhóm với nhau.")

# ------------------------------------------------------------------ ngày lễ
st.subheader("Giá trị đơn trung bình: ngày lễ Brazil và ngày thường")
hol = (valid.groupby("is_holiday")
            .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique")).reset_index())
hol["aov"] = hol["revenue"] / hol["orders"]
hol["nhom"] = hol["is_holiday"].map({True: "Ngày lễ quốc gia", False: "Ngày thường"})
h1, h2 = st.columns([1, 2])
with h1:
    st.dataframe(
        hol[["nhom", "orders", "revenue", "aov"]].rename(columns={"nhom": "Nhóm", "orders": "Số đơn", "revenue": "Doanh thu (R$)", "aov": "AOV (R$)"}),
        hide_index=True, **STRETCH,
        column_config={"Số đơn": st.column_config.NumberColumn(format="%d"),
                       "Doanh thu (R$)": st.column_config.NumberColumn(format="%.2f"),
                       "AOV (R$)": st.column_config.NumberColumn(format="%.2f")})
with h2:
    fig = px.bar(hol, x="nhom", y="aov", text=hol["aov"].map(lambda v: fmt_num(v)), labels={"aov": "AOV (R$)", "nhom": ""})
    fig.update_traces(marker_color=[AMBER if h else GREY for h in hol["is_holiday"]], textposition="outside")
    st.plotly_chart(style_fig(fig, 300), **STRETCH)
st.caption("Chỉ phản ánh mối liên hệ trong dữ liệu 2016–2018 với 27 ngày lễ quốc gia (thư viện holidays); không đủ cơ sở kết luận ngày lễ gây ra chênh lệch. "
           "Black Friday không phải ngày lễ quốc gia nên không nằm trong nhóm này.")

with st.expander("Xem dữ liệu chi tiết theo tháng"):
    st.dataframe(monthly.rename(columns={"year_month": "Tháng", "revenue": "Doanh thu (R$)", "orders": "Số đơn", "aov": "AOV (R$)"}),
                 hide_index=True, **STRETCH)

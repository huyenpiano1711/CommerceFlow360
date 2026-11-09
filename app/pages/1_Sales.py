"""F02 - Trang Sales (Task F02, Phương Anh). Nguồn: mart_sales.parquet, grain (order_id, order_item_id).

Câu hỏi kinh doanh: doanh thu biến động thế nào theo tháng, danh mục và bang nào đóng góp nhiều nhất,
và ngày lễ Brazil có làm giá trị đơn hàng khác đi không (mục 4.2 báo cáo).
"""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.ui import (
    STRETCH,
    AMBER, BLUE, GREY, empty_guard, filter_summary, fmt_int, fmt_money, fmt_money_short, fmt_num,
    page_header, setup_page, sidebar_filters, style_fig, vn_axis_ticks,
)
from services.data_loader import filter_sales, load_sales, partial_month_summary, sales_kpis

setup_page("Sales", "💰")
page_header("Phân tích doanh thu (mart_sales)",
            "Doanh thu = giá sản phẩm (price) của đơn hợp lệ; phí vận chuyển là measure riêng.")

filters = sidebar_filters(use_category=True, use_state=True)
sales_all = load_sales()
sales = filter_sales(sales_all, filters)
empty_guard(sales)
st.caption(filter_summary(filters))

valid = sales[sales["is_valid_sale"]]
empty_guard(valid, "Không có đơn hợp lệ nào khớp bộ lọc hiện tại.")
k = sales_kpis(sales)
excluded_orders = sales.loc[~sales["is_valid_sale"], "order_id"].nunique()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Doanh thu", fmt_money_short(k["revenue"]))
c2.metric("Số đơn hợp lệ", fmt_int(k["orders"]))
c3.metric("Doanh thu danh mục / đơn" if filters.categories else "AOV",
          fmt_money(k["aov"]),
          help=("Doanh thu của danh mục đã chọn trên mỗi đơn có sản phẩm thuộc danh mục đó."
                if filters.categories else "Doanh thu / số đơn hợp lệ."))
c4.metric("Số dòng hàng", fmt_int(k["items"]), help="Tổng item_count; đếm dòng sản phẩm, không phải số đơn.")
c5.metric("Phí vận chuyển", fmt_money_short(k["freight"]), help="Không cộng vào doanh thu.")
st.caption(f"Đã loại {fmt_int(excluded_orders)} đơn canceled/unavailable khỏi các KPI trên.")
if filters.categories:
    st.caption("Khi lọc danh mục, chỉ số doanh thu/đơn không phải AOV của toàn bộ đơn hàng.")

# ------------------------------------------------------------------ theo tháng
st.subheader("Doanh thu theo tháng")
monthly = (valid.groupby("year_month")
                .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique")).reset_index())
monthly["aov"] = monthly["revenue"] / monthly["orders"]
metric = st.radio("Chỉ số", ["Doanh thu", "Số đơn", "AOV"], horizontal=True, label_visibility="collapsed")
aov_chart_label = "Doanh thu danh mục / đơn (R$)" if filters.categories else "AOV (R$)"
col, label = {"Doanh thu": ("revenue", "Doanh thu (R$)"), "Số đơn": ("orders", "Số đơn"),
              "AOV": ("aov", aov_chart_label)}[metric]
monthly["hover_value"] = monthly[col].map(fmt_int if metric == "Số đơn" else fmt_money)
fig = go.Figure(go.Scatter(
    x=monthly["year_month"], y=monthly[col], customdata=monthly["hover_value"],
    mode="lines+markers", line=dict(color=BLUE, width=3), marker=dict(size=7),
    hovertemplate="%{x}<br>" + label + ": %{customdata}<extra></extra>",
))
fig.update_layout(yaxis_title=label, xaxis=dict(type="category", tickangle=-60),
                  yaxis=vn_axis_ticks(monthly[col]))
st.plotly_chart(style_fig(fig, 340), **STRETCH)
partial_summary = partial_month_summary(sales_all)
if partial_summary:
    st.caption(f"Các tháng ngoài giai đoạn đầy đủ trong dữ liệu: {partial_summary}; "
               "cân nhắc bộ lọc “Chỉ các tháng đầy đủ” khi so sánh xu hướng.")

# ------------------------------------------------------------------ danh mục và bang
left, right = st.columns(2)
with left:
    st.subheader("Top 10 danh mục theo doanh thu")
    cat = (valid.groupby("product_category")
                .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"))
                .sort_values("revenue", ascending=False).head(10).reset_index())
    cat["orders_label"] = cat["orders"].map(fmt_int)
    cat["revenue_label"] = cat["revenue"].map(fmt_money)
    fig = px.bar(cat.iloc[::-1], x="revenue", y="product_category", orientation="h",
                 custom_data=["orders_label", "revenue_label"], labels={"revenue": "Doanh thu (R$)", "product_category": ""})
    fig.update_traces(marker_color=BLUE, hovertemplate="%{y}<br>Số đơn: %{customdata[0]}<br>Doanh thu: %{customdata[1]}<extra></extra>")
    fig.update_xaxes(**vn_axis_ticks(cat["revenue"]))
    st.plotly_chart(style_fig(fig, 400), **STRETCH)
with right:
    st.subheader("Top 10 bang khách hàng theo doanh thu")
    st_rev = (valid.groupby("customer_state")
                   .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique")).reset_index())
    st_rev["aov"] = st_rev["revenue"] / st_rev["orders"]
    st_rev = st_rev.sort_values("revenue", ascending=False).head(10)
    st_rev["orders_label"] = st_rev["orders"].map(fmt_int)
    st_rev["aov_label"] = st_rev["aov"].map(fmt_money)
    st_rev["revenue_label"] = st_rev["revenue"].map(fmt_money)
    fig = px.bar(st_rev, x="customer_state", y="revenue",
                 custom_data=["orders_label", "aov_label", "revenue_label"],
                 labels={"revenue": "Doanh thu (R$)", "customer_state": "Bang"})
    fig.update_traces(marker_color=BLUE, hovertemplate="%{x}<br>Số đơn: %{customdata[0]}<br>AOV: %{customdata[1]}<br>Doanh thu: %{customdata[2]}<extra></extra>")
    fig.update_yaxes(**vn_axis_ticks(st_rev["revenue"]))
    st.plotly_chart(style_fig(fig, 400), **STRETCH)
st.caption("Số đơn theo danh mục/bang là số đơn riêng của từng nhóm; một đơn nhiều danh mục được tính ở mỗi danh mục nên không cộng các nhóm với nhau.")

# ------------------------------------------------------------------ ngày lễ
st.subheader("Giá trị đơn trung bình: ngày lễ Brazil và ngày thường")
hol = (valid.groupby("is_holiday")
            .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique")).reset_index())
hol["aov"] = hol["revenue"] / hol["orders"]
hol["nhom"] = hol["is_holiday"].map({True: "Ngày lễ quốc gia", False: "Ngày thường"})
h1, h2 = st.columns([1.5, 1.5])
with h1:
    hol_display = hol[["nhom", "orders", "revenue", "aov"]].rename(
        columns={"nhom": "Nhóm", "orders": "Số đơn", "revenue": "Doanh thu (R$)", "aov": "AOV (R$)"}
    ).copy()
    hol_display["Số đơn"] = hol_display["Số đơn"].map(fmt_int)
    hol_display["Doanh thu (R$)"] = hol_display["Doanh thu (R$)"].map(fmt_money)
    hol_display["AOV (R$)"] = hol_display["AOV (R$)"].map(fmt_money)
    st.dataframe(
        hol_display, hide_index=True, **STRETCH)
with h2:
    fig = px.bar(hol, x="nhom", y="aov", text=hol["aov"].map(lambda v: fmt_num(v)), labels={"aov": "AOV (R$)", "nhom": ""})
    fig.update_traces(marker_color=[AMBER if h else GREY for h in hol["is_holiday"]], textposition="outside")
    fig.update_yaxes(**vn_axis_ticks(hol["aov"]))
    st.plotly_chart(style_fig(fig, 300), **STRETCH)
st.caption("Chỉ phản ánh mối liên hệ giữa các ngày được gắn cờ là ngày lễ quốc gia trong dữ liệu 2016–2018; không đủ cơ sở kết luận ngày lễ gây ra chênh lệch. "
           "Black Friday không phải ngày lễ quốc gia nên không nằm trong nhóm này.")

with st.expander("Xem dữ liệu chi tiết theo tháng"):
    monthly_display = monthly.rename(
        columns={"year_month": "Tháng", "revenue": "Doanh thu (R$)", "orders": "Số đơn", "aov": "AOV (R$)"}
    ).copy()
    monthly_display["Doanh thu (R$)"] = monthly_display["Doanh thu (R$)"].map(fmt_money)
    monthly_display["Số đơn"] = monthly_display["Số đơn"].map(fmt_int)
    monthly_display["AOV (R$)"] = monthly_display["AOV (R$)"].map(fmt_money)
    st.dataframe(monthly_display, hide_index=True, **STRETCH)

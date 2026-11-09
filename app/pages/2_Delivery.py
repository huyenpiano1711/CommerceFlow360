"""F02 - Trang Delivery (Task F02, Phương Anh). Nguồn: mart_delivery.parquet, grain (order_id, seller_id).

Câu hỏi kinh doanh: bang nào giao trễ nhiều, giao trễ ảnh hưởng điểm đánh giá ra sao và những người bán nào
có tỷ lệ trễ cao (mục 4.3 báo cáo). Chỉ số cấp đơn được khử trùng theo order_id để không đếm lặp đơn nhiều người bán.
"""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.ui import (
    STRETCH,
    BLUE, GREEN, RED, empty_guard, filter_summary, fmt_int, fmt_num, fmt_pct, page_header,
    setup_page, sidebar_filters, style_fig, vn_axis_ticks,
)
from services.data_loader import (
    delivery_kpis, eligible_delivered, filter_delivery, load_delivery, orders_dedup,
)

setup_page("Delivery", "🚚")
page_header("Phân tích vận hành giao hàng (mart_delivery)",
            "Giao trễ = ngày khách nhận muộn hơn ngày dự kiến; chỉ tính đơn delivered có đủ hai mốc thời gian.")

filters = sidebar_filters(use_category=False, use_state=True)
delivery = filter_delivery(load_delivery(), filters)
empty_guard(delivery)
st.caption(filter_summary(filters, use_category=False))

el = eligible_delivered(delivery)
empty_guard(el, "Không có đơn delivered đủ điều kiện khớp bộ lọc hiện tại.")
k = delivery_kpis(delivery)
dd = orders_dedup(delivery)
not_eligible = len(dd) - len(el)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Tỷ lệ giao trễ", fmt_pct(k["late_rate"]))
c2.metric("Đơn giao trễ", fmt_int(k["late_orders"]), help="Trên tổng đơn đủ điều kiện: " + fmt_int(k["eligible_orders"]))
c3.metric("Số ngày giao TB", fmt_num(k["avg_delivery_days"], 1))
c4.metric("Số ngày trễ TB", fmt_num(k["avg_days_late"]), help="Trung bình days_late (không âm) trên đơn delivered đủ điều kiện, gồm cả đơn đúng hạn (0 ngày).")
c5.metric("Điểm đánh giá TB", fmt_num(k["avg_review"]))
st.caption(f"{fmt_int(not_eligible)} đơn chưa giao, đã hủy hoặc thiếu mốc thời gian được loại khỏi mẫu tính tỷ lệ (không xóa khỏi kho dữ liệu).")

# ------------------------------------------------------------------ theo bang
st.subheader("Tỷ lệ giao trễ theo bang khách hàng")
# Số đơn và tỷ lệ trễ cùng tính trên một tập: đơn delivered có đủ mốc thời gian (el), giống Bảng 4.3.1
# và bảng người bán bên dưới; trước đây số đơn gồm cả đơn delivered thiếu ngày nhận nên lệch mẫu số.
by_state = (el.groupby("customer_state")
              .agg(orders=("order_id", "count"), late_rate=("is_delivered_late", lambda s: s.astype(int).mean()),
                   avg_days_late=("days_late", lambda s: s.astype(float).mean())).reset_index())
mode = st.radio("Hiển thị", ["Top 10 bang nhiều đơn nhất", "Tất cả bang (≥ 100 đơn)"], horizontal=True, label_visibility="collapsed")
if mode.startswith("Top"):
    show = by_state.sort_values("orders", ascending=False).head(10)
else:
    show = by_state[by_state["orders"] >= 100].sort_values("late_rate", ascending=False)
show = show.assign(late_pct=show["late_rate"] * 100)
show["orders_label"] = show["orders"].map(fmt_int)
show["avg_days_late_label"] = show["avg_days_late"].map(fmt_num)
show["late_pct_label"] = show["late_pct"].map(fmt_num)
fig = px.bar(show, x="customer_state", y="late_pct",
             custom_data=["orders_label", "avg_days_late_label", "late_pct_label"],
             labels={"late_pct": "Tỷ lệ giao trễ (%)", "customer_state": "Bang"})
fig.update_traces(marker_color=RED, hovertemplate="%{x}<br>Tỷ lệ giao trễ: %{customdata[2]}%<br>Số đơn: %{customdata[0]}<br>Số ngày trễ TB: %{customdata[1]}<extra></extra>")
fig.update_yaxes(**vn_axis_ticks(show["late_pct"], digits=1))
fig.add_hline(y=k["late_rate"] * 100, line_dash="dash", line_color="#475569",
              annotation_text=f"Chung: {fmt_pct(k['late_rate'])}", annotation_position="top left")
st.plotly_chart(style_fig(fig, 380), **STRETCH)
st.caption("Khoảng cách địa lý tới trung tâm phân phối là giả thuyết hợp lý nhưng chưa được kiểm chứng trong dữ liệu; cần đối chiếu thêm mật độ người bán theo vùng.")

# ------------------------------------------------------------------ đánh giá và phân phối
left, right = st.columns(2)
with left:
    st.subheader("Điểm đánh giá: đúng hạn vs giao trễ")
    rated = el.dropna(subset=["review_score"]).copy()
    rated["nhom"] = rated["is_delivered_late"].map({True: "Giao trễ", False: "Đúng hạn"})
    rv = (rated.groupby("nhom").agg(orders=("order_id", "count"), avg_review=("review_score", lambda s: s.astype(float).mean()))
                .reindex(["Đúng hạn", "Giao trễ"]).reset_index())
    rv["orders_label"] = rv["orders"].map(fmt_int)
    fig = px.bar(rv, x="nhom", y="avg_review", text=rv["avg_review"].map(lambda v: fmt_num(v)),
                 custom_data=["orders_label"], labels={"avg_review": "Điểm đánh giá TB (1–5)", "nhom": ""})
    fig.update_traces(marker_color=[GREEN, RED], textposition="outside")
    fig.update_traces(hovertemplate="%{x}<br>Điểm trung bình: %{y:.2f}<br>Số đơn: %{customdata[0]}<extra></extra>")
    fig.update_yaxes(range=[0, 5])
    fig.update_yaxes(**vn_axis_ticks([0, 5], digits=1))
    st.plotly_chart(style_fig(fig, 360), **STRETCH)
    st.caption("So sánh nhóm, không khẳng định quan hệ nhân quả.")
with right:
    st.subheader("Phân phối số ngày giao hàng")
    cap = int(el["delivery_days"].astype(float).quantile(0.99))
    fig = px.histogram(el[el["delivery_days"].astype(float) <= cap].assign(d=lambda x: x["delivery_days"].astype(float)),
                       x="d", nbins=min(cap, 60), labels={"d": "Số ngày từ đặt đến nhận"})
    fig.update_traces(marker_color=BLUE)
    fig.update_layout(yaxis_title="Số đơn", bargap=0.05)
    fig.update_yaxes(**vn_axis_ticks())
    st.plotly_chart(style_fig(fig, 360), **STRETCH)
    st.caption(f"Hiển thị đến ngày thứ {cap} (phân vị 99); các đơn giao lâu hơn vẫn nằm trong KPI nhưng không vẽ để tránh kéo dài trục.")

# ------------------------------------------------------------------ theo tháng
st.subheader("Tỷ lệ giao trễ theo tháng")
MIN_MONTH_ORDERS = 30
by_month = (el.groupby("year_month")
              .agg(orders=("order_id", "count"), late_rate=("is_delivered_late", lambda s: s.astype(int).mean())).reset_index())
# Tháng quá ít đơn (vd. 09/2016 chỉ 1 đơn -> 100%) kéo trục lên và làm các tháng thật dẹt sát đáy
small_months = by_month[by_month["orders"] < MIN_MONTH_ORDERS]
by_month = by_month[by_month["orders"] >= MIN_MONTH_ORDERS]
by_month["late_label"] = by_month["late_rate"].map(fmt_pct)
by_month["orders_label"] = by_month["orders"].map(fmt_int)
fig = go.Figure(go.Scatter(x=by_month["year_month"], y=by_month["late_rate"] * 100, mode="lines+markers", line=dict(color=RED),
                           customdata=by_month[["late_label", "orders_label"]].values,
                           hovertemplate="%{x}<br>Tỷ lệ trễ: %{customdata[0]}<br>Số đơn: %{customdata[1]}<extra></extra>"))
fig.update_layout(yaxis_title="Tỷ lệ giao trễ (%)", xaxis=dict(type="category", tickangle=-60))
fig.update_yaxes(**vn_axis_ticks(by_month["late_rate"] * 100, digits=1))
st.plotly_chart(style_fig(fig, 320), **STRETCH)
if not small_months.empty:
    st.caption(f"Không vẽ các tháng có dưới {MIN_MONTH_ORDERS} đơn đủ điều kiện: "
               + ", ".join(f"{r.year_month} ({fmt_int(r.orders)} đơn)" for r in small_months.itertuples(index=False))
               + ". Các đơn này vẫn được tính trong KPI ở trên.")

# ------------------------------------------------------------------ người bán
st.subheader("Người bán có tỷ lệ giao trễ cao")
min_orders = st.slider("Số đơn giao tối thiểu của người bán", 10, 200, 30, step=5,
                       help="Mặc định 30 đơn như báo cáo 4.3, để tránh nhiễu từ mẫu quá nhỏ.")
# Grain (order_id, seller_id): một đơn nhiều người bán xuất hiện ở mỗi người bán của đơn đó
sel = delivery[(delivery["order_status"] == "delivered") & delivery["is_delivered_late"].notna()]
sellers = (sel.groupby("seller_id")
              .agg(orders=("order_id", "nunique"), late_rate=("is_delivered_late", lambda s: s.astype(int).mean()),
                   avg_review=("review_score", lambda s: s.astype(float).mean())).reset_index())
sellers = sellers[sellers["orders"] >= min_orders].sort_values(["late_rate", "seller_id"], ascending=[False, True]).head(10)
if sellers.empty:
    st.info("Không có người bán nào đạt ngưỡng số đơn trong bộ lọc hiện tại.")
else:
    sellers = sellers.assign(late_rate=sellers["late_rate"] * 100)
    sellers_display = sellers.rename(
        columns={"seller_id": "Người bán", "orders": "Số đơn", "late_rate": "Tỷ lệ trễ (%)", "avg_review": "Điểm ĐG TB"}
    ).copy()
    sellers_display["Số đơn"] = sellers_display["Số đơn"].map(fmt_int)
    sellers_display["Tỷ lệ trễ (%)"] = sellers_display["Tỷ lệ trễ (%)"].map(fmt_num)
    sellers_display["Điểm ĐG TB"] = sellers_display["Điểm ĐG TB"].map(fmt_num)
    st.dataframe(sellers_display, hide_index=True, **STRETCH)
    st.caption("Đơn có nhiều người bán được tính cho mỗi người bán tham gia đơn. Olist chỉ cho đánh giá theo đơn, "
               "nên điểm ĐG TB của người bán là điểm của các đơn họ tham gia: đơn nhiều người bán thì mọi người bán "
               "nhận chung một điểm, không phải điểm riêng cho từng người.")

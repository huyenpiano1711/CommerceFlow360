"""F02 - Trang Customer (Task F02, Phương Anh). Nguồn: mart_customer.parquet, grain customer_unique_id.

Câu hỏi kinh doanh: bao nhiêu khách quay lại mua, chi tiêu tập trung ở nhóm nào và khách đã "im lặng" bao lâu
(mục 4.4 báo cáo). Dùng customer_unique_id; chỉ tính khách có đơn hợp lệ.
"""
import plotly.express as px
import streamlit as st

from components.ui import (
    STRETCH,
    AMBER, BLUE, empty_guard, fmt_int, fmt_money, fmt_num, fmt_pct, fmt_pct_points, page_header, setup_page,
)
from services.data_loader import customer_kpis, load_customer, recency_distribution, spend_quartiles

setup_page("Customer", "👥")
page_header("Phân tích khách hàng (mart_customer)",
            "Một dòng cho mỗi customer_unique_id; customer_id chỉ là mã theo từng đơn nên không dùng để đếm khách.")

st.sidebar.header("Bộ lọc chung")
st.sidebar.info("Trang này không dùng bộ lọc thời gian, bang, danh mục: mart_customer đã tổng hợp theo khách hàng "
                "trên toàn bộ dữ liệu nên không có các chiều đó.")

customer = load_customer()
valid = customer[customer["has_valid_order"]]
empty_guard(valid)
k = customer_kpis(customer)
no_valid = len(customer) - len(valid)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Khách hàng", fmt_int(k["customers"]), help="customer_unique_id có ít nhất 1 đơn hợp lệ.")
c2.metric("Khách mua lại (≥ 2 đơn)", fmt_int(k["repeat_customers"]))
c3.metric("Tỷ lệ mua lại", fmt_pct(k["repeat_rate"]))
c4.metric("Tổng chi tiêu", fmt_money(k["total_spend"], 0), help="Tổng payment_value của đơn hợp lệ.")
st.caption(f"{fmt_int(no_valid)} khách chỉ có đơn canceled/unavailable được giữ trong mart để đối soát nhưng loại khỏi các chỉ số dưới đây.")

# ------------------------------------------------------------------ mua lại
left, right = st.columns(2)
with left:
    st.subheader("Khách mua 1 lần vs mua lại")
    grp = (valid.assign(nhom=valid["is_repeat_customer"].map({True: "Mua lại (≥ 2 đơn)", False: "Mua 1 lần"}))
                .groupby("nhom").agg(customers=("customer_unique_id", "count"), avg_spend=("total_spend", "mean")).reset_index())
    grp["pct"] = 100 * grp["customers"] / grp["customers"].sum()
    fig = px.bar(grp, x="nhom", y="pct", text=grp["pct"].map(lambda v: fmt_pct_points(v)),
                 hover_data={"customers": ":,.0f", "avg_spend": ":,.2f", "pct": ":.2f"},
                 labels={"pct": "% khách hàng", "nhom": ""})
    fig.update_traces(marker_color=[BLUE, AMBER] if grp.iloc[0]["nhom"].startswith("Mua lại") else [AMBER, BLUE], textposition="outside")
    fig.update_yaxes(range=[0, 110])
    st.plotly_chart(fig.update_layout(height=360), **STRETCH)
with right:
    st.subheader("Chi tiêu trung bình mỗi khách (R$)")
    fig = px.bar(grp, x="nhom", y="avg_spend", text=grp["avg_spend"].map(lambda v: fmt_num(v)),
                 labels={"avg_spend": "Chi tiêu TB (R$)", "nhom": ""})
    fig.update_traces(marker_color=[BLUE, AMBER] if grp.iloc[0]["nhom"].startswith("Mua lại") else [AMBER, BLUE], textposition="outside")
    st.plotly_chart(fig.update_layout(height=360), **STRETCH)
st.caption("Olist là marketplace đa ngành nên tỷ lệ mua lại thấp là đặc điểm của bộ dữ liệu; chênh lệch chi tiêu cho thấy giá trị tiềm năng của giữ chân khách.")

# ------------------------------------------------------------------ phân khúc chi tiêu
st.subheader("Phân khúc chi tiêu (quartile theo số khách)")
seg = spend_quartiles(valid)
fig = px.bar(seg, x=seg["spend_quartile"].astype(str), y="pct_revenue", text=seg["pct_revenue"].map(lambda v: fmt_pct_points(v)),
             hover_data={"customer_count": ":,.0f", "min_spend": ":,.2f", "max_spend": ":,.2f"},
             labels={"x": "Quartile (1 = chi tiêu thấp nhất)", "pct_revenue": "% tổng chi tiêu"})
fig.update_traces(marker_color=BLUE, textposition="outside")
fig.update_yaxes(range=[0, max(seg["pct_revenue"]) * 1.15])
st.plotly_chart(fig.update_layout(height=380), **STRETCH)
st.dataframe(
    seg.rename(columns={"spend_quartile": "Quartile", "customer_count": "Số khách", "min_spend": "Chi tiêu thấp nhất (R$)",
                        "max_spend": "Chi tiêu cao nhất (R$)", "total_spend_segment": "Tổng chi tiêu (R$)", "pct_revenue": "% tổng chi tiêu"}),
    hide_index=True, **STRETCH,
    column_config={"Chi tiêu thấp nhất (R$)": st.column_config.NumberColumn(format="%.2f"),
                   "Chi tiêu cao nhất (R$)": st.column_config.NumberColumn(format="%.2f"),
                   "Tổng chi tiêu (R$)": st.column_config.NumberColumn(format="%.2f"),
                   "% tổng chi tiêu": st.column_config.NumberColumn(format="%.2f")})
st.caption("Chỉ gồm khách có tổng chi tiêu > 0. Thể hiện mức độ tập trung doanh thu, không phải dự báo giá trị khách hàng.")

# ------------------------------------------------------------------ recency
st.subheader("Thời gian từ lần mua gần nhất (recency)")
rec = recency_distribution(valid)
fig = px.bar(rec, x="nhom_recency", y="pct_customers", text=rec["pct_customers"].map(lambda v: fmt_pct_points(v)),
             hover_data={"customer_count": ":,.0f"}, labels={"pct_customers": "% khách hàng", "nhom_recency": "Số ngày kể từ lần mua gần nhất"})
fig.update_traces(marker_color=BLUE, textposition="outside")
fig.update_yaxes(range=[0, max(rec["pct_customers"]) * 1.15])
st.plotly_chart(fig.update_layout(height=360), **STRETCH)
snapshot = valid["last_order_date"].max()
st.caption(f"Mốc so sánh là ngày đặt hàng lớn nhất trong dữ liệu ({snapshot:%d/%m/%Y}), không phải ngày hiện tại; "
           "đây không phải chỉ báo khách rời bỏ theo thời gian thực.")

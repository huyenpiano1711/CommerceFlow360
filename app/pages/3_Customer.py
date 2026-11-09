"""F02 - Trang Customer (Task F02, Phương Anh). Nguồn: mart_customer.parquet, grain customer_unique_id.

Câu hỏi kinh doanh: bao nhiêu khách quay lại mua, chi tiêu tập trung ở nhóm nào và khách đã "im lặng" bao lâu
(mục 4.4 báo cáo). Dùng customer_unique_id; chỉ tính khách có đơn hợp lệ.
"""
import plotly.express as px
import streamlit as st

from components.ui import (
    STRETCH,
    AMBER, BLUE, empty_guard, fmt_int, fmt_money, fmt_money_short, fmt_num, fmt_pct, fmt_pct_points, page_header,
    setup_page, style_fig, vn_axis_ticks,
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
c4.metric("Tổng chi tiêu", fmt_money_short(k["total_spend"]),
          help="Tổng payment_value khách trả của đơn hợp lệ, gồm phí vận chuyển (khác doanh thu price ở trang Sales).")
st.caption(f"{fmt_int(no_valid)} khách chỉ có đơn canceled/unavailable được giữ trong mart để đối soát nhưng loại khỏi các chỉ số dưới đây.")

# ------------------------------------------------------------------ mua lại
# Màu gán theo nhãn, thống nhất với Hình 4.4.1 của báo cáo (mua 1 lần: teal, mua lại: vàng)
REPEAT_COLORS = {"Mua 1 lần": BLUE, "Mua lại (≥ 2 đơn)": AMBER}
left, right = st.columns(2)
with left:
    st.subheader("Khách mua 1 lần vs mua lại")
    grp = (valid.assign(nhom=valid["is_repeat_customer"].map({True: "Mua lại (≥ 2 đơn)", False: "Mua 1 lần"}))
                .groupby("nhom").agg(customers=("customer_unique_id", "count"), avg_spend=("total_spend", "mean")).reset_index())
    grp["pct"] = 100 * grp["customers"] / grp["customers"].sum()
    grp["customers_label"] = grp["customers"].map(fmt_int)
    grp["avg_spend_label"] = grp["avg_spend"].map(fmt_money_short)
    grp["pct_label"] = grp["pct"].map(fmt_pct_points)
    fig = px.bar(grp, x="nhom", y="pct", text=grp["pct"].map(lambda v: fmt_pct_points(v)),
                 custom_data=["customers_label", "avg_spend_label", "pct_label"],
                 labels={"pct": "% khách hàng", "nhom": ""})
    fig.update_traces(marker_color=grp["nhom"].map(REPEAT_COLORS).tolist(),
                      textposition="outside",
                      hovertemplate="%{x}<br>Tỷ trọng: %{customdata[2]}<br>Số khách: %{customdata[0]}<br>Chi tiêu TB: %{customdata[1]}<extra></extra>")
    fig.update_yaxes(range=[0, 110])
    fig.update_yaxes(**vn_axis_ticks(grp["pct"], digits=1))
    st.plotly_chart(style_fig(fig, 360), **STRETCH)
with right:
    st.subheader("Chi tiêu trung bình mỗi khách (R$)")
    fig = px.bar(grp, x="nhom", y="avg_spend", text=grp["avg_spend"].map(lambda v: fmt_num(v)),
                 labels={"avg_spend": "Chi tiêu TB (R$)", "nhom": ""})
    fig.update_traces(marker_color=grp["nhom"].map(REPEAT_COLORS).tolist(), textposition="outside")
    fig.update_yaxes(**vn_axis_ticks(grp["avg_spend"]))
    st.plotly_chart(style_fig(fig, 360), **STRETCH)
st.caption("Olist là marketplace đa ngành nên tỷ lệ mua lại thấp là đặc điểm của bộ dữ liệu; chênh lệch chi tiêu cho thấy giá trị tiềm năng của giữ chân khách.")

# ------------------------------------------------------------------ phân khúc chi tiêu
st.subheader("Phân khúc chi tiêu (quartile theo số khách)")
seg = spend_quartiles(valid)
seg["customer_count_label"] = seg["customer_count"].map(fmt_int)
seg["min_spend_label"] = seg["min_spend"].map(fmt_money_short)
seg["max_spend_label"] = seg["max_spend"].map(fmt_money_short)
fig = px.bar(seg, x=seg["spend_quartile"].astype(str), y="pct_total_spend", text=seg["pct_total_spend"].map(lambda v: fmt_pct_points(v)),
             custom_data=["customer_count_label", "min_spend_label", "max_spend_label"],
             labels={"x": "Quartile (1 = chi tiêu thấp nhất)", "pct_total_spend": "% tổng chi tiêu"})
fig.update_traces(marker_color=BLUE, textposition="outside",
                  hovertemplate="Quartile %{x}<br>Tỷ trọng: %{y:.2f}%<br>Số khách: %{customdata[0]}<br>"
                                "Chi tiêu thấp nhất: %{customdata[1]}<br>Chi tiêu cao nhất: %{customdata[2]}<extra></extra>")
fig.update_yaxes(range=[0, max(seg["pct_total_spend"]) * 1.15])
fig.update_yaxes(**vn_axis_ticks(seg["pct_total_spend"], digits=1))
st.plotly_chart(style_fig(fig, 380), **STRETCH)
# Bỏ các cột *_label (chỉ dùng cho hover của biểu đồ) khỏi bảng hiển thị
seg_display = seg.drop(columns=["customer_count_label", "min_spend_label", "max_spend_label"]).rename(
    columns={"spend_quartile": "Quartile", "customer_count": "Số khách", "min_spend": "Chi tiêu thấp nhất (R$)",
             "max_spend": "Chi tiêu cao nhất (R$)", "total_spend_segment": "Tổng chi tiêu (R$)", "pct_total_spend": "% tổng chi tiêu"}
).copy()
seg_display["Số khách"] = seg_display["Số khách"].map(fmt_int)
for column in ["Chi tiêu thấp nhất (R$)", "Chi tiêu cao nhất (R$)"]:
    seg_display[column] = seg_display[column].map(fmt_money)
seg_display["Tổng chi tiêu (R$)"] = seg_display["Tổng chi tiêu (R$)"].map(fmt_money_short)
seg_display["% tổng chi tiêu"] = seg_display["% tổng chi tiêu"].map(fmt_num)
st.dataframe(seg_display, hide_index=True, **STRETCH)
st.caption("Chỉ gồm khách có tổng chi tiêu > 0. Thể hiện mức độ tập trung doanh thu, không phải dự báo giá trị khách hàng.")

# ------------------------------------------------------------------ recency
st.subheader("Thời gian từ lần mua gần nhất (recency)")
rec = recency_distribution(valid)
rec["customer_count_label"] = rec["customer_count"].map(fmt_int)
fig = px.bar(rec, x="nhom_recency", y="pct_customers", text=rec["pct_customers"].map(lambda v: fmt_pct_points(v)),
             custom_data=["customer_count_label"],
             labels={"pct_customers": "% khách hàng", "nhom_recency": "Số ngày kể từ lần mua gần nhất"})
fig.update_traces(marker_color=BLUE, textposition="outside")
fig.update_traces(hovertemplate="%{x}<br>Tỷ trọng: %{y:.2f}%<br>Số khách: %{customdata[0]}<extra></extra>")
fig.update_yaxes(range=[0, max(rec["pct_customers"]) * 1.15])
fig.update_yaxes(**vn_axis_ticks(rec["pct_customers"], digits=1))
st.plotly_chart(style_fig(fig, 360), **STRETCH)
snapshot = valid["last_order_date"].max()
st.caption(f"Mốc so sánh là ngày đặt hàng lớn nhất trong dữ liệu ({snapshot:%d/%m/%Y}), không phải ngày hiện tại; "
           "đây không phải chỉ báo khách rời bỏ theo thời gian thực.")

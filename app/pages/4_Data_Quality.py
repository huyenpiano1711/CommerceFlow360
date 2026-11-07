"""F03 - Trang Data Quality (Task F03, Phương Anh).

Hiển thị kết quả kiểm thử dbt (quality_results.parquet) và đối soát số liệu giữa các Data Mart (đọc từ Parquet).
Nếu repo có reports/tables/Bang_3.7.1_DoiSoatGold.csv (đối soát Bronze -> Silver -> Gold, task D04) thì dùng để đối chiếu thêm.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from components.ui import STRETCH, AMBER, BLUE, GREEN, RED, fmt_int, fmt_money, fmt_num, page_header, setup_page, style_fig
from services.data_loader import (
    load_customer, load_delivery, load_quality, load_reconciliation_reference, load_sales,
)

setup_page("Data Quality", "✅")
page_header("Chất lượng dữ liệu và đối soát",
            "Kết quả `dbt build` toàn bộ (Silver → Gold → Mart) và đối soát số liệu giữa các tầng, đọc từ Parquet.")
st.sidebar.header("Bộ lọc")
st.sidebar.info("Trang này không áp dụng bộ lọc chung vì các kiểm thử chạy trên toàn bộ dữ liệu.")

quality = load_quality().copy()


def layer_of(name: str) -> str:
    if "_mart_" in name or name.startswith("test_mart_") or name.startswith("test_sales_"):
        return "Mart"
    if "_gold_" in name or name.startswith("test_gold_"):
        return "Gold"
    return "Silver"


# Nhóm Silver/Gold/Mart được suy từ tên test để lọc nhanh, không phải cách phân loại chính thức trong Bảng 3.4.6
quality["tang"] = quality["test_name"].map(layer_of)
# test_sales_reconciliation đối soát Silver -> Gold; xếp vào nhóm Gold cho đúng ý nghĩa
quality.loc[quality["test_name"] == "test_sales_reconciliation", "tang"] = "Gold"
quality["loai"] = quality["test_name"].map(
    lambda n: next((p for p in ["accepted_values", "not_null", "relationships", "unique_combination", "unique"] if n.startswith(p)), "custom"))
quality["loai"] = quality["loai"].replace({"custom": "Tùy chỉnh (nghiệp vụ / đối soát)"})

# ------------------------------------------------------------------ tóm tắt
counts = quality["status"].value_counts()
total = len(quality)
bad = counts.get("fail", 0) + counts.get("error", 0)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tổng số test", fmt_int(total))
c2.metric("Pass", fmt_int(counts.get("pass", 0)))
c3.metric("Warn", fmt_int(counts.get("warn", 0)))
c4.metric("Fail / Error", fmt_int(bad))
if bad == 0:
    st.success("Không có lỗi khóa, grain hay đối soát ở bất kỳ tầng nào. Các cảnh báo (warn) là bất thường có thật của dữ liệu nguồn, không phải lỗi xử lý.")
else:
    st.error(f"Có {bad} test fail/error. Pipeline xuất Parquet lẽ ra đã dừng; hãy chạy lại `python scripts/export_parquet.py` và đọc log dbt.")

left, right = st.columns([1, 2])
with left:
    by_status = quality["status"].value_counts().rename_axis("status").reset_index(name="so_luong")
    fig = px.pie(by_status, names="status", values="so_luong", hole=0.55, color="status",
                 color_discrete_map={"pass": GREEN, "warn": AMBER, "fail": RED, "error": RED})
    fig.update_traces(textinfo="value+label")
    fig.update_layout(showlegend=False, title="Kết quả theo trạng thái")
    st.plotly_chart(style_fig(fig, 320), **STRETCH)
with right:
    by_type = quality.pivot_table(index="loai", columns="status", values="test_name", aggfunc="count", fill_value=0)
    long = by_type.reset_index().melt(id_vars="loai", var_name="status", value_name="so_luong")
    long = long[long["so_luong"] > 0]
    fig = px.bar(long, x="so_luong", y="loai", color="status", orientation="h", barmode="stack", text="so_luong",
                 color_discrete_map={"pass": GREEN, "warn": AMBER, "fail": RED, "error": RED},
                 labels={"loai": "", "so_luong": "Số test", "status": "Trạng thái"}, title="Số test theo loại")
    ticks = sorted(long["so_luong"].unique())
    fig.update_xaxes(tickmode="array", tickvals=ticks, ticktext=[fmt_int(value) for value in ticks])
    st.plotly_chart(style_fig(fig, 320), **STRETCH)

# ------------------------------------------------------------------ cảnh báo
st.subheader("Các cảnh báo (warn) và ý nghĩa")
WARN_NOTES = {
    "test_silver_carrier_after_purchase": "Đơn có ngày bàn giao cho đơn vị vận chuyển sớm hơn thời điểm đặt hàng. Đã gắn cờ flag_carrier_before_purchase ở Silver; không tự sửa giá trị.",
    "test_silver_review_after_purchase": "Đánh giá có ngày tạo sớm hơn ngày đặt hàng. Giữ nguyên, ghi nhận như nhiễu nguồn.",
    "test_silver_geolocation_customer_coverage": "Mã ZIP của khách hàng/người bán không khớp bảng geolocation; các thuộc tính địa lý có thể NULL.",
    "not_null_silver_geolocation_geolocation_lat": "ZIP không còn tọa độ hợp lệ trong lãnh thổ Brazil sau khi loại điểm ngoài khung tọa độ.",
    "not_null_silver_sellers_seller_city": "Người bán có tên thành phố không hợp lệ (số, email) bị chuyển NULL kèm cờ flag_city_invalid.",
}
warns = quality[quality["status"] == "warn"].copy()
if warns.empty:
    st.info("Không có cảnh báo nào trong lần chạy gần nhất.")
else:
    warns["y_nghia"] = warns["test_name"].map(WARN_NOTES).fillna("Cảnh báo chưa có diễn giải; xem dbt_project/README.md.")
    warns["failing_rows"] = warns["failing_rows"].map(fmt_int)
    st.dataframe(
        warns[["tang", "test_name", "failing_rows", "y_nghia"]].rename(
            columns={"tang": "Nhóm (theo tên test)", "test_name": "Test", "failing_rows": "Số bản ghi", "y_nghia": "Diễn giải"}),
        hide_index=True, **STRETCH)
st.caption("Test ở mức warn ghi nhận số lượng bất thường mà không chặn pipeline vì đó là đặc điểm của dữ liệu nguồn, không phải lỗi xử lý.")

# ------------------------------------------------------------------ đối soát giữa mart
st.subheader("Đối soát số liệu giữa các Data Mart")
sales, delivery, customer = load_sales(), load_delivery(), load_customer()

dup_sales = int(sales.duplicated(["order_id", "order_item_id"]).sum())
dup_customer = int(customer["customer_unique_id"].duplicated().sum())
orders_sales = sales["order_id"].nunique()
orders_delivery = delivery["order_id"].nunique()
rows = [
    ("Grain mart_sales: dòng trùng (order_id, order_item_id)", dup_sales, 0),
    ("Grain mart_customer: customer_unique_id trùng", dup_customer, 0),
    ("Số đơn: mart_sales so với mart_delivery (cùng từ fact_order_items)", orders_sales, orders_delivery),
]
recon = pd.DataFrame(rows, columns=["Kiểm tra", "Giá trị đo được", "Giá trị kỳ vọng"])
recon["Chênh lệch"] = recon["Giá trị đo được"] - recon["Giá trị kỳ vọng"]
recon["Kết quả"] = recon["Chênh lệch"].abs().map(lambda d: "Khớp" if d < 0.01 else "Lệch")

ref = load_reconciliation_reference()
if ref is not None:
    ref = ref.set_index("metric")
    extra = [
        ("Doanh thu: sum(mart_sales.revenue) so với item_revenue (Bảng 3.7.1)", float(sales["revenue"].sum()), float(ref.loc["item_revenue", "gold_value"])),
        ("Phí vận chuyển: sum(mart_sales.freight_value) so với freight_value (Bảng 3.7.1)", float(sales["freight_value"].sum()), float(ref.loc["freight_value", "gold_value"])),
        ("Số đơn: sum(mart_customer.order_count_all_status) so với order_count (Bảng 3.7.1)", float(customer["order_count_all_status"].sum()), float(ref.loc["order_count", "gold_value"])),
    ]
    add = pd.DataFrame(extra, columns=["Kiểm tra", "Giá trị đo được", "Giá trị kỳ vọng"])
    add["Chênh lệch"] = add["Giá trị đo được"] - add["Giá trị kỳ vọng"]
    add["Kết quả"] = add["Chênh lệch"].abs().map(lambda d: "Khớp" if d < 0.01 else "Lệch")
    recon = pd.concat([recon, add], ignore_index=True)

recon_display = recon.copy()
for column in ["Giá trị đo được", "Giá trị kỳ vọng", "Chênh lệch"]:
    recon_display[column] = [
        fmt_int(value) if label.startswith("Grain") or label.startswith("Số đơn") else fmt_money(value)
        for label, value in zip(recon["Kiểm tra"], recon[column])
    ]
st.dataframe(recon_display, hide_index=True, **STRETCH)
if (recon["Kết quả"] == "Lệch").any():
    st.error("Có chỉ số lệch. Không sửa số cho khớp; kiểm tra lại pipeline theo AGENTS.md.")
else:
    st.success("Các phép đối soát tính trực tiếp từ Parquet đều khớp.")
if ref is None:
    st.info("Không tìm thấy reports/tables/Bang_3.7.1_DoiSoatGold.csv nên chưa đối chiếu với tổng giá trị Bronze/Silver/Gold. "
            "Chạy notebook 05_Data_Quality.ipynb hoặc pipeline để tạo bảng này.")
else:
    with st.expander("Bảng 3.7.1 – Đối soát Bronze → Silver → Gold (task D04)"):
        ref_display = ref.reset_index().copy()
        for column in ["source_value", "silver_value", "gold_value",
                       "source_to_silver_difference", "silver_to_gold_difference"]:
            if column in ref_display:
                ref_display[column] = [
                    fmt_int(value) if metric == "order_count" else fmt_money(value)
                    for metric, value in zip(ref_display["metric"], ref_display[column])
                ]
        st.dataframe(ref_display, hide_index=True, **STRETCH)
st.caption(f"mart_delivery chỉ gồm đơn có ít nhất 1 dòng hàng ({fmt_int(orders_delivery)} đơn); các đơn không có order_items không nằm trong mart nên phải so với "
           "fact_order_items, không so với tổng fact_orders.")

# ------------------------------------------------------------------ danh sách test
st.subheader("Danh sách toàn bộ test")
f1, f2, f3 = st.columns(3)
status_sel = f1.multiselect("Trạng thái", sorted(quality["status"].unique()), default=sorted(quality["status"].unique()))
layer_sel = f2.multiselect("Nhóm (suy từ tên test)", ["Silver", "Gold", "Mart"], default=["Silver", "Gold", "Mart"])
type_sel = f3.multiselect("Loại test", sorted(quality["loai"].unique()), default=sorted(quality["loai"].unique()))
view = quality[quality["status"].isin(status_sel) & quality["tang"].isin(layer_sel) & quality["loai"].isin(type_sel)]
view_display = view[["tang", "loai", "test_name", "status", "failing_rows", "execution_time_sec"]].rename(
    columns={"tang": "Nhóm (theo tên test)", "loai": "Loại", "test_name": "Test", "status": "Trạng thái",
             "failing_rows": "Bản ghi vi phạm", "execution_time_sec": "Thời gian (s)"}
).copy()
view_display["Bản ghi vi phạm"] = view_display["Bản ghi vi phạm"].map(fmt_int)
view_display["Thời gian (s)"] = view_display["Thời gian (s)"].map(lambda value: fmt_num(value, 3))
st.dataframe(
    view_display, hide_index=True, **STRETCH, height=420)
st.caption(f"Hiển thị {fmt_int(len(view))}/{fmt_int(total)} test. Nguồn: data/exports/quality_results.parquet (từ target/run_results.json của dbt).")

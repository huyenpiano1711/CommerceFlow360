"""B02 - Phân tích khám phá dữ liệu (EDA) cho Chương 2.

Đọc các bảng silver_* trong commerceflow.duckdb (dữ liệu nguồn đã ép kiểu, CHƯA lọc trạng thái đơn,
chưa tổng hợp KPI) và sinh:
  * reports/tables/Bang_2.5 ... Bang_2.12 - số liệu của các bảng cùng số trong mục 2.3, 2.4;
  * reports/figures/Hinh_2.1 ... Hinh_2.6  - biểu đồ cùng số trong mục 2.3.

EDA mô tả dữ liệu nguồn nên KHÔNG dùng định nghĩa "đơn hợp lệ" của Data Mart: số đơn theo tháng tính trên
mọi trạng thái, giá trị sản phẩm theo tháng là tổng price của mọi dòng hàng. KPI chính thức nằm ở Chương 4.
Tỷ lệ khuyết thiếu lấy từ data/profiling/missing_values.csv (A02) để khớp với bước profiling dữ liệu gốc.

Chạy từ thư mục gốc repository (sau khi đã build Silver):
    python -m src.reporting.eda_report
"""
from __future__ import annotations

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import pandas as pd  # noqa: E402

from src.utils.project import DUCKDB_PATH, FIGURE_DIR, PROJECT_ROOT, TABLE_DIR  # noqa: E402

BLUE, RED, GREEN, AMBER, GREY = "#2563eb", "#dc2626", "#16a34a", "#f59e0b", "#64748b"
PROFILING_DIR = PROJECT_ROOT / "data" / "profiling"


def _vn(x: float, digits: int = 0) -> str:
    """Định dạng số kiểu Việt Nam: 1.234.567,8."""
    return f"{x:,.{digits}f}".replace(",", "§").replace(".", ",").replace("§", ".")


vn_int = mticker.FuncFormatter(lambda x, _: _vn(x))
vn_million = mticker.FuncFormatter(lambda x, _: _vn(x / 1e6, 1) + " tr")


def _save_table(df: pd.DataFrame, name: str) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLE_DIR / name, index=False, encoding="utf-8-sig")
    print("Bang:", name)


def _save_fig(fig, name: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / name, dpi=150, facecolor="white")
    plt.close(fig)
    print("Hinh:", name)


SQL = {
    "monthly": """
        select strftime(o.order_purchase_timestamp, '%Y-%m') as year_month,
               count(distinct o.order_id)                      as order_count,
               coalesce(sum(i.price), 0)                       as product_value
        from silver_orders o
        left join silver_order_items i on i.order_id = o.order_id
        group by 1 order by 1""",
    "status": """
        select order_status, count(*) as order_count,
               round(100.0 * count(*) / sum(count(*)) over (), 2) as pct_orders
        from silver_orders group by 1 order by 2 desc""",
    "items": "select price, freight_value from silver_order_items",
    "order_value": """
        select order_id, sum(price) as product_value, sum(freight_value) as freight_value
        from silver_order_items group by 1""",
    "payment_type": """
        select payment_type, count(*) as payment_rows,
               round(100.0 * count(*) / sum(count(*)) over (), 2)                  as pct_rows,
               round(sum(payment_value), 2)                                         as payment_value,
               round(100.0 * sum(payment_value) / sum(sum(payment_value)) over (), 2) as pct_value
        from silver_order_payments group by 1 order by 2 desc""",
    "installments": """
        select payment_installments, count(*) as payment_rows
        from silver_order_payments where payment_type = 'credit_card'
        group by 1 order by 1""",
    "delivery": """
        select date_diff('day', order_purchase_timestamp::date, order_delivered_customer_date::date)  as delivery_days,
               date_diff('day', order_purchase_timestamp::date, order_estimated_delivery_date::date)  as estimated_days,
               order_delivered_customer_date::date > order_estimated_delivery_date::date              as is_late
        from silver_orders
        where order_status = 'delivered'
          and order_delivered_customer_date is not null
          and order_estimated_delivery_date is not null""",
    "reviews": """
        select review_score, count(*) as order_count,
               round(100.0 * count(*) / sum(count(*)) over (), 2) as pct_orders
        from silver_order_reviews where is_latest_review group by 1 order by 1""",
    "customer_state": """
        select c.customer_state, count(*) as order_count,
               count(distinct c.customer_unique_id) as customer_count,
               round(100.0 * count(*) / sum(count(*)) over (), 2) as pct_orders
        from silver_orders o join silver_customers c on c.customer_id = o.customer_id
        group by 1 order by 2 desc""",
    "seller_state": """
        select seller_state, count(*) as seller_count,
               round(100.0 * count(*) / sum(count(*)) over (), 2) as pct_sellers
        from silver_sellers group by 1 order by 2 desc""",
    "grain": """
        select 'Đơn có từ 2 dòng hàng' as chi_so, count(*) as so_don from (
            select order_id from silver_order_items group by 1 having count(*) > 1)
        union all select 'Đơn có từ 2 dòng thanh toán', count(*) from (
            select order_id from silver_order_payments group by 1 having count(*) > 1)
        union all select 'Đơn có từ 2 đánh giá', count(*) from (
            select order_id from silver_order_reviews group by 1 having count(*) > 1)
        union all select 'Đơn không có dòng hàng', count(*) from silver_orders o
            where not exists (select 1 from silver_order_items i where i.order_id = o.order_id)
        union all select 'Số dòng khi nối thẳng order_items với payments', count(*)
            from silver_order_items i join silver_order_payments p on p.order_id = i.order_id
        union all select 'customer_unique_id gắn với nhiều customer_id', count(*) from (
            select customer_unique_id from silver_customers group by 1 having count(distinct customer_id) > 1)""",
}


def load(con: duckdb.DuckDBPyConnection) -> dict[str, pd.DataFrame]:
    return {key: con.execute(sql).df() for key, sql in SQL.items()}


def fig_missing() -> pd.DataFrame:
    """Hình 2.1 - các cột có giá trị thiếu (từ profiling A02)."""
    miss = pd.read_csv(PROFILING_DIR / "missing_values.csv")
    rows = pd.read_csv(PROFILING_DIR / "doi_chieu_so_dong.csv")[["file_name", "actual_rows"]]
    miss = miss.merge(rows, on="file_name")
    miss = miss[miss["missing_values"] > 0].copy()
    miss["missing_rate_pct"] = (100 * miss["missing_values"] / miss["actual_rows"]).round(2)
    miss["table"] = miss["file_name"].str.replace("olist_", "").str.replace("_dataset.csv", "")
    miss = miss.sort_values("missing_rate_pct")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    labels = miss["table"] + "." + miss["column_name"]
    bars = ax.barh(labels, miss["missing_rate_pct"], color=BLUE)
    for bar, n in zip(bars, miss["missing_values"]):
        ax.text(bar.get_width() + 0.6, bar.get_y() + bar.get_height() / 2, _vn(n) + " dòng",
                va="center", fontsize=8, color="#334155")
    ax.set_xlabel("Tỷ lệ thiếu (%)")
    ax.set_xlim(0, miss["missing_rate_pct"].max() * 1.22)
    ax.set_title("Các cột có giá trị thiếu trong dữ liệu nguồn Olist")
    _save_fig(fig, "Hinh_2.1_TyLeKhuyetThieu.png")
    out = miss[["table", "column_name", "missing_values", "actual_rows", "missing_rate_pct"]].iloc[::-1]
    _save_table(out, "Bang_2.5_KhuyetThieuTheoCot.csv")
    return out


def fig_monthly(monthly: pd.DataFrame) -> None:
    """Hình 2.2 - số đơn và giá trị sản phẩm theo tháng (mọi trạng thái)."""
    fig, ax = plt.subplots(figsize=(10, 4.4))
    x = range(len(monthly))
    ax.bar(x, monthly["order_count"], color="#bfdbfe", label="Số đơn (trục trái)")
    ax.set_ylabel("Số đơn")
    ax.yaxis.set_major_formatter(vn_int)
    ax2 = ax.twinx()
    ax2.plot(x, monthly["product_value"], color=BLUE, marker="o", linewidth=2, label="Giá trị sản phẩm (trục phải)")
    ax2.set_ylabel("Giá trị sản phẩm (R$)")
    ax2.yaxis.set_major_formatter(vn_million)
    ax2.set_ylim(bottom=0)
    ax.set_xticks(list(x))
    ax.set_xticklabels(monthly["year_month"], rotation=60, fontsize=8)
    ax.set_title("Số đơn hàng và giá trị sản phẩm theo tháng đặt hàng (mọi trạng thái đơn)")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8, frameon=False)
    _save_fig(fig, "Hinh_2.2_DonHangTheoThang.png")


def fig_price(items: pd.DataFrame, order_value: pd.DataFrame) -> pd.DataFrame:
    """Hình 2.3 - phân phối giá và phí vận chuyển (thang log)."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    bins = [10 ** (i / 20) for i in range(-1, 80)]
    axes[0].hist(items["price"], bins=bins, color=BLUE, alpha=0.85, label="price")
    axes[0].hist(items["freight_value"].clip(lower=0.1), bins=bins, color=AMBER, alpha=0.7, label="freight_value")
    axes[0].set_xscale("log")
    axes[0].set_xlabel("R$ (thang log)")
    axes[0].set_ylabel("Số dòng hàng")
    axes[0].yaxis.set_major_formatter(vn_int)
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].set_title("Giá và phí vận chuyển mỗi dòng hàng")
    data = [order_value["product_value"], order_value["freight_value"]]
    axes[1].boxplot(data, showfliers=False, widths=0.5)
    axes[1].set_xticks([1, 2])
    axes[1].set_xticklabels(["Giá trị sản phẩm/đơn", "Phí vận chuyển/đơn"])
    axes[1].set_ylabel("R$")
    axes[1].set_title("Cấp đơn hàng (không vẽ ngoại lệ)")
    _save_fig(fig, "Hinh_2.3_PhanPhoiGiaVaPhiVanChuyen.png")
    stats = pd.DataFrame({
        "chi_so": ["price (dòng hàng)", "freight_value (dòng hàng)", "Giá trị sản phẩm / đơn", "Phí vận chuyển / đơn"],
        "trung_binh": [items["price"].mean(), items["freight_value"].mean(),
                       order_value["product_value"].mean(), order_value["freight_value"].mean()],
        "trung_vi": [items["price"].median(), items["freight_value"].median(),
                     order_value["product_value"].median(), order_value["freight_value"].median()],
        "p75": [items["price"].quantile(.75), items["freight_value"].quantile(.75),
                order_value["product_value"].quantile(.75), order_value["freight_value"].quantile(.75)],
        "p99": [items["price"].quantile(.99), items["freight_value"].quantile(.99),
                order_value["product_value"].quantile(.99), order_value["freight_value"].quantile(.99)],
        "lon_nhat": [items["price"].max(), items["freight_value"].max(),
                     order_value["product_value"].max(), order_value["freight_value"].max()],
    }).round(2)
    _save_table(stats, "Bang_2.7_ThongKeGiaVaPhiVanChuyen.csv")
    return stats


def fig_payment(payment_type: pd.DataFrame, installments: pd.DataFrame) -> None:
    """Hình 2.4 - phương thức thanh toán và số kỳ trả góp thẻ tín dụng."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    pt = payment_type[payment_type["payment_rows"] > 10]
    axes[0].bar(pt["payment_type"], pt["pct_rows"], color=BLUE, label="% số dòng thanh toán")
    axes[0].bar(pt["payment_type"], pt["pct_value"], color=AMBER, width=0.4, label="% giá trị thanh toán")
    axes[0].set_ylabel("%")
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].set_title("Tỷ trọng phương thức thanh toán")
    inst = installments[installments["payment_installments"].between(1, 12)]
    axes[1].bar(inst["payment_installments"].astype(int), inst["payment_rows"], color=BLUE)
    axes[1].set_xticks(range(1, 13))
    axes[1].set_xlabel("Số kỳ trả góp")
    axes[1].set_ylabel("Số dòng thanh toán")
    axes[1].yaxis.set_major_formatter(vn_int)
    axes[1].set_title("Số kỳ trả góp (thẻ tín dụng)")
    _save_fig(fig, "Hinh_2.4_ThanhToan.png")
    _save_table(payment_type, "Bang_2.8_PhuongThucThanhToan.csv")


def fig_delivery_reviews(delivery: pd.DataFrame, reviews: pd.DataFrame) -> pd.DataFrame:
    """Hình 2.5 - thời gian giao thực tế và phân phối điểm đánh giá."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    cap = int(delivery["delivery_days"].quantile(0.99))
    d = delivery[delivery["delivery_days"] <= cap]
    axes[0].hist(d["delivery_days"], bins=range(0, cap + 2), color=BLUE, alpha=0.85, label="Thực tế")
    axes[0].axvline(delivery["delivery_days"].median(), color=RED, linestyle="--",
                    label=f"Trung vị thực tế: {delivery['delivery_days'].median():.0f} ngày")
    axes[0].axvline(delivery["estimated_days"].median(), color=GREEN, linestyle="--",
                    label=f"Trung vị dự kiến: {delivery['estimated_days'].median():.0f} ngày")
    axes[0].set_xlabel(f"Số ngày từ đặt đến nhận (hiển thị đến phân vị 99 = {cap} ngày)")
    axes[0].set_ylabel("Số đơn")
    axes[0].yaxis.set_major_formatter(vn_int)
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].set_title("Thời gian giao hàng (đơn delivered)")
    colors = [RED, "#f97316", AMBER, "#84cc16", GREEN]
    axes[1].bar(reviews["review_score"].astype(str), reviews["pct_orders"], color=colors)
    for x, p in zip(reviews["review_score"].astype(str), reviews["pct_orders"]):
        axes[1].text(x, p + 1, _vn(p, 2) + "%", ha="center", fontsize=8)
    axes[1].set_ylim(0, reviews["pct_orders"].max() * 1.15)
    axes[1].set_xlabel("Điểm đánh giá")
    axes[1].set_ylabel("% đơn có đánh giá")
    axes[1].set_title("Phân phối điểm đánh giá (đánh giá mới nhất mỗi đơn)")
    _save_fig(fig, "Hinh_2.5_GiaoHangVaDanhGia.png")
    stats = pd.DataFrame({
        "chi_so": ["Số đơn delivered đủ mốc", "Số ngày giao TB", "Trung vị số ngày giao", "Phân vị 90", "Phân vị 99",
                   "Dài nhất", "Số ngày dự kiến TB", "Tỷ lệ giao trễ (%)"],
        "gia_tri": [len(delivery), delivery["delivery_days"].mean(), delivery["delivery_days"].median(),
                    delivery["delivery_days"].quantile(.9), delivery["delivery_days"].quantile(.99),
                    delivery["delivery_days"].max(), delivery["estimated_days"].mean(), 100 * delivery["is_late"].mean()],
    }).round(2)
    _save_table(stats, "Bang_2.9_ThoiGianGiaoHang.csv")
    _save_table(reviews, "Bang_2.10_PhanPhoiDiemDanhGia.csv")
    return stats


def fig_geography(customer_state: pd.DataFrame, seller_state: pd.DataFrame) -> None:
    """Hình 2.6 - đơn hàng theo bang khách hàng và người bán theo bang."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    top = customer_state.head(10)
    axes[0].bar(top["customer_state"], top["order_count"], color=BLUE)
    axes[0].yaxis.set_major_formatter(vn_int)
    axes[0].set_ylabel("Số đơn")
    axes[0].set_title("Top 10 bang theo số đơn (bang khách hàng)")
    top_s = seller_state.head(10)
    axes[1].bar(top_s["seller_state"], top_s["seller_count"], color=AMBER)
    axes[1].yaxis.set_major_formatter(vn_int)
    axes[1].set_ylabel("Số người bán")
    axes[1].set_title("Top 10 bang theo số người bán")
    _save_fig(fig, "Hinh_2.6_PhanBoDiaLy.png")
    # Bảng 2.11: bang khách hàng kèm số người bán của bang (bang không có người bán ghi 0)
    merged = customer_state.merge(seller_state[["seller_state", "seller_count"]],
                                  left_on="customer_state", right_on="seller_state", how="left")
    merged["seller_count"] = merged["seller_count"].fillna(0).astype(int)
    _save_table(merged.drop(columns="seller_state"), "Bang_2.11_PhanBoTheoBang.csv")


def run_all() -> dict[str, pd.DataFrame]:
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as con:
        data = load(con)
    data["missing"] = fig_missing()
    fig_monthly(data["monthly"])
    data["price_stats"] = fig_price(data["items"], data["order_value"])
    fig_payment(data["payment_type"], data["installments"])
    data["delivery_stats"] = fig_delivery_reviews(data["delivery"], data["reviews"])
    fig_geography(data["customer_state"], data["seller_state"])
    _save_table(data["status"], "Bang_2.6_TrangThaiDonHang.csv")
    _save_table(data["grain"], "Bang_2.12_QuanHeMotNhieu.csv")
    return data


if __name__ == "__main__":
    run_all()
    print("\nHoan tat B02.")

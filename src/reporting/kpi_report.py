"""E04 - Bảng và biểu đồ KPI cho Chương 4 (Task E04, Quỳnh Kha).

Mỗi báo cáo đọc một file analytics/sql/analysis_<mart>_<nội dung>.sql trên commerceflow.duckdb,
lưu bảng vào reports/tables/Bang_4.x_*.csv và (nếu có) biểu đồ vào reports/figures/Hinh_4.x_*.png.
Dùng chung cho scripts/run_e04_analytics.py và notebooks/06_Business_Analytics.ipynb.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import duckdb
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from src.utils.project import DUCKDB_PATH, EXPORT_DIR, FIGURE_DIR, PROJECT_ROOT, TABLE_DIR

SQL_DIR = PROJECT_ROOT / "analytics" / "sql"
BLUE, RED, GREEN, AMBER = "#2563eb", "#dc2626", "#16a34a", "#f59e0b"
money_fmt = mticker.FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M")


def _plot_monthly_revenue(ax, df):
    x = range(len(df))
    ax.plot(x, df["revenue"], marker="o", color=BLUE)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{int(r.year)}-{int(r.month):02d}" for r in df.itertuples()], rotation=60, fontsize=7)
    ax.yaxis.set_major_formatter(money_fmt)
    ax.set_title("Doanh thu theo tháng (mart_sales, đơn hợp lệ)")
    ax.set_ylabel("Doanh thu (R$)")


def _plot_category_revenue(ax, df):
    ax.barh(df["product_category"][::-1], df["revenue"][::-1], color=BLUE)
    ax.xaxis.set_major_formatter(money_fmt)
    ax.set_title("Top 10 danh mục sản phẩm theo doanh thu")
    ax.set_xlabel("Doanh thu (R$)")


def _plot_state_revenue(ax, df):
    ax.bar(df["customer_state"], df["revenue"], color=BLUE)
    ax.yaxis.set_major_formatter(money_fmt)
    ax.set_title("Top 10 bang khách hàng theo doanh thu")
    ax.set_ylabel("Doanh thu (R$)")


def _plot_late_rate_by_state(ax, df):
    ax.bar(df["customer_state"], df["late_rate"] * 100, color=RED)
    ax.set_title("Tỷ lệ giao trễ theo bang khách hàng (top 10 đơn nhiều nhất)")
    ax.set_ylabel("Tỷ lệ giao trễ (%)")


def _plot_review_by_ontime(ax, df):
    ax.bar(df["nhom_giao_hang"], df["avg_review_score"], color=[GREEN, RED])
    ax.set_ylim(0, 5)
    ax.set_title("Điểm đánh giá trung bình: đúng hạn vs trễ")
    ax.set_ylabel("Điểm đánh giá (1-5)")


def _plot_repeat_rate(ax, df):
    ax.bar(df["nhom_khach_hang"], df["pct_customers"], color=[BLUE, AMBER])
    ax.set_title("Tỷ lệ khách mua 1 lần vs mua lại")
    ax.set_ylabel("% khách hàng")


def _plot_spend_segments(ax, df):
    ax.bar(df["spend_quartile"].astype(str), df["pct_revenue"], color=BLUE)
    ax.set_title("% tổng doanh thu theo phân khúc chi tiêu (quartile)")
    ax.set_xlabel("Quartile (1 = chi tiêu thấp nhất)")
    ax.set_ylabel("% tổng chi tiêu")


def _plot_recency(ax, df):
    ax.bar(df["nhom_recency"], df["pct_customers"], color=BLUE)
    ax.set_title("Phân bố thời gian từ lần mua gần nhất (recency)")
    ax.set_ylabel("% khách hàng")


@dataclass(frozen=True)
class Report:
    sql_file: str
    table: str
    plot: Callable | None = None
    figure: str | None = None
    figsize: tuple[float, float] = (8, 4.5)


# Thứ tự theo mục báo cáo 4.2 (Sales) -> 4.3 (Delivery) -> 4.4 (Customer)
REPORTS: dict[str, Report] = {
    "sales_monthly_revenue": Report(
        "analysis_sales_monthly_revenue.sql", "Bang_4.2.1_DoanhThuTheoThang.csv",
        _plot_monthly_revenue, "Hinh_4.2.1_DoanhThuTheoThang.png", (9, 4)),
    "sales_category_revenue": Report(
        "analysis_sales_category_revenue.sql", "Bang_4.2.2_Top10DanhMuc.csv",
        _plot_category_revenue, "Hinh_4.2.2_Top10DanhMuc.png", (9, 5)),
    "sales_state_revenue": Report(
        "analysis_sales_state_revenue.sql", "Bang_4.2.3_Top10BangKhachHang.csv",
        _plot_state_revenue, "Hinh_4.2.3_Top10BangKhachHang.png"),
    "sales_holiday_aov": Report(
        "analysis_sales_holiday_aov.sql", "Bang_4.2.4_AOV_NgayLe_vs_NgayThuong.csv"),
    "delivery_late_rate_by_state": Report(
        "analysis_delivery_late_rate_by_state.sql", "Bang_4.3.1_TyLeGiaoTreTheoBang.csv",
        _plot_late_rate_by_state, "Hinh_4.3.1_TyLeGiaoTreTheoBang.png"),
    "delivery_late_rate_by_seller": Report(
        "analysis_delivery_late_rate_by_seller.sql", "Bang_4.3.2_TopSellerGiaoTre.csv"),
    "delivery_review_by_ontime": Report(
        "analysis_delivery_review_by_ontime.sql", "Bang_4.3.3_DiemDanhGia_DungHan_vs_Tre.csv",
        _plot_review_by_ontime, "Hinh_4.3.2_DiemDanhGia_DungHan_vs_Tre.png", (5, 4.5)),
    "customer_repeat_rate": Report(
        "analysis_customer_repeat_rate.sql", "Bang_4.4.1_TyLeMuaLai.csv",
        _plot_repeat_rate, "Hinh_4.4.1_TyLeMuaLai.png", (5, 4.5)),
    "customer_spend_segments": Report(
        "analysis_customer_spend_segments.sql", "Bang_4.4.2_PhanKhucChiTieu.csv",
        _plot_spend_segments, "Hinh_4.4.2_PhanKhucChiTieu.png", (6, 4.5)),
    "customer_recency": Report(
        "analysis_customer_recency.sql", "Bang_4.4.3_PhanBoRecency.csv",
        _plot_recency, "Hinh_4.4.3_PhanBoRecency.png", (6, 4.5)),
}

TEST_SUMMARY_TABLE = "Bang_4.1.1_TomTatKiemThu.csv"


def run_report(key: str, show: bool = False) -> pd.DataFrame:
    """Chạy một báo cáo: truy vấn SQL, lưu bảng, vẽ và lưu biểu đồ (nếu có)."""
    report = REPORTS[key]
    sql = (SQL_DIR / report.sql_file).read_text(encoding="utf-8")
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as con:
        df = con.execute(sql).df()

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLE_DIR / report.table, index=False, encoding="utf-8-sig")
    print("Bang:", report.table)

    if report.plot is not None:
        FIGURE_DIR.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=report.figsize)
        report.plot(ax, df)
        fig.tight_layout()
        fig.savefig(FIGURE_DIR / report.figure, dpi=150)
        if show:
            plt.show()
        plt.close(fig)
        print("Hinh:", report.figure)
    return df


def export_test_summary() -> pd.DataFrame:
    """Bảng 4.1.1 - số test theo trạng thái, đọc từ quality_results.parquet (xuất bởi E05)."""
    quality = pd.read_parquet(EXPORT_DIR / "quality_results.parquet")
    summary = quality["status"].value_counts().rename_axis("status").reset_index(name="so_luong")
    summary = pd.concat([summary, pd.DataFrame([{"status": "total", "so_luong": len(quality)}])], ignore_index=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(TABLE_DIR / TEST_SUMMARY_TABLE, index=False, encoding="utf-8-sig")
    print("Bang:", TEST_SUMMARY_TABLE)
    return summary


def run_all(show: bool = False) -> dict[str, pd.DataFrame]:
    results = {"test_summary": export_test_summary()}
    for key in REPORTS:
        results[key] = run_report(key, show=show)
    return results

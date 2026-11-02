"""E04 - Truy vấn phân tích KPI (Task E04, Quỳnh Kha).

Chạy các file analytics/sql/analysis_<mart>_<nội dung>.sql trên commerceflow.duckdb,
lưu kết quả bảng vào reports/tables/Bang_4.x_*.csv và vẽ biểu đồ vào reports/figures/Hinh_4.x_*.png.
"""
from pathlib import Path
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = PROJECT_ROOT / "commerceflow.duckdb"
SQL_DIR = PROJECT_ROOT / "analytics" / "sql"
TABLES_DIR = PROJECT_ROOT / "reports" / "tables"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DUCKDB_PATH), read_only=True)


def run(sql_file):
    sql = (SQL_DIR / sql_file).read_text(encoding="utf-8")
    return con.execute(sql).df()


def save_table(df, name):
    path = TABLES_DIR / name
    df.to_csv(path, index=False)
    print("Bang:", path)


def save_fig(fig, name):
    path = FIGURES_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print("Hinh:", path)


money_fmt = mticker.FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M")

# ---------------------------------------------------------------- 4.2 Sales
df = run("analysis_sales_monthly_revenue.sql")
save_table(df, "Bang_4.2.1_DoanhThuTheoThang.csv")
fig, ax = plt.subplots(figsize=(9, 4))
x = range(len(df))
ax.plot(x, df["revenue"], marker="o", color="#2563eb")
ax.set_xticks(list(x))
ax.set_xticklabels([f"{int(r.year)}-{int(r.month):02d}" for r in df.itertuples()], rotation=60, fontsize=7)
ax.yaxis.set_major_formatter(money_fmt)
ax.set_title("Doanh thu theo tháng (mart_sales, đơn hợp lệ)")
ax.set_ylabel("Doanh thu (R$)")
save_fig(fig, "Hinh_4.2.1_DoanhThuTheoThang.png")

df = run("analysis_sales_category_revenue.sql")
save_table(df, "Bang_4.2.2_Top10DanhMuc.csv")
fig, ax = plt.subplots(figsize=(9, 5))
ax.barh(df["product_category"][::-1], df["revenue"][::-1], color="#2563eb")
ax.xaxis.set_major_formatter(money_fmt)
ax.set_title("Top 10 danh mục sản phẩm theo doanh thu")
ax.set_xlabel("Doanh thu (R$)")
save_fig(fig, "Hinh_4.2.2_Top10DanhMuc.png")

df = run("analysis_sales_state_revenue.sql")
save_table(df, "Bang_4.2.3_Top10BangKhachHang.csv")
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(df["customer_state"], df["revenue"], color="#2563eb")
ax.yaxis.set_major_formatter(money_fmt)
ax.set_title("Top 10 bang khách hàng theo doanh thu")
ax.set_ylabel("Doanh thu (R$)")
save_fig(fig, "Hinh_4.2.3_Top10BangKhachHang.png")

df = run("analysis_sales_holiday_aov.sql")
save_table(df, "Bang_4.2.4_AOV_NgayLe_vs_NgayThuong.csv")

# -------------------------------------------------------------- 4.3 Delivery
df = run("analysis_delivery_late_rate_by_state.sql")
save_table(df, "Bang_4.3.1_TyLeGiaoTreTheoBang.csv")
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(df["customer_state"], df["late_rate"] * 100, color="#dc2626")
ax.set_title("Tỷ lệ giao trễ theo bang khách hàng (top 10 đơn nhiều nhất)")
ax.set_ylabel("Tỷ lệ giao trễ (%)")
save_fig(fig, "Hinh_4.3.1_TyLeGiaoTreTheoBang.png")

df = run("analysis_delivery_late_rate_by_seller.sql")
save_table(df, "Bang_4.3.2_TopSellerGiaoTre.csv")

df = run("analysis_delivery_review_by_ontime.sql")
save_table(df, "Bang_4.3.3_DiemDanhGia_DungHan_vs_Tre.csv")
fig, ax = plt.subplots(figsize=(5, 4.5))
ax.bar(df["nhom_giao_hang"], df["avg_review_score"], color=["#16a34a", "#dc2626"])
ax.set_ylim(0, 5)
ax.set_title("Điểm đánh giá trung bình: đúng hạn vs trễ")
ax.set_ylabel("Điểm đánh giá (1-5)")
save_fig(fig, "Hinh_4.3.2_DiemDanhGia_DungHan_vs_Tre.png")

# ------------------------------------------------------------- 4.4 Customer
df = run("analysis_customer_repeat_rate.sql")
save_table(df, "Bang_4.4.1_TyLeMuaLai.csv")
fig, ax = plt.subplots(figsize=(5, 4.5))
ax.bar(df["nhom_khach_hang"], df["pct_customers"], color=["#2563eb", "#f59e0b"])
ax.set_title("Tỷ lệ khách mua 1 lần vs mua lại")
ax.set_ylabel("% khách hàng")
save_fig(fig, "Hinh_4.4.1_TyLeMuaLai.png")

df = run("analysis_customer_spend_segments.sql")
save_table(df, "Bang_4.4.2_PhanKhucChiTieu.csv")
fig, ax = plt.subplots(figsize=(6, 4.5))
ax.bar(df["spend_quartile"].astype(str), df["pct_revenue"], color="#2563eb")
ax.set_title("% tổng doanh thu theo phân khúc chi tiêu (quartile)")
ax.set_xlabel("Quartile (1 = chi tiêu thấp nhất)")
ax.set_ylabel("% tổng chi tiêu")
save_fig(fig, "Hinh_4.4.2_PhanKhucChiTieu.png")

df = run("analysis_customer_recency.sql")
save_table(df, "Bang_4.4.3_PhanBoRecency.csv")
fig, ax = plt.subplots(figsize=(6, 4.5))
ax.bar(df["nhom_recency"], df["pct_customers"], color="#2563eb")
ax.set_title("Phân bố thời gian từ lần mua gần nhất (recency)")
ax.set_ylabel("% khách hàng")
save_fig(fig, "Hinh_4.4.3_PhanBoRecency.png")

print("\nHoan tat E04.")

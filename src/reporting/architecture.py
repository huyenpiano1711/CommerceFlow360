"""Hình 3.1.1 - Kiến trúc tổng thể Medallion của CommerceFlow 360 (mục 3.1).

Sơ đồ tĩnh nhưng các con số (số bảng, số test) lấy từ kết quả chạy hiện tại khi được truyền vào,
mặc định là kết quả của lần dbt build dùng cho báo cáo (91 test: 70 Silver, 3 Gold, 18 Mart).

Chạy từ thư mục gốc repository:
    python -m src.reporting.architecture
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from src.utils.project import FIGURE_DIR  # noqa: E402

FIGURE_NAME = "Hinh_3.1.1_KienTrucTongThe.png"

LAYERS = [
    # (tiêu đề, dòng mô tả, màu viền, màu nền)
    ("NGUỒN DỮ LIỆU", "9 CSV Olist (Kaggle)\nholidays_brazil.csv\n(thư viện holidays)\n\ndata/raw/ — chỉ đọc", "#64748b", "#f1f5f9"),
    ("BRONZE", "10 bảng bronze_*\ngiữ nguyên chuỗi gốc\n+ _ingested_at,\n_source_file\n+ ingestion_log\nPython + DuckDB", "#a87a4f", "#f5eee6"),
    ("SILVER", "10 model silver_*\nép kiểu, chuẩn hóa,\nkhử trùng\ntheo grain,\ngắn cờ bất thường\ndbt · {silver} test", "#6b7f99", "#edf1f7"),
    ("GOLD", "Star Schema\n5 dim_* + 4 fact_*\nkhóa thay thế,\ngrain theo\ntừng quy trình\ndbt · {gold} test", "#c0a030", "#faf3d9"),
    ("DATA MART", "mart_sales\nmart_delivery\nmart_customer\n\n\ndbt · {mart} test", "#0f766e", "#e6f4f1"),
    ("KHAI THÁC", "4 file Parquet\n(data/exports)\n↓\nDashboard Streamlit\n5 trang\n+ 10 truy vấn KPI", "#7c3aed", "#f3effd"),
]


def draw(silver: int = 70, gold: int = 3, mart: int = 18) -> None:
    fig, ax = plt.subplots(figsize=(17, 6.4))
    ax.set_xlim(0, 1700)
    ax.set_ylim(0, 640)
    ax.axis("off")
    w, h, gap, y0 = 240, 360, 48, 150
    for i, (title, body, edge, face) in enumerate(LAYERS):
        x = 20 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0,rounding_size=14",
                                    linewidth=2.2, edgecolor=edge, facecolor=face))
        ax.text(x + w / 2, y0 + h - 34, title, ha="center", va="center", fontsize=14, weight="bold", color=edge)
        ax.text(x + w / 2, y0 + h / 2 - 20, body.format(silver=silver, gold=gold, mart=mart),
                ha="center", va="center", fontsize=11, linespacing=1.5, color="#1f2937")
        if i < len(LAYERS) - 1:
            ax.add_patch(FancyArrowPatch((x + w + 2, y0 + h / 2), (x + w + gap - 2, y0 + h / 2),
                                         arrowstyle="-|>", mutation_scale=20, color="#334155", linewidth=2))
    # khối điều phối và kiểm thử
    ax.add_patch(FancyBboxPatch((20, 40), 1680, 70, boxstyle="round,pad=0,rounding_size=12",
                                linewidth=1.6, edgecolor="#16a34a", facecolor="#ecfdf3", linestyle="--"))
    ax.text(860, 75, f"Kiểm thử & đối soát tự động (dbt test): {silver + gold + mart} test  ·  "
                     "đối soát số dòng và tổng tiền Bronze → Silver → Gold → Mart  ·  dừng xuất Parquet nếu có test FAIL",
            ha="center", va="center", fontsize=11, color="#14532d")
    ax.text(860, 600, "Một file DuckDB duy nhất (commerceflow.duckdb, schema main)  ·  "
                      "chạy lại toàn bộ bằng 3 lệnh: load_bronze.py → export_parquet.py → run_e04_analytics.py",
            ha="center", va="center", fontsize=11.5, color="#334155", style="italic")
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_DIR / FIGURE_NAME, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("Hinh:", FIGURE_NAME)


if __name__ == "__main__":
    draw()

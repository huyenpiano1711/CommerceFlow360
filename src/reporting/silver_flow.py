"""Hình 3.4.1 - Luồng xử lý Bronze -> Silver (Task C02-C03, Duy Lê).

Vẽ sơ đồ 10 bảng bronze_* -> silver_*, các macro làm sạch và số kiểm thử Silver. Số test
lấy từ kết quả dbt test của lần chạy hiện tại (không gõ tay), gọi từ notebooks/03_Silver_Transformation.ipynb.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from src.utils.project import FIGURE_DIR

FIGURE_NAME = "Hinh_3.4.1_LuongXuLySilver.png"

# (bảng gốc, grain Silver) theo thứ tự hiển thị
TABLES = [
    ("orders", "order_id"),
    ("order_items", "order_id + order_item_id"),
    ("order_payments", "order_id + payment_sequential"),
    ("order_reviews", "review_id + order_id"),
    ("customers", "customer_id"),
    ("sellers", "seller_id"),
    ("product_category_name_translation", "product_category_name"),
    ("products", "product_id"),
    ("geolocation", "geolocation_zip_code_prefix"),
    ("holidays", "holiday_date"),
]
# Khối macro nằm giữa hai tầng; mọi bảng đều đi qua khối này (mọi model silver_* dùng macro làm sạch)
MACRO_BOX = (612, 463, 308, 329)  # x, y, rộng, cao

MACROS = ("dbt macros\n\nclean_text\nclean_id · clean_code\nclean_state · clean_zip\n"
          "clean_timestamp\nclean_money · clean_int\nclean_city\n\nkhử trùng theo grain")


def _box(ax, x, y, w, h, edge, face="white", lw=2.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=8",
                                linewidth=lw, edgecolor=edge, facecolor=face))


def _arrow(ax, start, end, color="#777777", **kw):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=14,
                                 color=color, linewidth=1.5, **kw))


def draw_silver_flow(total: int, passed: int, warned: int, show: bool = False):
    """Vẽ và lưu Hình 3.4.1; total/passed/warned là số test Silver của lần chạy hiện tại."""
    # rc_context: font serif chỉ áp dụng cho hình này, không đổi font các hình vẽ sau trong cùng notebook
    with plt.rc_context({"font.family": "serif"}):
        fig = _draw(total, passed, warned)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_DIR / FIGURE_NAME, dpi=100, bbox_inches="tight", facecolor="white")
    if show:
        plt.show()
    plt.close(fig)
    print("Hinh:", FIGURE_NAME)


def _draw(total: int, passed: int, warned: int):
    fig, ax = plt.subplots(figsize=(20.5, 12))
    ax.set_xlim(0, 2055)
    ax.set_ylim(1200, 40)
    ax.axis("off")

    bronze_c, silver_c = "#a87a4f", "#6b7f99"
    _box(ax, 30, 57, 550, 1121, bronze_c, "#f5eee6")
    _box(ax, 952, 57, 654, 1121, silver_c, "#edf1f7")
    ax.text(305, 85, "TẦNG BRONZE", ha="center", va="center", fontsize=19, weight="bold")
    ax.text(305, 128, "dữ liệu thô, nạp nguyên trạng", ha="center", va="center", fontsize=14, style="italic")
    ax.text(1279, 85, "TẦNG SILVER", ha="center", va="center", fontsize=19, weight="bold")
    ax.text(1279, 128, "đã làm sạch, giữ nguyên grain", ha="center", va="center", fontsize=14, style="italic")

    mx, my, mw, mh = MACRO_BOX
    _box(ax, mx, my, mw, mh, "#999999")
    ax.text(766, 627, MACROS, ha="center", va="center", fontsize=12.5, linespacing=1.25)

    row_h, step, top = 66, 95.5, 157
    for i, (name, grain) in enumerate(TABLES):
        y = top + i * step
        mid = y + row_h / 2
        _box(ax, 62, y, 488, row_h, bronze_c)
        size = 14 if len(name) < 20 else 11
        ax.text(306, mid, f"bronze_{name}", ha="center", va="center", fontsize=size)
        _box(ax, 982, y, 594, row_h, silver_c)
        ax.text(1279, mid - 11, f"silver_{name}", ha="center", va="center", fontsize=size, weight="bold")
        ax.text(1279, mid + 15, f"grain: {grain}", ha="center", va="center", fontsize=11, color="#555555")
        # Bronze -> cạnh trái khối macro, cạnh phải khối macro -> Silver (cùng cao độ nếu nằm trong khối)
        port = min(max(mid, my + 15), my + mh - 15)
        ax.plot([550, mx], [mid, port], color="#777777", linewidth=1.2)
        _arrow(ax, (mx + mw, port), (980, mid))

    # silver_product_category_name_translation -> silver_products
    y_tr, y_pr = top + 6 * step + row_h / 2, top + 7 * step + row_h / 2
    _arrow(ax, (1576, y_tr), (1578, y_pr), color="#2f5b8a", connectionstyle="arc3,rad=-0.6")
    ax.text(1622, (y_tr + y_pr) / 2, "bổ sung\nbản dịch", ha="left", va="center", fontsize=12, color="#2f5b8a")

    _box(ax, 1698, 392, 270, 136, "#5b8c5a", "#eaf3ea")
    ax.text(1833, 460, f"dbt test\n{total} kiểm thử\n({passed} PASS, {warned} WARN)",
            ha="center", va="center", fontsize=13.5, linespacing=1.3)
    _box(ax, 1698, 656, 270, 136, "#c0a030", "#faf3d9")
    ax.text(1833, 724, "Tầng Gold\ndim_* / fact_*\n→ mart_*", ha="center", va="center", fontsize=14, linespacing=1.3)
    _arrow(ax, (1606, 460), (1696, 460), color="#444444")
    _arrow(ax, (1833, 530), (1833, 654), color="#444444")
    return fig

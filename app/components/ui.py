"""F01 - Thành phần giao diện dùng chung cho dashboard (Task F01, Phương Anh).

Gồm: cấu hình trang, bộ lọc chung ở thanh bên (giữ nguyên khi đổi trang), định dạng số theo
kiểu Việt Nam, bảng màu thống nhất với biểu đồ trong báo cáo (Hình 4.2-4.4).
"""
from __future__ import annotations

import inspect
import math

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from services.data_loader import (
    FULL_MONTH_END, FULL_MONTH_START, MissingExportError, Filters, category_options,
    check_exports, month_options, state_options,
)

# Streamlit mới đổi use_container_width=True thành width="stretch"; chọn đúng tham số theo phiên bản đang cài
STRETCH = ({"width": "stretch"} if "width" in inspect.signature(st.plotly_chart).parameters
           else {"use_container_width": True})

# Bảng màu trùng với src/reporting/kpi_report.py để dashboard và báo cáo nhìn thống nhất
BLUE, RED, GREEN, AMBER, GREY = "#2563eb", "#dc2626", "#16a34a", "#f59e0b", "#64748b"

pio.templates["commerceflow"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Source Sans Pro, Segoe UI, Arial, sans-serif", size=13),
        colorway=[BLUE, AMBER, GREEN, RED, GREY],
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(font=dict(size=15), x=0, xanchor="left"),
        hoverlabel=dict(font_size=12),
        xaxis=dict(showgrid=False, linecolor="#cbd5e1"),
        yaxis=dict(gridcolor="#e2e8f0", zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
)
pio.templates.default = "plotly_white+commerceflow"


# ---------------------------------------------------------------- định dạng số kiểu VN
def _vn(text: str) -> str:
    """1,234,567.89 -> 1.234.567,89"""
    return text.replace(",", "§").replace(".", ",").replace("§", ".")


def fmt_int(x: float) -> str:
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else _vn(f"{x:,.0f}")


def fmt_num(x: float, digits: int = 2) -> str:
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else _vn(f"{x:,.{digits}f}")


def fmt_money(x: float, digits: int = 2) -> str:
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else "R$ " + _vn(f"{x:,.{digits}f}")


def fmt_money_short(x: float) -> str:
    """Rút gọn theo kiểu báo cáo: R$ 1,00 triệu / R$ 120 nghìn."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if abs(x) >= 1e6:
        return "R$ " + _vn(f"{x / 1e6:,.2f}") + " triệu"
    if abs(x) >= 1e3:
        return "R$ " + _vn(f"{x / 1e3:,.0f}") + " nghìn"
    return fmt_money(x)


def fmt_pct(x: float, digits: int = 2) -> str:
    """x là tỷ lệ 0-1."""
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else _vn(f"{100 * x:,.{digits}f}") + "%"


def fmt_pct_points(x: float, digits: int = 2) -> str:
    """x đã là phần trăm 0-100."""
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else _vn(f"{x:,.{digits}f}") + "%"


# ------------------------------------------------------------------ cấu hình trang
def setup_page(title: str, icon: str = "📦") -> None:
    st.set_page_config(page_title=f"{title} | CommerceFlow 360", page_icon=icon, layout="wide")
    st.markdown(
        """
        <style>
        [data-testid="stMetric"] {background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;}
        [data-testid="stMetricLabel"] p {font-size:0.85rem;color:#475569;}
        .block-container {padding-top:2.2rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    try:
        check_exports()
    except MissingExportError as exc:
        st.error(str(exc))
        st.stop()


def page_header(title: str, caption: str) -> None:
    st.title(title)
    st.caption(caption)


# ------------------------------------------------------------------ bộ lọc chung
def _saved(key: str, default):
    return st.session_state.get(f"_saved_{key}", default)


def _save(key: str, value) -> None:
    st.session_state[f"_saved_{key}"] = value


def sidebar_filters(*, use_category: bool = True, use_state: bool = True) -> Filters:
    """Bộ lọc chung (thời gian, bang, danh mục) ở thanh bên.

    Giá trị được lưu trong session_state nên giữ nguyên khi chuyển trang. Trang nào không dùng một bộ lọc
    (vd. Delivery không có danh mục) thì truyền use_*=False để ẩn và hiển thị chú thích thay vì lọc ngầm.
    """
    months = month_options()
    states = state_options()
    categories = category_options()

    st.sidebar.header("Bộ lọc chung")

    full_only = st.sidebar.checkbox(
        f"Chỉ các tháng đầy đủ ({FULL_MONTH_START} → {FULL_MONTH_END})",
        value=_saved("full_only", False),
        help="09–12/2016 là giai đoạn khởi động (ít đơn) và 09/2018 bị cắt tại thời điểm trích xuất dữ liệu "
             "(chỉ 1 đơn). Bật để loại các tháng này khỏi so sánh theo tháng.",
    )
    _save("full_only", full_only)

    saved_range = _saved("range", (months[0], months[-1]))
    saved_range = tuple(m for m in saved_range)
    if saved_range[0] not in months or saved_range[1] not in months:
        saved_range = (months[0], months[-1])
    start, end = st.sidebar.select_slider("Khoảng thời gian (tháng đặt hàng)", options=months, value=saved_range)
    _save("range", (start, end))
    if full_only:
        start, end = max(start, FULL_MONTH_START), min(end, FULL_MONTH_END)

    chosen_states: tuple[str, ...] = ()
    if use_state:
        chosen_states = tuple(st.sidebar.multiselect(
            "Bang khách hàng", states, default=[s for s in _saved("states", []) if s in states],
            placeholder="Tất cả bang"))
        _save("states", list(chosen_states))

    chosen_cats: tuple[str, ...] = ()
    if use_category:
        chosen_cats = tuple(st.sidebar.multiselect(
            "Danh mục sản phẩm", categories, default=[c for c in _saved("cats", []) if c in categories],
            placeholder="Tất cả danh mục"))
        _save("cats", list(chosen_cats))
    else:
        st.sidebar.caption("Bộ lọc danh mục không áp dụng cho trang này (mart không có chiều danh mục).")

    st.sidebar.divider()
    st.sidebar.caption("Nguồn: data/exports/*.parquet (Data Mart). Doanh thu = giá sản phẩm (price) của đơn hợp lệ, "
                       "không gồm phí vận chuyển.")
    return Filters(start_month=start, end_month=end, states=chosen_states, categories=chosen_cats)


def filter_summary(f: Filters, *, use_category: bool = True) -> str:
    parts = [f"Tháng {f.start_month} → {f.end_month}"]
    parts.append(f"{len(f.states)} bang" if f.states else "tất cả bang")
    if use_category:
        parts.append(f"{len(f.categories)} danh mục" if f.categories else "tất cả danh mục")
    return "Đang lọc: " + " · ".join(parts)


def empty_guard(df, message: str = "Không có dữ liệu khớp bộ lọc hiện tại. Hãy nới rộng bộ lọc ở thanh bên.") -> None:
    if len(df) == 0:
        st.warning(message)
        st.stop()


def style_fig(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(height=height)
    return fig

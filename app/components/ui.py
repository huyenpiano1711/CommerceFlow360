"""F01 - Thành phần giao diện dùng chung cho dashboard (Task F01, Phương Anh).

Gồm: cấu hình trang, bộ lọc chung ở thanh bên (giữ nguyên khi đổi trang), định dạng số theo
kiểu Việt Nam, bảng màu thống nhất với biểu đồ trong báo cáo (Hình 4.2-4.4).
"""
from __future__ import annotations

import inspect
import html
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

# Bảng màu teal - coral - gold, dùng nhất quán cho toàn bộ dashboard
BLUE, RED, GREEN, AMBER, GREY = "#0f766e", "#e76f51", "#16845b", "#d99b22", "#64748b"

pio.templates["commerceflow"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Source Sans Pro, Segoe UI, Arial, sans-serif", size=13),
        colorway=[BLUE, AMBER, GREEN, RED, GREY],
        margin=dict(l=18, r=18, t=54, b=18),
        title=dict(font=dict(size=15, color="#183b3a"), x=0, xanchor="left"),
        hoverlabel=dict(font_size=12, bgcolor="#173f3e", bordercolor="#173f3e", font=dict(color="#ffffff")),
        xaxis=dict(showgrid=False, linecolor="#dbe5e3", tickfont=dict(color="#526466")),
        yaxis=dict(gridcolor="#e8efed", zeroline=False, tickfont=dict(color="#526466")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#526466")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
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


def vn_axis_ticks(values, digits: int = 0) -> dict:
    """Create readable Vietnamese-formatted Plotly ticks for non-negative measures."""
    numbers = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    maximum = max(numbers, default=0)
    if maximum <= 0:
        return {}
    ticks = [maximum * step / 4 for step in range(5)]
    return {
        "tickmode": "array",
        "tickvals": ticks,
        "ticktext": [fmt_num(value, digits) for value in ticks],
    }


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
        :root {
            --cf-accent:#0f766e;
            --cf-accent-soft:rgba(15,118,110,.09);
            --cf-border:rgba(100,116,139,.20);
            --cf-shadow:0 8px 22px rgba(27,62,59,.055);
            --cf-ink:#183b3a;
            --cf-muted:#607674;
        }
        .stApp {
            background:
                radial-gradient(ellipse at 85% 0%, rgba(15,118,110,.055), transparent 34rem),
                var(--background-color, #f6f9f8);
            color:var(--text-color, #183b3a);
        }
        [data-testid="stAppViewContainer"] .main {background:transparent;}
        .block-container {max-width:1480px;padding:2.4rem 2.6rem 4rem;}
        h1 {letter-spacing:-.035em;font-weight:750;}
        h2, h3 {letter-spacing:-.02em;}
        .cf-hero {
            position:relative;
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:2rem;
            overflow:hidden;
            margin:0 0 1.8rem;
            padding:2rem 2.2rem;
            border:1px solid rgba(255,255,255,.14);
            border-radius:22px;
            color:#f4fbf8;
            background:linear-gradient(118deg,#123f3d 0%,#0f766e 60%,#239184 100%);
            box-shadow:0 16px 38px rgba(15,75,69,.20);
        }
        .cf-hero:after {
            content:"";
            position:absolute;
            width:310px;height:310px;
            right:-80px;top:-180px;
            border:1px solid rgba(255,255,255,.16);
            border-radius:50%;
            box-shadow:0 0 0 28px rgba(255,255,255,.035),0 0 0 58px rgba(255,255,255,.025);
            pointer-events:none;
        }
        .cf-hero-copy {position:relative;z-index:1;max-width:860px;}
        .cf-hero-eyebrow {
            display:inline-flex;
            align-items:center;
            gap:.45rem;
            margin-bottom:.72rem;
            color:#bfe8df;
            font-size:.70rem;
            font-weight:750;
            letter-spacing:.16em;
            text-transform:uppercase;
        }
        .cf-hero-eyebrow:before {
            content:"";
            width:7px;height:7px;border-radius:50%;
            background:#e9bd64;
            box-shadow:0 0 12px rgba(233,189,100,.8);
        }
        .cf-hero h1 {
            margin:0 0 .58rem;
            color:#fff;
            font-size:clamp(1.7rem,3vw,2.5rem);
            line-height:1.12;
            letter-spacing:-.045em;
        }
        .cf-hero p {margin:0;color:#d9eeea;font-size:.98rem;line-height:1.65;max-width:780px;}
        .cf-hero-mark {
            position:relative;z-index:1;
            display:flex;align-items:baseline;gap:.12rem;
            padding:.3rem .6rem;
            color:rgba(255,255,255,.20);
            font-size:4.7rem;font-weight:800;letter-spacing:-.09em;line-height:1;
            user-select:none;
        }
        .cf-hero-mark span {color:#e9bd64;font-size:1.4rem;letter-spacing:.03em;}
        [data-testid="stSidebar"] {
            background:var(--secondary-background-color, #eef4f2);
            border-right:1px solid var(--cf-border);
        }
        [data-testid="stSidebar"] h2 {color:var(--text-color, #183b3a);}
        [data-testid="stMetric"] {
            background:var(--secondary-background-color, #ffffff);
            color:var(--text-color, #183b3a);
            border:1px solid var(--cf-border);
            border-left:3px solid var(--cf-accent);
            border-radius:14px;
            padding:16px 18px;
            box-shadow:var(--cf-shadow);
            transition:transform .16s ease, box-shadow .16s ease;
        }
        [data-testid="stMetric"]:hover {transform:translateY(-2px);box-shadow:0 12px 26px rgba(27,62,59,.11);}
        [data-testid="stMetricLabel"] p {font-size:.82rem;font-weight:600;color:var(--text-color, #526466);opacity:.78;}
        [data-testid="stMetricValue"], [data-testid="stMetricValue"] div {
            color:var(--text-color, #183b3a)!important;
            font-weight:750;
            letter-spacing:-.035em;
        }
        [data-testid="stMetricDelta"] {font-weight:600;}
        [data-testid="stHorizontalBlock"] [data-testid="stMetric"] {height:100%;min-height:112px;}
        [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
            border:1px solid var(--cf-border);
            border-radius:14px;
            overflow:hidden;
            box-shadow:var(--cf-shadow);
        }
        [data-testid="stDataFrame"] {background:var(--secondary-background-color, #ffffff);}
        [data-testid="stAlert"] {border-radius:12px;}
        [data-testid="stCaptionContainer"] {color:var(--text-color, #526466);opacity:.82;}
        [data-testid="stExpander"] {
            border:1px solid var(--cf-border);
            border-radius:12px;
            background:var(--secondary-background-color, #ffffff);
        }
        [data-testid="stRadio"] label[data-baseweb="radio"] {gap:.45rem;}
        [data-testid="stRadio"] [data-baseweb="radio"] > div:first-child {
            border-color:var(--cf-accent);
        }
        [data-testid="stCheckbox"] label {font-weight:600;}
        [data-testid="stSelectSlider"] [role="slider"] {background:var(--cf-accent);}
        button[kind="primary"] {background:var(--cf-accent);border-color:var(--cf-accent);}
        input[type="checkbox"] {accent-color:var(--cf-accent);}
        hr {border-color:var(--cf-border);}
        @media (max-width: 800px) {
            .block-container {padding:1.4rem 1rem 3rem;}
            [data-testid="stMetric"] {padding:12px 14px;border-radius:11px;}
            .cf-hero {padding:1.45rem 1.35rem;border-radius:17px;}
            .cf-hero-mark {display:none;}
        }
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
    safe_title = html.escape(title)
    safe_caption = html.escape(caption)
    st.markdown(
        f"""
        <header class="cf-hero">
            <div class="cf-hero-copy">
                <div class="cf-hero-eyebrow">CommerceFlow 360 · Data intelligence</div>
                <h1>{safe_title}</h1>
                <p>{safe_caption}</p>
            </div>
            <div class="cf-hero-mark" aria-hidden="true">360<span>°</span></div>
        </header>
        """,
        unsafe_allow_html=True,
    )


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
        value=_saved("full_only", True),
        help="Bật để loại các tháng đầu/cuối có thể chưa đầy đủ khỏi so sánh theo tháng.",
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

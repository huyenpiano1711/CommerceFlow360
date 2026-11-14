"""F01 - Thành phần giao diện dùng chung cho dashboard (Task F01, Phương Anh).

Gồm: cấu hình trang, bộ lọc chung ở thanh bên (giữ nguyên khi đổi trang), định dạng số theo
kiểu Việt Nam, bảng màu xanh dương, thẻ KPI có biểu tượng, nút tải CSV.
Theme nền (sáng, thanh bên xanh đậm) đặt ở .streamlit/config.toml.
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

# Bảng màu xanh dương (đồng bộ với slide báo cáo), dùng nhất quán cho toàn bộ dashboard
BLUE, RED, GREEN, AMBER, GREY = "#1f5eea", "#ef5d4e", "#16a34a", "#f5a524", "#64748b"
SKY, NAVY, LIGHT = "#7fb2ff", "#0b2a6b", "#cfe0ff"

pio.templates["commerceflow"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Be Vietnam Pro, Segoe UI, Arial, sans-serif", size=13, color="#334766"),
        colorway=[BLUE, AMBER, GREEN, RED, GREY],
        margin=dict(l=18, r=18, t=54, b=18),
        title=dict(font=dict(size=15, color="#0f2350"), x=0, xanchor="left"),
        hoverlabel=dict(font_size=12, bgcolor="#0b2a6b", bordercolor="#0b2a6b", font=dict(color="#ffffff")),
        xaxis=dict(showgrid=False, linecolor="#d6e3f8", tickfont=dict(color="#51607a")),
        yaxis=dict(gridcolor="#e9f0fb", zeroline=False, tickfont=dict(color="#51607a")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#51607a")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        # Dấu thập phân "," và dấu nghìn "." cho trục/nhãn số, thống nhất với fmt_* bên dưới
        separators=",.",
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


def vn_axis_ticks(values=None, digits: int = 0) -> dict:
    """Định dạng trục số kiểu VN; để Plotly tự chọn vạch tròn (0, 250.000, 500.000...).

    Trước đây vạch được chia đều từ giá trị lớn nhất nên ra số lẻ (752.897, 9,1...).
    Tham số values giữ lại để không phải sửa nơi gọi.
    """
    return {"tickformat": f",.{digits}f"}


def fmt_pct(x: float, digits: int = 2) -> str:
    """x là tỷ lệ 0-1."""
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else _vn(f"{100 * x:,.{digits}f}") + "%"


def fmt_pct_points(x: float, digits: int = 2) -> str:
    """x đã là phần trăm 0-100."""
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else _vn(f"{x:,.{digits}f}") + "%"


# ------------------------------------------------------------------ biểu tượng (SVG nét mảnh, không cần thư viện ngoài)
_ICON_PATHS = {
    "money": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/><path d="M6 12h.01M18 12h.01"/>',
    "cart": '<circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/>',
    "receipt": '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8M12 17.5v-11"/>',
    "box": '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5M12 22V12"/>',
    "truck": '<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2M15 18H9M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.62L18.3 9.38a1 1 0 0 0-.78-.38H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "star": '<path d="M11.5 2.3a.5.5 0 0 1 1 0l2.3 4.7a2 2 0 0 0 1.5 1.1l5.2.8a.5.5 0 0 1 .3.9l-3.8 3.7a2 2 0 0 0-.6 1.8l.9 5.2a.5.5 0 0 1-.8.6l-4.6-2.5a2 2 0 0 0-1.9 0l-4.6 2.5a.5.5 0 0 1-.8-.6l.9-5.2a2 2 0 0 0-.6-1.8L1.2 9.8a.5.5 0 0 1 .3-.9l5.2-.8a2 2 0 0 0 1.5-1.1Z"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "repeat": '<path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14M7 22l-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/>',
    "percent": '<path d="M19 5 5 19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
    "check": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4M12 17h.01"/>',
    "x": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6M9 9l6 6"/>',
    "layers": '<path d="m12.83 2.18 8.58 3.9a1 1 0 0 1 0 1.83l-8.58 3.9a2 2 0 0 1-1.66 0L2.6 7.9a1 1 0 0 1 0-1.83l8.58-3.9a2 2 0 0 1 1.66 0Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65M22 12.65l-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
    "chart": '<path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M18 17V9M13 17V5M8 17v-3"/>',
    "map": '<path d="M20 10c0 4.99-5.54 10.19-7.4 11.8a1 1 0 0 1-1.2 0C9.54 20.19 4 14.99 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    "download": '<path d="M12 15V3M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/>',
}

# Gợi ý biểu tượng theo nội dung nhãn, để mọi thẻ KPI có biểu tượng mà không phải khai báo từng chỗ
_ICON_RULES = [
    ("fail", "x"), ("error", "x"), ("warn", "alert"), ("pass", "check"), ("test", "check"),
    ("trễ", "truck"), ("giao", "truck"), ("ngày", "clock"), ("recency", "clock"), ("đánh giá", "star"), ("review", "star"),
    ("mua lại", "repeat"), ("tỷ lệ", "percent"), ("khách", "users"), ("người bán", "users"),
    ("vận chuyển", "truck"), ("dòng hàng", "box"), ("chi tiêu", "money"), ("doanh thu", "money"), ("aov", "receipt"),
    ("đơn", "cart"), ("bang", "map"), ("dòng", "layers"),
]
_TONES = {"blue": ("#1f5eea", "#4d9bff"), "green": ("#16a34a", "#4ade80"), "amber": ("#f59e0b", "#fbbf24"),
          "red": ("#ef4444", "#f87171"), "navy": ("#0b2a6b", "#1f5eea")}


def icon_svg(name: str, size: int = 22, color: str = "#ffffff") -> str:
    body = _ICON_PATHS.get(name, _ICON_PATHS["chart"])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>')


def _auto_icon(label: str) -> str:
    low = label.lower()
    return next((icon for key, icon in _ICON_RULES if key in low), "chart")


def _auto_tone(label: str) -> str:
    low = label.lower()
    if "fail" in low or "error" in low:
        return "red"
    if "warn" in low or "trễ" in low:
        return "amber"
    if "pass" in low:
        return "green"
    return "blue"


def kpi(target, label: str, value: str, help: str | None = None, icon: str | None = None,
        tone: str | None = None, note: str | None = None) -> None:
    """Thẻ KPI có biểu tượng, thay cho st.metric (cùng thứ tự tham số: nhãn, giá trị, help)."""
    c1, c2 = _TONES.get(tone or _auto_tone(label), _TONES["blue"])
    tip = f' title="{html.escape(help)}"' if help else ""
    info = '<span class="cf-kpi-info">i</span>' if help else ""
    sub = f'<div class="cf-kpi-note">{html.escape(note)}</div>' if note else ""
    target.markdown(
        f'<div class="cf-kpi"{tip}>'
        f'<div class="cf-kpi-icon" style="background:linear-gradient(135deg,{c2},{c1})">{icon_svg(icon or _auto_icon(label))}</div>'
        f'<div class="cf-kpi-body"><div class="cf-kpi-label">{html.escape(label)}{info}</div>'
        f'<div class="cf-kpi-value">{html.escape(str(value))}</div>{sub}</div></div>',
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str | None = None, icon: str | None = None) -> None:
    """Tiêu đề mục: biểu tượng tròn + tiêu đề + mô tả ngắn."""
    sub = f'<p>{html.escape(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f'<div class="cf-sec"><div class="cf-sec-icon">{icon_svg(icon or _auto_icon(title), 18)}</div>'
        f'<div><h3>{html.escape(title)}</h3>{sub}</div></div>',
        unsafe_allow_html=True,
    )


def download_csv(df, filename: str, label: str = "Tải dữ liệu đang xem (CSV)", key: str | None = None) -> None:
    """Nút tải bảng đang hiển thị (đã áp bộ lọc) ra CSV, mở được bằng Excel (UTF-8 có BOM)."""
    data = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(f"⬇  {label}", data=data, file_name=filename, mime="text/csv", key=key or f"dl_{filename}")


def sidebar_brand() -> None:
    st.sidebar.markdown(
        f'<div class="cf-brand"><div class="cf-brand-logo">{icon_svg("database", 22)}</div>'
        '<div><div class="cf-brand-name">CommerceFlow 360</div>'
        '<div class="cf-brand-sub">Data Warehouse · Nhóm 08</div></div></div>',
        unsafe_allow_html=True,
    )


# Cụm tòa nhà kính vẽ bằng SVG cho băng tiêu đề (không dùng ảnh ngoài)
def _skyline() -> str:
    spec = [(0, 34, 70), (40, 46, 108), (92, 56, 150), (154, 40, 96), (200, 34, 124), (240, 30, 64)]
    parts = []
    for x, w, h in spec:
        y = 160 - h
        rows = "".join(f"M{x},{yy}h{w}" for yy in range(y + 12, 160, 12))
        cols = "".join(f"M{x + w * k // 4},{y}v{h}" for k in (1, 2, 3))
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="url(#cfg)"/>'
                     f'<path d="{rows}{cols}" stroke="#ffffff" stroke-opacity=".25" stroke-width="1"/>')
    return ('<svg class="cf-hero-art" viewBox="0 0 270 160" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            '<defs><linearGradient id="cfg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity=".55"/>'
            '<stop offset="1" stop-color="#ffffff" stop-opacity=".08"/></linearGradient></defs>' + "".join(parts) + "</svg>")


# ------------------------------------------------------------------ cấu hình trang
def setup_page(title: str, icon: str = "📦") -> None:
    st.set_page_config(page_title=f"{title} | CommerceFlow 360", page_icon=icon, layout="wide")
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        :root {
            --cf-blue:#1f5eea; --cf-deep:#0b3ba8; --cf-navy:#0b2a6b; --cf-sky:#4d9bff; --cf-gold:#ffc857;
            --cf-ink:#0f2350; --cf-muted:#51607a; --cf-card:#ffffff; --cf-border:#dfe8f8;
            --cf-shadow:0 2px 6px rgba(15,35,80,.05), 0 14px 34px rgba(31,94,234,.10);
            --cf-radius:20px;
        }
        html, body, .stApp, p, li, label, input, textarea, select, button, h1, h2, h3, h4,
        [data-testid="stMarkdownContainer"], [data-baseweb="tag"] span, [data-testid="stSidebarNav"] span {
            font-family:"Be Vietnam Pro", "Segoe UI", Arial, sans-serif;
        }
        .stApp {
            background-color:#f3f7ff;
            background-image:
                radial-gradient(ellipse 55rem 26rem at 100% -8%, rgba(77,155,255,.20), transparent 70%),
                radial-gradient(ellipse 40rem 26rem at -8% 108%, rgba(140,120,255,.12), transparent 70%),
                radial-gradient(rgba(31,94,234,.08) 1px, transparent 1px);
            background-size:auto, auto, 24px 24px;
            background-attachment:fixed;
            color:var(--cf-ink);
        }
        [data-testid="stHeader"] {background:transparent;}
        .block-container {max-width:1480px;padding:1.8rem 2.6rem 4rem;}
        h1, h2, h3 {color:var(--cf-ink);letter-spacing:-.02em;}
        /* st.subheader cũ: thêm chấm tròn nhấn thay vì vạch thẳng */
        [data-testid="stHeadingWithActionElements"] h3 {display:flex;align-items:center;gap:.65rem;margin-top:.8rem;font-weight:750;}
        [data-testid="stHeadingWithActionElements"] h3:before {
            content:"";flex:0 0 auto;width:14px;height:14px;border-radius:50%;
            background:linear-gradient(135deg,var(--cf-sky),var(--cf-blue));box-shadow:0 0 0 5px rgba(31,94,234,.12);
        }
        /* ---------- băng tiêu đề */
        .cf-hero {
            position:relative;display:flex;align-items:flex-end;justify-content:space-between;gap:2rem;overflow:hidden;
            margin:0 0 1.5rem;padding:2rem 2.3rem 1.9rem;border-radius:26px;color:#fff;
            background:
                radial-gradient(circle at 85% 0%, rgba(255,255,255,.22), transparent 16rem),
                linear-gradient(120deg,#0b2a6b 0%,#1f5eea 55%,#4d9bff 100%);
            box-shadow:0 22px 46px rgba(31,94,234,.28);
        }
        .cf-hero:before {
            content:"";position:absolute;width:420px;height:420px;left:-140px;bottom:-300px;border-radius:50%;
            border:1px solid rgba(255,255,255,.18);box-shadow:0 0 0 36px rgba(255,255,255,.04),0 0 0 72px rgba(255,255,255,.03);
        }
        .cf-hero-copy {position:relative;z-index:1;max-width:900px;}
        .cf-hero-eyebrow {
            display:inline-flex;align-items:center;gap:.5rem;margin-bottom:.8rem;padding:.32rem .8rem;border-radius:999px;
            background:rgba(255,255,255,.16);color:#e6efff;font-size:.72rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
        }
        .cf-hero-eyebrow:before {content:"";width:7px;height:7px;border-radius:50%;background:var(--cf-gold);box-shadow:0 0 10px var(--cf-gold);}
        .cf-hero h1 {margin:0 0 .5rem;color:#fff!important;font-size:clamp(1.7rem,3vw,2.55rem);font-weight:800;line-height:1.1;letter-spacing:-.04em;}
        .cf-hero p {margin:0;color:#dbe7ff;font-size:1rem;line-height:1.6;max-width:820px;}
        .cf-hero-chips {display:flex;flex-wrap:wrap;gap:.5rem;margin-top:1rem;}
        .cf-hero-chips span {padding:.3rem .75rem;border-radius:999px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);
            color:#fff;font-size:.78rem;font-weight:600;}
        .cf-hero-art {position:relative;z-index:1;width:260px;flex:0 0 auto;margin-bottom:-1.95rem;opacity:.95;}
        /* ---------- tiêu đề mục */
        .cf-sec [data-testid="stHeadingWithActionElements"] h3:before, .cf-sec h3:before {display:none!important;content:none!important;}
        .cf-sec [data-testid="stHeaderActionElements"] {display:none;}
        /* ---------- nút điều hướng nhanh (st.page_link) */
        [data-testid="stPageLink"] a {background:#fff;border:1px solid var(--cf-border);border-radius:16px;padding:.55rem .8rem;
            box-shadow:var(--cf-shadow);justify-content:center;transition:transform .15s ease;}
        [data-testid="stPageLink"] a:hover {transform:translateY(-2px);border-color:var(--cf-sky);background:#f7faff;}
        [data-testid="stPageLink"] a p {font-weight:700;color:var(--cf-ink);}
        /* tab đang chọn */
        [data-testid="stTabs"] button[role="tab"] {border-radius:999px;padding:.35rem 1rem;margin-right:.3rem;border:1px solid var(--cf-border);background:#fff;}
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {background:var(--cf-blue);border-color:var(--cf-blue);}
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {color:#fff!important;font-weight:700;}
        .cf-sec {display:flex;align-items:center;gap:.8rem;margin:1.6rem 0 .8rem;}
        .cf-sec-icon {width:38px;height:38px;border-radius:12px;display:flex;align-items:center;justify-content:center;
            background:linear-gradient(135deg,var(--cf-sky),var(--cf-blue));box-shadow:0 8px 18px rgba(31,94,234,.25);}
        .cf-sec h3 {margin:0!important;padding:0!important;font-size:1.25rem;font-weight:750;color:var(--cf-ink);}
        .cf-sec p {margin:.1rem 0 0;color:var(--cf-muted);font-size:.86rem;}
        /* ---------- thẻ KPI */
        .cf-kpi {display:flex;flex-direction:column;gap:.55rem;height:100%;min-height:128px;padding:1rem 1.1rem 1.05rem;
            background:var(--cf-card);border:1px solid var(--cf-border);border-radius:var(--cf-radius);box-shadow:var(--cf-shadow);
            transition:transform .16s ease, box-shadow .16s ease;}
        .cf-kpi:hover {transform:translateY(-3px);box-shadow:0 20px 40px rgba(31,94,234,.16);}
        .cf-kpi-icon {flex:0 0 auto;width:44px;height:44px;border-radius:14px;display:flex;align-items:center;justify-content:center;
            box-shadow:0 10px 20px rgba(31,94,234,.22);}
        .cf-kpi-body {min-width:0;}
        .cf-kpi-label {display:flex;align-items:flex-start;gap:.35rem;color:var(--cf-muted);font-size:.8rem;font-weight:600;line-height:1.3;}
        .cf-kpi-info {flex:0 0 auto;display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;border-radius:50%;
            background:#e6efff;color:var(--cf-blue);font-size:.62rem;font-weight:800;cursor:help;margin-top:1px;}
        .cf-kpi-value {color:var(--cf-ink);font-size:clamp(1.15rem,1.55vw,1.65rem);font-weight:800;letter-spacing:-.03em;line-height:1.15;margin-top:.2rem;}
        .cf-kpi-note {color:var(--cf-muted);font-size:.75rem;margin-top:.15rem;}
        /* st.metric (nếu còn dùng) cùng phong cách */
        [data-testid="stMetric"] {background:var(--cf-card);border:1px solid var(--cf-border);border-radius:var(--cf-radius);
            padding:16px 18px;box-shadow:var(--cf-shadow);}
        /* ---------- khung biểu đồ, bảng */
        [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
            background:var(--cf-card);border:1px solid var(--cf-border);border-radius:var(--cf-radius);
            overflow:hidden;box-shadow:var(--cf-shadow);padding:10px 10px 4px;
        }
        [data-testid="stExpander"] {border:1px solid var(--cf-border)!important;border-radius:16px!important;background:var(--cf-card);box-shadow:var(--cf-shadow);}
        [data-testid="stAlert"] {border-radius:14px;}
        [data-testid="stCaptionContainer"] {color:var(--cf-muted);}
        /* radio ngang thành nút chọn dạng viên thuốc */
        [data-testid="stRadio"] [role="radiogroup"] {gap:.4rem;flex-wrap:wrap;}
        [data-testid="stRadio"] [role="radiogroup"] label {background:#fff;border:1px solid var(--cf-border);border-radius:999px;
            padding:.3rem .9rem;box-shadow:0 2px 6px rgba(15,35,80,.04);}
        [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {background:var(--cf-blue);border-color:var(--cf-blue);}
        [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p {color:#fff!important;font-weight:700;}
        [data-testid="stRadio"] [role="radiogroup"] label > div:first-child {display:none;}
        /* tab */
        [data-baseweb="tab-list"] {gap:.4rem;}
        [data-baseweb="tab"] {background:#fff;border-radius:999px!important;padding:.35rem 1rem!important;border:1px solid var(--cf-border);}
        [data-baseweb="tab"][aria-selected="true"] {background:var(--cf-blue);color:#fff;}
        [data-baseweb="tab"][aria-selected="true"] p {color:#fff;}
        [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {display:none;}
        /* nút tải */
        [data-testid="stDownloadButton"] button, .stButton button {border-radius:999px;border:1px solid var(--cf-blue);
            color:var(--cf-blue);background:#fff;font-weight:700;padding:.45rem 1.1rem;}
        [data-testid="stDownloadButton"] button:hover, .stButton button:hover {background:var(--cf-blue);color:#fff;}
        /* ---------- thanh bên */
        [data-testid="stSidebar"] {background:linear-gradient(180deg,#0b2a6b 0%,#0a2257 100%);border-right:none;
            box-shadow:6px 0 24px rgba(11,42,107,.18);}
        [data-testid="stSidebar"] * {color:#e6efff;}
        [data-testid="stSidebarNav"] a {border-radius:12px;margin:2px 6px;}
        [data-testid="stSidebarNav"] a:hover {background:rgba(255,255,255,.08);}
        [data-testid="stSidebarNav"] a[aria-current="page"] {background:linear-gradient(90deg,rgba(77,155,255,.35),rgba(77,155,255,.12));}
        [data-testid="stSidebarNav"] a span {font-weight:600;}
        [data-testid="stSidebar"] [data-baseweb="select"] > div, [data-testid="stSidebar"] input {background:rgba(255,255,255,.08)!important;
            border-color:rgba(255,255,255,.18)!important;}
        [data-testid="stSidebar"] [data-baseweb="tag"] {background:var(--cf-blue)!important;}
        [data-testid="stSidebar"] [data-testid="stAlert"] {background:rgba(255,255,255,.07);border:1px solid rgba(255,200,87,.35);}
        [data-testid="stSidebar"] hr {border-color:rgba(255,255,255,.14);}
        .cf-brand {display:flex;align-items:center;gap:.75rem;margin:.2rem 0 1.1rem;padding:.85rem .9rem;border-radius:18px;
            background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);}
        .cf-brand-logo {width:42px;height:42px;border-radius:14px;display:flex;align-items:center;justify-content:center;
            background:linear-gradient(135deg,#4d9bff,#1f5eea);box-shadow:0 8px 18px rgba(0,0,0,.25);}
        .cf-brand-name {font-weight:800;font-size:1rem;color:#fff;letter-spacing:-.01em;}
        .cf-brand-sub {font-size:.72rem;color:#a9c4f5!important;}
        .cf-side-title {margin:.4rem 0 .4rem;font-size:.72rem!important;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#a9c4f5!important;}
        /* ---------- thẻ thông tin dùng ở trang Pipeline */
        .cf-card {background:var(--cf-card);border:1px solid var(--cf-border);border-radius:var(--cf-radius);box-shadow:var(--cf-shadow);
            padding:1.2rem 1.3rem;height:100%;}
        .cf-card h4 {margin:.2rem 0 .35rem;color:var(--cf-ink);font-weight:750;}
        .cf-card p {margin:0;color:var(--cf-muted);font-size:.9rem;line-height:1.55;}
        .cf-pill {display:inline-block;padding:.2rem .65rem;border-radius:999px;background:#e6efff;color:var(--cf-blue);
            font-size:.72rem;font-weight:700;margin:.15rem .2rem .15rem 0;}
        .cf-flow {display:flex;flex-wrap:wrap;align-items:center;gap:.5rem;margin:.4rem 0 .2rem;}
        .cf-flow span.step {padding:.55rem 1rem;border-radius:999px;color:#fff;font-weight:700;font-size:.9rem;
            background:linear-gradient(135deg,var(--cf-sky),var(--cf-blue));box-shadow:0 8px 18px rgba(31,94,234,.22);}
        .cf-flow span.arrow {color:var(--cf-sky);font-weight:800;font-size:1.2rem;}
        @media (max-width: 900px) {
            .block-container {padding:1.2rem 1rem 3rem;}
            .cf-hero {padding:1.4rem 1.3rem;border-radius:20px;}
            .cf-hero-art {display:none;}
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


def page_header(title: str, caption: str, chips: list[str] | None = None) -> None:
    chips = chips if chips is not None else ["Olist · Brazil 2016–2018", "Medallion · DuckDB · dbt", "91 kiểm thử dữ liệu"]
    chip_html = "".join(f"<span>{html.escape(c)}</span>" for c in chips)
    st.markdown(
        f"""
        <header class="cf-hero">
            <div class="cf-hero-copy">
                <div class="cf-hero-eyebrow">CommerceFlow 360 · Data intelligence</div>
                <h1>{html.escape(title)}</h1>
                <p>{html.escape(caption)}</p>
                <div class="cf-hero-chips">{chip_html}</div>
            </div>
            {_skyline()}
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

    sidebar_brand()
    st.sidebar.markdown('<p class="cf-side-title">Bộ lọc chung</p>', unsafe_allow_html=True)

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
        if start > end:
            st.sidebar.warning("Khoảng thời gian đã chọn nằm hoàn toàn ngoài giai đoạn tháng đầy đủ. "
                               "Tắt “Chỉ các tháng đầy đủ” hoặc chọn lại khoảng thời gian.")

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

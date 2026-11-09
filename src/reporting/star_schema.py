"""Hình 3.5.1 - Sơ đồ Star Schema tầng Gold, sinh trực tiếp từ cấu trúc bảng trong DuckDB.

Đọc danh sách cột của 5 dim_* và 4 fact_* bằng DESCRIBE nên sơ đồ luôn khớp với model dbt đang chạy
(khóa chính in đậm, khóa ngoại *_key nối tới dimension tương ứng). Cần Graphviz (lệnh `dot`).

Chạy từ thư mục gốc repository:
    python -m src.reporting.star_schema
"""
from __future__ import annotations

import html
import shutil
import subprocess

import duckdb

from src.utils.project import DUCKDB_PATH, FIGURE_DIR

FIGURE_NAME = "Hinh_3.5.1_StarSchema.png"
DIMS = ["dim_customer", "dim_product", "dim_seller", "dim_date", "dim_geography"]
FACTS = ["fact_orders", "fact_order_items", "fact_payments", "fact_reviews"]
PRIMARY = {
    "dim_customer": {"customer_key"}, "dim_product": {"product_key"}, "dim_seller": {"seller_key"},
    "dim_date": {"date_key"}, "dim_geography": {"geography_key"},
    "fact_orders": {"order_id"}, "fact_order_items": {"order_id", "order_item_id"},
    "fact_payments": {"order_id", "payment_sequential"}, "fact_reviews": {"review_id", "order_id"},
}
GRAIN = {
    "fact_orders": "1 dòng / đơn hàng", "fact_order_items": "1 dòng / dòng hàng",
    "fact_payments": "1 dòng / dòng thanh toán", "fact_reviews": "1 dòng / (review, đơn)",
}


def _target(column: str) -> str | None:
    if column == "customer_key":
        return "dim_customer"
    if column == "product_key":
        return "dim_product"
    if column == "seller_key":
        return "dim_seller"
    if column.endswith("geography_key"):
        return "dim_geography"
    if column.endswith("date_key"):
        return "dim_date"
    return None


def _table_node(name: str, columns: list[tuple[str, str]], fact: bool) -> str:
    head = "#1e3a5f" if fact else "#0f766e"
    sub = f'<BR/><FONT POINT-SIZE="9">{GRAIN[name]}</FONT>' if fact else ""
    rows = [f'<TR><TD BGCOLOR="{head}" COLSPAN="2"><FONT COLOR="white"><B>{name}</B>{sub}</FONT></TD></TR>']
    for col, typ in columns:
        label = html.escape(col)
        if col in PRIMARY[name]:
            label = f"<B>{label}</B> (PK)"
        elif fact and _target(col):
            label = f"{label} (FK)"
        typ = html.escape(typ.lower().replace("decimal", "dec"))
        rows.append(f'<TR><TD ALIGN="LEFT" PORT="{col}">{label}</TD>'
                    f'<TD ALIGN="RIGHT" PORT="{col}_t"><FONT COLOR="#64748b">{typ}</FONT></TD></TR>')
    return (f'{name} [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" '
            f'BGCOLOR="white" COLOR="{head}">{"".join(rows)}</TABLE>>];')


def build_dot(con: duckdb.DuckDBPyConnection) -> str:
    lines = ["digraph G {", 'graph [rankdir=LR, nodesep=0.25, ranksep=1.6, fontname="DejaVu Sans"];',
             'node [shape=plaintext, fontname="DejaVu Sans", fontsize=10];',
             'edge [color="#94a3b8", arrowhead=crow, arrowtail=tee, dir=both, arrowsize=0.7];']
    columns = {t: [(r[0], r[1]) for r in con.execute(f"describe {t}").fetchall()] for t in DIMS + FACTS}
    lines.append("subgraph cluster_f { style=invis; " + " ".join(_table_node(t, columns[t], True) for t in FACTS) + "}")
    lines.append("subgraph cluster_d { style=invis; " + " ".join(_table_node(t, columns[t], False) for t in DIMS) + "}")
    pk = {"dim_customer": "customer_key", "dim_product": "product_key", "dim_seller": "seller_key",
          "dim_date": "date_key", "dim_geography": "geography_key"}
    for fact in FACTS:
        for col, _ in columns[fact]:
            dim = _target(col)
            if dim:
                lines.append(f"{dim}:{pk[dim]}_t:e -> {fact}:{col}:w;")
    lines.append("}")
    return "\n".join(lines)


def draw() -> None:
    if not shutil.which("dot"):
        raise FileNotFoundError("Cần cài Graphviz (lệnh dot) để vẽ sơ đồ Star Schema.")
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as con:
        dot = build_dot(con)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(["dot", "-Tpng", "-Gdpi=170", "-o", str(FIGURE_DIR / FIGURE_NAME)],
                   input=dot, text=True, check=True)
    print("Hinh:", FIGURE_NAME)


if __name__ == "__main__":
    draw()

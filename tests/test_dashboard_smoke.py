"""Chạy thử (smoke test) 7 trang dashboard bằng streamlit.testing, không cần mở trình duyệt.

Đọc data/exports/*.parquet có sẵn trong repo; bỏ qua nếu máy chưa cài streamlit/plotly.
"""
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP_DIR = Path(__file__).resolve().parents[1] / "app"
PAGES = ["Home.py", "pages/1_Sales.py", "pages/2_Delivery.py", "pages/3_Customer.py", "pages/4_Data_Quality.py",
         "pages/5_Data_Explorer.py", "pages/6_Pipeline.py"]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_error(page: str) -> None:
    at = AppTest.from_file(str(APP_DIR / page), default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]
    # Thẻ KPI là khối HTML class "cf-kpi" (components/ui.py: kpi), không còn dùng st.metric
    assert sum('class="cf-kpi"' in m.value for m in at.markdown) >= 3


def test_category_filter_explains_delivery_scope() -> None:
    at = AppTest.from_file(str(APP_DIR / "Home.py"), default_timeout=120).run()
    at.sidebar.multiselect[1].select(at.sidebar.multiselect[1].options[0]).run()
    assert not at.exception
    assert any("không có chiều danh mục" in c.value for c in at.caption)


def test_range_outside_full_months_warns_instead_of_crashing() -> None:
    at = AppTest.from_file(str(APP_DIR / "pages/1_Sales.py"), default_timeout=120).run()
    months = at.sidebar.select_slider[0].options
    at.sidebar.select_slider[0].set_value((months[0], months[1])).run()  # 2016-09 → 2016-10
    assert not at.exception
    assert any("ngoài giai đoạn tháng đầy đủ" in w.value for w in at.sidebar.warning)


def test_cache_follows_parquet_mtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import os
    import shutil
    import sys

    sys.path.insert(0, str(APP_DIR))
    try:
        from services import data_loader
    finally:
        sys.path.remove(str(APP_DIR))
    for name in data_loader.REQUIRED_FILES:
        shutil.copy(data_loader.EXPORT_DIR / f"{name}.parquet", tmp_path)
    monkeypatch.setattr(data_loader, "EXPORT_DIR", tmp_path)

    before = len(data_loader.load_quality())
    import pandas as pd
    path = tmp_path / "quality_results.parquet"
    pd.read_parquet(path).head(3).to_parquet(path, index=False)
    os.utime(path, ns=(path.stat().st_atime_ns, path.stat().st_mtime_ns + 10**9))
    assert before > 3
    assert len(data_loader.load_quality()) == 3  # đọc lại file mới, không trả bản cache cũ

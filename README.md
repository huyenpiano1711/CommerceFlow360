# CommerceFlow 360

## Mục tiêu

CommerceFlow 360 là đồ án môn **Nhà kho dữ liệu và Tích hợp**, xây dựng kho dữ liệu tích hợp để phân tích hiệu quả kinh doanh, vận hành đơn hàng và hành vi khách hàng trong thương mại điện tử. Kiến trúc Medallion:

`Olist CSV + Brazil Holidays → Bronze → Silver → Gold (Star Schema) → Data Mart → Parquet → Streamlit`

Đã hoàn thành: A01–A02 (repository, dữ liệu nguồn), B01 (Bronze), C01–C03 (Silver + dbt test), D02–D04 (Gold + kiểm thử), E01–E05 (Data Mart, phân tích KPI, xuất Parquet), F01–F04 (dashboard Streamlit). B02 (EDA) thực hiện bằng `src/reporting/eda_report.py`. Còn lại: G01 (notebook chạy toàn bộ pipeline).

**Hướng dẫn chạy chi tiết, số liệu đối soát và quy tắc nghiệp vụ: xem [AGENTS.md](AGENTS.md).**

## Nguồn dữ liệu

- Tên: **Brazilian E-Commerce Public Dataset by Olist**, đơn vị công bố: **Olist**.
- Nguồn: [Kaggle – Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
- Phạm vi: các đơn hàng 2016–2018 tại Brazil; dùng 9 CSV Olist nguyên bản trong `data/raw/`.
- Ngày kiểm tra nguồn: **2026-10-27**.
- Giấy phép: **chưa xác minh độc lập**. Kiểm tra mục License trên trang Kaggle trước khi phân phối lại hoặc dùng ngoài phạm vi học tập.

Ngày lễ quốc gia Brazil 2016–2018 được sinh bằng thư viện Python `holidays`; phiên bản thư viện ghi trong `data/reference/holidays_brazil_metadata.json`.

## Công nghệ

Python, Pandas, DuckDB, dbt Core (`dbt-duckdb`), PyArrow, Matplotlib, `holidays`, KaggleHub, Streamlit, Plotly, pytest; chạy được trên máy cá nhân và Google Colab.

## Cấu trúc repository

```text
CommerceFlow360/
├── .streamlit/config.toml  # Theme cố định của dashboard
├── analytics/sql/          # 10 truy vấn KPI analysis_<mart>_<nội dung>.sql (E04)
├── app/                    # Dashboard Streamlit F01–F04 (Home.py, pages/, services/, components/)
├── data/
│   ├── raw/                # 9 CSV Olist (CHỈ ĐỌC) + holidays_brazil.csv (sinh bởi src/ingestion)
│   ├── reference/          # Metadata nguồn ngày lễ
│   ├── profiling/          # Báo cáo kiểm tra dữ liệu nguồn (A02)
│   └── exports/            # mart_*.parquet, quality_results.parquet (đầu vào dashboard)
├── dbt_project/            # Silver → Gold → Mart + test (xem dbt_project/README.md)
├── docs/                   # Star Schema, bus matrix, kết quả kiểm thử
├── notebooks/              # 01–06: minh chứng từng task, chạy local hoặc Colab
├── reports/                # tables/, figures/ cho báo cáo
├── scripts/                # 3 lệnh chạy pipeline (gọi hàm trong src/)
├── src/
│   ├── ingestion/          # Sinh ngày lễ, nạp Bronze
│   ├── validation/         # Profiling dữ liệu nguồn
│   ├── reporting/          # Xuất Parquet, bảng/hình báo cáo
│   └── utils/              # Đường dẫn, chạy dbt, truy vấn DuckDB dùng chung
├── tests/                  # pytest: đầu ra A02, nạp Bronze, profiling, đọc kết quả dbt
├── requirements.txt
└── AGENTS.md               # Hướng dẫn chạy pipeline
```

## Chạy nhanh (Windows PowerShell)

```powershell
git clone https://github.com/huyenpiano1711/CommerceFlow360.git
cd CommerceFlow360
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt ipykernel
New-Item -ItemType Directory -Force "$env:USERPROFILE\.dbt" | Out-Null
Copy-Item dbt_project\profiles.yml.example "$env:USERPROFILE\.dbt\profiles.yml"

python scripts\load_bronze.py        # B01: 10 bảng bronze_*
python scripts\export_parquet.py     # C–E05: dbt build toàn bộ + xuất Parquet
python scripts\run_e04_analytics.py  # E04: bảng/hình Chương 4
streamlit run app/Home.py            # F01–F04: dashboard
pytest                               # kiểm thử Python (tests/)
python -m src.reporting.eda_report     # B02: bảng/hình Chương 2 (Bang_2.x, Hinh_2.x)
```

Trên Colab hoặc Linux/macOS, xem mục 4 của [AGENTS.md](AGENTS.md). Colab có phiên làm việc tạm thời: file DuckDB có thể mất khi runtime kết thúc, nên tải về hoặc sao lưu (notebook 02 có tùy chọn sao lưu lên Drive).
Dashboard đọc các file Parquet trong `data/exports/`; nếu thiếu, chạy `scripts/export_parquet.py` trước.

## Lấy dữ liệu Olist

Repository đã lưu 9 CSV Olist trong `data/raw/`. Nếu thiếu file, notebook `01_Data_Source_Setup.ipynb` có cell tùy chọn dùng `kagglehub` để tải và chỉ sao chép file còn thiếu. Dùng Kaggle credentials qua biến môi trường hoặc Colab Secrets, không hardcode khóa.

## Quy tắc làm việc với GitHub

- Tạo branch theo task; không push trực tiếp lên `main`, mở pull request để review.
- Commit message theo mẫu `[CODE] <nội dung>` hoặc `[BÁO CÁO] <nội dung>`.
- Không commit `.env`, token, virtual environment, cache, log, `commerceflow.duckdb`, `dbt_project/target/`.
- Không chỉnh sửa 9 CSV gốc trong `data/raw/`. Dữ liệu dẫn xuất nằm ngoài `data/raw/` (trừ file ngày lễ được sinh có kiểm soát).

## Lưu ý kích thước dữ liệu

`olist_geolocation_dataset.csv` khoảng 59 MiB: thấp hơn giới hạn cứng 100 MiB/file của GitHub nhưng cao hơn mức 50 MiB GitHub khuyến nghị. Repository chưa dùng Git LFS.
